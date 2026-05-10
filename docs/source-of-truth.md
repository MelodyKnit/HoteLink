# HoteLink 源码对齐基线

## 1. 目的

本文件是“文档与源码对齐”的基线说明。
若其他文档与源码冲突，以以下事实优先：

1. `backend/apps/api/urls.py`
2. `backend/apps/api/views.py`
3. `backend/apps/*/models.py`
4. `docker-compose.dev.yml` / `docker-compose.prod.yml`
5. `frontend/apps/*/src/router/index.ts`

### 1.1 这份文档怎么用

- 想确认某个功能是不是“真的已经做了”，先看这里。
- 想快速知道系统现在的路由、模型、AI 和前端规模，也先看这里。
- 如果你需要接口参数细节，请继续看 [`api-spec.md`](./api-spec.md)。
- 如果你需要页面和交互细节，请继续看 [`frontend-system-design.md`](./frontend-system-design.md)。
- 如果你看到 `feature-improvements.md` 里有某项写得很大，但不确定是否已落地，以本文为准。

---

## 2. 已核对的真实实现

### 2.1 后端路由与接口

- 已注册路由：`127`（含 `/api/v1/` 根路由）
- 根路由：`1`
- 系统：`2`
- 通用：`4`
- 公共：`10`
- 用户端：`37`
- 管理端：`72`
- 其他：`1`（`/api/v1/payments/notify`）
- 完整清单见：[`api-inventory.md`](./api-inventory.md)（由脚本自动生成）

### 2.2 数据模型

- 业务模型总数：`22`（`backend/apps` 7 个业务模块）
- users: 1（`UserProfile`）
- hotels: 3（`Hotel`/`RoomType`/`RoomInventory`）
- bookings: 1（`BookingOrder`）
- payments: 1（`PaymentRecord`）
- crm: 10（含 `ChatSession`、`ChatMessage`）
- reports: 1（`ReportTask`）
- operations: 5（含 `AICallLog`、`PlatformConfig`、`RuntimeConfig`）
- `PaymentRecord` 已扩展为真实支付与前台结算预留结构，除基础流水号/金额外，还包含 `gateway_name`、`gateway_label`、`provider_type`、`scene`、`external_trade_no`、请求/响应载荷与 `notify_payload` 回调载荷字段。
- `RuntimeConfig` 当前同时承担 AI 供应商配置与支付网关运行时配置持久化；支付网关配置包含 `notify_secret`，用于真实支付异步通知的 HMAC 签名校验，接口响应不回显明文。
- `UserProfile` 使用双积分口径：`member_points` 是会员成长积分，只用于等级升级；`consume_points` 是可兑换消费积分余额；`points` 作为旧接口兼容字段保留并等同消费积分。
- `PointsLog` 使用 `point_type=consume|member` 区分两类积分流水，`balance` 表示对应类型的变动后余额。
- `BookingOrder.points_earned` 表示本单发放的消费积分，`BookingOrder.member_points_earned` 表示本单累计的会员积分。
- `BookingOrder.status` 包含 `no_show`，用于表示已支付/已确认订单在未办理入住的情况下超过生命周期窗口；`no_show_at` 记录标记时间，支付状态不因未入住自动改为退款。
- `InvoiceRequest` 保存申请时的订单金额、发票类型、抬头、税号和邮箱快照，并保存管理端处理后的发票代码、发票号码、电子票链接、处理人、处理时间和处理说明；同一订单只能存在一条发票申请。
- `SystemNotice.notice_type` 包含 `invoice`，管理端发票处理结果会通过站内通知关联到对应订单。

### 2.3 Celery 与定时任务

- Celery 已启用且有真实任务，不是“仅框架预留”：
  - `apps.bookings.tasks.auto_cancel_unpaid_order`
  - `apps.bookings.tasks.sweep_timeout_unpaid_orders`
  - `apps.bookings.tasks.sweep_order_lifecycle_anomalies`
  - `apps.bookings.tasks.send_upcoming_checkin_reminders`
- 订单生命周期巡检会自动完结过期在住订单，并将过期未入住的 `paid/confirmed` 订单标记为 `no_show`；订单列表/详情读取和关键写操作也会触发生命周期修复，避免展示或操作陈旧状态。
- Beat 调度已在 `config/settings/base.py` 配置：
  - `order-timeout-sweep`
  - `order-lifecycle-sweep`
  - `checkin-reminder-sweep`
  - `coupon-expire-sweep`

### 2.4 AI 能力

- 用户端 AI 已实现并可调用：
  - 聊天 `/user/ai/chat`
  - 流式聊天 `/user/ai/chat/stream`
  - 聊天与流式接口均会自动持久化会话消息，可通过可选 `session_id` 续聊
  - 推荐 `/user/ai/recommendations`（`POST`）
  - 酒店对比 `/user/ai/hotel-compare`（`POST`）
  - 会话列表/删除 `/user/ai/sessions`（`GET`/`POST`）
  - 会话消息 `/user/ai/sessions/<int:session_id>/messages`
- 管理端 AI 已实现并落地：
  - 摘要、回复建议、定价、经营报告（含流式）
  - 情感分析、营销文案、内容生成、异常分析
  - AI 调用日志、AI 用量统计
  - 供应商管理（增删改切换）

### 2.5 前端路由

- user-web：`28` 个路由项（含 404 捕获），`25` 个视图文件
- admin-web：`28` 个路由项（含 404 捕获），`26` 个视图文件

---

## 3. 防漂移维护规则

1. 路由、模型、页面数量以源码和生成文档为准，不在官方文档中保留历史统计痕迹。
2. API 方法、枚举、状态流转、支付/积分/发票等业务口径必须直接对齐 `views.py`、`serializers.py` 与模型字段。
3. 已实现能力写入当前状态说明；未实现能力仅放入规划区，不能与已落地接口混排。
4. 设计推演、审查记录、局部修复理由和交付过程记录放入 `worknote/`，不写入官方文档。

---

## 4. 项目缺少的“防漂移”能力（已补齐）

已新增脚本：

- [`../scripts/docs/generate_api_inventory.py`](../scripts/docs/generate_api_inventory.py)

作用：

- 自动解析 `urls.py + views.py`
- 继承解析 `APIView` 方法（`GET/POST/DELETE/...`）
- 生成文档：[`api-inventory.md`](./api-inventory.md)

建议在每次改动 API 路由后执行：

```bash
python scripts/docs/generate_api_inventory.py --repo-root .
```

---

## 5. 仍属“规划中”的能力（源码未落地）

以下方向在文档中可保留为规划，但不能写成“已实现”：

- Room 实体与房间维度房态看板
- 退款单/押金/账单模型与流程
- RBAC 细粒度权限模型（角色-权限-菜单-按钮）
- WebSocket 实时通知
- 活动管理、导出任务等多项后台扩展页
