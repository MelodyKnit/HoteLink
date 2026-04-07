# HoteLink 酒店管理系统

## 项目定位

HoteLink 是一个面向酒店业务的前后端分离系统，覆盖两类核心使用方：

- 用户 APP 界面：面向住客，支持浏览酒店、查看房型、下单预订、在线支付、订单查询、入住前后服务。
- 酒店管理 APP 界面：面向酒店运营人员，支持房态管理、订单管理、入住退房、客户管理、财务统计、运营配置。

系统采用统一后端、双前端应用的方案，并要求同时兼容 PC 端和移动端。

### 快速命令

后端测试：

```bash
cd backend
python manage.py test apps.api.tests
```

前端类型检查：

```bash
cd frontend
npm run type-check
```

后端健康检查：

```bash
cd backend
python manage.py check
```

## 文档更新约定

为保证“系统能力与文档一致”，后续开发默认执行以下约定：

- 新增或修改接口：同步更新 `docs/api-spec.md`
- 新增或修改 AI 能力：同步更新 `docs/ai-integration.md`
- 新增架构能力或模块：同步更新 `docs/architecture.md`
- 新增前端页面、路由、交互协议：同步更新 `docs/frontend-system-design.md`
- 新增部署或环境变量：同步更新 `docs/deployment.md` 与相关 `.env.example`

建议在每次合并前执行一次“文档差异复核”，确认实现、接口、示例、枚举值一致。

## 本地伪数据脚本约定

为避免将伪数据/临时生成逻辑提交到正式代码区，项目约定如下：

- `backend` 内只保留管理命令桥接壳，不存放具体伪数据实现。
- 真实伪数据脚本统一放在以下任一目录：
  - `backend/private/local-dev/seed_commands/`（Docker 容器默认可见）
  - `private/local-dev/seed_commands/`（仓库根目录本地私有）
  以上目录均被 `.gitignore` 忽略，不参与提交。
- 目前已桥接的命令：
  - `python scripts/generate/seed_demo_data.py`
  - `python scripts/generate/import_hotels_from_dist_images.py --count 200 --images-dir dist/images`
- 若本地缺少对应脚本，命令会直接报错提示，不会影响生产代码。

## 已确定技术方向

### 后端

- Django
- Django REST Framework
- MySQL 8
- Redis
- Celery
- JWT 鉴权
- OpenAI Python SDK
- DeepSeek OpenAI 兼容模型接入

### 前端

- Vue 3
- Vite
- TypeScript
- Pinia
- Vue Router
- ECharts + Vue ECharts
- Tailwind CSS
- Less
- Axios

## 推荐技术补全

### 后端推荐

- `django`：主框架，负责业务建模、后台能力、配置管理。
- `djangorestframework`：统一 REST API 输出。
- `djangorestframework-simplejwt`：用户端和管理端统一 JWT 鉴权。
- `django-cors-headers`：跨域配置。
- `django-filter`：列表筛选与后台查询。
- `mysqlclient` 或 `pymysql`：MySQL 驱动。
- `redis`：缓存、验证码、会话、限流、分布式锁。
- `celery`：异步任务，如短信通知、订单超时关闭、报表生成。
- `django-celery-beat`：定时任务管理。
- `drf-spectacular`：OpenAPI 文档生成。
- `openai`：统一 AI SDK 接入层，用于兼容 DeepSeek 的 OpenAI 风格接口。

### 前端推荐

- `pinia`：状态管理。
- `vue-router`：双端路由管理。
- `axios`：接口请求封装。
- `@vueuse/core`：组合式工具库，适合响应式与端适配能力。
- `echarts` + `vue-echarts`：管理端仪表盘、营收趋势、入住率、订单来源等图表展示。
- `tailwindcss`：基础原子样式与响应式布局。
- `less`：主题变量、复杂样式组织。
- `eslint` + `prettier` + `stylelint`：代码规范。
- `vitest`：单元测试。
- `playwright`：端到端测试。

## 建议项目架构

推荐采用 Monorepo 结构：

