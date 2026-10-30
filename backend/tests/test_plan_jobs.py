import threading
import time
import unittest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.api.main import app
from app.models.schemas import TripPlan
from test_planning import plan, request


class PlanJobTests(unittest.TestCase):
    def test_long_plan_returns_job_immediately_and_can_be_polled(self):
        release = threading.Event()
        planner = Mock()
        planner.plan_trip.side_effect = lambda _: (release.wait(2), TripPlan(**plan()))[1]
        client = TestClient(app)
        try:
            with patch('app.api.routes.trip.get_trip_planner_agent', return_value=planner):
                response = client.post('/api/trip/plan/jobs', json=request().model_dump())
                self.assertEqual(response.status_code, 202)
                job_url = '/api/trip/plan/jobs/' + response.json()['id']
                self.assertEqual(client.get(job_url).json()['status'], 'pending')
                release.set()
                for _ in range(50):
                    result = client.get(job_url)
                    if result.json()['status'] != 'pending':
                        break
                    time.sleep(.02)
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.json()['status'], 'completed')
                self.assertEqual(result.json()['result']['data']['city'], '北京')
        finally:
            release.set()

    def test_unknown_job_returns_404(self):
        self.assertEqual(TestClient(app).get('/api/trip/plan/jobs/no-such-job').status_code, 404)


if __name__ == '__main__':
    unittest.main()
