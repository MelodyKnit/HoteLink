# HoteLink 技术架构（源码对齐版）

> 若与其他文档冲突，请优先参考 [`source-of-truth.md`](./source-of-truth.md)

## 1. 总体架构

### 1.1 三十秒读懂系统

HoteLink 目前是一个“一个 Django 后端 + 两个 Vue 前端”的酒店系统：

- 用户端负责浏览酒店、下单、支付、订单与会员服务
- 管理端负责房态、订单、入住退房、发票、报表、AI 与系统配置
- 后端统一提供 API、鉴权、支付、AI、通知和定时任务
- Redis 与 Celery 负责缓存、异步任务和定时巡检

如果你刚接手项目，可以按这个顺序阅读：

1. 先看本文，建立整体结构感。
2. 再看 [`source-of-truth.md`](./source-of-truth.md)，确认当前真实实现规模。
3. 之后按需要进入 [`api-spec.md`](./api-spec.md) 或 [`frontend-system-design.md`](./frontend-system-design.md)。

系统采用“统一后端 + 双前端应用”：

- 后端：Django + DRF（统一 API）
- 用户端：`frontend/apps/user-web`
- 管理端：`frontend/apps/admin-web`

部署形态支持：

- 本地直接运行（SQLite/MySQL 可切换）
- Docker 开发环境
- Docker 生产环境

---

## 2. 技术栈

### 2.1 后端

- Python `3.12`
- Django `6.0.x`
- Django REST Framework
- SimpleJWT
- MySQL（容器化）/ SQLite（本地可回退）
- Redis
- Celery + Celery Beat
- drf-spectacular（`/schema` `/docs` `/redoc`）
- OpenAI Python SDK（兼容多供应商）
- Jinja2 Prompt 模板

### 2.2 前端

- Vue 3 + TypeScript + Vite
- Vue Router + Pinia
- Axios
- ECharts
- Tailwind CSS + Less

---

## 3. 当前规模（按源码统计）

### 3.1 API 与后端

- 路由总数：`127`（含 `/api/v1/` 根路由）
- View 类：`108`
- Serializer 类：`80`
- 业务模型：`22`

### 3.2 前端

- user-web：`28` 路由项、`25` 视图文件
- admin-web：`28` 路由项、`26` 视图文件
- 共享包：
  - `packages/api`
  - `packages/store`
  - `packages/ui`
  - `packages/utils`
  - `packages/styles`

---

## 4. 业务域模型

### 4.1 users

- `UserProfile`（角色、状态、会员等级、资料；`member_points` 为会员成长积分，`consume_points` 为可兑换消费积分，`points` 保留为旧接口兼容字段并等同消费积分）

### 4.2 hotels

- `Hotel`（含 `type` 字段区分酒店/民宿/短租，`facilities` JSON 设施列表，`tags` JSON 标签列表；`is_recommended` 字段已加 `db_index`）
- `RoomType`（已添加 `hotel` + `name` 复合索引）
- `RoomInventory`

### 4.3 bookings

- `BookingOrder`（新增 `PAYMENT_REFUNDING` 退款中状态；`created_at` 已加 `db_index`；`points_earned` 记录本单消费积分，`member_points_earned` 记录本单会员积分）

### 4.4 payments

- `PaymentRecord`（支持真实网关支付、异步回调载荷、前台退房补收与续住补差流水）

### 4.5 crm

- `CustomerProfile`
- `FavoriteHotel`
- `Review`（新增 `is_visible` 字段，管理端可控制评价可见性）
- `PointsLog`（通过 `point_type=consume|member` 区分消费积分流水与会员积分流水，`balance` 表示对应积分类型的变动后余额）
- `CouponTemplate`
- `UserCoupon`
- `InvoiceTitle`
- `InvoiceRequest`（保存申请时订单金额、购买方抬头/税号/邮箱快照，以及发票号码、电子票链接、处理人、处理时间和取消原因）
- `ChatSession`
- `ChatMessage`

### 4.6 reports

- `ReportTask`

### 4.7 operations

- `PlatformConfig`
- `AuditLog`
- `SystemNotice`（支持 `related_order` 关联字段和发票通知类型，用于订单/支付/发票通知精确跳转）
- `AICallLog`（`error_message` 为 `TextField`，可存储完整错误堆栈，截断上限 5000 字符）
- `RuntimeConfig`

---

## 5. 核心能力现状

### 5.1 订单主流程

已实现用户下单、支付、取消，以及管理端改状态、办理入住、办理退房、续住/换房与未入住处理。订单生命周期区分 `paid/confirmed`、`checked_in`、`completed`、`no_show` 等状态：未办理入住且生命周期已结束的已支付订单会进入 `no_show`，不会被错误保留为“已支付”或绕过入住流程直接完结。真实网关支付通过 `/api/v1/payments/notify` 进行签名回调确认；退房额外消费和续住补差会写入 `PaymentRecord`，保证订单金额、支付流水和前台操作可追踪。行前提醒任务会为即将入住的有效订单创建站内通知，提醒住客查看酒店地址、联系方式与入住须知。

### 5.2 会员与 CRM

已实现会员等级、双积分流水、优惠券模板/领取/使用、发票抬头、发票申请与管理端开票处理、收藏、评价与回复。会员积分用于成长升级且不因兑换扣减；消费积分用于优惠券兑换，并为后续礼品兑换保留扩展口径。发票申请会固化订单金额与购买方信息，管理端处理后将发票号码、电子票链接或取消原因回写给用户端，并同步站内通知与审计日志。

### 5.3 AI 能力

已实现：

- 用户端聊天与流式聊天
- 用户端 AI 推荐与酒店对比
- 会话持久化（`ChatSession` / `ChatMessage`）
- 管理端多场景 AI（摘要、定价、经营报告、情感分析、文案生成、异常分析）
- AI 供应商运行时管理
- AI 调用日志与用量统计

### 5.4 异步与巡检

Celery 不仅“框架就绪”，而且已有任务落地：

- 单订单超时取消
- 批量超时订单巡检
- 订单生命周期巡检（过期在住订单自动完结，过期未入住订单标记为 `no_show`）
- 入住前行前提醒巡检（为次日有效订单创建幂等站内通知）
- `sweep_expired_coupons`（每 6 小时巡检过期优惠券，自动标记为 expired）

### 5.5 缓存与性能优化

- `AdminDashboardOverview`：30 s Django cache
- `CommonCitiesView`：10 min Django cache
- `PublicHomeView`：2 min Django cache
- 订单列表视图使用 `_has_review=Count("review")` annotation 避免 N+1
- 通知列表使用 `select_related("related_order")` 避免额外查询
- 库存批量更新使用 `bulk_update` 减少数据库写入次数

---

## 6. API 分域

- `system/*`：系统初始化
- `common/*`：上传、缩略图、字典、城市
- `public/*`：公开查询与认证
- `user/*`：用户业务与 AI
- `admin/*`：管理业务、系统配置与 AI

完整路由见 [`api-inventory.md`](./api-inventory.md)。

---

## 7. 当前未落地（仍为规划）

以下能力可作为“下一阶段”或“后续扩展方向”，但不应写成已实现：

- Room 实体与房间维度房态看板
- 退款单/押金/账单体系
- RBAC 细粒度权限
- WebSocket 实时通知
- 活动管理、导出任务

---

## 8. 文档维护要求

1. 变更 API 后先执行：

```bash
python scripts/docs/generate_api_inventory.py --repo-root .
```

2. 修改模型或核心流程后同步更新本文。
3. 对“规划中”功能必须明确标注，禁止混写为“已实现”。
