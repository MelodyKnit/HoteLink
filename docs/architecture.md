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

### 6.1 users

负责：

- C 端用户
- 酒店员工
- 角色权限
- 登录认证
- 令牌刷新
- 账号状态管理

建议：

- 用户与员工可采用统一账户表 + 扩展资料表方案
- 管理端权限采用 RBAC

### 6.2 hotels

负责：

- 酒店基础资料
- 房型管理
- 房间管理
- 房态管理
- 设施服务

核心实体建议：

- Hotel
- RoomType
- Room
- RoomInventory
- Facility

### 6.3 bookings

负责：

- 预订订单
- 入住登记
- 续住
- 换房
- 退房
- 订单取消

核心实体建议：

- BookingOrder
- BookingGuest
- CheckInRecord
- CheckOutRecord
- StayExtension

### 6.4 payments

负责：

- 支付单
- 退款单
- 押金
- 账单
- 对账

核心实体建议：

- PaymentOrder
- RefundOrder
- DepositRecord
- Bill
- BillItem

### 6.5 crm

负责：

- 客户档案
- 常住客偏好
- 会员等级
- 评价记录

### 6.6 reports

负责：

- 入住率
- 营收统计
- 房态统计
- 订单来源分析

### 6.7 operations

负责：

- 短信/邮件/站内通知
- 系统消息
- 审计日志
- 异步任务

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

## 8. 前端架构建议

## 8.1 user-web

推荐页面：

- 首页
- 酒店列表
- 房型详情
- 提交订单
- 支付结果
- 我的订单
- 会员中心

设计重点：

- 移动端优先
- 表单操作简洁
- 价格、日期、可订状态突出

## 8.2 admin-web

推荐页面：

- 登录页
- 工作台
- 房态总览
- 订单管理
- 入住办理
- 退房结算
- 客户档案
- 财务统计
- 系统设置

设计重点：

- PC 端高信息密度
- 移动端简化列表和审批类操作
- 支持多角色菜单裁剪
- 为房态、营收、订单来源等统计页面预留图表容器

## 8.3 样式体系

建议职责划分：

- Tailwind CSS：布局、间距、字体、响应式、原子样式
- Less：主题变量、业务组件样式、品牌皮肤
- ECharts：统计面板、趋势分析、经营报表的数据可视化

## 8.4 当前前端工程状态

当前已经完成：

- 双应用工作区结构初始化
- 两个应用各自的 `Vite + Vue 3 + TypeScript` 入口
- `Pinia`、`Vue Router`、`Axios` 基础依赖安装
- `Tailwind CSS + Less` 全局样式入口
- `ECharts + Vue ECharts` 图表依赖接入

推荐启动方式：

```bash
cd frontend
npm run dev
```

补充说明：

- `npm run dev` 同时启动两个应用
- `npm run dev:user` 单独启动用户端
- `npm run dev:admin` 单独启动管理端

建议维护以下设计令牌：

- 主色、辅助色、语义色
- 字号层级
- 间距规范
- 圆角规范
- 阴影规范
- 断点规范

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

### 10.1 MySQL

适合核心事务数据：

- 用户
- 酒店
- 房型
- 房间
- 订单
- 支付
- 账单

### 10.2 Redis

适合：

- 登录验证码
- 短期缓存
- 热门酒店列表
- 订单锁定
- 限流与防刷
- Celery Broker / Result Backend

## 11. 异步与定时任务

Celery 任务建议覆盖：

- 订单超时自动取消
- 入住前提醒
- 支付结果异步回调处理
- 日报和统计报表生成
- 短信与邮件发送

## 12. 部署建议

推荐部署形态：

- Nginx
- Django API
- Celery Worker
- Celery Beat
- MySQL
- Redis

建议使用 Docker Compose 启动开发与测试环境，后续再演进到容器化部署。

### 12.1 当前生产容器方案

当前仓库已经提供生产部署骨架：

- 根编排文件：[`docker-compose.prod.yml`](D:\Nakamoto\Documents\Codes\Python\HoteLink\docker-compose.prod.yml)
- 后端镜像：[`backend/Dockerfile`](D:\Nakamoto\Documents\Codes\Python\HoteLink\backend\Dockerfile)
- 前端镜像：[`frontend/Dockerfile`](D:\Nakamoto\Documents\Codes\Python\HoteLink\frontend\Dockerfile)
- 网关配置：[`frontend/docker/nginx.conf`](D:\Nakamoto\Documents\Codes\Python\HoteLink\frontend\docker\nginx.conf)

### 12.2 容器职责

- `web`：Nginx 托管用户端与管理端静态文件，并将 `/api/` 等路径转发到 Django
- `backend`：Gunicorn 承载 Django API，启动时可自动迁移和收集静态资源
- `celery-worker`：处理异步任务
- `celery-beat`：处理定时任务
- `mysql`：主业务库
- `redis`：缓存与消息队列

### 12.3 路由规划

- `/` -> 用户端前端
- `/admin/` -> 酒店管理端前端
- `/api/` -> Django REST API
- `/static/` -> Django collectstatic 产物
- `/media/` -> 用户上传资源

### 12.4 当前状态

当前仓库已经完成：

- 前端双应用工程初始化
- 后端 Django 项目骨架初始化
- `manage.py`
- `config/settings/dev.py`
- `config/settings/prod.py`
- `config/wsgi.py`
- `config/asgi.py`
- `config/celery.py`
- 基础 app 和初始迁移文件

当前仍需继续补充：

- 具体业务模型关系
- 序列化器
- 服务层
- 权限体系
- 真实业务接口

### 12.5 开发环境容器方案

当前也已经补充开发环境编排：

- [`docker-compose.dev.yml`](D:\Nakamoto\Documents\Codes\Python\HoteLink\docker-compose.dev.yml)
- [`backend/Dockerfile.dev`](D:\Nakamoto\Documents\Codes\Python\HoteLink\backend\Dockerfile.dev)
- [`frontend/Dockerfile.dev`](D:\Nakamoto\Documents\Codes\Python\HoteLink\frontend\Dockerfile.dev)

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

## 13. 测试与质量保障

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

## 14. 第一阶段推荐开发范围

建议第一阶段先完成最小可用闭环：

1. 用户登录与员工登录
2. 酒店、房型、房间基础资料
3. 房态管理
4. 订单创建、取消、查询
5. 入住登记、退房结算
6. 基础统计看板

## 15. 第二阶段可扩展能力

- 多酒店/连锁组织架构
- 会员积分体系
- 优惠券
- 微信/支付宝支付
- 发票管理
- 营销活动
- 多语言与国际化
- BI 报表

## 16. 下一步实施建议

从工程落地角度，建议按下面顺序推进：

1. 初始化 Django 项目和基础 app。
2. 初始化前端 Monorepo。
3. 先建用户、酒店、房间、订单四类核心模型。
4. 完成登录鉴权与菜单权限。
5. 实现房态与订单主链路页面。
