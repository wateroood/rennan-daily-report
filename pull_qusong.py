# -*- coding: utf-8 -*-
"""
pull_qusong.py —— 从国色星洗 SaaS 系统读取人南片区取送（配送）明细，替代线下 Excel。

数据源：/api/zhcx/deliveryinfo/query（配送信息查询页数据源，经实测与导出的
「配送信息-*.xls」字段/口径完全一致：8.1-8.11 共 1329 单/3519 件，0 差异）。

口径：
- 取「已完成」(deliveryStatus=Y) 记录；
- 订单日期 = 预约时间(planDeliveryDatetime)；
- 筛选范围默认 2026-08-01 ~ 今天（每日滚动，可用 --start/--end 覆盖）；
- 输出 qusong_rows.json，供 analysis.py 使用（analysis.py 不再读 .xls）。

用法：
    python pull_qusong.py                     # 默认 8.1 ~ 今天
    python pull_qusong.py --end 2026-08-20    # 指定截止日
"""
import argparse
import json
import os
import sys
from datetime import date, datetime, timedelta
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "etl"))
from gsx_client import GSXClient, load_config

# 人南片区 7 店（成都公司口径门店 id）
RENNAN_SHOPS = [8, 4, 73, 19, 20, 1, 42]  # 东湖/东苑/大世界/新希望路/盛和路/紫荆/高攀路

PARTNERS = ['杨龙', '何国举', '罗旺', '贺亮', '王明志', '桑尉焜']


def norm(rec: dict) -> dict:
    """API 记录 -> 与旧 Excel 分析相同的行结构（多保留原始字段便于核对）"""
    def s(v):
        return str(v).strip() if v is not None else ""
    plan = s(rec.get("planDeliveryDatetime"))
    return {
        "store": s(rec.get("shopName")),
        "dtype": s(rec.get("deliveryType")),           # 取衣/送衣
        "customer": s(rec.get("customerName")),
        "tel": s(rec.get("tel")),
        "address": s(rec.get("address")),
        "running": s(rec.get("runningNumber")),        # 流水号
        "date": plan[:10],                              # 预约时间 → 订单日期
        "plan_time": plan,
        "assign_staff": s(rec.get("assignStaffName")), # 派单人
        "assign_time": s(rec.get("assignDatetime")),   # 派单时间
        "pieces": int(rec.get("clothesCount") or 0),    # 衣物数量
        "deliverer": s(rec.get("deliveryStaffName")),   # 配送人
        "done_time": s(rec.get("deliveryDatetime")),    # 完成时间
        "status": s(rec.get("deliveryStatus")),         # Y 已完成 / N 未完成
        "on_time": s(rec.get("onTime")),                # 是否超时
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-08-01", help="分析窗口起点（默认改革观察起点 8.1）")
    ap.add_argument("--end", default=date.today().isoformat(), help="分析窗口终点（默认今天，每日滚动）")
    ap.add_argument("--shops", default=",".join(map(str, RENNAN_SHOPS)))
    ap.add_argument("--status", default="Y")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "qusong_rows.json"))
    args = ap.parse_args()
    shops = [int(x) for x in args.shops.split(",") if x]
    start, end = args.start, args.end

    cfg = load_config()
    with GSXClient(cfg) as c:
        # 注意：服务端按「记录创建时间」过滤（实测与导出的 Excel 口径一致），
        # 不要加前后 padding —— 加了会把 7 月创建、预约时间落在窗口内的记录多算进来（+12 条）。
        recs = c.delivery_info(shops, start, end, status=args.status)

    rows = []
    for r in recs:
        n = norm(r)
        if start <= n["date"] <= end and n["dtype"] in ("取衣", "送衣"):
            rows.append(n)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"source": "system-api:/api/zhcx/deliveryinfo/query",
                   "status": args.status, "start": start, "end": end,
                   "pulled_at": datetime.now().isoformat(timespec="seconds"),
                   "shops": shops, "rows": rows}, f, ensure_ascii=False)

    # 摘要
    print(f"窗口 {start} ~ {end}  status={args.status}  订单={len(rows)}")
    print("按日:", dict(sorted(Counter(x['date'] for x in rows).items())))
    print("按店:", dict(sorted(Counter(x['store'] for x in rows).items())))
    print("按类型:", dict(Counter(x['dtype'] for x in rows)))
    print("6位伙伴:", {p: sum(1 for x in rows if x['deliverer'] == p) for p in PARTNERS})
    print("保存 ->", args.out)


if __name__ == "__main__":
    main()
