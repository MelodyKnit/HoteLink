# HoteLink 论文与实现对齐说明

## 1. 文档目的

本文用于记录论文表述、设计文档与当前仓库实现之间的对齐关系，避免文档描述超过系统现状。

当前判断"是否已经实现"的主要依据为：

- 路由与接口代码：[backend/apps/api/urls.py](../backend/apps/api/urls.py)
- 视图实现：[backend/apps/api/views.py](../backend/apps/api/views.py)
- Docker 编排：[docker-compose.dev.yml](../docker-compose.dev.yml) 与 [docker-compose.prod.yml](../docker-compose.prod.yml)
- 部署脚本：[scripts/docker.ps1](../scripts/docker.ps1) 与 [scripts/docker.sh](../scripts/docker.sh)
- 前端路由：[frontend/apps/user-web/src/router/](../frontend/apps/user-web/src/router/) 与 [frontend/apps/admin-web/src/router/](../frontend/apps/admin-web/src/router/)

> 关联文档：
> - 接口设计：[api-spec.md](./api-spec.md)
> - 技术架构：[architecture.md](./architecture.md)
> - AI 集成：[ai-integration.md](./ai-integration.md)
> - 前端设计：[frontend-system-design.md](./frontend-system-design.md)
> - 功能规划：[feature-improvements.md](./feature-improvements.md)

## 2. 论文核心定位

- 系统名称：酒店预订与管理平台
- 角色：普通用户、酒店管理员、系统管理员
- 架构：前后端分离（Django + Vue 3）
- 论文数据库基线：SQLite（项目工程增强：MySQL + Redis）

## 3. 当前已实现并可用于论文表述的能力

### 3.1 后端

- **103 条 API 路由**已注册（含 `/api/v1/` 根路由），覆盖：认证、公共查询、用户中心、订单、评价、收藏、优惠券、发票、积分、通知、AI 辅助、管理端经营管理
- **21 个 Django Model**（跨 7 个业务 app）：hotels(3)、bookings(1)、payments(1)、crm(10)、operations(4)、reports(1)、users(1)
- JWT 认证：注册、登录、管理员登录、令牌刷新
- 完整的订单生命周期：创建 → 支付 → 入住 → 退房 → 评价
- AI 多供应商接入：5 家供应商预设（DeepSeek / OpenAI / 智谱 / Moonshot / 通义千问），多轮对话 + 流式输出 + 意图识别 + 预订引导

### 3.2 前端

- **用户端**：26 条路由项 / 24 个视图页面，覆盖首页、酒店浏览、预订支付、订单管理、会员中心、AI 客服等
- **管理端**：20 条路由项 / 19 个视图页面，覆盖工作台、酒店管理、房型管理、库存管理、订单处理、报表、AI 配置等
- **共享包**：10 个 UI 组件 + 2 个 Composable + ~27 个 API 模块 + 2 个 Pinia Store
- 用户端 AI 客服已支持 SSE 流式回答、Markdown 渲染、订房动作卡片

### 3.3 部署

- Docker 开发环境与生产环境已分别提供独立编排文件（`docker-compose.dev.yml`、`docker-compose.prod.yml`）
- 统一脚本入口：`scripts/docker.ps1`（Windows）、`scripts/docker.sh`（Linux/macOS）
- 系统初始化、系统重置、演示数据填充能力已落地

## 4. 论文主线功能与实现对照

### 4.1 公共访问区

| 论文功能 | 后端 API | 前端页面 | 状态 |
|---------|---------|---------|------|
| 首页 | `GET /api/v1/public/home` | `HomeView.vue` | ✅ 已实现 |
| 登录 / 注册 | `POST .../auth/login` `register` | `LoginView.vue` `RegisterView.vue` | ✅ 已实现 |
| 管理员登录 | `POST .../auth/admin-login` | `LoginView.vue`（admin） | ✅ 已实现 |
| 酒店列表 | `GET /api/v1/public/hotels` | `HotelListView.vue` | ✅ 已实现 |
| 酒店详情 | `GET .../hotels/detail` | `HotelDetailView.vue` | ✅ 已实现 |

### 4.2 用户中心区

| 论文功能 | 后端 API | 前端页面 | 状态 |
|---------|---------|---------|------|
| 个人资料 | `GET /api/v1/user/profile` + `POST /api/v1/user/profile/update` | `ProfileView.vue` | ✅ 已实现 |
| 收藏酒店 | `GET /api/v1/user/favorites` + `POST /add` + `POST /remove` | `FavoriteListView.vue` | ✅ 已实现 |
| 订单列表 | `GET /api/v1/user/orders` | `OrderListView.vue` | ✅ 已实现 |
| 订单详情 | `GET .../orders/detail` | `OrderDetailView.vue` | ✅ 已实现 |
| 订单支付 | `POST .../orders/pay` | `PaymentView.vue` | ✅ 已实现 |
| 订单取消 | `POST .../orders/cancel` | —（在订单详情内操作） | ✅ 已实现 |
| 评价提交 | `POST /api/v1/user/reviews/create` | `ReviewListView.vue` | ✅ 已实现 |
| 积分明细 | `GET .../points/logs` | — | ✅ 后端已实现 |
| 优惠券 | `GET /api/v1/user/coupons` | `CouponListView.vue` | ✅ 已实现 |
| 发票 | `GET/POST .../invoices` | `InvoiceView.vue` | ✅ 已实现 |

