# rag-local：从 0 到 1 的本地 RAG（不调用 open.bigmodel）

该子项目提供一套**完全本地**可运行的 RAG（Retrieval-Augmented Generation）最小可用工程，包含：

- 文档加载器（txt / md / pdf / docx）
- 文本分割器（递归字符切分，支持重叠）
- Embedding 模型（本地 `sentence-transformers`）
- 向量数据库（本地持久化 `Chroma`）
- 检索器（相似度检索 + 可选 MMR）
- LLM（默认本机 `Ollama`；不依赖任何外部 SaaS URL）
- Prompt 模板（含引用片段拼装）

## 1) 环境准备

### 安装 Python 依赖

```bash
cd rag-local
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### 安装并启动 Ollama（本地 LLM）

1) 安装 Ollama（Windows 版）
2) 拉取模型，例如：

```bash
ollama pull qwen2.5:7b-instruct
```

默认会用 `http://127.0.0.1:11434`。

## 2) 运行 API

```bash
cd rag-local
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

健康检查：

- `GET /health`

## 3) 入库（ingest）

把一个目录下的文档批量入库：

```bash
python -m app.scripts.ingest_folder --path "../docs" --collection "default"
```

也可用 API 上传文件入库：

- `POST /api/ingest`（multipart/form-data：`files`）

## 4) 查询（query）

- `POST /api/query`

body 示例：

```json
{
  "query": "这份文档里关于退款规则怎么说？",
  "collection": "default",
  "top_k": 5
}
```

返回包含：`answer`、`contexts`（检索到的片段及来源）。

## 5) 配置

复制 `rag-local/.env.example` 到 `rag-local/.env` 后按需修改：

- `EMBEDDING_MODEL`：Embedding 模型名（默认 `sentence-transformers/all-MiniLM-L6-v2`）
- `CHROMA_DIR`：Chroma 持久化目录（默认 `./data/chroma`）
- `OLLAMA_BASE_URL`：Ollama 地址（默认 `http://127.0.0.1:11434`）
- `OLLAMA_MODEL`：Ollama 模型（默认 `qwen2.5:7b-instruct`）

