# memU 项目深度分析报告

## 1. 项目概览

| 属性 | 内容 |
|------|------|
| **项目名称** | memU (PyPI: `memu-py`) |
| **版本** | 1.4.0 |
| **定位** | 面向 24/7 常驻 AI Agent 的主动式记忆框架 |
| **开发组织** | NevaMind AI |
| **许可证** | Apache License 2.0 |
| **主语言** | Python 3.13+ (15,549 行), Rust (PyO3 扩展) |
| **构建系统** | Maturin (Rust+Python 混合构建) |
| **包管理** | uv |
| **总提交数** | 277 |
| **核心贡献者** | sairin1202 (110 commits), Wu (56), Cattylllo (19), Arnav (13), An Kaisen (13) |

---

## 2. 核心定位与设计理念

memU 的核心目标是为**长时间运行的 AI Agent** 提供**主动式记忆系统**。与传统的被动式记忆检索不同，memU 强调:

1. **持续学习** — 自动从每次交互中提取并存储记忆，无需显式命令
2. **主动预测** — 预测用户意图，在用户发问之前主动准备相关上下文
3. **成本控制** — 通过缓存洞察、避免冗余 LLM 调用来降低长期运行的 token 成本
4. **文件系统式隐喻** — 将记忆组织为类似文件系统的层级结构 (Category → Item → Resource)

---

## 3. 目录结构

```
memU/
├── src/
│   ├── lib.rs                     # Rust 扩展入口 (PyO3)
│   └── memu/
│       ├── __init__.py            # 公共 API 入口
│       ├── app/                   # 核心应用层
│       │   ├── service.py         # MemoryService 主服务 (Mixin 模式)
│       │   ├── memorize.py        # 记忆摄取管道 (MemorizeMixin)
│       │   ├── retrieve.py        # 记忆检索管道 (RetrieveMixin)
│       │   ├── crud.py            # CRUD 操作 (CRUDMixin)
│       │   ├── patch.py           # 分类补丁操作
│       │   └── settings.py        # Pydantic 配置模型
│       ├── database/              # 数据持久化层
│       │   ├── interfaces.py      # Protocol 接口定义
│       │   ├── models.py          # 核心数据模型 (Pydantic)
│       │   ├── factory.py         # 数据库后端工厂
│       │   ├── repositories/      # 仓库抽象接口
│       │   ├── inmemory/          # 内存存储实现
│       │   ├── postgres/          # PostgreSQL + pgvector 实现
│       │   └── sqlite/            # SQLite 实现
│       ├── llm/                   # LLM 客户端层
│       │   ├── wrapper.py         # LLM 客户端代理 + 拦截器
│       │   ├── openai_sdk.py      # OpenAI SDK 客户端
│       │   ├── http_client.py     # HTTP 直连客户端
│       │   ├── lazyllm_client.py  # LazyLLM 客户端
│       │   └── backends/          # 提供商适配 (OpenAI, Grok, Doubao, OpenRouter)
│       ├── embedding/             # 向量嵌入模块
│       │   ├── openai_sdk.py      # OpenAI Embedding 客户端
│       │   ├── http_client.py     # HTTP Embedding 客户端
│       │   └── backends/          # 嵌入后端 (OpenAI, Doubao)
│       ├── workflow/              # 工作流引擎
│       │   ├── pipeline.py        # 管道管理器 (版本控制)
│       │   ├── runner.py          # 工作流执行器
│       │   ├── step.py            # 工作流步骤定义
│       │   └── interceptor.py     # 工作流拦截器
│       ├── prompts/               # Prompt 模板库
│       │   ├── preprocess/        # 预处理 Prompt (conversation, document, image, video, audio)
│       │   ├── memory_type/       # 记忆类型 Prompt (profile, event, knowledge, behavior, skill, tool)
│       │   ├── category_summary/  # 分类摘要生成 Prompt
│       │   ├── category_patch/    # 分类补丁 Prompt
│       │   └── retrieve/          # 检索相关 Prompt (query_rewriter, judger, ranker)
│       ├── integrations/          # 第三方集成
│       │   └── langgraph.py       # LangGraph/LangChain 工具适配器
│       ├── blob/                  # 文件存储
│       │   └── local_fs.py        # 本地文件系统操作
│       ├── client/                # 客户端封装
│       │   └── openai_wrapper.py  # OpenAI 兼容接口
│       └── utils/                 # 工具类
│           ├── conversation.py    # 对话处理
│           ├── references.py      # 引用解析
│           ├── tool.py            # 工具记忆
│           └── video.py           # 视频处理
├── tests/                         # 测试目录
├── examples/                      # 示例代码
├── docs/                          # 文档
├── assets/                        # 静态资源
├── Cargo.toml                     # Rust 项目配置
├── pyproject.toml                 # Python 项目配置
└── Makefile                       # 开发命令
```