### 4.3 管理后台区

| 论文功能 | 后端 API | 前端页面 | 状态 |
|---------|---------|---------|------|
| 经营概览 | `GET /api/v1/admin/dashboard/overview` | `DashboardView.vue` | ✅ 已实现 |
| 酒店管理 | `CRUD /api/v1/admin/hotels` | `HotelListView.vue` | ✅ 已实现 |
| 房型管理 | `CRUD /api/v1/admin/room-types` | `RoomTypeListView.vue` | ✅ 已实现 |
| 价格库存管理 | `GET /api/v1/admin/inventory/calendar` + `POST /api/v1/admin/inventory/update` | `InventoryView.vue` | ✅ 已实现 |
| 订单管理 | `GET /api/v1/admin/orders` | `OrderListView.vue` | ✅ 已实现 |
| 入住 / 退房 | `POST .../check-in` `check-out` | —（在订单页内操作） | ✅ 后端已实现 |
| 评价回复 | `POST .../reviews/reply` | `ReviewListView.vue` | ✅ 已实现 |
| 经营报表 | `GET /api/v1/admin/reports` | `ReportView.vue` | ✅ 已实现 |
| 用户管理 | `GET /api/v1/admin/users` | `UserListView.vue` | ✅ 已实现 |

## 5. 工程增强项（超出论文基线的已实现能力）

以下能力已在项目中实现，但超出论文最小闭环范围，论文中应标注为"扩展能力"或"后续优化方向"：

| 增强项 | 说明 |
|--------|------|
| MySQL + Redis | 论文基线为 SQLite，项目 Docker 生产环境使用 MySQL 8 + Redis |
| Docker 化部署 | 开发环境 + 生产环境完整编排，Nginx 反向代理 |
| AI 多供应商接入 | 5 家供应商预设，运行时切换，多轮对话，流式输出 |
| AI 智能客服 | 用户端 `/ai-chat`，SSE 流式问答，预订引导，Markdown 渲染 |
| AI 管理端辅助 | 经营摘要、评价摘要、回复建议、定价、经营报告、情感分析、文案生成等（已接入 AI 服务，含 fallback） |
| 会员与优惠券体系 | 会员等级管理、优惠券模板、发放与核销 |
| 通知系统 | 站内通知推送 + 已读管理 |
| 系统重置 | 高危操作二次确认的全量数据重置 |

## 6. 当前应谨慎表述或明确为"未实现/规划中"的内容

- WebSocket 实时通知目前没有对应的后端实现，不应在论文中表述为已交付能力
- 管理端前台业务流程（新建预订、入住办理、退房结算、续住/换房）仅有后端基础接口，前端独立页面尚未开发
- 管理端财务模块（财务总览、账单管理、支付记录、退款记录）尚未有独立前端页面
- 角色权限细粒度管理（RBAC）尚未实现前端页面
- Celery 异步任务已落地（超时取消、批量巡检、生命周期异常巡检）
- 管理端 AI 辅助接口（`report-summary`、`review-summary`、`reply-suggestion`）已接入 AI 服务；当 AI 不可用时会返回 fallback 结果

## 7. 当前文档约束

- [api-spec.md](./api-spec.md)：以已实现 HTTP 接口为主，规划项显式标注 `[规划中]`
- [deployment.md](./deployment.md)：只记录仓库内真实存在的脚本、镜像和编排能力
- [ai-integration.md](./ai-integration.md)：区分已实际调用 LLM 的能力与壳接口
- [frontend-system-design.md](./frontend-system-design.md)：§7 / §8 开头实现总览表区分"已实现"与"设计中"
- [architecture.md](./architecture.md)：模块描述与实际 Model 字段一致

## 8. 论文批注回应材料对照

论文批注中要求补充的材料，当前项目已提供的对应产出：

| 批注要求 | 对应产出 | 状态 |
|---------|---------|------|
| 系统架构图 | `architecture.md` §3 / `frontend-system-design.md` §3-§5 (Mermaid) | ✅ 已有 |
| E-R 图 | — | ❌ 待补充 |
| 典型数据表字段说明 | `architecture.md` §6 模块描述含字段列表 | ✅ 已有 |
| 典型接口请求/响应示例 | `api-spec.md` 全部接口含 Request/Response 示例 | ✅ 已有 |
| 关键业务流程图 | `frontend-system-design.md` §9 用户旅程图 (Mermaid) | ✅ 已有 |
| AI 扩展能力说明 | `ai-integration.md` 完整文档 | ✅ 已有 |
| 页面截图 | — | ❌ 待补充 |

## 9. 维护要求

- 新增接口、页面、脚本、Docker 能力时，同步更新对应文档
- 如果论文表述采用了工程能力，必须先确认该能力已经进入代码和路由
- 若发现文档描述超前于实现，应优先修改文档
- 每次系统新增超出论文范围的能力，在 §5 中补充"工程增强项"
- 每次论文主线功能调整，同步修改 §4 中的对照表