```text
HoteLink/
├─ backend/                      # Django 后端
│  ├─ apps/
│  │  ├─ users/                  # 用户、员工、角色、权限
│  │  ├─ hotels/                 # 酒店、房型、房间、设施
│  │  ├─ bookings/               # 预订、订单、入住、退房
│  │  ├─ payments/               # 支付、退款、账单
│  │  ├─ crm/                    # 客户档案、会员、评价
│  │  ├─ reports/                # 经营报表、统计分析
│  │  └─ operations/             # 通知、任务、审计日志
│  ├─ config/
│  │  ├─ settings/
│  │  │  ├─ base.py
│  │  │  ├─ dev.py
│  │  │  └─ prod.py
│  │  ├─ urls.py
│  │  ├─ wsgi.py
│  │  └─ asgi.py
│  ├─ requirements/
│  └─ manage.py
├─ frontend/
│  ├─ apps/
│  │  ├─ user-web/               # 用户端 Web / H5
│  │  └─ admin-web/              # 酒店管理端 Web / H5
│  ├─ packages/
│  │  ├─ ui/                     # 通用组件库
│  │  ├─ api/                    # API 封装
│  │  ├─ utils/                  # 工具函数
│  │  ├─ store/                  # 通用状态模块
│  │  └─ styles/                 # Tailwind、Less、主题变量
│  ├─ package.json
│  ├─ tailwind.config.cjs
│  ├─ postcss.config.cjs
│  └─ tsconfig.base.json
├─ docs/
│  └─ architecture.md
└─ README.md
```

## 两套前端应用建议

### 1. 用户 APP 界面

主要功能：

- 酒店列表、房型详情、价格日历
- 用户注册登录
- 下单预订、支付、退款申请
- 订单查询、取消订单
- 会员中心、发票信息、评价反馈
- 移动端优先，兼顾 PC 浏览与预订

适合的界面策略：

- 以移动端优先设计
- PC 端采用居中内容区和更丰富的信息布局
- 组件风格更偏消费端产品体验

### 2. 酒店管理 APP 界面

主要功能：

- 房态总览
- 房型与房间配置
- 订单管理
- 入住登记与退房结算
- 客户信息维护
- 财务统计与报表
- 系统设置、员工权限、审计日志

适合的界面策略：

- 以 PC 端优先设计，提高管理效率
- 移动端提供简化操作能力，如查房态、改订单、办入住
- 支持不同角色的导航差异化展示

## PC 与移动端适配建议

- 采用同一套 Vue 应用分别适配 PC 和移动端，而不是拆成四个独立项目。
- 使用 Tailwind 的断点系统处理主体布局。
- 通过 Less 管理主题变量、业务色板、间距规范、圆角和阴影。
- 封装 `AppShell`、`PageContainer`、`ResponsiveTable/CardList` 等自适应基础组件。
- 管理端在移动端将表格切换为卡片列表或抽屉详情。
- 用户端页面优先做触控体验，PC 端增强信息密度与筛选能力。

## 核心业务模块建议

### 用户与权限

- C 端用户账户
- 酒店员工账户
- 角色权限 RBAC
- 登录、注销、刷新令牌

### 酒店资源

- 酒店信息
- 房型管理
- 房间管理
- 房态管理
- 设施服务配置

### 订单与入住

- 预订订单
- 入住登记
- 续住
- 换房
- 退房结算
- 订单取消与超时关闭

### 支付与财务

- 订单支付
- 押金管理
- 退款管理
- 账单明细
- 营收统计

### 客户与会员

- 客户档案
- 常住客偏好
- 会员等级
- 评价反馈

## 数据库建议

首选：

- MySQL 8：主业务库
- Redis：缓存、验证码、限流、任务队列辅助

后续可补充：

- Elasticsearch：全文检索与运营分析
- OSS/MinIO：图片、附件、发票等文件存储

## 接口设计建议

- `/api/v1/user/*`：用户端接口
- `/api/v1/admin/*`：管理端接口
- `/api/v1/common/*`：公共能力，如地区、上传、字典

