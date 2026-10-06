#!/usr/bin/env python3
"""gen_client_config.py — 从服务端参数生成客户端配置片段

输出三份：
  mihomo-snippet.yaml   节点+组+规则片段（贴进本地 profile / CMFA / FlClash；Verge 扩展脚本的 JS 写法见 client-setup.md）
  stash-override.yaml   iOS Stash 覆写（粘贴用）
  vless-link.txt        分享链接（Android 快速导入）

用法：
  python3 gen_client_config.py \
    --vps-ip 203.0.113.10 --uuid <U> --pubkey <PUB> --short-id <SID> \
    --res-ip 198.51.100.7 --res-port 5514 --res-user <user> --res-pass <pass> \
    --sni gateway.icloud.com --out ./out
"""

import argparse
import os

IDENTITY = [
    "claude.ai", "anthropic.com", "claude.com", "clau.de",
    "claudeusercontent.com", "claudemcpclient.com", "claudemcpcontent.com",
    "openai.com", "chatgpt.com", "chat.com", "oaistatic.com",
    "oaiusercontent.com", "oaistatsig.com",
    "x.com", "twitter.com", "twimg.com", "t.co",
    "gmail.com", "googlemail.com", "googleusercontent.com", "google.com",
    "challenges.cloudflare.com", "withpersona.com", "stripe.com",
    "stripe.network", "featuregates.org", "statsigapi.net", "statsig.com",
    "sentry.io", "browser-intake-datadoghq.com",
    "appleid.apple.com", "idmsa.apple.com", "buy.itunes.apple.com",
    "paypal.com", "paypalobjects.com",
    "ipify.org", "ip.sb",
]
HEAVY = ["drive.google.com", "photos.google.com"]


def yaml_block(a) -> str:
    lines = ["proxies:"]
    lines += [
        '  - name: "VPS-Relay"',
        "    type: vless",
        f"    server: {a.vps_ip}",
        "    port: 443",
        f"    uuid: {a.uuid}",
        "    flow: xtls-rprx-vision",
        "    tls: true",
        f"    servername: {a.sni}",
        f'    reality-opts: {{ public-key: {a.pubkey}, short-id: {a.short_id} }}',
        "    client-fingerprint: chrome",
        "    udp: true",
        "    tfo: true",
        '  - name: "Residential"',
        "    type: http",
        f"    server: {a.res_ip}",
        f"    port: {a.res_port}",
        f"    username: {a.res_user}",
        f"    password: {a.res_pass}",
        '    dialer-proxy: "VPS-Relay"',
        "",
        "proxy-groups:",
        '  - name: "US-Identity"',
        "    type: select",
        '    proxies: ["Residential", "VPS-Relay"]',
        "",
        "rules:",
    ]
    for d in HEAVY:
        lines.append(f"  - DOMAIN-SUFFIX,{d},Default Proxy")
    for d in IDENTITY:
        lines.append(f"  - DOMAIN-SUFFIX,{d},US-Identity")
    return "\n".join(lines) + "\n"


def vless_link(a) -> str:
    return (
        f"vless://{a.uuid}@{a.vps_ip}:443?encryption=none&flow=xtls-rprx-vision"
        f"&security=reality&sni={a.sni}&fp=chrome&pbk={a.pubkey}&sid={a.short_id}"
        f"&type=tcp#VPS-Relay\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vps-ip", required=True)
    ap.add_argument("--uuid", required=True)
    ap.add_argument("--pubkey", required=True)
    ap.add_argument("--short-id", required=True)
    ap.add_argument("--sni", default="gateway.icloud.com")
    ap.add_argument("--res-ip", required=True)
    ap.add_argument("--res-port", required=True)
    ap.add_argument("--res-user", required=True)
    ap.add_argument("--res-pass", required=True)
    ap.add_argument("--out", default=".")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    files = {
        "mihomo-snippet.yaml": yaml_block(args),
        "stash-override.yaml": yaml_block(args),  # 结构相同，Stash 直接粘贴
        "vless-link.txt": vless_link(args),
    }
    for name, content in files.items():
        path = os.path.join(args.out, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
