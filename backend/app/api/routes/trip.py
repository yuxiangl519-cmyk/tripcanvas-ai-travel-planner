"""旅行规划API路由"""

from fastapi import APIRouter, HTTPException
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from time import monotonic
from uuid import uuid4
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
job_executor = ThreadPoolExecutor(max_workers=1)
job_lock = Lock()
plan_jobs = {}


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


@router.post("/plan/jobs", status_code=202, summary="提交旅行规划任务")
def create_plan_job(request: TripRequest):
    now = monotonic()
    with job_lock:
        for job_id, (created, future) in list(plan_jobs.items()):
            if future.done() and now - created > 3600:
                del plan_jobs[job_id]
        if sum(not future.done() for _, future in plan_jobs.values()) >= 10:
            raise HTTPException(status_code=429, detail="当前规划任务较多，请稍后再试")
        job_id = uuid4().hex
        plan_jobs[job_id] = (now, job_executor.submit(plan_trip, request))
    return {"id": job_id}


@router.get("/plan/jobs/{job_id}", summary="查询旅行规划任务")
def get_plan_job(job_id: str):
    with job_lock:
        job = plan_jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="任务不存在或已过期，请重新生成")
    future = job[1]
    if not future.done():
        return {"status": "pending"}
    try:
        return {"status": "completed", "result": future.result()}
    except HTTPException as exc:
        raise exc
    except Exception:
        logger.exception("旅行规划任务失败")
        raise HTTPException(status_code=502, detail="旅行规划任务失败，请重试") from None


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

