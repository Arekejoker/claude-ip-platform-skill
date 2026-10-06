#!/usr/bin/env bash
# bootstrap_server.sh — 阶段 3 服务器初始化（在全新 Ubuntu/Debian VPS 上以 root 运行）
#
# 幂等说明：
#   - 不带参数运行：装好依赖与 Xray；若已有配置则原样保留（打印提示后退出）
#   - 带 U/PK/SID 参数运行：重写配置（自动备份旧文件）
#   - 缺参数时自动生成（UUID / x25519 密钥 / shortId）
#
# 用法：
#   bash bootstrap_server.sh                       # 首次或维持现状
#   FORCE=1 bash bootstrap_server.sh               # 强制重写（重新生成参数）
#   U=<uuid> PK=<priv> SID=<sid> bash bootstrap_server.sh   # 用指定参数重写
#
# 执行完把末尾「交接参数」整段记下，交给客户端配置阶段。

set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "请用 root 运行"; exit 1; }

PORT="${PORT:-443}"
SNI="${SNI:-gateway.icloud.com}"
XRAY_CONF=/usr/local/etc/xray/config.json

echo "==> [1/6] 系统更新"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get -y upgrade

echo "==> [2/6] 网络调优（BBR + TFO + MTU probing）"
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
sysctl --system >/dev/null
sysctl net.ipv4.tcp_congestion_control net.ipv4.tcp_fastopen

echo "==> [3/6] 防火墙（22 + ${PORT}）"
ufw allow 22/tcp || true
ufw allow "${PORT}/tcp" || true
ufw --force enable || true
ufw status | head -8

echo "==> [4/6] 安装 Xray"
if ! command -v xray >/dev/null 2>&1; then
  bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
fi
xray version | head -1

if [ -f "$XRAY_CONF" ] && [ "${FORCE:-0}" != "1" ] && [ -z "${U:-}" ] && [ -z "${PK:-}" ] && [ -z "${SID:-}" ]; then
  echo "==> 已存在配置，未重写。要重写：FORCE=1 bash $0（会重新生成参数并备份旧配置）"
  exit 0
fi

echo "==> [5/6] 生成参数"
U="${U:-$(xray uuid)}"
if [ -z "${PK:-}" ] || [ -z "${PUB:-}" ]; then
  OUT="$(xray x25519)"
  PK="$(printf '%s\n' "$OUT" | awk -F': *' '/[Pp]rivate/{print $2}' | head -1)"
  PUB="$(printf '%s\n' "$OUT" | awk -F': *' '/([Pp]ublic|[Pp]assword)/{print $2}' | head -1)"
fi
SID="${SID:-$(openssl rand -hex 8)}"

echo "==> [6/6] 写配置（先备份）"
[ -f "$XRAY_CONF" ] && cp "$XRAY_CONF" "$XRAY_CONF.bak-$(date +%Y%m%d-%H%M%S)"

cat > "$XRAY_CONF" <<EOF
{
  "inbounds": [{
    "listen": "0.0.0.0",
    "port": ${PORT},
    "protocol": "vless",
    "settings": {
      "clients": [{ "id": "${U}", "flow": "xtls-rprx-vision" }],
      "decryption": "none"
    },
    "streamSettings": {
      "network": "tcp",
      "security": "reality",
      "realitySettings": {
        "dest": "${SNI}:443",
        "serverNames": ["${SNI}"],
        "privateKey": "${PK}",
        "shortIds": ["${SID}"]
      },
      "sockopt": { "tcpFastOpen": true, "tcpNoDelay": true }
    }
  }],
  "outbounds": [{ "protocol": "freedom" }]
}
EOF

xray -test -config "$XRAY_CONF"
systemctl restart xray
systemctl is-active --quiet xray && echo "xray: active"
ss -lntp | grep ":${PORT}" || true

echo
echo "===== 交接参数（记下，交给客户端配置）====="
echo "SERVER_IP   = <本机公网 IP，自行补上>"
echo "PORT        = ${PORT}"
echo "UUID        = ${U}"
echo "PUBLIC_KEY  = ${PUB}"
echo "SHORT_ID    = ${SID}"
echo "SNI         = ${SNI}"
echo "FLOW        = xtls-rprx-vision"
