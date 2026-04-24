# 带记忆的聊天机器人（前后端分离）

## 结构

- `backend/`：FastAPI + SQLAlchemy，SQLite 持久化会话与消息；调用 OpenAI 兼容接口（可选）。
- `backend-node/`：Node.js + Express，JSON 文件持久化会话与消息；调用 OpenAI 兼容接口（可选）。
- `frontend/`：React + TypeScript + Vite，侧边栏会话列表与聊天区。

## 环境要求

- **Node.js 18+**（前端 Vite 构建需要；Node 后端在较低版本也可运行）
- **Python 3.10+**（如使用 Python 后端）

## 后端（Python 版）

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# 编辑 .env，按需填写 OPENAI_API_KEY
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8020
```

- 未配置 `OPENAI_API_KEY` 时返回演示回复，仍会把对话写入数据库作为「记忆」。
- 数据库文件默认：`backend/data/chat_memory.db`。

## 后端（Node.js 版）

```bash
cd backend-node
copy .env.example .env
npm install
npm run dev
```

- 默认端口：`8001`
- 数据文件：`backend-node/data/chat_memory.json`
- 可配置：`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`、`HISTORY_LIMIT`
- 与 Python 版保持同一套 API 结构（见下方 API 摘要）

## 前端

```bash
cd frontend
npm install
npm run dev
```

前端开发服务默认 **http://localhost:8080**，Vite 代理指向 Python 后端 `http://127.0.0.1:8020`。若改接 Node 后端，可在 `frontend/vite.config.ts` 将代理目标改为 `http://127.0.0.1:8001`。

## API 摘要

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/health` | 健康检查 |
| GET | `/api/sessions` | 会话列表 |
| POST | `/api/sessions` | 新建会话 |
| GET | `/api/sessions/{id}/messages` | 某会话消息 |
| DELETE | `/api/sessions/{id}` | 删除会话 |
| POST | `/api/chat` | 发送消息（body: `message`, 可选 `session_id`） |
