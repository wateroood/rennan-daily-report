import json
from datetime import date, datetime, timedelta
from collections import defaultdict

# ===== 数据源：系统读取（pull_qusong.py 拉取并归一化的取送明细 JSON）=====
# 2026-08-12 起不再读线下 Excel，改为国色星洗 SaaS 接口
# /api/zhcx/deliveryinfo/query（配送信息查询页数据源，字段与 Excel 完全一致，经实测 0 差异）。
import os
_qs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qusong_rows.json")
if not os.path.exists(_qs_path):
    raise SystemExit(
        f"缺少 {_qs_path}。请先运行: python pull_qusong.py（从系统拉取取送明细），"
        "或恢复旧数据源（配送信息-8.1-8.11.xls）。"
    )
_qs = json.load(open(_qs_path, encoding="utf-8"))
_raw_rows = _qs["rows"]

# 2026-09-01 起：杨龙离职，其岗位由梁几斗接替。
# 梁几斗仅自接替日起计入伙伴口径（其 9 月前的顶班记录不计入伙伴维度，保留在片区/门店总体）。
PARTNERS = ['梁几斗', '何国举', '罗旺', '贺亮', '王明志', '桑尉焜']
PARTNER_SET = set(PARTNERS)
PARTNER_SINCE = {'梁几斗': '2026-09-01'}  # 伙伴任职起始日

def in_role(p, dt):
    """伙伴任职判断：dt 当日 p 是否属于现役伙伴口径。"""
    return dt >= PARTNER_SINCE.get(p, '0000-00-00')

rows = []
for r in _raw_rows:
    dtype = r['dtype']
    if dtype not in ('取衣', '送衣'):
        continue
    rows.append({
        'store': r['store'],
        'dtype': dtype,
        'date': r['date'],
        'pieces': int(r['pieces'] or 0),
        'deliverer': r['deliverer'],
    })

# ===== 分析窗口：取自系统拉取（pull_qusong.py 的 meta.start/end），每日滚动 =====
START, END = _qs["start"], _qs["end"]
rows = [x for x in rows if START <= x['date'] <= END]

# ===== 手工修正（覆盖特定 日期/伙伴/类型 的件数合计）=====
# 用途：系统源数据存在录入偏差时人工订正；作用于归一化后的明细，重拉数据后依然生效。
# 规则：仅调整件数合计、不改变订单数；把差额加到首个匹配行上（差额为负时不低于 0）。
CORRECTIONS = {
    ('2026-08-16', '王明志', '取衣'): 40,
}
for (_date, _del, _dtype), _target in CORRECTIONS.items():
    _m = [r for r in rows if r['date'] == _date and r['deliverer'] == _del and r['dtype'] == _dtype]
    if not _m:
        print(f"[修正] 未找到匹配行: {_date} {_del} {_dtype}（跳过）")
        continue
    _cur = sum(r['pieces'] for r in _m)
    if _cur == _target:
        continue
    _diff = _target - _cur
    _m[0]['pieces'] = max(0, _m[0]['pieces'] + _diff)
    print(f"[修正] {_date} {_del} {_dtype} 件数: {_cur} -> {_target}（差额 {_diff}，首行修正至 {_m[0]['pieces']}）")


def _daterange(s, e):
    out, d = [], date.fromisoformat(s)
    end = date.fromisoformat(e)
    while d <= end:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out

dates = _daterange(START, END)
REFORM_DATE = '2026-08-12'          # 取送机制改革启动日（固定节点）
if REFORM_DATE not in dates:
    raise SystemExit(f"分析窗口 {START}~{END} 不包含改革日 {REFORM_DATE}，请检查 pull_qusong.py 的窗口参数。")
DT = ['取衣', '送衣']

def empty_daily(dlist):
    return {d: {'取衣': {'orders': 0, 'pieces': 0},
                '送衣': {'orders': 0, 'pieces': 0}} for d in dlist}

def accumulate(daily, dtype, date, pieces):
    cell = daily[date][dtype]
    cell['orders'] += 1
    cell['pieces'] += pieces

# ---- Stores ----
store_daily = defaultdict(lambda: empty_daily(dates))
for x in rows:
    accumulate(store_daily[x['store']], x['dtype'], x['date'], x['pieces'])

# ---- Partners (现役 6 位；梁几斗 9.1 起接替杨龙，只计 9.1 后数据) ----
partner_daily = defaultdict(lambda: empty_daily(dates))
for x in rows:
    if x['deliverer'] in PARTNER_SET and in_role(x['deliverer'], x['date']):
        accumulate(partner_daily[x['deliverer']], x['dtype'], x['date'], x['pieces'])

