# HoteLink 技术架构设计

## 1. 总体目标

本系统面向酒店业务场景，建设统一后端与双前端应用：

- 用户端：面向住客，支持预订、支付、订单查询、会员与服务。
- 管理端：面向酒店运营人员，支持房态、订单、入住退房、客户、财务、权限配置。

系统要求：

- 同时支持 PC 端和移动端自适应。
- 前后端分离。
- 支持后期多酒店或连锁门店扩展。
- 保留支付、通知、报表、会员体系的扩展能力。

### 1.1 与毕业论文的口径关系

当前项目文档采用“双层口径”：

- 毕业设计基线方案：以论文原文为准，核心数据库口径为 SQLite，重点验证酒店预订与管理闭环
- 工程增强方案：在不破坏论文主线的前提下，扩展 MySQL、Redis、Docker、AI 等能力

相关对齐说明见：

- [`thesis-alignment.md`](./thesis-alignment.md)

## 2. 技术选型

### 2.1 后端

- 核心框架：Django
- API 框架：Django REST Framework
- 鉴权方案：JWT
- 数据库：MySQL 8
- 缓存与队列：Redis
- 异步任务：Celery
- 定时任务：Celery Beat
- 接口文档：drf-spectacular
- AI 接入层：OpenAI Python SDK
- Prompt 引擎：Jinja2（服务端模板渲染）
- AI 模型：DeepSeek OpenAI 兼容模型

### 2.2 前端

- 构建工具：Vite
- 开发语言：TypeScript
- 核心框架：Vue 3
- 路由管理：Vue Router
- 状态管理：Pinia
- 图表方案：ECharts + Vue ECharts
- 样式方案：Tailwind CSS + Less
- 请求层：Axios
- 测试：Vitest + Playwright

## 3. 架构原则

### 3.1 统一后端，双前端应用

后端统一暴露 REST API，前端拆分为两个独立应用：

- `user-web`
- `admin-web`

这样做的好处：

- 业务角色边界清晰
- 菜单、权限、页面风格可独立演进
- 发布节奏更灵活
- 共享组件和 API 能力仍可复用

### 3.2 响应式优先，而不是多套重复项目

建议每个前端应用只保留一套代码，通过响应式布局适配 PC 与移动端：

- 用户端：移动优先
- 管理端：PC 优先

这样可以降低重复开发和维护成本。

### 3.3 包共享

前端公共逻辑抽到 `packages`：

- `packages/ui`
- `packages/api`
- `packages/utils`
- `packages/store`
- `packages/styles`

## 4. 推荐目录结构

```text
HoteLink/
├─ backend/
│  ├─ apps/
│  │  ├─ api/
│  │  ├─ users/
│  │  ├─ hotels/
│  │  ├─ bookings/
│  │  ├─ payments/
│  │  ├─ crm/
│  │  ├─ reports/
│  │  └─ operations/
│  ├─ config/
│  │  ├─ settings/
│  │  ├─ urls.py
│  │  ├─ wsgi.py
│  │  └─ asgi.py
│  ├─ tests/
│  ├─ manage.py
│  └─ pyproject.toml
├─ frontend/
│  ├─ apps/
│  │  ├─ user-web/
│  │  └─ admin-web/
│  ├─ packages/
│  │  ├─ ui/
│  │  ├─ api/
│  │  ├─ utils/
│  │  ├─ store/
│  │  └─ styles/
│  ├─ package.json
│  ├─ tailwind.config.cjs
│  ├─ postcss.config.cjs
│  └─ tsconfig.base.json
└─ docs/
```

## 5. 后端分层建议

建议 Django 采用如下分层：

- `models`：数据库模型
- `serializers`：输入输出序列化
- `services`：核心业务逻辑
- `selectors`：复杂查询封装
- `views`：接口层
- `tasks`：异步任务

这样可以避免业务逻辑全部堆积在 View 或 Model 中。

## 6. 核心业务模块

### 6.1 api

负责：

