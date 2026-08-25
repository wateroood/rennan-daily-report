# -*- coding: utf-8 -*-
"""
run_daily.py —— 人南片区取送日报一键流水线（供每日 20:30 自动化任务调用）

步骤：
  1. pull_qusong.py   从国色星洗 SaaS 拉取取送明细（默认窗口 2026-08-01 ~ 今天，每日滚动）
  2. analysis.py      重新计算 门店/伙伴/基线/日环比 指标 → analysis_data.json
  3. build_html.py    生成交互式 HTML 仪表盘（文件名按窗口动态生成）
  4. 复制最新 HTML 到 dist/index.html（供线上部署）

用法：
  python run_daily.py                 # 默认截止今天
  python run_daily.py --end 2026-08-20  # 指定截止日（回补历史）

说明：线上部署由自动化任务在脚本跑完后调用部署工具完成（Python 无法直接调云部署）。
"""
import datetime
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(name, args):
    print(f"\n===== STEP: {name} =====", flush=True)
    r = subprocess.run([PY, os.path.join(HERE, name)] + args, cwd=HERE)
    if r.returncode != 0:
        raise SystemExit(f"[run_daily] {name} 失败（exit={r.returncode}），终止。")
    return r


def main():
    args = sys.argv[1:]
    end = None
    if args and args[0].startswith("--end"):
        end = args[1]
    today = datetime.date.today().isoformat()
    pull_args = [f"--end={end or today}"]
    run("pull_qusong.py", pull_args)
    run("analysis.py", [])
    run("build_html.py", [])

    dist = os.path.join(HERE, "dist")
    os.makedirs(dist, exist_ok=True)
    htmls = [f for f in os.listdir(HERE)
             if f.startswith("人南片区取送情况分析_") and f.endswith(".html")]
    if not htmls:
        raise SystemExit("[run_daily] 未找到生成的 HTML 文件。")
    htmls.sort(key=lambda f: os.path.getmtime(os.path.join(HERE, f)), reverse=True)
    src = os.path.join(HERE, htmls[0])
    dst = os.path.join(dist, "index.html")
    shutil.copy(src, dst)
    print(f"\n✅ 已生成 {htmls[0]}（{os.path.getsize(src)} bytes）→ dist/index.html（{os.path.getsize(dst)} bytes）")
    print("下一步：部署 dist 目录到线上。")


if __name__ == "__main__":
    main()
