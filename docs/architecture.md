# HoteLink 技术架构（源码对齐版）

> 更新时间：2026-04-13  
> 若与其他文档冲突，请优先参考 [`source-of-truth.md`](./source-of-truth.md)

## 1. 总体架构

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

- 路由总数：`103`（含 `/api/v1/` 根路由）
- View 类：`89`
- Serializer 类：`71`
- 业务模型：`21`

### 3.2 前端

- user-web：`26` 路由项、`24` 视图文件
- admin-web：`20` 路由项、`19` 视图文件
- 共享包：
  - `packages/api`
  - `packages/store`
  - `packages/ui`
  - `packages/utils`
  - `packages/styles`

---

## 4. 业务域模型

### 4.1 users

- `UserProfile`（角色、状态、会员等级、积分、资料）

### 4.2 hotels

- `Hotel`
- `RoomType`
- `RoomInventory`

### 4.3 bookings

- `BookingOrder`

### 4.4 payments

- `PaymentRecord`

### 4.5 crm

- `CustomerProfile`
- `FavoriteHotel`
- `Review`
- `PointsLog`
- `CouponTemplate`
- `UserCoupon`
- `InvoiceTitle`
- `InvoiceRequest`
- `ChatSession`
- `ChatMessage`

### 4.6 reports

- `ReportTask`

### 4.7 operations

- `PlatformConfig`
- `AuditLog`
- `SystemNotice`
- `AICallLog`

---

## 5. 核心能力现状

### 5.1 订单主流程

已实现用户下单、支付、取消，以及管理端改状态、办理入住、办理退房。

### 5.2 会员与 CRM

已实现会员等级、积分流水、优惠券模板/领取/使用、发票抬头与申请、收藏、评价与回复。

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
- 订单生命周期异常巡检（自动完结/标记异常）

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

以下能力可作为“下一阶段”或“论文扩展方向”，但不应写成已实现：

- Room 实体与房间维度房态看板
- 续住/换房独立流程
- 退款单/押金/账单体系
- RBAC 细粒度权限
- WebSocket 实时通知
- 活动管理、导出任务、审计日志页面

---

## 8. 文档维护要求

1. 变更 API 后先执行：

```bash
python scripts/docs/generate_api_inventory.py --repo-root .
```

2. 修改模型或核心流程后同步更新本文。
3. 对“规划中”功能必须明确标注，禁止混写为“已实现”。