- 统一路由注册（`urls.py`）
- 所有 REST 视图（`views.py`，当前 60+ 个 View）
- 序列化器（`serializers.py`，当前 42+ 个 Serializer）
- 权限类（`permissions.py`：`IsAdminRole`、`IsSystemAdminRole`）
- 统一响应格式（`responses.py`：`ApiResponse`、分页辅助）

说明：

- 本项目将所有接口层集中在 `apps/api` 中，其他 app 仅定义 Model 和 Service
- 这种架构避免了 View 分散在多个 app 中导致的路由管理复杂性
- 当前 URL 路由约 71 条，分为 `system/`、`common/`、`public/`、`user/`、`admin/` 五大域

### 6.2 users

负责：

- C 端用户与酒店员工（统一账户表 + 扩展资料表）
- 角色权限（`user` / `hotel_admin` / `system_admin`）
- 登录认证（JWT，用户端与管理端共用）
- 令牌刷新（SimpleJWT）
- 账号状态管理（`active` / `disabled` / `locked`）
- 会员等级体系（`normal` / `silver` / `gold` / `platinum` / `diamond`）

已实现模型：

- **UserProfile**（OneToOne → Django User）：nickname、avatar、mobile、gender、birthday、role、status、member_level、points
- 会员等级关联折扣率（normal 1.0 → diamond 0.88）、积分倍率（normal 1.0x → diamond 3.0x）

### 6.3 hotels

负责：

- 酒店基础资料
- 酒店图片管理（封面图 `cover_image` + 图片画廊 `images` JSONField）
- 房型管理（含房型主图 `image`）
- 库存日历管理

已实现模型：

- **Hotel**：name、city、address、star（1-5）、phone、description、cover_image、images（JSON）、rating、min_price、latitude、longitude、is_recommended、status（draft/online/offline）
- **RoomType**：hotel（FK）、name、bed_type（single/double/queen/twin/family）、area、breakfast_count、base_price、max_guest_count、stock、status（online/offline）、image、description
- **RoomInventory**：room_type（FK）、date、price、stock、status（available/reserved/occupied/cleaning/maintenance/offline）；联合唯一约束 (room_type, date)

规划中模型：

- Room（具体房间管理）
- Facility（设施服务）

### 6.4 bookings

负责：

- 预订订单
- 订单状态流转
- 入住 / 退房操作（管理端）
- 订单取消

已实现模型：

- **BookingOrder**：user（FK）、hotel（FK PROTECT）、room_type（FK PROTECT）、order_no（唯一）、status（pending_payment/paid/confirmed/checked_in/completed/cancelled/refunding/refunded）、payment_status（unpaid/paid/failed/refunded）、check_in_date、check_out_date、guest_name、guest_mobile、guest_count、room_no、remark、operator_remark、original_amount、member_discount_amount、coupon_discount_amount、discount_amount、pay_amount、coupon（FK）、points_earned

规划中模型：

- CheckInRecord、CheckOutRecord（独立入住退房记录）
- StayExtension（续住管理）

### 6.5 payments

负责：

- 支付单管理

已实现模型：

- **PaymentRecord**：order（FK CASCADE）、payment_no（唯一）、method（mock/wechat/alipay/cash/card）、status（unpaid/paid/failed/refunded）、amount、paid_at

规划中模型：

- RefundOrder（退款单）
- DepositRecord（押金管理）
- Bill / BillItem（账单与明细）

### 6.6 crm

负责：

- 客户档案
- 收藏酒店
- 评价管理
- 积分体系
- 优惠券体系
- 发票管理

已实现模型：

