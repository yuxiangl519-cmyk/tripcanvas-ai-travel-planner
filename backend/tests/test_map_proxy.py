import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from app.api.main import app, settings


class MapProxyTests(unittest.TestCase):
    def test_proxy_sends_security_code_only_to_amap(self):
        upstream = MagicMock(status_code=200, content=b'{"status":"1"}', headers={"content-type": "application/json"})
        client = AsyncMock()
        client.get.return_value = upstream
        manager = AsyncMock()
        manager.__aenter__.return_value = client
        with patch.object(settings, "amap_security_js_code", "test-private-code"), \
             patch("app.api.main.httpx.AsyncClient", return_value=manager):
            response = TestClient(app).get("/_AMapService/v3/ip?key=public-key")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("test-private-code", response.text)
        upstream_url = client.get.call_args.args[0]
        self.assertEqual(upstream_url.host, "restapi.amap.com")
        self.assertIn(("jscode", "test-private-code"), client.get.call_args.kwargs["params"])


if __name__ == "__main__":
    unittest.main()
