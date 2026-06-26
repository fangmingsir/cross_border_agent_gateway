# Interview Pack: 跨境电商 Agent 工具网关

## 简历 4 行

- 基于 OpenAI Agents SDK 思路二次设计跨境电商运营 Agent 网关，模拟商品、订单、退款、利润等内部业务系统工具接入，支持 SKU 诊断、listing 优化和运营建议生成。
- 设计 Planner Agent + 业务 Tools 的调用链路，定义工具入参/出参、错误码和部分失败兜底策略，提升 Agent 输出的可解释性和稳定性。
- 引入 human-in-the-loop、trace log 与简单 cost log，沉淀 5 条典型运营 query 的评测用例，用于分析 tool call 准确性、证据完整性和异常恢复。
- 对比阅读 OpenClaw/Hermes 类 Agent 框架的运行形态、技能扩展、持久记忆和安全风险，形成轻量 Python 后端 Agent 应用的上线与调优方案。

## 代码讲解顺序

1. `app/api.py`：FastAPI 入口，核心接口是 `POST /agent/analyze-sku`。
2. `app/schemas.py`：请求、tool result、trace、cost、最终响应结构。
3. `app/tools.py`：5 个业务工具，分别模拟商品、订单、退款、利润和 listing 建议。
4. `app/agent.py`：Planner、guardrail、fallback、human review、cost estimate 的主链路。
5. `eval/eval_cases.json`：5 条面试用例，说明如何评估 tool call、证据和兜底。

## 高频 Q&A

**Q：你没有真实用过 OpenClaw/Hermes，怎么匹配 JD？**  
A：我不会伪造上线经验。我做的是替代条件方向：基于 Python Agent SDK 思路做业务 Agent 应用设计，重点覆盖 tool use、context、guardrail、评测、成本和内部系统接入；OpenClaw/Hermes 我作为框架对照阅读，能讲机制差异和安全取舍。

**Q：你的 Agent 怎么接公司内部系统？**  
A：把内部系统抽象成受控 tool：商品库、订单库、退款风险、利润估算。Agent 不直接访问数据库，而是通过 typed tool schema 调用，便于权限、审计、限流和 mock 测试。

**Q：如何降低调用成本？**  
A：固定系统 prompt，业务资料不全量塞上下文；SKU、订单等结构化数据通过 tool 按需取；高频查询做缓存；日志记录每次模型调用和工具调用，后续按 case 分析是否需要小模型路由。

**Q：失败兜底怎么做？**  
A：工具超时或返回缺字段时，Agent 输出部分结论并标记缺失证据；高风险建议不自动执行，转人工确认；关键证据缺失时进入 fallback，避免编造业务数据。

**Q：如果真的上线，你会补什么？**  
A：接真实鉴权、限流、审计日志和可观测性；把 mock JSON 换成内部服务 SDK；接入更严格的 eval pipeline；对工具调用做超时、重试、熔断；将高风险动作接入审批流。

## PPT 提示词

生成一份 6 页中文技术面试 PPT，主题是《跨境电商运营 Agent 工具网关》。包含项目背景、架构图、请求流/tool 调用流、context 与成本优化、评测与兜底、限制和下一步。风格偏工程面试，不要营销页。