**源码规模**: 114 个 Python 文件, 1 个 Rust 文件, 共�� 15,549 行 Python 代码。

---

## 4. 架构设计

### 4.1 分层架构

```
┌─────────────────────────────────────────────────┐
│              Public API (__init__.py)            │
├─────────────────────────────────────────────────┤
│          Application Layer (app/)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │Memorize  │ │Retrieve  │ │  CRUD    │         │
│  │ Mixin    │ │ Mixin    │ │  Mixin   │         │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘         │
│       └─────────────┴────────────┘               │
│              MemoryService                       │
├─────────────────────────────────────────────────┤
│          Workflow Engine (workflow/)              │
│  Pipeline → Steps → Runner (+ Interceptors)     │
├──────────────┬──────────────┬────────────────────┤
│ LLM Layer    │ Embedding    │ Database Layer     │
│ (llm/)       │ (embedding/) │ (database/)        │
│ - OpenAI     │ - OpenAI     │ - InMemory         │
│ - Grok       │ - Doubao     │ - PostgreSQL       │
│ - Doubao     │ - HTTP       │ - SQLite           │
│ - OpenRouter │              │                    │
│ - LazyLLM   │              │                    │
└──────────────┴──────────────┴────────────────────┘
```

### 4.2 核心设计模式

| 模式 | 使用位置 | 说明 |
|------|---------|------|
| **Mixin** | `MemoryService` | 将 memorize/retrieve/crud 能力分离到不同 Mixin |
| **Repository** | `database/` | 数据访问抽象，Protocol 定义接口 |
| **Factory** | `database/factory.py` | 根据配置创建不同数据库后端 |
| **Pipeline** | `workflow/pipeline.py` | 可编排、可版本控制的处理管道 |
| **Strategy** | `retrieve.py` | RAG vs LLM 两种检索策略 |
| **Proxy** | `llm/wrapper.py` | LLM 客户端代理，透明注入拦截器 |
| **Interceptor** | `workflow/`, `llm/` | 前置/后置/错误钩子，用于观测和扩展 |
| **Command** | `workflow/step.py` | 工作流步骤封装为独立命令对象 |

---

## 5. 核心数据模型

### 5.1 三层记忆体系

```
Category (分类层)
├── name: str           # 分类名称
├── description: str    # 分类描述
├── summary: str        # 聚合摘要 (含 [ref:ITEM_ID] 引用)
├── embedding: list     # 摘要向量
│
├── CategoryItem (关联层, 多对多)
│   ├── category_id
│   └── item_id
│
└── MemoryItem (条目层)
    ├── type: profile | event | knowledge | behavior | skill | tool
    ├── summary: str        # 条目内容
    ├── embedding: list     # 内容向量
    ├── resource_id: str    # 来源资源引用
    └── extra: dict         # 元数据 (reinforcement_count, content_hash, ref_id, tool_call_result)
        │
        └── Resource (资源层)
            ├── url: str         # 原始资源路径
            ├── modality: str    # conversation | document | image | video | audio
            ├── content: str     # 预处理后内容
            └── embedding: list  # 内容向量
```

### 5.2 记忆类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `profile` | 用户画像 | 偏好、个人信息 |
| `event` | 事件记录 | 发生的具体事件 |
| `knowledge` | 知识存储 | 领域知识、事实 |
| `behavior` | 行为模式 | 习惯、交互模式 |
| `skill` | 技能记录 | 从执行日志中提取的技能 |
| `tool` | 工具调用 | 工具调用元数据和结果 |

---

## 6. 两大核心流程

### 6.1 Memorize (记忆摄取管道)

```
Resource URL → ingest_resource
                    ↓
             preprocess_multimodal  (按 modality 分发: conversation/document/image/video/audio)
                    ↓
             extract_items          (LLM 结构化提取记忆条目)
                    ↓
             dedupe_merge           (基于 content_hash 去重 + 强化计数)
                    ↓
             categorize_items       (向量匹配/创建分类 + 生成 embedding)
                    ↓
             persist_index          (持久化 + 更新分类摘要)
                    ↓
             build_response         (返回 resource + items + categories)
```