- **CustomerProfile**（OneToOne → User）：full_name、mobile、note
- **FavoriteHotel**：user（FK）、hotel（FK）；联合唯一约束 (user, hotel)
- **Review**（OneToOne → BookingOrder）：user（FK）、hotel（FK）、score（1-5）、content、images（JSON）、reply_content
- **PointsLog**：user（FK）、log_type（consume_reward/review_reward/coupon_exchange/admin_adjust/level_up_gift）、points（±）、balance、description、order（FK 可选）
- **CouponTemplate**：name、coupon_type（cash/discount）、amount、discount、min_amount、total_count、claimed_count、per_user_limit、required_level、points_cost、status、valid_days、valid_start、valid_end
- **UserCoupon**：user（FK）、template（FK）、name、coupon_type、amount、discount、min_amount、status（unused/used/expired）、used_order、valid_start、valid_end、used_at
- **InvoiceTitle**：user（FK）、invoice_type（personal/company）、title、tax_no、email
- **InvoiceRequest**：order（FK）、invoice_title（FK）、status（pending/issued/cancelled）

### 6.7 reports

负责：

- 经营报表任务管理

已实现模型：

- **ReportTask**：hotel（FK 可选）、report_type（revenue_summary/order_summary/review_summary）、start_date、end_date、status（pending/running/success/failed）、result_summary

### 6.8 operations

负责：

- 站内通知
- 审计日志
- AI 服务编排

已实现模型：

- **AuditLog**：user（FK 可选）、action、target、detail（JSON）
- **SystemNotice**：user（FK）、notice_type（order/payment/activity/system/review/member/coupon）、title、content、is_read

### 6.9 ai（当前归属 operations + config）

负责：

- AI 配置读取与持久化（`config/ai.py`）
- AI Provider 统一封装（OpenAI SDK 兼容层）
- 多 Provider 并行配置与运行时切换
- 已内置 5 家供应商预设：DeepSeek、OpenAI、智谱、Moonshot、Qwen
- Prompt 模板管理（Jinja2 + StrictUndefined）
- AI 场景白名单与问答边界控制（防幻觉）
- 流式输出能力（SSE）

当前实现要点：

- 配置类：`AIProviderConfig` + `AISettings`（支持磁盘持久化 `.ai_providers.json`）
- 工厂方法：`build_ai_client(provider)` 返回 OpenAI 兼容客户端
- 服务类：`AIChatService` — 支持普通/流式问答、订房编排、数据上下文注入
- Prompt 模板目录：`backend/prompts/customer_service/`（system.j2 + user.j2）
- 模板渲染：`PromptTemplateService`（Jinja2 + StrictUndefined）
- 场景规范化：`general` / `booking_assistant` → `customer_service`
- 未支持场景直接拒绝（`PromptSceneError`），避免无约束生成
- 客服上下文绑定：用户订单、关联酒店/房型、系统通知、系统字典、推荐酒店
- 智能订房编排：命中订房意图时，服务端按城市→酒店→房型阶段输出结构化动作
- 接口层能力：`/api/v1/user/ai/chat`（普通）与 `/api/v1/user/ai/chat/stream`（SSE 流式）
- **当前未真正调用 LLM 的管理端视图**：`AdminAIReportSummaryView`、`AdminAIReviewSummaryView`、`AdminAIReplySuggestionView`（仅返回 fallback 文案）

### 6.10 system-ops

负责：

- 管理端系统重置能力
- 测试环境一键回到初始状态
- 高危操作审计与权限控制

关键约束：

- 仅 `system_admin` 可以执行重置
- 需要明确确认字符串（`RESET`）
- 重置默认保留管理员账号，其余业务数据清空

## 7. 接口规范建议

### 7.1 接口分域

- `/api/v1/user/`
- `/api/v1/admin/`
- `/api/v1/common/`

### 7.2 返回结构

建议统一：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

分页建议统一：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

### 7.3 权限策略

- 用户端接口基于登录态和订单归属控制
- 管理端接口基于角色、菜单、按钮权限控制
- 关键操作增加审计日志

## 8. 前端架构（已落地）

### 8.1 user-web（25 个 Vue 文件）

已实现页面：