建议统一返回结构、错误码规范、分页格式、上传规范，并优先维护 OpenAPI 文档。

## 非功能性建议

- 日志：接入结构化日志和审计日志
- 安全：JWT + 刷新令牌 + 限流 + 权限校验
- 测试：后端 `pytest`，前端 `vitest` + `playwright`
- 部署：Nginx + Docker + Gunicorn/Uvicorn + Celery Worker
- 监控：Sentry + Prometheus + Grafana

## 当前阶段建议开发顺序

1. 先确定业务模块和数据库模型。
2. 优先细化数据库模型与实体关系。
3. 先完成认证、房态、订单三个主链路。
4. 再补支付、报表、会员、通知等增强模块。
5. 最后补 AI 功能、营销能力和数据分析增强能力。

## 前端当前初始化结果

目前 `frontend` 已完成这些基础搭建：

- `apps/user-web`：用户端应用骨架
- `apps/admin-web`：酒店管理端应用骨架
- `packages/styles`：全局 Tailwind 和 Less 主题入口
- `packages/ui`、`packages/api`、`packages/utils`、`packages/store`：共享包占位结构
- 已安装 `Vue 3`、`Vite`、`TypeScript`、`Pinia`、`Vue Router`、`Axios`、`Tailwind CSS`、`Less`、`ECharts`、`Vue ECharts`

前端启动命令：

```bash
cd frontend
npm run dev
```

说明：

- `npm run dev` 会同时启动 `user-web` 和 `admin-web`
- `npm run dev:user` 单独启动用户端
- `npm run dev:admin` 单独启动管理端

## Docker 生产部署

### 一键 Docker 启动

项目根目录已经提供统一脚本：

- [`scripts/docker.ps1`](scripts/docker.ps1)
- [`scripts/docker.sh`](scripts/docker.sh)

推荐直接使用一条命令启动：

PowerShell：

```powershell
.\scripts\docker.ps1 dev up
.\scripts\docker.ps1 prod up
```

macOS / Linux / Git Bash：

```bash
sh ./scripts/docker.sh dev up
sh ./scripts/docker.sh prod up
```

说明：

- `dev up` 一键启动开发环境
- `prod up` 一键启动生产环境
- 如果 `.env.docker.dev` 或 `.env.docker` 不存在，脚本会自动根据示例文件创建
- 开发环境后端检查可直接运行 `.\scripts\docker.ps1 dev check` 或 `sh ./scripts/docker.sh dev check`

项目已经补充了生产部署所需的 Docker 文件：

- [`docker-compose.prod.yml`](docker-compose.prod.yml)
- [`backend/Dockerfile`](backend/Dockerfile)
- [`backend/docker/entrypoint.sh`](backend/docker/entrypoint.sh)
- [`frontend/Dockerfile`](frontend/Dockerfile)
- [`frontend/docker/nginx.conf`](frontend/docker/nginx.conf)
- [`.env.docker.example`](.env.docker.example)

### 部署结构

- `mysql`：MySQL 8 主数据库
- `redis`：缓存与 Celery Broker
- `backend`：Django + Gunicorn API 服务
- `celery-worker`：异步任务执行器
- `celery-beat`：定时任务调度器
- `web`：Nginx 网关，负责托管用户端、管理端并反向代理后端接口

### 部署后的访问路径

- `/`：用户端
- `/admin/`：酒店管理端前端应用
- `/api/`：后端接口
- `/docs/`、`/redoc/`、`/schema/`：后端文档与 schema

### 使用方式

1. 按你的生产环境修改 `.env.docker`

2. 一键启动生产环境：

```powershell
.\scripts\docker.ps1 prod up
```

或：

```bash
sh ./scripts/docker.sh prod up
```

### 当前注意事项

- 前端镜像已经可以正常构建，并已适配管理端部署到 `/admin/`
- 后端 Django 项目骨架已经初始化完成，包含 `manage.py`、`config/settings`、`config/wsgi.py`、`config/asgi.py`、`config/celery.py`
- Django 自带后台为避免与管理端前端路由冲突，使用 `/superadmin/`
- 后端第一批真实接口已经接入，覆盖认证、公共酒店查询、用户中心、订单、后台概览、酒店管理、房型管理、库存管理、评价与 AI 辅助接口

