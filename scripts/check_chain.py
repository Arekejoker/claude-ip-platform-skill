#!/usr/bin/env python3
"""check_chain.py — 经本地代理口检查身份链出口（在用户电脑上运行）

前提：身份域名规则已置顶（ipify.org 走身份组），本地代理口可用。
需要 python3；没有 python3 的环境用等价命令：
  for i in $(seq 1 20); do curl -s -x http://127.0.0.1:7897 https://api.ipify.org; echo; done

用法：
  python3 check_chain.py --port 7897 --count 20
  python3 check_chain.py --port 7897 --expect 203.0.113.7   # 校验出口是否等于住宅 IP
"""

import argparse
import collections
import json
import sys
import time
import urllib.request


def one(port: int, timeout: float):
    proxy = urllib.request.ProxyHandler({
        "http": f"http://127.0.0.1:{port}",
        "https": f"http://127.0.0.1:{port}",
    })
    opener = urllib.request.build_opener(proxy)
    t0 = time.time()
    try:
        with opener.open("https://api.ipify.org", timeout=timeout) as r:
            return r.read(64).decode().strip(), time.time() - t0, None
    except Exception as e:  # noqa: BLE001
        return None, time.time() - t0, f"{type(e).__name__}: {str(e)[:80]}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=7897, help="本地混合代理端口")
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--expect", default=None, help="期望的出口 IP（住宅 IP）；不传则只统计")
    ap.add_argument("--timeout", type=float, default=10.0)
    args = ap.parse_args()

    ips, times, fails = [], [], 0
    for i in range(args.count):
        ip, dt, err = one(args.port, args.timeout)
        times.append(dt)
        if err:
            fails += 1
            print(f"[{i + 1}/{args.count}] FAIL  {err}  ({dt:.2f}s)")
        else:
            ips.append(ip)
            print(f"[{i + 1}/{args.count}] {ip}  ({dt:.2f}s)")

    dist = dict(collections.Counter(ips))
    summary = {
        "ok": len(ips),
        "fail": fails,
        "exit_ips": dist,
        "avg_s": round(sum(times) / len(times), 2),
    }
    print("---")
    print(json.dumps(summary, ensure_ascii=False))

    if args.expect:
        bad = sorted({ip for ip in ips if ip != args.expect})
        if fails or bad:
            print(f"❌ 未通过：期望 {args.expect}；异常出口 {bad or '（有失败）'}")
            sys.exit(1)
        print(f"✅ 全部 {len(ips)} 次命中期望出口 {args.expect}")


if __name__ == "__main__":
    main()
