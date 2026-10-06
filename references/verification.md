# 验收（阶段 6）

全部通过才算完工；任何一项不过 → references/troubleshooting.md 分诊。

## A. 出口正确性（必须）

1. 电脑经身份链请求 `https://api.ipify.org` → 应 = 住宅 IP
   （ipify.org / ip.sb 已在置顶规则里走身份组；命令 `curl -x http://127.0.0.1:<混合端口> https://api.ipify.org`）
2. 连续 20 次，失败 0
3. 手机浏览器打开 `https://ip.sb` → 同一住宅 IP
4. 浏览器打开 claude.ai 登录页正常加载；`anthropic.com` 200
   （注意：命令行 curl 访问 claude.ai 返回 403 是 Cloudflare 反爬，正常现象，不代表被墙）

## B. IP 质量三库交叉（参考性，不迷信单一分数）

| 库 | 看什么 | 我们样本（2026-10，仅供参考） |
|---|---|---|
| ip-api.com | hosting 字段 | 住宅 hosting=false；机房 hosting=true |
| proxycheck.io | proxy / type / risk | 住宅 risk 0、type=Business；机房 risk 66、type=VPN |
| scamalytics.com | Fraud Score | 住宅 33；机房 32（两者接近，单看没意义） |

- 不同数据库结论会打架；以**多库 + 实际连通**综合判断
- 免费接口有频率限制，别连刷
- 参考判定：hosting=false + proxycheck risk 低/type=Business + 无主要 DNSBL 记录 ≈ 合格

## C. 链路稳定（参考）

- 20 连发失败率 = 0（同 A.2）
- 服务器 → 住宅端口 TCP 时延：在 VPS 上测（`time` 一次 TCP 连接，或多点几次）——我们样本 16–22ms
- 晚高峰再抽测一轮更好

## D. 使用纪律提醒（发给用户）

- 这条线只给账号/AI 域名用；不挂下载、不跑大流量
- 流量套餐额度（如 250GB/月）心里有数
- 一个住宅 IP 只服务一个账号体系；不外借、不换号共用

## 验收报告模板（发给用户）

```
✅ 搭建完成
- 出口 IP：<住宅IP>（电脑/手机一致）
- 质量参考：ip-api hosting=false；proxycheck risk=<x>；scamalytics <y>
- 稳定性：20 连发 0 失败；服务器→住宅 <xx>ms
- 已配端：电脑 ✅ / 手机 ✅
- 已知限制：不承诺「不被封」；只覆盖出口 IP 这一环
- 维护：改配置先备份；订阅更新后查运行时；流量纪律
```

## 使用手册（维护卡，交给用户保存）

```markdown
【我的专属出口】
- 出口 IP：<住宅IP>（电脑 / 手机应一致）
- 走这条线的域名：AI 与账号相关（Claude、OpenAI、X、Google 账号、支付等 40 条左右）
- 纪律：不挂下载/流媒体；不换 IP；不外借；一号一 IP

【每月看一眼】
- 住宅流量用量（Webshare 后台）别超套餐
- 续费日期：VPS <日期> / 住宅 <日期>

【遇到异常怎么办】
- 浏览器打开 ip.sb：还是住宅 IP → 正常；不是住宅 IP → 停下来联系我，先别登账号
- 客户端 / 订阅更新后：跑一遍 scripts/check_chain.py（或看 ip.sb）核对出口

【凭证在哪】
- 密码管理器里：VPS root、Webshare 代理账密（不放在聊天记录里）
```

## 不通过时

逐项对照本文件 → troubleshooting.md 找对应条目 → 修完从 A 重新验。
