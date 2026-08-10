# AI Knowledge Assistant

一个基于 RAG 架构的企业知识库智能问答系统。用户上传企业文档后，系统自动解析、切片、向量化并写入 ChromaDB；问答时检索相关片段，通过 LLM 生成带来源引用的回答。

## 技术栈

| 分类 | 技术 |
| --- | --- |
| Backend | Python, FastAPI |
| AI | RAG, Embedding, LLM API, Prompt Engineering |
| Vector Database | ChromaDB |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Deployment | Docker, Docker Compose, Nginx |

## 核心功能

- 多格式文档上传与 PDF / TXT / Markdown 解析
- 自动文本切片、Embedding 向量生成与 ChromaDB 语义检索
- RAG 智能问答、回答来源引用和相似度展示
- OpenAI 兼容 LLM API 与 Mock 回退模式
- JWT 用户认证、用户数据隔离与聊天历史保存
- SSE 流式输出接口与 Docker Compose 部署

## 系统架构

```text
用户 → Frontend → FastAPI Backend → Document Processing → Embedding
                                                      ↓
                                                   ChromaDB
                                                      ↓
Retriever → LLM → Answer
```

SQLite 保存用户、文档元数据和聊天历史；ChromaDB 保存文档切片及向量。

## 本地运行

```powershell
cd E:\AI-Projects\ai-knowledge-assistant
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --app-dir backend --reload
```

另开终端运行：

```powershell
python -m http.server 8080 --directory frontend
```

访问 `http://localhost:8080`，前端 API 地址使用 `http://localhost:8000/api/v1`；接口文档为 `http://localhost:8000/docs`。

## Docker 运行

```powershell
Copy-Item .env.example .env
docker compose up --build
```

前端地址：`http://localhost:8080`。生产环境请基于 `.env.production.example` 创建 `.env`，并替换 `LLM_API_KEY` 和高强度 `JWT_SECRET_KEY`。

## API

除注册和登录外，接口需要 `Authorization: Bearer <token>`。

| 分类 | 方法 | 接口 | 说明 |
| --- | --- | --- | --- |
| 认证 | POST | `/api/v1/auth/register` | 注册并返回 JWT Token |
| 认证 | POST | `/api/v1/auth/login` | 登录并返回 JWT Token |
| 文档 | POST | `/api/v1/documents/upload` | 上传并建立索引 |
| 文档 | GET | `/api/v1/documents` | 查询当前用户文档 |
| 文档 | DELETE | `/api/v1/documents/{id}` | 删除文档及向量 |
| 聊天 | POST | `/api/v1/chat/query` | RAG 问答 |
| 聊天 | POST | `/api/v1/chat/query/stream` | SSE 流式问答 |

## 项目截图

将截图放在 [`docs/screenshots/`](docs/screenshots/)：

- `home.png`：首页
- `document-upload.png`：文档上传
- `ai-chat.png`：AI 聊天与来源引用
- `docker-running.png`：Docker 运行

## 测试

```powershell
python -m pytest tests/backend -q
npm run build --prefix frontend
```