def summarize(daily, dlist=None, use_active_days=False):
    # use_active_days=True：伙伴维度专用——当天休息（当日 0 单）不纳入计算，
    # 不算天数：日均 = 总单/件 ÷ 实际出勤天数；active_days/rest_days 同步输出。
    dlist = dlist or dates
    tot_o = tot_p = q_o = q_p = s_o = s_p = 0
    for d in dlist:
        for t in DT:
            o = daily[d][t]['orders']; p = daily[d][t]['pieces']
            tot_o += o; tot_p += p
            if t == '取衣': q_o += o; q_p += p
            else:          s_o += o; s_p += p
    ndays = len(dlist)
    active_days = sum(1 for d in dlist if daily[d]['取衣']['orders'] + daily[d]['送衣']['orders'] > 0)
    rest_days = ndays - active_days
    denom = active_days if (use_active_days and active_days > 0) else ndays
    return {
        'total_orders': tot_o, 'total_pieces': tot_p,
        'quyi_orders': q_o, 'quyi_pieces': q_p,
        'songyi_orders': s_o, 'songyi_pieces': s_p,
        'active_days': active_days, 'rest_days': rest_days,
        'daily_avg_orders': round(tot_o / denom, 2),
        'daily_avg_pieces': round(tot_p / denom, 2),
        'avg_pieces_per_order': round(tot_p / tot_o, 2) if tot_o else 0,
        'quyi_avg_pieces': round(q_p / q_o, 2) if q_o else 0,
        'songyi_avg_pieces': round(s_p / s_o, 2) if s_o else 0,
    }

def series(daily):
    out = {'dates': dates}
    for t in DT + ['合计']:
        if t == '合计':
            out['orders'] = [daily[d]['取衣']['orders'] + daily[d]['送衣']['orders'] for d in dates]
            out['pieces'] = [daily[d]['取衣']['pieces'] + daily[d]['送衣']['pieces'] for d in dates]
        else:
            out[t + '_orders'] = [daily[d][t]['orders'] for d in dates]
            out[t + '_pieces'] = [daily[d][t]['pieces'] for d in dates]
    return out

stores_out = {}
for st in sorted(store_daily.keys()):
    stores_out[st] = {'daily': series(store_daily[st]), 'summary': summarize(store_daily[st], dates)}

partners_out = {}
for p in PARTNERS:  # keep given order
    since = PARTNER_SINCE.get(p, START)
    dlist_p = [d for d in dates if d >= since]  # 只在其任职窗口内算出勤/休息
    partners_out[p] = {'daily': series(partner_daily[p]),
                       'summary': summarize(partner_daily[p], dlist_p, use_active_days=True)}

# Overall (all stores, all deliverers)
overall_daily = empty_daily(dates)
for x in rows:
    accumulate(overall_daily, x['dtype'], x['date'], x['pieces'])
overall = {'daily': series(overall_daily), 'summary': summarize(overall_daily, dates)}

# Partners-only overall（现役伙伴口径）
ponly_daily = empty_daily(dates)
for x in rows:
    if x['deliverer'] in PARTNER_SET and in_role(x['deliverer'], x['date']):
        accumulate(ponly_daily, x['dtype'], x['date'], x['pieces'])
ponly = {'daily': series(ponly_daily), 'summary': summarize(ponly_daily, dates)}

# ===== 改革前基线（改革日之前的天数，每日滚动）=====
PRE_DATES = [d for d in dates if d < REFORM_DATE]
pre_rows = [x for x in rows if x['date'] < REFORM_DATE]
PRE_PERIOD = f"{PRE_DATES[0]} ~ {PRE_DATES[-1]}"

def baseline_for(filter_fn):
    d = empty_daily(PRE_DATES)
    for x in pre_rows:
        if filter_fn(x):
            accumulate(d, x['dtype'], x['date'], x['pieces'])
    return summarize(d, PRE_DATES, use_active_days=True)

base_overall = baseline_for(lambda x: True)
base_partners = {p: baseline_for(lambda x, p=p: x['deliverer'] == p and in_role(p, x['date'])) for p in PARTNERS}

result = {
    'meta': {
        'title': '人南片区取送情况分析',
        'period': f"{START} ~ {END}",
        'days': len(dates),
        'reform_date': REFORM_DATE,
        'reform_index': dates.index(REFORM_DATE),
        'pre_period': PRE_PERIOD,
        'pre_days': len(PRE_DATES),
        'partners': PARTNERS,
        'partner_active_from': PARTNER_SINCE,
        'partner_change_note': '杨龙 2026-09-01 起离职，岗位由梁几斗接替（梁几斗自 9.1 起计入伙伴统计，其 9 月前的顶班记录不计入伙伴维度）',
        'stores': sorted(store_daily.keys()),
        'order_date_field': '预约时间',
        'total_rows_in_window': len(rows),
        'data_source': '系统接口 /api/zhcx/deliveryinfo/query（deliveryStatus=Y 已完成）',
    },
    'dates': dates,
    'overall': overall,
    'partners_overall': ponly,
    'stores': stores_out,
    'partners': partners_out,
    'baseline': {
        'pre_period': PRE_PERIOD,
        'pre_days': len(PRE_DATES),
        'overall': base_overall,
        'partners': base_partners,
    },
}

with open('analysis_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print("rows in window:", len(rows))
print("stores:", list(stores_out.keys()))
print("overall summary:", json.dumps(overall['summary'], ensure_ascii=False))
print("partners_overall:", json.dumps(ponly['summary'], ensure_ascii=False))
print("partner summaries:")
for p in PARTNERS:
    print(" ", p, json.dumps(partners_out[p]['summary'], ensure_ascii=False))
print("BASELINE (1-11) overall:", json.dumps(base_overall, ensure_ascii=False))
print("BASELINE (1-11) partners:")
for p in PARTNERS:
    print(" ", p, json.dumps(base_partners[p], ensure_ascii=False))