| 页面 | 路由 | 说明 |
|------|------|------|
| 首页 | `/` | Banner、推荐酒店、搜索 |
| 酒店列表 | `/hotels` | 搜索、筛选、排序 |
| 酒店详情 | `/hotels/:id` | 轮播、房型列表、评价 |
| 预订填写 | `/booking` | 入住人、日期、优惠券 |
| 支付页 | `/payment/:orderId` | 模拟支付 |
| 支付结果 | `/payment/result/:orderId` | 支付状态展示 |
| 登录 | `/login` | 用户名密码登录 |
| 注册 | `/register` | 用户注册 |
| 我的 | `/my` | 个人中心入口 |
| 我的订单 | `/my/orders` | 订单列表与筛选 |
| 订单详情 | `/my/orders/:id` | 订单信息与操作 |
| 个人资料 | `/my/profile` | 头像、昵称、联系方式编辑 |
| 会员中心 | `/my/membership` | 会员等级、权益 |
| 优惠券 | `/my/coupons` | 优惠券列表与领取 |
| 收藏 | `/my/favorites` | 收藏酒店管理 |
| 评价 | `/my/reviews` | 评价列表与创建 |
| 发票 | `/my/invoices` | 发票抬头与申请 |
| 通知 | `/my/notifications` | 站内通知列表 |
| AI 客服 | `/ai-chat` | 智能客服问答 |
| AI 订房 | `/ai-booking` | AI 辅助订房 |
| 帮助中心 | `/help` | 常见问题 |
| 关于我们 | `/about` | 品牌介绍 |
| 联系我们 | `/contact` | 联系方式 |
| 404 | `/404` | 未找到页面 |

布局组件：`MainLayout.vue`（顶部导航与底部信息）

路由守卫：

- 未登录访问需认证页 → 重定向 `/login?redirect=...`
- 已登录访问登录/注册页 → 重定向首页
- 页面刷新时自动恢复用户信息

设计重点：

- 移动端优先
- 表单操作简洁
- 价格、日期、可订状态突出

### 8.2 admin-web（20 个 Vue 文件）

已实现页面：

| 页面 | 路由 | 说明 |
|------|------|------|
| 系统初始化 | `/admin/setup` | 首次创建管理员 |
| 登录 | `/admin/login` | 管理员登录 |
| 工作台 | `/admin` | 今日指标、趋势图表 |
| 酒店管理 | `/admin/hotels` | 增删改查、图片画廊 |
| 房型管理 | `/admin/room-types` | 按酒店筛选、增删改查 |
| 库存日历 | `/admin/inventory` | 价格库存逐日编辑 |
| 订单管理 | `/admin/orders` | 搜索、筛选、状态操作 |
| 订单详情 | `/admin/orders/:id` | 完整订单信息与操作 |
| 用户管理 | `/admin/users` | 用户列表与状态管理 |
| 会员管理 | `/admin/members` | 会员等级分布 |
| 优惠券管理 | `/admin/coupons` | 券模板增删改 |
| 评价管理 | `/admin/reviews` | 评价列表、AI 回复、手动回复 |
| 报表 | `/admin/reports` | 报表任务管理 |
| 员工管理 | `/admin/employees` | 员工列表与创建 |
| 系统设置 | `/admin/settings` | 平台设置与系统重置 |
| AI 助手 | `/admin/ai` | AI 能力概览 |
| AI 设置 | `/admin/ai-settings` | 供应商管理、模型配置 |
| 404 | `/admin/404` | 未找到页面 |

布局组件：`AdminLayout.vue`（侧边栏 + 顶部操作区）

路由守卫：

- 系统未初始化 → 强制跳转 `/admin/setup`
- 未登录 → 重定向 `/admin/login`
- 登录后角色校验 → 非管理员自动登出
- 页面刷新时自动恢复会话

### 8.3 样式体系

当前职责划分：

- **Tailwind CSS**：布局、间距、字体、响应式、原子样式；品牌色 `#0f766e`（dark `#115e59`、light `#14b8a6`）
- **Less**：主题变量、业务组件样式、品牌皮肤
- **ECharts**：仪表盘趋势图表（营收、订单量、入住率）

### 8.4 公共组件与交互体系（packages/）

当前已实现的共享包：

