"""旅行规划：地图数据查询与 Agent 编排。"""

import json
import logging
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor
from hello_agents import SimpleAgent
from ..services.llm_service import get_llm
from ..services.amap_service import get_amap_service
from ..models.schemas import TripRequest, TripPlan, Budget

# ============ Agent提示词 ============

PLANNER_AGENT_PROMPT = """你是行程规划专家。你的任务是根据景点信息和天气信息,生成详细的旅行计划。

请严格按照以下JSON格式返回旅行计划:
```json
{
  "city": "城市名称",
  "start_date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD",
  "days": [
    {
      "date": "YYYY-MM-DD",
      "day_index": 0,
      "description": "第1天行程概述",
      "transportation": "交通方式",
      "accommodation": "住宿类型",
      "hotel": {
        "name": "酒店名称",
        "address": "酒店地址",
        "location": {"longitude": 116.397128, "latitude": 39.916527},
        "price_range": "300-500元",
        "rating": "4.5",
        "distance": "距离景点2公里",
        "type": "经济型酒店",
        "estimated_cost": 400
      },
      "attractions": [
        {
          "name": "景点名称",
          "address": "详细地址",
          "location": {"longitude": 116.397128, "latitude": 39.916527},
          "visit_duration": 120,
          "description": "景点详细描述",
          "category": "景点类别",
          "ticket_price": 60
        }
      ],
      "meals": [
        {"type": "breakfast", "name": "早餐推荐", "description": "早餐描述", "estimated_cost": 30},
        {"type": "lunch", "name": "午餐推荐", "description": "午餐描述", "estimated_cost": 50},
        {"type": "dinner", "name": "晚餐推荐", "description": "晚餐描述", "estimated_cost": 80}
      ]
    }
  ],
  "weather_info": [
    {
      "date": "YYYY-MM-DD",
      "day_weather": "晴",
      "night_weather": "多云",
      "day_temp": 25,
      "night_temp": 15,
      "wind_direction": "南风",
      "wind_power": "1-3级"
    }
  ],
  "overall_suggestions": "总体建议",
  "budget": {
    "total_attractions": 180,
    "total_hotels": 1200,
    "total_meals": 480,
    "total_transportation": 200,
    "total": 2060
  }
}
```

**重要提示:**
1. weather_info只包含天气查询结果中已有的日期，不得编造天气
2. 温度必须是纯数字(不要带°C等单位)
3. 每天安排2-3个景点
4. 考虑景点之间的距离和游览时间
5. 每天必须包含早中晚三餐
6. 提供实用的旅行建议
7. **必须包含预算信息**:
   - 景点门票价格(ticket_price)
   - 餐饮预估费用(estimated_cost)
   - 酒店预估费用(estimated_cost)
   - 预算汇总(budget)包含各项总费用
"""


