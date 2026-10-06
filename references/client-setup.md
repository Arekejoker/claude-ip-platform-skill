# 客户端配置（阶段 4 电脑 / 阶段 5 手机）

目标：让「身份域名清单」的流量走固定住宅 IP，其余流量照旧；**出口 IP 永远显示住宅 IP**。

## 第 0 步：先装客户端（还没有的话）

| 设备 | 推荐 | 哪里装 | 费用 |
|---|---|---|---|
| Windows / macOS | Clash Verge Rev | 官网 / GitHub Releases | 免费 |
| Android | CMFA（Clash Meta for Android） | GitHub Releases / Play / F-Droid | 免费 |
| Android（想统一 UI） | FlClash | GitHub Releases | 免费 |
| iPhone | Stash | App Store（**付费 App，约 $3.99，需外区 Apple ID**） | 付费 |
| iPhone（免费替代） | sing-box 官方 App / Karing | 对应 App Store（外区） | 免费 |

- 一律从官方渠道下载，不用来路不明的分流包
- 安装时间先别改默认设置；下一步按本文件加节点

## 通用原则

1. **备路不备出口**：路径可以有多条（直连住宅 / 经 VPS 中转），但出口 IP 只有一个（住宅 IP）
2. **一号一出口**：这个住宅 IP 只服务 AI/账号类域名，不挂下载、视频、大流量
3. **改前备份**：任何配置改动前先备份（`.bak-日期`），并说明回滚方法
4. **Clash Verge Rev 的坑（2026-10 实测）**：
   - 官方已废弃 `prepend-rules / append-rules / prepend-proxies` 写法（GitHub issue #2455/#3150），写了不生效
   - 订阅每 12h 自动更新会重新生成主配置，**手工改生成文件会被吞掉**
   - 正确做法：用「扩展脚本（JS）」或独立 profile；改完必须查**运行时**（API 的 /configs、/proxies）确认生效，而不是只看文件
5. **模式选择**：默认用「系统代理」模式就够了，**不要开 TUN**（TUN 会接管所有流量、和现有网络工具/局域网访问打架）；只在明确需要"全部流量强制走代理"时才考虑

## 电脑：Clash Verge Rev（mihomo）

### 两个节点

```yaml
proxies:
  - name: "VPS-Relay"
    type: vless
    server: <VPS_IP>
    port: 443
    uuid: <U>
    flow: xtls-rprx-vision
    tls: true
    servername: gateway.icloud.com
    reality-opts: { public-key: <PUB>, short-id: <SID> }
    client-fingerprint: chrome
    udp: true
    tfo: true
  - name: "Residential"
    type: http
    server: <住宅IP>
    port: <端口>
    username: <用户名>
    password: <密码>
    dialer-proxy: "VPS-Relay"    # 经 VPS 中转（换路不换出口）
```

### 分组

```yaml
proxy-groups:
  - name: US-Identity
    type: select
    proxies: ["Residential", "VPS-Relay"]   # 备路：平时 Residential，直连不通时可切
```

### 规则（置顶，全部指向 US-Identity）

| 分组 | 域名 |
|---|---|
| hf 镜像 → DIRECT | hf-mirror.com / hf.co / cas-bridge.xethub.hf.co |
| 大流量排除 → Default Proxy | drive.google.com / photos.google.com |
| Claude | claude.ai / anthropic.com / claude.com / clau.de / claudeusercontent.com / claudemcpclient.com / claudemcpcontent.com |
| OpenAI | openai.com / chatgpt.com / chat.com / oaistatic.com / oaiusercontent.com / oaistatsig.com |
| X / Twitter | x.com / twitter.com / twimg.com / t.co |
| Google 账号 | gmail.com / googlemail.com / googleusercontent.com / google.com |
| 验证与风控 | challenges.cloudflare.com / withpersona.com / stripe.com / stripe.network / featuregates.org / statsigapi.net / statsig.com / sentry.io / browser-intake-datadoghq.com |
| Apple 账号 | appleid.apple.com / idmsa.apple.com / buy.itunes.apple.com |
| 支付 | paypal.com / paypalobjects.com |
| 检测 | ipify.org / ip.sb |

> 规则名按用户实际订阅里的组名调整（没有 Default Proxy 就用 MATCH 对应组）；置顶优先级必须高于任何 geosite/cn 规则集。
> 同一份清单也写在 `scripts/gen_client_config.py` 的 IDENTITY 数组里——**改的时候两边一起改**。

### 推荐落地方式：扩展脚本（抗订阅更新）

Verge「扩展脚本 / 全局扩展脚本」每次生成配置时执行：

```javascript
function main(config) {
  config.proxies = config.proxies || [];
  config["proxy-groups"] = config["proxy-groups"] || [];
  config.rules = config.rules || [];
  config.proxies.unshift(
    /* VPS-Relay 节点对象 */,
    /* Residential 节点对象 */
  );
  config["proxy-groups"].unshift({
    name: "US-Identity", type: "select",
    proxies: ["Residential", "VPS-Relay"]
  });
  const identity = [
    "DOMAIN-SUFFIX,claude.ai", "DOMAIN-SUFFIX,anthropic.com",
    /* …完整清单… */
  ].map(r => r + ",US-Identity");
  config.rules.unshift(
    "DOMAIN-SUFFIX,drive.google.com,Default Proxy",
    "DOMAIN-SUFFIX,photos.google.com,Default Proxy",
    ...identity
  );
  return config;
}
```

### 热重载与验证

- 拿 API 地址与 secret（Verge 设置可见；unix socket 或 127.0.0.1:9090）
- `PUT /configs?force=true` 重载 → 期望 204
- 验证：
  - `curl -x http://127.0.0.1:<混合端口> https://api.ipify.org` → 住宅 IP（ipify/ip.sb 已走身份组）
  - `GET /proxies/US-Identity` → 选择与预期一致
- 防呆：把 GLOBAL 模式的选择设为 Default Proxy，防止误触全局模式时裸连

## iOS：Stash

- Stash **不支持导入文件**，用「覆写（Override）」粘贴 YAML（proxies + proxy-groups + rules，结构同上；Stash 支持 `dialer-proxy`）
- 手机直连住宅代理在 4G/5G 下可能被干扰/断连（实测），手机端节点默认用**经 VPS 中转**版本
- 保存启用后，浏览器打开 `https://ip.sb` 验证 = 住宅 IP

## Android：CMFA / FlClash

- 默认 CMFA（Clash Meta for Android）；纯小白 / 要统一 UI → FlClash
- 导入：分享链接或整段 YAML
- vless 分享链接模板：

```
vless://<U>@<VPS_IP>:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=gateway.icloud.com&fp=chrome&pbk=<PUB>&sid=<SID>&type=tcp#VPS-Relay
```

- 链式（Residential 经 VPS）：mihomo 内核支持 `dialer-proxy`，写法同电脑

## 双端小验收

电脑和手机分别访问 `https://ip.sb` → 两处显示同一个住宅 IP 即通过。