| 包 | 内容 |
|----|------|
| `@hotelink/api` | 23 个 API 模块（Axios 实例 + Bearer Token 拦截器 + 401 自动跳转） |
| `@hotelink/store` | 2 个 Pinia Store（`useAuthStore` 管理端、`useUserAuthStore` 用户端） |
| `@hotelink/ui` | 10 个公共组件（StatCard、DataTable、ModalDialog、StatusBadge、PageHeader、EmptyState、Pagination、Toast、SelectField、ConfirmDialog）+ 2 个 Composable（`useToast`、`useConfirm`）|
| `@hotelink/utils` | 5 个格式化工具（formatDate、formatDateTime、formatMoney、debounce、extractApiError）+ 6 个枚举映射（ORDER_STATUS_MAP、ROOM_STATUS_MAP、HOTEL_STATUS_MAP、BED_TYPE_MAP、PAYMENT_METHOD_MAP、PAYMENT_STATUS_MAP）|
| `@hotelink/styles` | 全局 Tailwind + Less 样式入口 |

### 8.5 前端工程状态

当前已完成：

- 双应用工作区结构（`apps/admin-web` + `apps/user-web`）
- 两个应用各自的 `Vite + Vue 3 + TypeScript` 入口
- `Pinia`、`Vue Router`、`Axios` 基础依赖
- `Tailwind CSS + Less` 全局样式入口
- `ECharts + Vue ECharts` 图表依赖
- 用户端 23 个页面、管理端 18 个页面已完整实现
- 共享组件库、API SDK、状态管理、工具函数全部落地

启动方式：

```bash
cd frontend
npm run dev          # 同时启动两应用
npm run dev:user     # 单独启动用户端（5173）
npm run dev:admin    # 单独启动管理端（5174）
npm run build        # 构建两应用
npm run type-check   # TypeScript 类型检查
```

构建配置：

- TypeScript 目标：ES2020，严格模式
- Vite 开发代理：`/api`、`/media`、`/static`、`/docs`、`/redoc`、`/schema` → 后端 8000 端口

## 9. 自适应策略

### 9.1 断点建议

- `sm`：移动端
- `md`：平板
- `lg`：小屏桌面
- `xl`：桌面管理端主体验

### 9.2 用户端

- 列表改为单列或双列卡片
- 日期选择和订单流程优先触摸操作
- 底部导航适配移动端

### 9.3 管理端

- 宽屏下采用侧边栏 + 顶部操作区
- 小屏下切换为抽屉菜单
- 表格在移动端退化为卡片详情块

## 10. 数据库与缓存策略

### 10.1 MySQL / SQLite

当前双模式配置：

- **开发本地**：SQLite（`backend/db.sqlite3`），无需安装额外数据库
- **Docker 开发**：MySQL 8.4 容器，通过环境变量 `DB_HOST` 切换
- **生产环境**：MySQL 8.4 容器，charset `utf8mb4`

核心事务数据（16 个模型）：

- users：UserProfile
- hotels：Hotel、RoomType、RoomInventory
- bookings：BookingOrder
- payments：PaymentRecord
- crm：CustomerProfile、FavoriteHotel、Review、PointsLog、CouponTemplate、UserCoupon、InvoiceTitle、InvoiceRequest
- reports：ReportTask
- operations：AuditLog、SystemNotice

### 10.2 Redis

当前已配置 3 个 DB：

- **DB 0**：通用缓存（`REDIS_URL` 环境变量）
- **DB 1**：Celery Broker
- **DB 2**：Celery Result Backend

Docker 环境使用 Redis 7.4 Alpine，AOF 持久化已开启。

当前实际使用场景：

- Celery 消息队列（已配置，待任务定义）
- 图片缩略图缓存（`CommonImageThumbView` 使用内存缓存，可切换 Redis）

规划中的 Redis 使用场景：

- 登录验证码
- 短期缓存
- 热门酒店列表
- 订单锁定
- 限流与防刷
- Celery Broker / Result Backend

## 11. 异步与定时任务

