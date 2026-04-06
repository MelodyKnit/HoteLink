# HoteLink AI 集成说明

## 1. 文档目标

本文件用于说明项目中的 AI 能力如何接入、放在哪些功能里最合适、如何配置，以及如何保证密钥与隐私安全。

## 2. 当前接入方式

项目当前采用：

- OpenAI Python SDK
- DeepSeek OpenAI 兼容接口

当前代码位置：

- [`../backend/config/ai.py`](../backend/config/ai.py)
- [`../backend/apps/operations/services/ai_service.py`](../backend/apps/operations/services/ai_service.py)
- [`../backend/.env.example`](../backend/.env.example)

当前默认配置：

- `AI_PROVIDER=deepseek`
- `AI_BASE_URL=https://api.deepseek.com`
- `AI_MODEL=deepseek-chat`
- `AI_REASONING_MODEL=deepseek-reasoner`

## 3. 为什么推荐这样接入

- `openai` SDK 生态成熟，后续如果切换模型提供方，改动成本较低
- DeepSeek 提供 OpenAI 兼容接口，便于统一接入
- 所有 AI 调用放在后端，避免密钥暴露到前端

## 4. AI 功能应该优先加在哪些地方

建议先加在“低风险、高价值、强辅助”的场景，而不是直接介入核心交易逻辑。

### 4.1 用户端推荐优先级

#### 第一优先级

- 智能客服
- 酒店推荐
- 房型推荐
- FAQ 智能问答
- 入住须知解释

原因：

- 用户直接感知强
- 对订单转化有帮助
- 风险相对可控

#### 第二优先级

- 订单问答助手
- 发票与退改政策解释
- 行程建议与周边推荐

#### 不建议一开始就交给 AI 的能力

- 支付结果确认
- 最终退款判定
- 最终房态判断
- 最终价格计算

这些必须由业务规则决定。

### 4.2 管理端推荐优先级

#### 第一优先级

- 经营报表智能总结
- 差评摘要
- 客诉优先级建议
- 常见回复建议
- 营销文案辅助

原因：

- 对运营和客服效率提升明显
- 风险比直接控制订单和支付低

#### 第二优先级

- 客户偏好标签建议
- 异常订单摘要
- 房态异常提醒文案
- 酒店内容编辑辅助

## 5. 推荐的具体 AI 功能清单

### 5.1 用户端

#### 智能客服页 / 悬浮助手

解决：

- 入住时间
- 早餐政策
- 停车政策
- 退改规则
- 发票问题
- 联系酒店

#### 智能推荐模块

放置位置：

- 首页
- 酒店列表页
- 酒店详情页
- 会员中心

推荐内容：

- 推荐酒店
- 推荐房型
- 推荐套餐
- 推荐加购服务

#### 订单问答助手

放置位置：

- 订单详情页

可回答：

- 当前订单状态
- 是否支持取消
- 发票如何申请
- 入住需要带什么

### 5.2 管理端

#### AI 经营分析助手

放置位置：

- 工作台
- 财务总览页
- 经营报表页

可输出：

- 本日营收总结
- 入住率波动原因提示
- 渠道变化摘要
- 异常指标说明

#### AI 客诉与评价分析

放置位置：

- 评价与反馈管理页
- 客户档案页

可输出：

- 差评摘要
- 高频投诉标签
- 客户情绪等级建议
- 回复建议

#### AI 营销助手

放置位置：

- 活动管理页
- 内容管理页

可输出：

- 活动标题建议
- Banner 文案草稿
- 会员活动描述
- 节假日营销文案

## 6. AI 配置项说明

建议统一使用环境变量：

- `AI_PROVIDER`
- `AI_ENABLED`
- `AI_BASE_URL`
- `AI_API_KEY`
- `AI_MODEL`
- `AI_REASONING_MODEL`
- `AI_TIMEOUT`

### 6.1 多供应商支持（新增）

系统现已支持多供应商并行配置，支持运行时切换：

- 可在管理端添加多个供应商（如 DeepSeek / OpenAI / 智谱 / Moonshot / Qwen）
- 可设置当前活跃供应商
- 当 A 供应商额度不足时，可即时切换到 B 供应商，无需重启服务

后端实现位置：

- `backend/config/ai.py`
- `backend/apps/operations/services/ai_service.py`
- `backend/apps/api/views.py`（`AdminAISettingsView` 及 provider 管理接口）

### 6.2 管理端接口（新增）

- `GET /api/v1/admin/ai/settings`：读取 AI 开关、活跃供应商、供应商列表
- `POST /api/v1/admin/ai/settings/update`：更新 AI 开关/活跃供应商/供应商配置
- `POST /api/v1/admin/ai/provider/add`：新增或编辑供应商
- `POST /api/v1/admin/ai/provider/switch`：切换活跃供应商
- `POST /api/v1/admin/ai/provider/delete`：删除非活跃供应商

### 6.3 前端页面（新增）

管理端 AI 设置页已升级：

- 查看所有供应商状态
- 快捷添加内置供应商
- 编辑供应商模型与 Base URL
- 切换当前活跃供应商
- 删除非活跃供应商

这些变量当前已写入：

- [`../backend/.env.example`](../backend/.env.example)
- [`../.env.docker.example`](../.env.docker.example)
- [`../.env.docker.dev.example`](../.env.docker.dev.example)

## 7. 安全要求

### 7.1 绝对不能提交到 GitHub 的内容

- 真实 `AI_API_KEY`
- 真实数据库密码
- 真实 Redis 密码
- 私钥、证书
- 本地 `.env`

### 7.2 可以提交到 GitHub 的内容

- `.env.example`
- `.env.docker.example`
- `.env.docker.dev.example`
- AI 配置读取代码
- AI 服务封装代码

### 7.3 当前项目的保护措施

- [`../.gitignore`](../.gitignore) 已忽略 `.env` 和 `.env.*`
- `.gitignore` 允许提交示例配置文件
- AI 只在后端调用，不在前端暴露密钥

## 8. AI 使用边界

- AI 默认输出为建议，不是最终业务结论
- 涉及金额、库存、订单状态、入住资格、退款结果的内容，必须以业务系统规则为准
- AI 返回内容需要考虑幻觉风险
- 高风险场景需要人工确认

## 9. 后续扩展建议

1. 增加 AI 调用日志表
2. 增加 Prompt 模板管理
3. 增加 AI 开关和模型配置后台页面
4. 增加 AI 使用额度与频控
5. 增加 AI 输出审计机制

## 10. 文档维护要求

- 每次新增 AI 场景，都要同步更新本文件
- 每次 AI 配置项发生变化，都要同步更新本文件和 `README.md`
- 每次 AI 页面入口发生变化，都要同步更新 `frontend-system-design.md`
