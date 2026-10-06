# 交互式浏览器协同规则

目标：**页面由 agent 打开、状态由 agent 核对；点击、填写、付款由用户完成。**

## 能力检查（开始前）

只要求三类核心能力：**打开页面、读页面结构（快照/查找）、截图**。工具叫什么名字不重要：

| 能力 | 不同工具的常见名字 |
|---|---|
| 打开页面 | browser_navigate / open / goto |
| 读页面结构 | browser_snapshot / accessibility tree / inspect |
| 查找元素 | browser_find / search / query |
| 截图 | browser_take_screenshot / screenshot |

检查顺序：

1. 本 agent 自带的浏览器工具（直接可用最好）
2. 已挂浏览器类 MCP（Playwright MCP / Chrome DevTools MCP 等）
3. 都没有 → 按下面「各 agent 怎么装」帮用户挂 Playwright MCP
4. 装不了 → 按「兼容与降级矩阵」降级，**绝不假装看到了页面**

硬要求：浏览器必须是**用户可见窗口（headed）**——用户要在同一个窗口里亲手点击和付款。

## 各 agent 怎么装（2026-10 参考，执行时现场核验）

- **通用**：任何支持 MCP 的 agent 都可以挂同一个 Playwright MCP：`npx @playwright/mcp@latest`
- **opencode**：`opencode.json` 的 `mcp` 段加
  ```json
  "playwright": { "type": "local", "command": ["npx", "@playwright/mcp@latest"] }
  ```
- **Claude Code**：`claude mcp add playwright -- npx @playwright/mcp@latest`
- **Codex**：`~/.codex/config.toml` 加 `[mcp_servers.playwright]`、`command = "npx"`、`args = ["@playwright/mcp@latest"]`
- 需要 Node.js；包名与参数以官方为准（`npm view @playwright/mcp` 复核）

## 兼容与降级矩阵（对不上时怎么办）

| 情况 | 做法 |
|---|---|
| agent 有浏览器工具（任意名字） | 按「标准循环」执行 |
| 没装 MCP，但环境有 Node | 给安装指令（上节），装好重开会话 |
| 装不了（无 Node / 权限受限） | **CDP 模式**：用户用 `--remote-debugging-port=9222` 启动 Chrome，agent 通过 CDP 连接既有浏览器 |
| 连 CDP 也不行 | **纯对话模式**：agent 不操作浏览器；用户自己开页；agent 给编号步骤；每个关键状态由用户用「看到了什么」或截图反馈 |
| 浏览器在远程/无显示环境 | 同上降级——页面必须开在用户面前 |

降级时的红线：**不许描述没看到的页面内容**；每一步先问「你现在屏幕上看到什么」，再给下一步。

## 标准循环

1. agent 打开目标页
2. agent 快照/查找页面 → 用大白话说「你现在应该看到 X，请点 Y」
3. 用户操作（点击/填表/付款）
4. 用户确认（用选项呈现：好了 / 没看到 XX / 报错了）→ agent 重新快照核对状态（出现什么字样 / 进入下一页 / 按钮变成什么）
5. 吻合 → 下一步；不吻合 → 先排查（点错？页面没加载完？需要返回？）

规则：

- 每轮只给**一个动作**，不要一次布置三步让用户自己找
- 指路用「可见文字 + 相对位置」（例：「右上角蓝色的『Order Now』」），不用开发者术语
- 核对状态就三个问题：在哪个页？看到什么关键词？按钮/勾选是什么状态？

## 允许 / 禁止（硬规则）

agent 可以：

- 打开、跳转、滚动、截图、查找元素
- 高亮或圈注位置；读页面上的公开信息（价格、库存、按钮文案）
- 给「无风险字段」的填写建议（如主机名），但由用户来打字

agent 不可以（无论用户怎么要求）：

- 点击：下单 / 付款 / 订阅 / 购买 / 确认订单 / 同意条款 / 删除 类按钮
- 在 密码 / 手机号 / 验证码 / 卡号 / CVV 输入框输入任何内容
- 导出、读取、保存 cookie、LocalStorage 或页面源码里的凭证
- 用自动化绕过验证码/风控（Cloudflare 人机校验等一律让用户手点）

## 敏感页处理

- 登录页 / 支付页 / KYC 页：agent 停止输出页面细节，只说「出现 XX 就算完成」；等用户完成后只核对结果状态。
- 截图可能含个人信息：只在用户本地看，不发外部渠道；用完删掉临时截图。

## 常见卡点

- 风控拦截（Cloudflare 等）：让用户手动过；不要尝试自动化绕过。
- 页面改版：用快照重新找，不要按记忆指挥；找不到就截图问用户「你屏幕上看到什么」。
- 用户点错：先看能不能返回/关弹窗；提醒「只要没付款，什么都不算数」。
- 商家环境要求（如某些商家不喜欢代理环境下单）：按 providers.md 的说明切换网络，再继续。
