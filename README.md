# 旅途手记 TripCanvas

**AI 智能旅行规划助手 | AI Travel Planner · Vue 3 · FastAPI · 高德地图 · MCP**

输入目的地、日期、预算与偏好，旅途手记结合大模型和高德地图信息生成可编辑的旅行计划，帮助你从灵感走到出发。

TripCanvas is an AI-powered travel itinerary planner built with Vue 3, FastAPI, HelloAgents and Amap MCP. It brings together attractions, weather, route planning, budgets and an interactive map.

## 功能

- 按目的地、旅行日期、出行人数、预算、交通和兴趣生成多日行程。
- 查询景点、天气和住宿信息，在地图中展示行程相关地点。
- 查看每日安排、费用估算和路线；支持调整单日计划与编辑行程。
- 支持导出行程，在当前浏览器保存和打开最近行程。
- 提供响应式界面、表单校验、键盘焦点和减少动画支持。

地图信息、天气和模型生成内容可能有误，费用为估算值；出行前请自行核实。历史行程保存在浏览器本地，清理浏览器数据可能导致记录丢失。

## 技术栈

| 部分 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、Ant Design Vue、Axios |
| 后端 | Python、FastAPI、Pydantic、HelloAgents |
| 外部服务 | 高德地图 Web 服务与 JavaScript API、MCP、兼容的 LLM API |
| 动效 | 参考 Magic UI 的 Vue 适配，许可证见 `frontend/MAGIC_UI_LICENSE.md` |

## 本地运行

需要 Python 3.12、Node.js 20 或更高版本、可访问的模型 API，以及高德地图 Web 服务和 JavaScript API 的 Key。地图 MCP 首次运行需要联网下载依赖。

### 1. 启动后端

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS / Linux: source .venv/bin/activate
pip install -r requirements.txt
# 复制 .env.example 为 .env，并填写密钥
uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

后端配置文件 `backend/.env`：

| 变量 | 用途 |
| --- | --- |
| `AMAP_API_KEY` | 高德地图 Web 服务 Key |
| `LLM_MODEL_ID` | 模型名称 |
| `LLM_API_KEY` | 模型服务密钥 |
| `LLM_BASE_URL` | 兼容模型服务的 API 地址 |
| `LLM_TIMEOUT` | 单次模型请求超时时间（秒） |
| `CORS_ORIGINS` | 允许访问后端的前端地址，多个地址以逗号分隔 |

### 2. 启动前端

```bash
cd frontend
npm ci
# 复制 .env.example 为 .env，并填写本地配置
npm run dev
```

在 `frontend/.env` 中配置 `VITE_API_BASE_URL=http://localhost:8000`、`VITE_AMAP_WEB_JS_KEY`，以及本地开发所需的 `VITE_AMAP_SECURITY_JS_CODE`。前端地址以 Vite 终端输出为准；后端 API 文档为 `http://localhost:8000/docs`。

`VITE_` 变量会被打包到浏览器代码中。**生产环境不要把高德安全密钥放到前端环境变量**，应按高德官方要求配置服务端安全代理。不要将 `.env` 或模型密钥提交到仓库。

## 项目结构

```text
backend/
  app/agents/      行程规划 Agent
  app/api/         FastAPI 应用和路由
  app/models/      请求、响应与行程数据模型
  app/services/    地图、模型和图片服务
  tests/           后端回归测试
frontend/
  src/views/       表单页与行程结果页
  src/components/  可复用组件与动效
  src/services/    后端请求与浏览器历史记录
  src/assets/      界面图片
```

## 部署说明

前端可构建为静态文件：`cd frontend && npm ci && npm run build`，产物位于 `frontend/dist`。Cloudflare Pages 可以托管这些文件；构建时需提供公开的高德 JS Key 和实际后端地址。`localhost` 只能指向访问者自己的设备，不能作为公网后端地址。

后端需要能够运行 Python 和 `uvx` 子进程的运行环境、可访问的模型服务以及私密环境变量。现有地图 MCP 通过 `uvx` 启动子进程，不能直接作为普通 Cloudflare Pages 静态站点运行。生产上线还需要配置高德安全代理、后端 HTTPS/CORS，以及访问控制和调用配额，避免公开接口消耗模型及地图服务额度。

## 许可与致谢

本项目基于 [Datawhale Hello-Agents](https://github.com/datawhalechina/hello-agents/tree/main/code/chapter13/helloagents-trip-planner) 第 13 章旅行规划项目修改，保留原项目 **CC BY-NC-SA 4.0** 许可及来源；详见 [LICENSE.txt](LICENSE.txt)。本版本调整了前后端交互、界面、验证和测试。第三方组件仍遵循其各自许可，Magic UI 相关许可见 [frontend/MAGIC_UI_LICENSE.md](frontend/MAGIC_UI_LICENSE.md)。
