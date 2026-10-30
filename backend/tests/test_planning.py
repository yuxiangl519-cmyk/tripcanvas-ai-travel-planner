import json
import unittest
from unittest.mock import Mock, patch
from pydantic import ValidationError
from app.models.schemas import TripRequest, TripPlan
from app.services.amap_service import AmapService
from app.agents.trip_planner_agent import MultiAgentTripPlanner


def request(**changes):
    values = dict(city='北京', start_date='2026-11-01', end_date='2026-11-02', travel_days=2,
                  transportation='步行', accommodation='酒店', preferences=[])
    values.update(changes)
    return TripRequest(**values)


def plan():
    return {'city': '北京', 'start_date': '2026-11-01', 'end_date': '2026-11-02',
            'days': [{'date': f'2026-11-0{i+1}', 'day_index': i, 'description': '行程',
                      'transportation': '步行', 'accommodation': '酒店',
                      'attractions': [{'name': f'景点{i}', 'address': '地址',
                                       'location': {'longitude': 116.4, 'latitude': 39.9},
                                       'visit_duration': 120, 'description': '介绍', 'ticket_price': 30}],
                      'hotel': {'name': '酒店', 'estimated_cost': 100},
                      'meals': [{'type': 'lunch', 'name': '午餐', 'estimated_cost': 20}]} for i in range(2)],
            'overall_suggestions': '建议',
            'budget': {'total_attractions': 1, 'total_hotels': 1, 'total_meals': 1, 'total_transportation': 10, 'total': 999}}


