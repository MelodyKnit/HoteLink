# HoteLink 文档导航

## 1. 文档使用原则

- `docs/` 只存放项目正式文档，用于说明当前系统、接口、部署、前端设计和 AI 集成，不放论文类内容。
- 如果文档和代码出现冲突，优先以源码为准，再回头更新文档。
- 需要确认“当前真实实现”时，优先看 [`source-of-truth.md`](./source-of-truth.md) 和 [`api-inventory.md`](./api-inventory.md)。
- [`api-inventory.md`](./api-inventory.md) 是脚本自动生成文档，不应手工修改。

## 2. 三分钟上手

- 想知道“这个系统现在到底做到了什么”：先看 [`source-of-truth.md`](./source-of-truth.md)
- 想知道“系统整体怎么分层、模块怎么划分”：看 [`architecture.md`](./architecture.md)
- 想联调接口、确认请求响应：看 [`api-spec.md`](./api-spec.md)
- 想确认某条路由是否真实存在：看 [`api-inventory.md`](./api-inventory.md)
- 想看页面、路由、交互闭环：看 [`frontend-system-design.md`](./frontend-system-design.md)
- 想看 AI 能力、边界和接入方式：看 [`ai-integration.md`](./ai-integration.md)
- 想本地启动、部署、跑 CI：看 [`deployment.md`](./deployment.md)
- 想看后续规划而不是当前事实：看 [`feature-improvements.md`](./feature-improvements.md)

## 3. 推荐阅读顺序

1. 先看 [`source-of-truth.md`](./source-of-truth.md)：确认当前系统真实状态、路由数量、模型结构和对齐基线。
2. 再看 [`architecture.md`](./architecture.md)：理解系统整体架构、模块划分和技术栈。
3. 需要联调接口时看 [`api-spec.md`](./api-spec.md) 和 [`api-inventory.md`](./api-inventory.md)。
4. 需要看页面与交互时看 [`frontend-system-design.md`](./frontend-system-design.md)。
5. 需要部署、运行、CI 或环境变量时看 [`deployment.md`](./deployment.md)。
6. 需要理解 AI 能力时看 [`ai-integration.md`](./ai-integration.md)。
7. 需要评估后续演进方向时看 [`feature-improvements.md`](./feature-improvements.md)。

## 4. 按角色阅读

- 新接手项目的开发：先看 [`source-of-truth.md`](./source-of-truth.md) + [`architecture.md`](./architecture.md)
- 前端开发：重点看 [`frontend-system-design.md`](./frontend-system-design.md) + [`api-spec.md`](./api-spec.md)
- 后端开发：重点看 [`api-spec.md`](./api-spec.md) + [`source-of-truth.md`](./source-of-truth.md)
- 运维或部署：重点看 [`deployment.md`](./deployment.md)
- AI 功能维护者：重点看 [`ai-integration.md`](./ai-integration.md)
- 产品或规划梳理：先看 [`source-of-truth.md`](./source-of-truth.md)，再看 [`feature-improvements.md`](./feature-improvements.md)

## 5. 文档清单

| 文档 | 作用说明 | 适用场景 |
|---|---|---|
| [`source-of-truth.md`](./source-of-truth.md) | 源码对齐基线，说明当前真实路由、模型、AI 能力、前端路由和维护规则。 | 判断某个能力是否真的已经落地、文档是否漂移时先看它。 |
| [`architecture.md`](./architecture.md) | 技术架构总览，描述后端、前端、数据模型、核心流程和系统规模。 | 新成员了解项目结构、做架构评审、梳理模块边界时查看。 |
| [`api-spec.md`](./api-spec.md) | API 规范说明，描述接口分组、统一请求响应、权限、安全基线和关键业务流。 | 前后端联调、补接口文档、确认参数与返回结构时查看。 |
| [`api-inventory.md`](./api-inventory.md) | 自动生成的 API 路由总清单，逐条列出 Method、Path、View、Name。 | 需要快速确认某条路由是否存在、请求方法是什么时查看。 |
| [`frontend-system-design.md`](./frontend-system-design.md) | 前端系统设计文档，覆盖用户端、管理端页面清单、交互逻辑和页面定位。 | 做页面开发、交互排版、前后台功能闭环检查时查看。 |
| [`ai-integration.md`](./ai-integration.md) | AI 集成说明，描述 AI 接入方式、核心代码位置、调用链、安全边界和配置方式。 | 开发 AI 聊天、流式输出、提示词、供应商切换和 AI 安全策略时查看。 |
| [`deployment.md`](./deployment.md) | 部署与运行说明，包含 Docker、本地运行、环境变量、安全基线、CI 与质量门禁。 | 本地启动、部署上线、排查环境问题、配置 GitHub Actions 时查看。 |
| [`feature-improvements.md`](./feature-improvements.md) | 功能增强与演进规划，记录历史规划、扩展方向和后续可增强模块。 | 评估下一阶段开发优先级、整理需求池或做功能规划时查看。 |

## 6. 快速定位

- 看当前系统到底做到了什么：[`source-of-truth.md`](./source-of-truth.md)
- 看接口规范怎么定义：[`api-spec.md`](./api-spec.md)
- 看某条 API 有没有、叫什么：[`api-inventory.md`](./api-inventory.md)
- 看页面和交互应该怎么设计：[`frontend-system-design.md`](./frontend-system-design.md)
- 看 AI 功能怎么接入和限制：[`ai-integration.md`](./ai-integration.md)
- 看部署、环境变量、CI、测试门禁：[`deployment.md`](./deployment.md)
- 看后续规划而不是当前事实：[`feature-improvements.md`](./feature-improvements.md)