**关键特性**:
- 多模态支持: 文本、音频、视频、图片均有对应预处理 Prompt
- 自动分类: 基于向量相似度匹配已有分类，或自动创建新分类
- 去重与强化: 相同内容通过 hash 识别，增加 reinforcement_count (显著性追踪)
- 引用跟踪: 分类摘要中嵌入 `[ref:ITEM_ID]` 引用，可追溯到具体记忆条目

### 6.2 Retrieve (记忆检索管道)

#### RAG 模式 (快速向量检索)

```
Query → route_intention           (LLM 判断是否需要检索, 重写查询)
            ↓
       route_category             (向量搜索分类摘要)
            ↓
       sufficiency_after_category (充分性检查: 是否需要更细粒度检索)
            ↓
       recall_items               (向量搜索记忆条目)
            ↓
       sufficiency_after_items    (充分性检查)
            ↓
       recall_resources           (向量搜索原始资源)
            ↓
       build_context              (组装最终上下文)
```

#### LLM 模式 (深度语义排序)

结构类似 RAG 模式，但使用 LLM 代替向量相似度进行排序，适用于需要推理的复杂检索场景。

**两种模式对比**:

| 维度 | RAG 模式 | LLM 模式 |
|------|---------|---------|
| 速度 | 毫秒级 | 秒级 |
| 成本 | 仅 Embedding | LLM 推理 |
| 场景 | 实时监控、持续上下文 | 复杂意图理解 |
| 精度 | 语义相似度 | 深度语义推理 |

---

## 7. 技术栈与依赖

### 7.1 运行时依赖

| 依赖 | 版本 | 用途 |
|------|------|------|
| `openai` | >=2.8.0 | LLM 和 Embedding 调用 |
| `pydantic` | >=2.12.4 | 数据模型和配置验证 |
| `sqlmodel` | >=0.0.27 | ORM (SQLite/PostgreSQL) |
| `alembic` | >=1.14.0 | 数据库迁移 |
| `httpx` | >=0.28.1 | 异步 HTTP 客户端 |
| `numpy` | >=2.3.4 | 向量计算 |
| `pendulum` | >=3.1.0 | 时间处理 |
| `langchain-core` | >=1.2.7 | LangChain 集成 |
| `lazyllm` | >=0.7.3 | LazyLLM 集成 |
| `defusedxml` | >=0.7.1 | 安全 XML 解析 |
| `pyo3` | 0.27.1 | Rust-Python 绑定 |

### 7.2 可选依赖

| 组名 | 包含 | 用途 |
|------|------|------|
| `postgres` | pgvector, sqlalchemy | PostgreSQL + 向量索引 |
| `langgraph` | langgraph, langchain-core | LangGraph Agent 集成 |
| `claude` | claude-agent-sdk | Claude Agent 集成 |

### 7.3 开发工具链

| 工具 | 用途 |
|------|------|
| `uv` | 包管理与虚拟环境 |
| `maturin` | Rust/Python 混合构建 |
| `ruff` | Linting + 格式化 |
| `mypy` | 静态类型检查 |
| `deptry` | 依赖分析 |
| `pytest` + `pytest-asyncio` | 异步测试 |
| `pre-commit` | Git 钩子 |
| `mkdocs-material` | 文档生成 |

---

## 8. LLM 提供商支持

| 提供商 | 后端 | Chat | Embedding | Vision |
|--------|------|------|-----------|--------|
| OpenAI | SDK / HTTP | ✅ | ✅ | ✅ |
| OpenRouter | HTTP | ✅ | ✅ | ✅ |
| Grok (xAI) | HTTP | ✅ | - | - |
| Doubao (豆包) | HTTP | ✅ | ✅ | - |
| LazyLLM | LazyLLM SDK | ✅ | - | - |
| 阿里云 (通义千问) | SDK (OpenAI 兼容) | ✅ | - | - |
| Voyage AI | SDK (OpenAI 兼容) | - | ✅ | - |

支持通过 `llm_profiles` 为不同用���配置不同提供商 (如 default 用 OpenAI，embedding 用 Voyage)。

---

## 9. 数据库后端

| 后端 | 持久化 | 向量搜索 | 适用场景 |
|------|--------|---------|---------|
| **InMemory** | 否 | numpy cosine | 开发/测试、临时使用 |
| **PostgreSQL** | 是 | pgvector | 生产环境 |
| **SQLite** | 是 | 内置向量 | 轻量级部署、本地使用 |

