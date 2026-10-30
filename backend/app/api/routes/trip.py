"""旅行规划API路由"""

from fastapi import APIRouter, HTTPException
from threading import Lock
import logging
from ...models.schemas import (
    TripRequest,
    TripPlanResponse,
    ReplanDayRequest,
    ErrorResponse
)
from ...agents.trip_planner_agent import get_trip_planner_agent

router = APIRouter(prefix="/trip", tags=["旅行规划"])
planner_lock = Lock()
logger = logging.getLogger(__name__)


@router.post(
    "/plan",
    response_model=TripPlanResponse,
    summary="生成旅行计划",
    description="根据用户输入的旅行需求,生成详细的旅行计划"
)
def plan_trip(request: TripRequest):
    try:
        # 复用的 Agent 带有状态，避免并发请求混用上下文。
        with planner_lock:
            trip_plan = get_trip_planner_agent().plan_trip(request)
        return TripPlanResponse(success=True, message="旅行计划生成成功", data=trip_plan)
    except Exception as exc:
        logger.exception("旅行规划失败")
        raise HTTPException(status_code=502, detail=f"旅行规划失败：{exc}") from exc


@router.post("/replan-day", response_model=TripPlanResponse, summary="调整某一天行程")
def replan_day(request: ReplanDayRequest):
    try:
        with planner_lock:
            plan = get_trip_planner_agent().replan_day(request.plan, request.day_index, request.instruction)
        return TripPlanResponse(success=True, message="行程调整成功", data=plan)
    except Exception as exc:
        logger.exception("调整行程失败")
        raise HTTPException(status_code=502, detail=f"调整行程失败：{exc}") from exc


@router.get(
    "/health",
    summary="健康检查",
    description="检查旅行规划服务是否正常"
)
def health_check():
    """健康检查"""
    try:
        # 检查Agent是否可用
        agent = get_trip_planner_agent()
        
        return {
            "status": "healthy",
            "service": "trip-planner",
            "agent_name": agent.planner_agent.name,
            "tools_count": len(agent.map_service.mcp_tool._available_tools)
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"服务不可用: {str(e)}"
        )

