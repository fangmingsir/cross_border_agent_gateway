# Framework Comparison Notes

## OpenAI Agents SDK

- 适合本项目作为主线：Python、轻量、tool use 和 handoff 概念清晰。
- 面试重点：Agent 接收业务请求，按需调用工具，输出结构化结果和 trace。
- 风险：它不是现成跨境电商系统，需要自己补业务 mock 和评测。

## OpenClaw / Hermes 类框架对照

- 可以作为 JD 对照阅读，不建议在 2 天 interview-only 阶段声称“完整部署上线”。
- 可讲方向：本地运行形态、技能/工具扩展、记忆、权限、安全隔离、消息平台入口。
- 安全取舍：自治能力越强，越需要权限控制、工具沙箱、审计和人工确认。

## Why Lightweight Python

- 用户当前水平是“基本不会”，2 天目标是能投递、能面试、能讲清。
- 轻量 Python 项目更容易讲清 input/output、tool schema、fallback 和 eval。
- 不依赖 GPU、多机、多云服务，符合本地电脑 + Docker 的资源约束。

