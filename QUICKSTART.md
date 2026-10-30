# Windows 快速启动

先根据 [README](README.md) 准备 Python、Node.js、模型服务和高德地图密钥，并创建 `backend/.env` 与 `frontend/.env`。

在项目目录打开两个 PowerShell 终端：

```powershell
# 首次安装后端依赖
uv venv --python 3.12 backend/.venv
uv pip install --python backend/.venv/Scripts/python.exe -r backend/requirements.txt
# 首次安装前端依赖
cd frontend
npm.cmd ci
cd ..
```

```powershell
# 终端 1：后端
powershell -ExecutionPolicy Bypass -File .\run-backend.ps1
```

```powershell
# 终端 2：前端
powershell -ExecutionPolicy Bypass -File .\run-frontend.ps1
```

前端地址以终端输出为准。后端文档地址为 http://localhost:8000/docs。首次地图查询可能需要联网下载 MCP 依赖。