Celery 框架已配置完成（Broker: Redis DB1，Result Backend: Redis DB2），Docker 开发/生产环境均已包含 `celery-worker` 和 `celery-beat` 服务。

当前状态：**框架已就绪，暂无具体任务定义**。`autodiscover_tasks()` 已启用，后续在 app 中添加 `tasks.py` 即可生效。

规划中的 Celery 任务：

- 订单超时自动取消
- 入住前提醒
- 支付结果异步回调处理
- 日报和统计报表生成
- 短信与邮件发送
- AI 摘要与标签生成
- 差评分析与风险预警任务

## 12. AI 能力架构建议

### 12.1 接入原则

- 统一通过后端接入 AI，前端不直接暴露真实 API Key
- 使用 `openai` SDK 作为统一客户端
- 通过 `base_url` 对接 DeepSeek OpenAI 兼容接口
- 所有 AI 密钥只放在本地 `.env` 或部署环境变量中

### 12.2 推荐 AI 功能落点

#### 用户端

- 智能客服问答
- 酒店推荐助手
- 房型推荐助手
- 订单说明与入住须知解读
- 发票与退改规则解释

#### 管理端

- 经营数据智能总结
- 差评与反馈自动摘要
- 客诉优先级判断建议
- 营销活动文案生成
- 运营公告草稿生成
- 常见客服回复建议

### 12.3 风险边界

- AI 不直接决定支付、退款、入住资格等高风险结果
- AI 输出默认是建议，不是最终业务结果
- 涉及金额、库存、订单状态的内容必须以数据库与业务规则为准
- 需要保留 AI 调用日志与人工复核入口

## 13. 部署建议

推荐部署形态：

- Nginx
- Django API
- Celery Worker
- Celery Beat
- MySQL
- Redis

建议使用 Docker Compose 启动开发与测试环境，后续再演进到容器化部署。

### 13.1 当前生产容器方案

当前仓库已经提供生产部署骨架：

- 根编排文件：[`../docker-compose.prod.yml`](../docker-compose.prod.yml)
- 后端镜像：[`../backend/Dockerfile`](../backend/Dockerfile)
- 前端镜像：[`../frontend/Dockerfile`](../frontend/Dockerfile)
- 网关配置：[`../frontend/docker/nginx.conf`](../frontend/docker/nginx.conf)

### 13.2 容器职责

- `web`：Nginx 托管用户端与管理端静态文件，并将 `/api/` 等路径转发到 Django
- `backend`：Gunicorn 承载 Django API，启动时可自动迁移和收集静态资源
- `celery-worker`：处理异步任务
- `celery-beat`：处理定时任务
- `mysql`：主业务库
- `redis`：缓存与消息队列

### 13.3 路由规划

- `/` -> 用户端前端
- `/admin/` -> 酒店管理端前端
- `/api/` -> Django REST API
- `/static/` -> Django collectstatic 产物
- `/media/` -> 用户上传资源

### 13.4 当前状态

当前仓库已经完成：

- 后端 Django 项目完整骨架与配置（settings、wsgi、asgi、celery、ai）
- 7 个业务 app（users、hotels、bookings、payments、crm、reports、operations）
- 16 个数据库模型（完整字段、关系、约束）
- 60+ 个 REST 视图（涵盖系统初始化、认证、公共查询、用户端全流程、管理端全功能）
- 42+ 个序列化器
- 71 条 URL 路由（system / common / public / user / admin）
- AI 多供应商接入层（5 家预设 + 运行时切换 + 磁盘持久化）
- AI 客服 + 订房编排（Jinja2 Prompt、上下文注入、SSE 流式输出）
- 前端双应用完整实现（用户端 23 页面 + 管理端 18 页面）
- 共享包体系（API SDK、Store、UI 组件库、工具库、样式）
- Docker 开发与生产环境编排、Nginx 网关、统一脚本

规划中待补充：

