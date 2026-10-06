# 服务器搭建（阶段 3）

把一台全新 Ubuntu/Debian VPS 跑成 Xray VLESS + REALITY 服务端：只开放一个 TCP 443 入站。
本文件是 agent 的操作手册；用户在阶段 1 已提供 IP + root 密码（一次性使用）。

> 命令、版本、下载地址执行时现场核验；下面是 2026-10 实测可用的路径。

## 0. 登录与加固（密码只活一次）

1. 用用户给的密码首次登录 `ssh root@<VPS_IP>`（核对指纹后接受）
2. 立即部署 agent 的公钥（没有就先生成 `ssh-keygen -t ed25519`）
3. 新开终端验证密钥登录成功 → 回原会话轮换 root 密码（`passwd`），新密码交给用户保管
4. 密码永不写入文件、不回显进聊天记录
5. 可选加固：`PermitRootLogin prohibit-password`、装 fail2ban（先保证能连，再谈加固）
6. 可用脚本顶替第 2–7 节的人工步骤：`scp scripts/bootstrap_server.sh root@<IP>:/root/ && ssh root@<IP> 'bash /root/bootstrap_server.sh'`（幂等，重复跑不会重写配置）；首次建议人肉跟一遍，理解每步在做什么

## 1. 体检（30 秒）

```bash
uname -a; cat /etc/os-release | head -3; free -h; df -h /
curl -s "http://ip-api.com/json" | head -c 300    # VPS 自身出口，记录备用
```

## 2. 系统更新 + 网络调优

```bash
apt update && apt full-upgrade -y
cat > /etc/sysctl.d/99-tuning.conf <<'EOF'
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
net.ipv4.tcp_fastopen=3
net.ipv4.tcp_slow_start_after_idle=0
net.core.rmem_max=16777216
net.core.wmem_max=16777216
net.ipv4.tcp_rmem=4096 87380 16777216
net.ipv4.tcp_wmem=4096 65536 16777216
net.ipv4.tcp_notsent_lowat=131072
net.ipv4.tcp_mtu_probing=1
EOF
sysctl --system
sysctl net.ipv4.tcp_congestion_control net.ipv4.tcp_fastopen   # 应显示 bbr / 3
```

## 3. 防火墙

```bash
ufw allow 22/tcp
ufw allow 443/tcp
ufw --force enable
ufw status          # 只应有 22 和 443
```

## 4. 安装 Xray

```bash
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
xray version
```

## 5. 生成 REALITY 参数

```bash
xray uuid                 # → UUID，记为 U
xray x25519               # → PrivateKey（服务端）与 Password/PublicKey（客户端公钥），记为 PK / PUB
openssl rand -hex 8       # → shortId，记为 SID
```

记下四样：**U / PK / PUB / SID**。

## 6. 写配置

`/usr/local/etc/xray/config.json`（改前先备份 `cp config.json config.json.bak-<日期>`）。关键结构：

```json
{
  "inbounds": [{
    "listen": "0.0.0.0", "port": 443, "protocol": "vless",
    "settings": { "clients": [{ "id": "<U>", "flow": "xtls-rprx-vision" }], "decryption": "none" },
    "streamSettings": {
      "network": "tcp", "security": "reality",
      "realitySettings": {
        "dest": "gateway.icloud.com:443",
        "serverNames": ["gateway.icloud.com"],
        "privateKey": "<PK>",
        "shortIds": ["<SID>"]
      },
      "sockopt": { "tcpFastOpen": true, "tcpNoDelay": true }
    }
  }],
  "outbounds": [{ "protocol": "freedom" }]
}
```

要点：

- `dest` 与 `serverNames` 必须一致，并选**证书链不超过 8KB** 的站点
- 客户端的 `flow / serverName / publicKey / shortId` 必须与服务端逐字一致，错一个就握手失败

## 7. 启动与自检

```bash
xray -test -config /usr/local/etc/xray/config.json
systemctl restart xray && systemctl is-active xray
ss -lntp | grep ':443'                          # 应有 xray 监听
journalctl -u xray -n 30 --no-pager             # 无报错即正常
```

## 8. 已知坑（2026-10 实测）

1. **REALITY 握手失败 / 白屏超时**：Xray 26.x 用 `www.microsoft.com` 作伪装目标时，证书链过大（约 8273B，超过 REALITY 8192B 上限）触发失败（上游 issue #6356）。换 `gateway.icloud.com`（证书链约 3.2KB）即可。
2. **日志出现 apple/icloud 目标的提示**：属信息性警告（该域名可能被特别对待），先观察连通性，必要时换目标域名。
3. **443 被占**：`ss -lntp` 排查，单机只留一个服务监听 443。
4. **改配置纪律**：备份 → 改 → `xray -test` → 重启 → 看 journalctl；任何一步不过就回滚。

## 9. 交接给阶段 4 的参数清单

服务器 IP、端口 443、UUID、公钥 PUB、shortId、SNI（gateway.icloud.com）、flow（xtls-rprx-vision）。
