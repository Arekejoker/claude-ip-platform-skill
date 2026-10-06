# claude-ip-platform-setup — 专属固定 IP 平台搭建 Skill

给 AI agent 用的「陪跑」技能包（[Agent Skills](https://agentskills.io) 开放格式，Claude Code / Codex / Cursor / OpenClaw 等均可使用）：**agent 打开页面并核对状态，用户负责点击和付款**，分六个阶段完成「买 VPS → 买固定住宅 IP → 串成链式代理 → 配好电脑和手机 → 验收」。

- **人机协同**：agent 开页、指路、核对状态；下单、付款、密码永远由用户亲手完成
- **六阶段**：探测问询 → 买 VPS → 买住宅 IP → 服务器（Xray REALITY）→ 电脑 / 手机客户端 → 验收
- **环境自动适配**：先探测（系统 / 手机 / 支付 / 网络 / 已有设施），再一题一题问询（选项卡式），输出定制方案卡
- **防幻觉护栏**：价格、页面文案、商家政策一律现场核验；「应该可以」不算「已验证」
- **可中断恢复**：进度落盘（`ip-platform-progress.md`），换会话、隔几天回来都能接着做
- **兼容降级**：自带浏览器工具 → Playwright MCP → CDP → 纯对话引导，四档降级（降级时不假装看到页面）

> 边界：仅限个人自用；**不承诺「不被封」**——本技能只解决「出口 IP 干净、固定、自主可控」这一环；不提供规避地区限制 / KYC / 多账号的指导。

## 安装

选一个：

```bash
# 任意 agent（自动识别 Claude Code / Codex / Cursor 等）
npx skills add Arekejoker/claude-ip-platform-skill

# GitHub 官方 CLI（gh ≥ 2.90）
gh skill install Arekejoker/claude-ip-platform-skill claude-ip-platform-setup --agent claude-code

# OpenClaw
openclaw skills install git:Arekejoker/claude-ip-platform-skill@main
```

或手动：把整个目录复制到 agent 的 skills 目录（如 opencode：`~/.config/opencode/skills/claude-ip-platform-setup/`；Claude Code：`~/.claude/skills/`）。

## 使用

安装后直接对 agent 说：

- 「帮我搭一套固定 IP 平台」
- 「我想照着教程买 VPS + 住宅 IP，带我一一步步做」
- 「给 AI 账号搞个稳定的专属出口」

agent 会先做能力检查与设备探测，然后按六阶段推进，每阶段停下等确认。

## 目录结构

```
claude-ip-platform-skill/
├── SKILL.md                     # 主流程（触发条件、六阶段、协同协议、红线、防幻觉护栏）
├── references/
│   ├── intake.md                # 问询题库 + 设备/支付/预算决策矩阵
│   ├── browser-guide.md         # 交互式浏览器协同规则 + 各 agent 安装法 + 降级矩阵
│   ├── providers.md             # 采购陪跑（RackNerd / Webshare 案例，价格以官网为准）
│   ├── server-setup.md          # 服务器初始化 + Xray REALITY（含踩坑）
│   ├── client-setup.md          # Clash Verge Rev / Stash / Android 配置（含链式代理）
│   ├── verification.md          # 验收清单 + 使用手册（维护卡）
│   └── troubleshooting.md       # 常见故障排查
└── scripts/
    ├── bootstrap_server.sh      # 服务器一键初始化（幂等，跑在 VPS 上）
    ├── check_chain.py           # 身份链出口自检（跑在用户电脑上，仅标准库）
    └── gen_client_config.py     # 从服务端参数生成客户端配置（mihomo / Stash / vless 链接）
```

## 前置要求

- agent 侧：交互式浏览器能力（推荐；没有会按降级矩阵处理）、本机 shell；阶段 3 起需要 SSH（agent 代跑服务器命令）
- 用户侧：两种支付方式（如 支付宝 + 银联卡 / Apple Pay / USDT）；一台电脑 + 可选手机

## 边界与免责

- 仅限个人自用；不提供规避地区限制 / KYC / 多账号的指导
- 不承诺「不被封」——本技能解决的是「出口 IP 干净、固定、自主可控」
- 文档中的价格、套餐名、页面文案均为 2026-10 快照，**执行时以官网现场为准**（见 SKILL.md 防幻觉护栏）
- 技能包内不含任何真实凭证；用户的所有密码 / 密钥只存在于用户与用户自己的会话中

## 版本

- 2026-10 初版：基于一次真实搭建全程（RackNerd VPS + Webshare 住宅 IP + Xray REALITY + Clash Verge / Stash）
