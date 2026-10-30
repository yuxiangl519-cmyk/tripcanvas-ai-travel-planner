"""高德地图MCP服务封装"""

import json
import logging
import requests
from typing import List, Dict, Any, Optional
from hello_agents.tools import MCPTool
from ..config import get_settings
from ..models.schemas import Location, POIInfo, WeatherInfo

# 全局MCP工具实例
_amap_mcp_tool = None


def get_amap_mcp_tool() -> MCPTool:
    """
    获取高德地图MCP工具实例(单例模式)
    
    Returns:
        MCPTool实例
    """
    global _amap_mcp_tool
    
    if _amap_mcp_tool is None:
        settings = get_settings()
        
        if not settings.amap_api_key:
            raise ValueError("高德地图API Key未配置,请在.env文件中设置AMAP_API_KEY")
        
        # 创建MCP工具
        _amap_mcp_tool = MCPTool(
            name="amap",
            description="高德地图服务,支持POI搜索、路线规划、天气查询等功能",
            # amap-mcp-server 0.1.11 固定 mcp 1.8.1，需要兼容的 Pydantic。
            server_command=["uvx", "--with", "pydantic==2.10.6", "amap-mcp-server==0.1.11"],
            env={"AMAP_MAPS_API_KEY": settings.amap_api_key},
            auto_expand=True  # 自动展开为独立工具
        )
        
        if not _amap_mcp_tool._available_tools:
            _amap_mcp_tool = None
            raise RuntimeError("高德 MCP 未加载任何工具，请检查 MCP 子进程的启动日志")

        print(f"✅ 高德地图MCP工具初始化成功")
        print(f"   工具数量: {len(_amap_mcp_tool._available_tools)}")
        
        # 打印可用工具列表
        if _amap_mcp_tool._available_tools:
            print("   可用工具:")
            for tool in _amap_mcp_tool._available_tools[:5]:  # 只打印前5个
                print(f"     - {tool.get('name', 'unknown')}")
            if len(_amap_mcp_tool._available_tools) > 5:
                print(f"     ... 还有 {len(_amap_mcp_tool._available_tools) - 5} 个工具")
    
    return _amap_mcp_tool


class AmapService:
    """将 MCP 返回值转换为应用的数据模型。"""

    def __init__(self):
        self.mcp_tool = get_amap_mcp_tool()

    def _call(self, tool_name: str, arguments: dict) -> dict:
        result = self.mcp_tool.run({"action": "call_tool", "tool_name": tool_name, "arguments": arguments})
        # HelloAgents MCPTool 在 JSON 前加一行说明。
        start = result.find("{")
        if start < 0:
            raise RuntimeError(f"高德工具 {tool_name} 调用失败: {result}")
        data = json.loads(result[start:])
        if "error" in data:
            raise RuntimeError(f"高德工具 {tool_name} 调用失败: {data['error']}")
        return data

    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[POIInfo]:
        data = self._call("maps_text_search", {"keywords": keywords, "city": city,
                                              "citylimit": str(citylimit).lower()})
        pois = []
        # 服务的搜索结果不含坐标，因此对候选项单独地理编码。
        for poi in data["pois"][:10]:
            try:
                location = self.geocode(poi["name"], city)
            except RuntimeError as exc:
                logging.getLogger(__name__).warning("景点定位失败 %s: %s", poi["name"], exc)
                continue
            if location is not None:
                pois.append(POIInfo(id=poi["id"], name=poi["name"],
                                    type=poi.get("typecode") or "", address=poi.get("address") or "",
                                    location=location))
        return pois

    def get_weather(self, city: str) -> List[WeatherInfo]:
        data = self._call("maps_weather", {"city": city})
        return [WeatherInfo(date=item["date"], day_weather=item["dayweather"],
                            night_weather=item["nightweather"], day_temp=item["daytemp"],
                            night_temp=item["nighttemp"], wind_direction=item["daywind"],
                            wind_power=item["daypower"]) for item in data["forecasts"]]

    def plan_route(self, origin_address: str, destination_address: str,
                   origin_city: Optional[str] = None, destination_city: Optional[str] = None,
                   route_type: str = "walking") -> Dict[str, Any]:
        if route_type == "transit":
            # MCP 0.1.11 的公交工具会向协议 stdout 打印内容，因此直接调用高德 Web 服务。
            origin = self.geocode(origin_address, origin_city)
            destination = self.geocode(destination_address, destination_city)
            if origin is None or destination is None:
                raise RuntimeError("无法定位起点或终点")
            try:
                response = requests.get("https://restapi.amap.com/v3/direction/transit/integrated", params={
                    "key": get_settings().amap_api_key,
                    "origin": f"{origin.longitude},{origin.latitude}",
                    "destination": f"{destination.longitude},{destination.latitude}",
                    "city": origin_city, "cityd": destination_city or origin_city,
                }, timeout=15)
                response.raise_for_status()
            except requests.RequestException:
                raise RuntimeError("公交路线服务连接失败，请稍后重试") from None
            data = response.json()
            if data.get("status") != "1":
                raise RuntimeError(f"公交路线查询失败: {data.get('info')}")
            route = data["route"]
            if not route["transits"]:
                raise RuntimeError("未找到公交路线")
            option = route["transits"][0]
            distance = route["distance"]
            description = "公共交通，详情请以地图导航为准"
        else:
            tool_map = {"walking": "maps_direction_walking_by_address",
                        "driving": "maps_direction_driving_by_address"}
            arguments = {"origin_address": origin_address, "destination_address": destination_address}
            if origin_city:
                arguments["origin_city"] = origin_city
            if destination_city:
                arguments["destination_city"] = destination_city
            route = self._call(tool_map[route_type], arguments)["route"]
            option = route["paths"][0]
            distance = option["distance"]
            description = "；".join(step["instruction"] for step in option["steps"] if step.get("instruction"))
        return {"distance": float(distance), "duration": int(option["duration"]),
                "route_type": route_type, "description": description}

    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        arguments = {"address": address}
        if city:
            arguments["city"] = city
        results = self._call("maps_geo", arguments)["return"]
        if not results:
            return None
        longitude, latitude = results[0]["location"].split(",")
        return Location(longitude=float(longitude), latitude=float(latitude))

    def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        return self._call("maps_search_detail", {"id": poi_id})


# 创建全局服务实例
_amap_service = None


def get_amap_service() -> AmapService:
    """获取高德地图服务实例(单例模式)"""
    global _amap_service
    
    if _amap_service is None:
        _amap_service = AmapService()
    
    return _amap_service

