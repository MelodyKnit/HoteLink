# HoteLink API 规范（源码对齐版）

> 更新时间：2026-04-18  
> 对齐基线：`backend/apps/api/urls.py`、`backend/apps/api/views.py`

## 1. 文档范围

本文件仅描述仓库**已落地实现**的 HTTP API 规范。  
完整路由清单请直接查看自动生成文档：

- [`api-inventory.md`](./api-inventory.md)

若本文件与代码不一致，以源码和 `api-inventory.md` 为准。

---

## 2. 当前实现快照

- API 前缀：`/api/v1/`
- 已注册路由：`114`
- 分组统计：
  - system：`2`
  - common：`4`
  - public：`10`
  - user：`36`
  - admin：`61`

---

## 3. 统一请求与响应

### 3.1 请求格式

- 默认：`Content-Type: application/json`
- 上传：`multipart/form-data`
- 认证：`Authorization: Bearer <access_token>`

### 3.2 统一响应结构

后端统一通过 `api_response()` 返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

说明：

- 当前后端未统一返回 `request_id` 与 `timestamp` 字段。

### 3.3 分页结构

列表接口统一通过 `paginated_response()` 返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0
  }
}
```

---

## 4. 认证与权限

### 4.1 认证方式

- 认证框架：`JWT (SimpleJWT)`
- 登录接口：
  - `POST /api/v1/public/auth/login`
  - `POST /api/v1/public/auth/admin-login`
- 刷新接口：
  - `POST /api/v1/public/auth/refresh`
- 登出接口：
  - `POST /api/v1/user/auth/logout`

补充说明：

- 刷新接口启用 Refresh Token 轮换，成功响应会返回新的 `access_token`，并在启用轮换时一并返回新的 `refresh_token`
- 登出接口会尝试将提交的 `refresh_token` 加入黑名单，降低令牌泄露后的持续利用风险

### 4.2 角色

- `user`
- `hotel_admin`
- `system_admin`

管理端关键配置、系统重置等高风险接口只允许管理员访问，部分仅 `system_admin` 可用。

### 4.3 安全基线

- 全局启用 DRF 限流，匿名与登录用户都有默认速率限制
- 登录、刷新、登出、首次初始化、上传、AI 生成类接口使用更严格的 scoped throttle
- 注册接口独立限流（`3/minute`），防止批量注册
- 用户修改密码后，旧 Token 会被加入黑名单，同时返回新 Token
- 已禁用的用户尝试登录时，登录接口直接拒绝
- 生产环境默认关闭 `/docs/`、`/redoc/`、`/schema/`，仅在 `ENABLE_API_DOCS=1` 时显式开启

---

## 5. 错误码（当前代码中已使用）

| code | 含义 |
|---|---|
| `0` | 成功 |
| `4001` | 参数错误 |
| `4002` | 缺少必要参数 |
| `4003` | 业务规则不满足 |
| `4010` | 用户名或密码错误 / 未登录 |
| `4011` | Token 无效 |
| `4030` | 无权限 |
| `4040` | 资源不存在 |
| `4090` | 资源冲突（如唯一键冲突） |
| `4093` | 状态冲突（当前状态不允许操作） |

---

## 6. 已实现接口域

完整接口见 [`api-inventory.md`](./api-inventory.md)。本节给出核心域说明。

### 6.1 System

- 系统初始化检查：`GET /api/v1/system/init-check`
- 系统首次初始化：`POST /api/v1/system/init-setup`

### 6.2 Common

- 文件上传：`POST /api/v1/common/upload`
- 图片缩略图：`GET /api/v1/common/image-thumb`
- 城市列表：`GET /api/v1/common/cities`
- 字典查询：`GET /api/v1/common/dicts`

### 6.3 Public

- 首页、酒店列表、酒店详情、评价、房态日历
- `GET /api/v1/public/hotels` 支持查询参数：`keyword`、`city`、`star`、`type`（hotel/homestay/short_rent）、`facilities`（逗号分隔）、`min_price`、`max_price`、`sort`
- 用户注册/登录、管理员登录、刷新令牌

### 6.4 User

- 用户资料、头像、改密
- 收藏、订单、支付、取消、评价、积分、优惠券、发票、通知
- AI：聊天、流式聊天、推荐、对比、会话管理
- 发票抬头编辑/删除：`POST /api/v1/user/invoices/title/update`、`POST /api/v1/user/invoices/title/delete`（有开票记录的抬头不可删除，返回 4091）

注意：

- `/api/v1/user/ai/recommendations` 当前是 `POST`（非 `GET`）
- `/api/v1/user/ai/hotel-compare` 当前是 `POST`
- `/api/v1/user/notices` 支持 `GET`/`POST`/`DELETE`
- `/api/v1/user/notices` 的 `GET` 响应项新增 `related_order_id`、`related_order_no`，用于订单通知直达详情页
- `/api/v1/user/orders` 支持多维筛选参数：`status`、`payment_status`、`keyword`、`check_in_start`、`check_in_end`、`created_start`、`created_end`、`amount_min`、`amount_max`
- `/api/v1/user/ai/chat` 与 `/api/v1/user/ai/chat/stream` 支持可选 `session_id`（续聊）；服务端会自动写入会话消息
- `/api/v1/user/ai/chat` 与 `/api/v1/user/ai/chat/stream` 支持可选 `conversation_summary`（历史对话压缩摘要，最长 4000 字符）

### 6.5 Admin

- 仪表盘、酒店/房型/库存、订单处理、评价、用户、员工、设置、报表
- 优惠券与会员概览
- 系统状态与系统重置
- AI：配置、供应商管理、摘要、定价、经营报告（含流式）、情感分析、文案与内容生成、异常分析、调用日志、用量统计
- **员工管理完善**：`POST /api/v1/admin/employees/update`（编辑昵称/手机/角色，仅限 hotel_admin↔receptionist）、`POST /api/v1/admin/employees/change-status`（启用/禁用）、`POST /api/v1/admin/employees/reset-password`（重置为 Abc123456）
- **用户管理完善**：`POST /api/v1/admin/users/update`（编辑昵称/手机/会员等级）、`POST /api/v1/admin/users/reset-password`（重置为 Abc123456）
- **优惠券管理完善**：`POST /api/v1/admin/coupons/update` 现支持全字段编辑（名称/类型/面额/折扣/门槛/库存/积分/等级/有效期/状态）；新增 `POST /api/v1/admin/coupons/delete`（已有用户领取则返回 4091 禁止删除）
- **报表任务删除**：`POST /api/v1/admin/reports/tasks/delete`（运行中的任务不可删除，返回 4091）
- **删除安全**：酒店删除和房型删除前校验是否存在进行中订单（4091 阻断），通知批量删除前端增加二次确认弹窗

补充说明：

- `GET /api/v1/admin/ai/settings` 仅 `system_admin` 可访问，供应商列表不会回传明文 `api_key`；编辑时若不提交 `api_key`，服务端会保留原密钥。
- `POST /api/v1/admin/ai/test` 用于管理端连通性测试，可验证当前或指定供应商是否可用。
- `GET /api/v1/admin/ai/call-logs` 分页查询 AI 调用历史记录；支持 `scene`、`status` 过滤参数；响应字段包含 `id`、`scene`、`provider`、`model`、`input_tokens`、`output_tokens`、`total_tokens`、`latency_ms`、`cost_estimate`、`status`、`error_message`（完整错误文本，最长 5000 字符）、`username`、`created_at`。
- `GET /api/v1/admin/ai/usage-stats` 按场景/状态汇总 token 用量与费用；支持 `start_date`、`end_date` 过滤；响应包含 `success_count`、`failed_count`、`total_tokens`、`cost_estimate`、`by_scene`、`by_status`。
- `GET /api/v1/admin/hotels` 支持 `type` 查询参数过滤酒店类型
- `POST /api/v1/admin/hotels/batch-update` 批量更新酒店类型，接受 `hotel_ids`（列表）和 `type`
- `GET /api/v1/common/dicts` 新增字典项：`hotel_type`（酒店/民宿/短租）、`hotel_facility`（16 项设施枚举）
- `GET /api/v1/admin/orders` 支持筛选参数：`status`、`payment_status`、`keyword`、`check_in_date`（入住日期）、`check_out_date`（退房日期），其中 `check_in_date` / `check_out_date` 为精确日期过滤
- 管理端列表接口支持 `ordering` 参数（白名单校验，非法值自动回退为 `-id`）：
  - `GET /api/v1/admin/orders`：`id`、`order_no`、`guest_name`、`guest_mobile`、`hotel__name`、`room_type__name`、`check_in_date`、`check_out_date`、`pay_amount`、`status`、`payment_status`、`created_at`、`updated_at`
  - `GET /api/v1/admin/users`：`id`、`user__username`、`nickname`、`mobile`、`gender`、`role`、`member_level`、`points`、`status`、`created_at`、`updated_at`
  - `GET /api/v1/admin/employees`：`id`、`user__username`、`nickname`、`mobile`、`role`、`status`、`created_at`、`updated_at`
  - `GET /api/v1/admin/reports/tasks`：`id`、`report_type`、`hotel__name`、`start_date`、`end_date`、`status`、`created_at`、`updated_at`

注意：

- `/api/v1/admin/orders/detail` 返回订单基础信息外，还包含 `payments`（支付记录列表）与订单状态时间字段（如 `paid_at`、`confirmed_at`、`checked_in_at`、`completed_at`、`cancelled_at`）

---

## 7. 关键业务流示例

### 7.1 用户下单并支付

1. `POST /api/v1/user/orders/create`
2. `POST /api/v1/user/orders/pay`
3. 管理端可后续执行：
   - `POST /api/v1/admin/orders/check-in`
   - `POST /api/v1/admin/orders/check-out`
  - `POST /api/v1/admin/orders/extend-stay`
  - `POST /api/v1/admin/orders/switch-room`

### 7.2 用户 AI 对话（含订房编排）

1. `POST /api/v1/user/ai/chat`
2. 如需流式输出：`POST /api/v1/user/ai/chat/stream`
3. 会话记录：
   - `GET /api/v1/user/ai/sessions`
   - `POST /api/v1/user/ai/sessions`（删除动作）
   - `GET /api/v1/user/ai/sessions/<int:session_id>/messages`

返回约定补充（客服快捷操作）：

- `data.booking_assistant.phase = "quick_actions"`
- 订房场景识别到客服诉求时：`data.booking_assistant.phase = "switch_to_customer_service"`
- `data.booking_assistant.context.detected_intent`：服务端识别的意图（如 `cancel_order`、`pay_order`、`invoice`、`review`）
- `data.booking_assistant.options[]` 支持统一动作协议字段：
  - `type`：动作类型（如 `navigate_cancel_order`、`navigate_reviews`、`navigate_ai_booking`、`navigate_ai_customer_service`）
  - `action_type`：当前为 `navigate`
  - `route` / `target`：目标路由
  - `query` / `params`：跳转参数（含 `source=ai`、`intent`、`from`，跨助手切换时可带 `ask`）
  - `requires_confirmation`：是否建议二次确认
  - `priority`：动作优先级（数值越小越优先）
  - `tracking_id`：动作追踪 ID

---

## 8. 规划中接口（未实现）

以下接口在历史文档中出现过，但当前代码未落地，仅可作为规划项记录：

- Room 维度接口（`/admin/rooms*`）
- 活动管理（`/admin/activities*`）
- 导出任务（`/admin/exports*`）
- 后台通知中心（`/admin/notices*`）
- 审计日志查询（`/admin/audit-logs`）
- RBAC（`/admin/roles*`、`/admin/permissions`）
- 退款/押金/账单（`/admin/refunds*`、`/admin/deposits*`、`/admin/bills*`）
- 浏览历史/订单分享（`/user/browsing-history*`、`/user/orders/share`）

---

## 9. 维护规则

1. 改动路由或请求方法后，先更新代码，再执行：

```bash
python scripts/docs/generate_api_inventory.py --repo-root .
```

2. `api-spec.md` 只保留“规则和分组语义”，不再手工维护超长逐条路由表。
3. 所有逐条路由列表统一以 [`api-inventory.md`](./api-inventory.md) 为准。