---

## 10. 可扩展性设计

### 10.1 工作流管道自定义

```python
# 注册自定义步骤
pipeline_manager.insert_after("extract_items", custom_step)
pipeline_manager.replace_step("categorize_items", my_categorizer)
pipeline_manager.remove_step("dedupe_merge")
```

管道支持:
- 步骤插入 (`insert_after` / `insert_before`)
- 步骤替换 (`replace_step`)
- 步骤移除 (`remove_step`)
- 步骤配置 (`config_step`)
- 版本追踪 (`PipelineRevision`)

### 10.2 拦截器系统

**LLM 拦截器**: 在每次 LLM 调用前后注入逻辑
```python
service.register_llm_interceptor(
    before=log_request,
    after=track_tokens,
    on_error=alert_failure
)
```

**工作流拦截器**: 在每个工作流步骤前后注入逻辑
```python
service.register_workflow_interceptor(
    before=trace_step,
    after=log_result
)
```

### 10.3 自定义 Prompt

通过 `CustomPrompt` 系统支持可组合的 Prompt 块:
```python
custom_prompts = [
    CustomPrompt(ordinal=1, content="系统指令..."),
    CustomPrompt(ordinal=2, content="额外约束..."),
]
```

---

## 11. 第三方集成

### 11.1 LangGraph 集成

通过 `MemULangGraphTools` 适配器将 memU 暴露为 LangChain 工具:
- `save_memory` — 保存记忆到 memU
- `search_memory` — 从 memU 检索记忆

可直接嵌入 LangGraph Agent 工作流中。

### 11.2 Cloud API (v3)

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v3/memory/memorize` | 注册持续学习任务 |
| GET | `/api/v3/memory/memorize/status/{task_id}` | 查询处理状态 |
| POST | `/api/v3/memory/categories` | 列出自动分类 |
| POST | `/api/v3/memory/retrieve` | 查询记忆 |

---

## 12. 创新亮点

| 创新点 | 说明 |
|--------|------|
| **层级检索 + 充分性检查** | 三层检索 (Category → Item → Resource)，每层后 LLM 判断是否需要更细粒度检索，避免不必要的计算 |
| **引用追踪** | Category 摘要中嵌入 `[ref:ITEM_ID]`，实现从摘要到具体记忆的可追溯性 |
| **显著性强化** | 通过 `reinforcement_count` 追踪记忆被访问/匹配的频率，高频记忆更容易被召回 |
| **双模检索** | RAG (向量) + LLM (语义推理) 两种检索模式可按场景切换 |
| **文件系统隐喻** | 将记忆组织为文件系统结构，直观且可导出/迁移 |
| **多模态统一** | 文本、图片、音频、视频、对话均可统一处理为结构化记忆 |
| **主动意图预测** | 不等待用户查询，自动预测并准备可能需要的上下文 |

---

## 13. 性能基准

在 **Locomo 基准测试** 上取得 **92.09% 平均准确率**，涵盖所有推理任务类别。

详细实验数据: [memU-experiment](https://github.com/NevaMind-AI/memU-experiment)

---

## 14. 生态系统

| 仓库 | 说明 |
|------|------|
| **memU** (本项目) | 核心主动记忆引擎 |
| **memU-server** | 后端服务，支持实时同步 |
| **memU-ui** | 可视化记忆仪表盘 |
| **memU bot** | 开箱即用的 Agent 机器人 (memu.bot) |

---

## 15. 开发工作流

```bash
# 安装开发环境
make install        # uv sync + pre-commit install

# 质量检查
make check          # lock 一致性 + ruff lint + mypy 类型检查 + deptry 依赖分析

# 运行测试
make test           # pytest + coverage

# 构建 (含 Rust 扩展)
maturin develop     # 开发模式编译 Rust + 安装 Python 包
```

---

## 16. 总结

memU 是一个**架构精良、可扩展性强**的 AI Agent 记忆框架。它通过三层记忆体系、双模检索策略、可编排的工作流管道、以及丰富的拦截器系统，为 24/7 常驻 Agent 提供了一套完整的**主动式记忆解决方案**。项目代码组织清晰，使用 Protocol 定义接口、Mixin 分离关注点、Factory 管理后端，展现了优秀的 Python 工程实践。Rust 扩展目前为占位符，为未来性能敏感模块预留了优化空间。