## Docker 开发环境

项目也已经补充了开发环境编排，目的是：

- 不在本机额外安装 MySQL
- 不在本机额外安装 Redis
- 前后端都可以在容器里跑开发服务
- 改代码后继续使用挂载目录和热更新，而不是每次重新部署生产容器

相关文件：

- [`docker-compose.dev.yml`](docker-compose.dev.yml)
- [`.env.docker.dev.example`](.env.docker.dev.example)
- [`backend/Dockerfile.dev`](backend/Dockerfile.dev)
- [`backend/docker/entrypoint.dev.sh`](backend/docker/entrypoint.dev.sh)
- [`frontend/Dockerfile.dev`](frontend/Dockerfile.dev)

### 开发环境服务

- `mysql`：开发数据库
- `redis`：开发缓存和 Celery Broker
- `backend-dev`：Django 开发容器
- `user-web-dev`：用户端 Vite 开发服务
- `admin-web-dev`：管理端 Vite 开发服务

### 使用方式

1. 按需修改 `.env.docker.dev`

2. 一键启动开发环境：

```powershell
.\scripts\docker.ps1 dev up
```

或：

```bash
sh ./scripts/docker.sh dev up
```

3. 访问地址：

- 用户端：[http://localhost:5173](http://localhost:5173)
- 管理端：[http://localhost:5174/admin/](http://localhost:5174/admin/)
- 后端开发服务：[http://localhost:8000](http://localhost:8000)

### 当前注意事项

- 前端开发容器已经可以直接跑起来
- 后端开发容器会先安装 Poetry 依赖
- 后端 Django 项目骨架已经初始化完成，`backend-dev` 后续可以直接跑 Django 开发服务
- 当前阶段已经具备继续开发和联调第一批真实业务接口的基础

## 后端当前实现进度

当前后端已完成的核心能力包括：

- JWT 注册、登录、管理员登录、刷新令牌、当前用户信息
- 公共首页、酒店列表、搜索建议、酒店详情、评价列表、房型价格日历
- 通用基础接口：上传、城市、字典
- 用户中心资料维护、头像上传、密码修改、收藏、订单创建、订单支付、订单取消、评价提交、优惠券、发票申请、消息通知
- 管理端经营概览、趋势图表、酒店管理、房型管理、库存管理、订单处理、评价回复、用户状态管理、员工账号、系统配置
- AI 辅助接口：用户智能问答、管理端经营摘要、评价摘要、回复建议

当前仍属于第一阶段接口实现，后续还可以继续补：

- WebSocket 实时通知
- 更完整的权限和酒店维度隔离
- 更细的发票、优惠券、系统配置持久化

## 后端演示数据

为了方便本地联调，后端已经提供演示数据初始化命令：

```bash
cd backend
python scripts/generate/seed_demo_data.py
```

如果你使用 Anaconda 的 `Website` 环境，可以运行：

```bash
conda run -n Website python scripts/generate/seed_demo_data.py
```

初始化后可直接使用：

- 管理员账号：`admin / Password123`
- 普通用户账号：`zhangsan / Password123`

## 后端测试与检查

本地开发可运行：

```bash
cd backend
python manage.py check
python manage.py test apps.api
```

如果你使用 Anaconda 的 `Website` 环境，可以运行：

```bash
conda run -n Website python manage.py check
conda run -n Website python manage.py test apps.api
```

Docker 开发环境也已经支持后端检查：

```powershell
.\scripts\docker.ps1 dev check
```

或：

```bash
sh ./scripts/docker.sh dev check
```

说明：
- `backend-dev` 启动时会自动执行 `python manage.py check`
- `backend-check` 仅在开发环境检查时临时使用 MySQL `root` 账号创建 `test_*` 测试库
- 日常业务容器仍使用普通业务账号，避免为了测试放大业务账号权限
- 后续新增前端单元测试时，也需要把测试命令同步补进文档，保证整个项目测试入口完整

说明：

- `backend-dev` 启动前会先执行 `python manage.py check`
- `backend-check` 会在开发容器内执行 `check + test`

## 部署文档

单独的开发环境与生产环境部署说明见：

- [`docs/deployment.md`](docs/deployment.md)

## API 文档

接口设计文档见：

- [`docs/api-spec.md`](docs/api-spec.md)

## AI 集成与密钥安全

项目已经补充了基于 `OpenAI Python SDK` 的 AI 接入骨架，用于对接 DeepSeek 的 OpenAI 兼容接口：

- [`backend/config/ai.py`](backend/config/ai.py)
- [`backend/apps/operations/services/ai_service.py`](backend/apps/operations/services/ai_service.py)
- [`backend/.env.example`](backend/.env.example)

当前默认配置：

- `AI_PROVIDER=deepseek`
- `AI_BASE_URL=https://api.deepseek.com`
- `AI_MODEL=deepseek-chat`
- `AI_REASONING_MODEL=deepseek-reasoner`

推荐的 AI 落点：

- 用户端：
  - 智能客服
  - 酒店 / 房型智能推荐
  - 订单问答与入住指引
  - FAQ 智能问答
- 管理端：
  - 经营数据智能解读
  - 差评与客户反馈摘要
  - 房态 / 营收异常提示
  - 客服回复建议
  - 营销活动文案辅助

建议原则：

- AI 先做“辅助能力”，不要一开始就让 AI 接管关键交易逻辑
- 涉及订单金额、退款、入住资格、支付状态的最终结果必须由业务规则决定
- AI 输出默认视为建议，不应直接作为高风险操作依据

安全规则：

- 真实密钥只写进本地 `.env`、`.env.docker`、`.env.docker.dev`
- 示例文件只保留占位值，可以提交到 GitHub
- `.gitignore` 已经忽略 `.env`、`.env.*`、证书、私钥和本地 secrets 目录
- 不要把真实 `AI_API_KEY` 写进源码、README、提交记录或前端环境变量中

## 架构与界面设计文档

系统架构图、前端信息架构、用户端与管理端完整页面清单见：

- [`docs/frontend-system-design.md`](docs/frontend-system-design.md)

## 论文对齐文档

项目与毕业论文内容对齐说明见：

- [`docs/thesis-alignment.md`](docs/thesis-alignment.md)

## 毕设私密文件管理

与毕业设计直接相关的私密原始材料，例如：

- 论文正文源文件
- 论文提取稿
- 批注版文档
- 答辩材料草稿

统一放在项目根目录的 `private/` 下，例如：

- `private/thesis/`

安全约定：

- `private/` 目录默认加入 `.gitignore`
- 该目录中的内容不上传到 GitHub
- 若后续新增毕设私密材料，也统一放入 `private/` 下管理
- 公开文档中可以引用本地绝对路径，但不要把私密内容复制进公开仓库文档正文

## 文档维护约定

- 新增模块、配置、部署方式、页面、AI 能力时，需要同步更新 `README.md` 与 `docs/` 下相关文档
- 技术架构变更时，优先更新 [`docs/architecture.md`](docs/architecture.md)
- 部署方式变更时，优先更新 [`docs/deployment.md`](docs/deployment.md)
- 页面与功能结构变更时，优先更新 [`docs/frontend-system-design.md`](docs/frontend-system-design.md)
- 接口范围、字段和枚举变更时，优先更新 [`docs/api-spec.md`](docs/api-spec.md)
- AI 相关配置、能力边界和安全规则变更时，优先更新 [`docs/ai-integration.md`](docs/ai-integration.md)
- 与毕业论文主线范围或口径有关的变更时，优先更新 [`docs/thesis-alignment.md`](docs/thesis-alignment.md)

## 当前建议的下一步

1. 设计数据库实体关系图和表结构
2. 设计前端路由表与菜单表
3. 设计认证、权限、菜单与角色体系
4. 设计第一批真实 API 接口
