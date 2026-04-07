# HoteLink 论文与实现对齐说明

## 1. 文档目的

本文用于记录论文表述、设计文档与当前仓库实现之间的对齐关系，避免文档描述超过系统现状。

当前判断“是否已经实现”的主要依据为：

- 路由与接口代码：[backend/apps/api/urls.py](D:\Nakamoto\Documents\Codes\Python\HoteLink\backend\apps\api\urls.py)
- 视图实现：[backend/apps/api/views.py](D:\Nakamoto\Documents\Codes\Python\HoteLink\backend\apps\api\views.py)
- Docker 编排：[docker-compose.dev.yml](D:\Nakamoto\Documents\Codes\Python\HoteLink\docker-compose.dev.yml) 与 [docker-compose.prod.yml](D:\Nakamoto\Documents\Codes\Python\HoteLink\docker-compose.prod.yml)
- 部署脚本：[scripts/docker.ps1](D:\Nakamoto\Documents\Codes\Python\HoteLink\scripts\docker.ps1) 与 [scripts/docker.sh](D:\Nakamoto\Documents\Codes\Python\HoteLink\scripts\docker.sh)

## 2. 当前已实现并可用于论文表述的能力

- 用户端与管理端双前端应用已经具备独立开发与生产构建能力。
- Django 后端已经具备认证、公共查询、用户中心、订单、评价、优惠券、发票、通知、AI 辅助、后台经营管理等接口。
- Docker 开发环境与生产环境已经分别提供独立编排文件与统一脚本入口。
- 系统初始化与系统重置能力已经落地。
- AI 配置已经支持通过环境变量与后台接口进行管理。

## 3. 当前应谨慎表述或明确为“未实现/规划中”的内容

- WebSocket 实时通知目前没有对应的后端实现，不应在论文中表述为已交付能力。
- 文档中的设计草图、页面规划、扩展模块，如果尚未进入实际路由或后端逻辑，不应写成“系统已支持”。
- 仓库中不存在的脚本、配置文件、部署命令，不应继续保留在正式文档中。

## 4. 当前文档约束

- [docs/api-spec.md](D:\Nakamoto\Documents\Codes\Python\HoteLink\docs\api-spec.md) 应以已实现 HTTP 接口为主，规划项必须显式标注。
- [docs/deployment.md](D:\Nakamoto\Documents\Codes\Python\HoteLink\docs\deployment.md) 只允许记录仓库内真实存在的脚本、镜像和编排能力。
- [docs/ai-integration.md](D:\Nakamoto\Documents\Codes\Python\HoteLink\docs\ai-integration.md) 只描述当前环境变量、后端配置与接口中已接入的 AI 能力。
- [docs/frontend-system-design.md](D:\Nakamoto\Documents\Codes\Python\HoteLink\docs\frontend-system-design.md) 若包含规划内容，必须让读者能区分“设计目标”与“已实现页面”。

## 5. 维护要求

- 新增接口、页面、脚本、Docker 能力时，同步更新对应文档。
- 如果论文表述采用了工程能力，必须先确认该能力已经进入代码和路由，而不是仅停留在设计稿。
- 若发现文档描述超前于实现，应优先修改文档，不允许保留“计划中”却写成“已完成”的表述。