class PlanningTests(unittest.TestCase):
    def test_date_range_must_match_days(self):
        with self.assertRaises(ValidationError):
            request(travel_days=1)
        with self.assertRaises(ValidationError):
            request(start_date='invalid')

    def test_travel_constraints_are_validated_and_sent_to_planner(self):
        with self.assertRaises(ValidationError):
            request(traveler_count=0)
        with self.assertRaises(ValidationError):
            request(daily_hours=25)
        req = request(traveler_count=3, budget_limit=6000, daily_hours=6)
        planner = MultiAgentTripPlanner.__new__(MultiAgentTripPlanner)
        query = planner._build_planner_query(req, '景点', '天气', '酒店')
        self.assertIn('3人', query)
        self.assertIn('6000元', query)
        self.assertIn('6小时', query)

    def test_budget_is_recomputed_and_wrong_dates_rejected(self):
        planner = MultiAgentTripPlanner.__new__(MultiAgentTripPlanner)
        result = planner._parse_response(json.dumps(plan()), request())
        self.assertEqual(result.budget.total, 310)
        bad = plan()
        bad['days'][1]['date'] = '2026-11-05'
        with self.assertRaises(ValueError):
            planner._parse_response(json.dumps(bad), request())

    def test_invalid_model_output_is_not_replaced_by_fake_plan(self):
        planner = MultiAgentTripPlanner.__new__(MultiAgentTripPlanner)
        with self.assertRaises(ValueError):
            planner._parse_response('没有 JSON', request())

    def test_search_weather_and_route_parse_mcp_results(self):
        service = AmapService.__new__(AmapService)
        results = [
            {'pois': [{'id': '1', 'name': '故宫', 'address': '北京', 'typecode': '110000'}]},
            {'return': [{'location': '116.4,39.9'}]},
            {'forecasts': [{'date': '2026-11-01', 'dayweather': '晴', 'nightweather': '阴', 'daytemp': '20', 'nighttemp': '10', 'daywind': '东', 'daypower': '3'}]},
            {'route': {'paths': [{'distance': '1000', 'duration': '600', 'steps': [{'instruction': '向东走'}]}]}}
        ]
        service.mcp_tool = Mock()
        service.mcp_tool.run.side_effect = ['工具执行结果:\n' + json.dumps(r) for r in results]
        self.assertEqual(service.search_poi('故宫', '北京')[0].location.longitude, 116.4)
        self.assertEqual(service.get_weather('北京')[0].day_temp, 20)
        self.assertEqual(service.plan_route('起点', '终点')['duration'], 600)

    def test_planner_uses_verified_coordinates_and_forecast(self):
        planner = MultiAgentTripPlanner.__new__(MultiAgentTripPlanner)
        planner.map_service = Mock()
        from app.models.schemas import POIInfo, Location, WeatherInfo
        poi = POIInfo(id='1', name='景点0', address='真实地址', type='景点',
                      location=Location(longitude=120, latitude=30))
        poi2 = POIInfo(id='2', name='景点1', address='真实地址2', type='景点',
                       location=Location(longitude=121, latitude=31))
        planner.map_service.search_poi.side_effect = lambda keywords, city: [poi, poi2] if keywords == "景点" else [poi]
        planner.map_service.get_weather.return_value = [WeatherInfo(date='2026-11-01', day_weather='晴')]
        planner.planner_agent = Mock()
        invented = plan()
        invented['weather_info'] = [{'date': '2026-11-02', 'day_weather': '雨'}]
        planner.planner_agent.run.return_value = json.dumps(invented)
        result = planner.plan_trip(request())
        self.assertEqual(result.days[0].attractions[0].location.longitude, 120)
        self.assertEqual([w.date for w in result.weather_info], ['2026-11-01'])
        self.assertEqual(result.days[0].attractions[0].poi_id, '1')

    def test_weather_and_hotel_failure_produces_partial_plan_with_warning(self):
        planner = MultiAgentTripPlanner.__new__(MultiAgentTripPlanner)
        planner.map_service = Mock()
        from app.models.schemas import POIInfo, Location
        candidates = [POIInfo(id=str(i), name=f'景点{i}', address='地址', type='景点',
                              location=Location(longitude=116.4, latitude=39.9)) for i in range(2)]
        planner.map_service.search_poi.side_effect = lambda keywords, city: candidates if keywords == '景点' else (_ for _ in ()).throw(RuntimeError('hotel down'))
        planner.map_service.get_weather.side_effect = RuntimeError('weather down')
        planner.planner_agent = Mock()
        planner.planner_agent.run.return_value = json.dumps(plan())
        result = planner.plan_trip(request())
        self.assertEqual(result.weather_info, [])
        self.assertIsNone(result.days[0].hotel)
        self.assertEqual(len(result.warnings), 2)

    def test_planner_rejects_attractions_outside_search_results(self):
        planner = MultiAgentTripPlanner.__new__(MultiAgentTripPlanner)
        planner.map_service = Mock()
        planner.map_service.search_poi.return_value = []
        planner.map_service.get_weather.return_value = []
        planner.planner_agent = Mock()
        planner.planner_agent.run.return_value = json.dumps(plan())
        with self.assertRaises(RuntimeError):
            planner.plan_trip(request())

    def test_replan_changes_only_requested_day_and_preserves_hotel(self):
        planner = MultiAgentTripPlanner.__new__(MultiAgentTripPlanner)
        planner.map_service = Mock()
        from app.models.schemas import POIInfo, Location
        candidate = POIInfo(id='3', name='博物馆', address='博物馆地址', type='景点',
                            location=Location(longitude=120, latitude=30))
        planner.map_service.search_poi.return_value = [candidate]
        changed = plan()
        changed['days'] = [changed['days'][1]]
        changed['days'][0]['day_index'] = 0
        changed['days'][0]['attractions'][0]['name'] = '博物馆'
        changed['days'][0]['hotel']['name'] = '模型替换的酒店'
        changed['start_date'] = changed['end_date'] = '2026-11-02'
        planner.planner_agent = Mock()
        planner.planner_agent.run.return_value = json.dumps(changed)
        original = TripPlan(**plan(), budget_limit=100)
        updated = planner.replan_day(original, 1, '改成博物馆')
        self.assertEqual(updated.days[0], original.days[0])
        self.assertEqual(updated.days[1].hotel, original.days[1].hotel)
        self.assertEqual(updated.days[1].attractions[0].poi_id, '3')
        self.assertEqual(updated.days[1].day_index, 1)
        self.assertEqual(updated.budget.total, 310)
        self.assertTrue(any('预算' in warning for warning in updated.warnings))

    def test_budget_and_duration_warnings_reflect_constraints(self):
        planner = MultiAgentTripPlanner.__new__(MultiAgentTripPlanner)
        planner.map_service = Mock()
        from app.models.schemas import POIInfo, Location
        pois = [POIInfo(id=str(i), name=f'景点{i}', address='地址', type='景点',
                        location=Location(longitude=116.4, latitude=39.9)) for i in range(2)]
        planner.map_service.search_poi.return_value = pois
        planner.map_service.get_weather.return_value = []
        data = plan()
        data['days'][0]['attractions'][0]['visit_duration'] = 300
        planner.planner_agent = Mock()
        planner.planner_agent.run.return_value = json.dumps(data)
        result = planner.plan_trip(request(budget_limit=100, daily_hours=4))
        self.assertEqual(result.daily_hours, 4)
        self.assertTrue(any('预算' in warning for warning in result.warnings))
        self.assertTrue(any('时间' in warning for warning in result.warnings))

    def test_api_rejects_bad_dates_and_reports_planner_failure(self):
        from fastapi.testclient import TestClient
        from app.api.main import app
        client = TestClient(app)
        bad_request = request().model_dump()
        bad_request['travel_days'] = 1
        self.assertEqual(client.post('/api/trip/plan', json=bad_request).status_code, 422)
        with patch('app.api.routes.trip.get_trip_planner_agent') as get_planner:
            get_planner.return_value.plan_trip.side_effect = RuntimeError('地图不可用')
            response = client.post('/api/trip/plan', json=request().model_dump())
        self.assertEqual(response.status_code, 502)
        self.assertIn('地图不可用', response.json()['detail'])

    def test_health_uses_current_planner_structure(self):
        from fastapi.testclient import TestClient
        from app.api.main import app
        client = TestClient(app)
        with patch('app.api.routes.trip.get_trip_planner_agent') as get_planner:
            get_planner.return_value.planner_agent.name = '规划专家'
            get_planner.return_value.map_service.mcp_tool._available_tools = [{}, {}]
            response = client.get('/api/trip/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['tools_count'], 2)

    def test_one_failed_geocode_does_not_discard_other_candidates(self):
        service = AmapService.__new__(AmapService)
        service.mcp_tool = Mock()
        service.mcp_tool.run.side_effect = [
            'result:\n' + json.dumps({'pois': [
                {'id': '1', 'name': '失效酒店', 'address': '地址', 'typecode': '酒店'},
                {'id': '2', 'name': '可用酒店', 'address': '地址', 'typecode': '酒店'}]}),
            'result:\n' + json.dumps({'error': 'ENGINE_RESPONSE_DATA_ERROR'}),
            'result:\n' + json.dumps({'return': [{'location': '116.4,39.9'}]})
        ]
        self.assertEqual([poi.id for poi in service.search_poi('酒店', '北京')], ['2'])

    def test_transit_uses_direct_route_response_after_geocoding(self):
        from app.models.schemas import Location
        service = AmapService.__new__(AmapService)
        service.geocode = Mock(side_effect=[Location(longitude=116.4, latitude=39.9), Location(longitude=116.5, latitude=39.95)])
        response = Mock()
        response.json.return_value = {'status': '1', 'route': {'distance': '2000', 'transits': [{'duration': '900'}]}}
        with patch('app.services.amap_service.requests.get', return_value=response) as get:
            result = service.plan_route('起点', '终点', '北京', '北京', 'transit')
        self.assertEqual(result['duration'], 900)
        self.assertEqual(result['distance'], 2000)
        self.assertEqual(get.call_args.kwargs['params']['origin'], '116.4,39.9')

    def test_transit_network_error_does_not_expose_query_parameters(self):
        import requests
        from app.models.schemas import Location
        service = AmapService.__new__(AmapService)
        service.geocode = Mock(return_value=Location(longitude=116.4, latitude=39.9))
        with patch('app.services.amap_service.requests.get', side_effect=requests.RequestException('key=secret')):
            with self.assertRaises(RuntimeError) as error:
                service.plan_route('起点', '终点', '北京', '北京', 'transit')
        self.assertNotIn('secret', str(error.exception))

    def test_map_error_propagates(self):
        service = AmapService.__new__(AmapService)
        service.mcp_tool = Mock()
        service.mcp_tool.run.return_value = '工具执行结果:\n{"error":"invalid key"}'
        with self.assertRaises(RuntimeError):
            service.get_weather('北京')


if __name__ == '__main__':
    unittest.main()