class MultiAgentTripPlanner:
    """旅行规划：地图数据查询与 Agent 编排。"""

    def __init__(self):
        self.map_service = get_amap_service()
        self.llm = get_llm()
        self.planner_agent = SimpleAgent(name="行程规划专家", llm=self.llm,
                                         system_prompt=PLANNER_AGENT_PROMPT)

    def plan_trip(self, request: TripRequest) -> TripPlan:
        # 三项查询彼此独立，分别使用 MCP 连接。
        with ThreadPoolExecutor(max_workers=3) as pool:
            attractions_future = pool.submit(self.map_service.search_poi,
                                             request.preferences[0] if request.preferences else "景点", request.city)
            weather_future = pool.submit(self.map_service.get_weather, request.city)
            hotels_future = pool.submit(self.map_service.search_poi, request.accommodation, request.city)
            attractions = attractions_future.result()
            optional_results = []
            warnings = []
            for label, future in (("天气", weather_future), ("酒店", hotels_future)):
                try:
                    optional_results.append(future.result())
                except Exception as exc:
                    logging.getLogger(__name__).warning("%s查询失败: %s", label, exc)
                    warnings.append(f"{label}查询失败，相关信息暂不可用")
                    optional_results.append([])
            weather, hotels = optional_results
        if not attractions:
            raise RuntimeError("没有查询到可定位的景点，请调整目的地或偏好后重试")

        query = self._build_planner_query(
            request,
            json.dumps([poi.model_dump() for poi in attractions], ensure_ascii=False),
            json.dumps([item.model_dump() for item in weather], ensure_ascii=False),
            json.dumps([poi.model_dump() for poi in hotels], ensure_ascii=False),
        )
        self.planner_agent.clear_history()
        result = self._parse_response(self.planner_agent.run(query), request)
        candidates = {poi.name: poi for poi in attractions}
        for day in result.days:
            for attraction in day.attractions:
                if attraction.name not in candidates:
                    raise RuntimeError(f"规划包含未查询到的景点：{attraction.name}")
                poi = candidates[attraction.name]
                attraction.location = poi.location
                attraction.address = poi.address
                attraction.poi_id = poi.id
        hotel_candidates = {poi.name: poi for poi in hotels}
        for day in result.days:
            if day.hotel and day.hotel.name in hotel_candidates:
                hotel = hotel_candidates[day.hotel.name]
                day.hotel.location, day.hotel.address = hotel.location, hotel.address
            elif day.hotel:
                day.hotel = None
        # 天气只使用工具返回的预报，绝不采纳模型生成的天气。
        result.weather_info = [item for item in weather if request.start_date <= item.date <= request.end_date]
        result.traveler_count = request.traveler_count
        result.budget_limit = request.budget_limit
        result.daily_hours = request.daily_hours
        result.warnings = warnings
        self._update_budget(result)
        return result

    def replan_day(self, plan: TripPlan, day_index: int, instruction: str) -> TripPlan:
        day = plan.days[day_index]
        candidates = self.map_service.search_poi(instruction, plan.city)
        if not candidates:
            raise RuntimeError("没有找到符合修改要求的景点，请换一个描述重试")
        request = TripRequest(city=plan.city, start_date=day.date, end_date=day.date, travel_days=1,
                              transportation=day.transportation, accommodation=day.accommodation,
                              free_text_input=instruction, traveler_count=plan.traveler_count,
                              budget_limit=plan.budget_limit, daily_hours=plan.daily_hours)
        query = self._build_planner_query(request, json.dumps([p.model_dump() for p in candidates], ensure_ascii=False),
                                          json.dumps([w.model_dump() for w in plan.weather_info if w.date == day.date], ensure_ascii=False),
                                          json.dumps(day.hotel.model_dump() if day.hotel else None, ensure_ascii=False))
        self.planner_agent.clear_history()
        revised = self._parse_response(self.planner_agent.run(query), request).days[0]
        by_name = {poi.name: poi for poi in candidates}
        for attraction in revised.attractions:
            if attraction.name not in by_name:
                raise RuntimeError(f"修改结果包含未查询到的景点：{attraction.name}")
            poi = by_name[attraction.name]
            attraction.location, attraction.address, attraction.poi_id = poi.location, poi.address, poi.id
        revised.day_index, revised.hotel = day_index, day.hotel
        updated = plan.model_copy(deep=True)
        updated.days[day_index] = revised
        self._update_budget(updated)
        return updated

    @staticmethod
    def _update_budget(trip_plan: TripPlan):
        attractions = sum(a.ticket_price for day in trip_plan.days for a in day.attractions)
        hotels = sum(day.hotel.estimated_cost for day in trip_plan.days if day.hotel)
        meals = sum(meal.estimated_cost for day in trip_plan.days for meal in day.meals)
        transportation = trip_plan.budget.total_transportation if trip_plan.budget else 0
        trip_plan.budget = Budget(total_attractions=attractions, total_hotels=hotels,
                                 total_meals=meals, total_transportation=transportation,
                                 total=attractions + hotels + meals + transportation)
        budget_warning = "估算费用超过预算上限，请调整行程或预算"
        time_warning = "部分日期的景点游览时间已超过每日活动时间，尚未计入交通与休息"
        trip_plan.warnings = [warning for warning in trip_plan.warnings if warning not in (budget_warning, time_warning)]
        if trip_plan.budget_limit and trip_plan.budget.total > trip_plan.budget_limit:
            trip_plan.warnings.append(budget_warning)
        if any(sum(a.visit_duration for a in day.attractions) > trip_plan.daily_hours * 60 for day in trip_plan.days):
            trip_plan.warnings.append(time_warning)

    def _build_planner_query(self, request: TripRequest, attractions: str, weather: str, hotels: str = "") -> str:
        """构建行程规划查询"""
        query = f"""请根据以下信息生成{request.city}的{request.travel_days}天旅行计划:

**基本信息:**
- 城市: {request.city}
- 日期: {request.start_date} 至 {request.end_date}
- 天数: {request.travel_days}天
- 交通方式: {request.transportation}
- 住宿: {request.accommodation}
- 偏好: {', '.join(request.preferences) if request.preferences else '无'}
- 同行人数: {request.traveler_count}人
- 全程预算上限: {str(request.budget_limit) + '元' if request.budget_limit else '未设定'}
- 每日活动时间上限: {request.daily_hours}小时

**景点信息:**
{attractions}

**天气信息（仅供参考，最终天气由程序填入）:**
{weather}

**酒店信息:**
{hotels}

**要求:**
1. 每天安排2-3个景点
2. 每天必须包含早中晚三餐
3. 酒店只能从提供的候选酒店中选择，名称完全一致；没有候选时设为null
3. 考虑景点之间的距离和交通方式
4. 预算为所有同行人员的全程估算，结合人数和预算上限；每天游览及交通总时长尽量不超过每日活动时间上限
5. 返回完整的JSON格式数据
5. 景点名称必须与提供的候选景点名称完全一致，不得编造景点
6. 如候选景点不足，可跨天重复，但每一天至少安排一个候选景点
"""
        if request.free_text_input:
            query += f"\n**额外要求:** {request.free_text_input}"

        return query
    
    def _parse_response(self, response: str, request: TripRequest) -> TripPlan:
        """
        解析Agent响应
        
        Args:
            response: Agent响应文本
            request: 原始请求
            
        Returns:
            旅行计划
        """
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            json_str = response[json_start:json_end].strip()
        elif "```" in response:
            json_start = response.find("```") + 3
            json_end = response.find("```", json_start)
            json_str = response[json_start:json_end].strip()
        elif "{" in response and "}" in response:
            json_str = response[response.find("{"):response.rfind("}") + 1]
        else:
            raise ValueError("模型响应中未找到 JSON 数据")

        trip_plan = TripPlan.model_validate_json(json_str)
        start = date.fromisoformat(request.start_date)
        if (trip_plan.city != request.city or trip_plan.start_date != request.start_date
                or trip_plan.end_date != request.end_date or len(trip_plan.days) != request.travel_days):
            raise ValueError("生成的目的地或日期与请求不一致")
        for index, day in enumerate(trip_plan.days):
            if day.day_index != index or day.date != (start + timedelta(days=index)).isoformat():
                raise ValueError("生成的每日行程日期或顺序不正确")
            if not day.attractions:
                raise ValueError("每日行程至少需要一个景点")

        self._update_budget(trip_plan)
        return trip_plan


# 全局旅行规划器实例
_multi_agent_planner = None


def get_trip_planner_agent() -> MultiAgentTripPlanner:
    """获取旅行规划器实例。"""
    global _multi_agent_planner

    if _multi_agent_planner is None:
        _multi_agent_planner = MultiAgentTripPlanner()

    return _multi_agent_planner