- 具体房间（Room）模型与房态看板
- 独立入住/退房记录模型
- 续住、换房流程
- 退款单、押金、账单模型
- WebSocket 实时通知
- RBAC 精细权限管理
- 管理端 AI 功能真正调用 LLM（当前为 fallback）
- Celery 异步任务定义（框架已配置，暂无具体任务）
- 详见 [feature-improvements.md](./feature-improvements.md) 完整规划
- 序列化器
- 服务层
- 权限体系
- 真实业务接口

### 13.5 开发环境容器方案

当前也已经补充开发环境编排：

- [`../docker-compose.dev.yml`](../docker-compose.dev.yml)
- [`../backend/Dockerfile.dev`](../backend/Dockerfile.dev)
- [`../frontend/Dockerfile.dev`](../frontend/Dockerfile.dev)

开发环境的目标是：

- 用容器承载 MySQL 和 Redis
- 用容器直接运行 Django 开发服务
- 用容器直接运行两个 Vite 开发服务
- 使用卷挂载源码，避免每次改代码都重新部署生产镜像

开发环境默认端口：

- `5173`：用户端
- `5174`：管理端
- `8000`：后端
- `3306`：MySQL
- `6379`：Redis

## 14. 测试与质量保障

后端：

- `pytest`
- `pytest-django`
- `factory-boy`

前端：

- `vitest`
- `@testing-library/vue`
- `playwright`

规范工具：

- `eslint`
- `prettier`
- `stylelint`
- `commitlint`

## 15. 已完成的开发范围

当前系统已完成以下核心闭环：

1. ✅ 用户注册、用户登录、管理员登录、JWT 令牌管理
2. ✅ 酒店、房型、库存日历基础资料 CRUD
3. ✅ 订单创建、支付、取消、查询（用户端 + 管理端）
4. ✅ 入住登记、退房结算（管理端操作）
5. ✅ 经营统计看板（今日指标 + 趋势图表）
6. ✅ 评价系统（用户创建评价 + 管理端回复 + AI 回复建议）
7. ✅ 会员等级体系（5 级 + 折扣 + 积分倍率）
8. ✅ 优惠券体系（模板、领取、下单使用）
9. ✅ 发票管理（抬头、申请）
10. ✅ 站内通知（7 种类型 + 已读管理）
11. ✅ AI 客服与订房编排（多轮对话 + SSE 流式）
12. ✅ AI 多供应商管理（5 家预设 + 运行时切换）
13. ✅ Docker 开发与生产环境完整部署
14. ✅ 前端双端完整页面实现

## 16. 下一阶段可扩展能力

- 具体房间管理与房态看板
- 续住 / 换房 / 退款单 / 押金 / 账单
- RBAC 精细权限管理
- WebSocket 实时通知
- 管理端 AI 功能真正调用 LLM
- AI 智能定价、经营报告、情感分析、营销文案等
- 多酒店 / 连锁组织架构
- 微信 / 支付宝真实支付
- 全文搜索引擎
- 多语言与国际化
- BI 报表深化

详见 [feature-improvements.md](./feature-improvements.md) 完整规划。

## 17. 文档维护要求

- 新增模块时同步更新本文件
- 新增部署方式时同步更新 `deployment.md`
- 新增页面或菜单时同步更新 `frontend-system-design.md`
- 新增 AI 能力时同步更新 `ai-integration.md`
- 新增与论文口径有关的差异时同步更新 `thesis-alignment.md`

## 18. 下一步实施建议

从工程落地角度，建议按下面顺序推进后续开发：

1. 管理端 AI 三个视图接入真实 LLM 调用（P0，详见 feature-improvements.md §1.1）
2. 具体房间（Room）模型与房态看板（P1）
3. 续住 / 换房 / 退款单 / 押金 / 账单模型与接口（P1）
4. RBAC 精细权限模型（P1）
5. Celery 异步任务落地（订单超时取消、入住提醒等）（P1）
6. AI 智能定价、情感分析、营销文案等高级 AI 功能（P2）
7. WebSocket 实时通知（P2）
8. 自动化测试覆盖率提升（P2）
