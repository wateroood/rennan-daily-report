# -*- coding: utf-8 -*-
"""
国色星洗 SaaS (server.guosexiran.com) 取数客户端 —— 跨电脑可移植版

设计要点（均为实测踩坑后固化，勿随意改动）：
  1. 站点为 Cookie 鉴权（非 Bearer token）。最稳的方式是 Playwright 登录后，
     在同源页面内用 JS fetch 调 API（credentials:'include'），免去手工搬 Cookie。
  2. 前端启动时会尝试读取本机 MAC，读不到会抛 "获取mac地址失败"。
     解决：add_init_script 预置 window.__LOCAL_MAC__ + localStorage，并吞掉 pageerror。
  3. API 调用形状：源码 Object(C["b"])({method:"post", data:t, params:e, url:...})
     → 第 1 参 = querystring(分页)，第 2 参 = body。故分页必须走 ?page=N&size=N。
  4. ⚠️时间格式因接口而异（最大坑）：
       - getPageYybb        : startTime/endTime 用纯日期，且为**半开区间** [start, next_day)
       - financialtotal     : 必须 ISO  YYYY-MM-DDTHH:mm:ss，用空格分隔会静默返回空
       - getClothesDetails  : 必须 ISO  YYYY-MM-DDTHH:mm:ss
       - getPageXfbb        : 必须 ISO  YYYY-MM-DDTHH:mm:ss
  5. yybb 必须分页拉取（size=500），且需按 (date, shopName) 去重防分页重叠。

用法：
    from gsx_client import GSXClient, load_config
    cfg = load_config()
    with GSXClient(cfg) as c:
        rows = c.yybb(c.all_shop_ids, "2026-08-07", "2026-08-08")
        ft   = c.financial_total(c.all_shop_ids, "2026-08-07", "2026-08-07")
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_CFG = HERE / "config.json"

# 页面内执行的通用 fetch 助手：统一抹平 data 是 数组 / {records,total} / 单对象 三种返回形状
_JS_FETCH = """async (a) => {
  let u = a.url;
  if (a.qs) u += (u.includes('?') ? '&' : '?') + a.qs;
  const o = { method: 'POST', headers: { 'content-type': 'application/json' }, credentials: 'include' };
  if (a.body !== null && a.body !== undefined) o.body = JSON.stringify(a.body);
  try {
    const r = await fetch(u, o);
    const t = await r.text();
    let j = null; try { j = JSON.parse(t); } catch (e) {}
    let recs = null, total = null;
    if (j && j.data) {
      if (Array.isArray(j.data)) recs = j.data;
      else if (j.data.records) { recs = j.data.records; total = j.data.total; }
      else recs = [j.data];
    }
    return { recs: recs || [], total: total,
             success: j ? j.success : null,
             msg: j ? (j.msg || j.message) : t.slice(0, 200),
             http: r.status };
  } catch (e) {
    return { recs: [], total: null, success: false, msg: 'ERR:' + e.message, http: 0 };
  }
}"""


# --------------------------------------------------------------------------- #
# 配置
# --------------------------------------------------------------------------- #
def local_mac() -> str:
    """本机真实 MAC，格式 AA-BB-CC-DD-EE-FF"""
    n = uuid.getnode()
    return "-".join(f"{(n >> i) & 0xFF:02X}" for i in range(40, -8, -8))


def load_config(path: str | Path | None = None) -> dict:
    cfg = json.loads(Path(path or DEFAULT_CFG).read_text(encoding="utf-8"))
    # 环境变量覆盖，便于在别的电脑/CI 上换账号而不改文件
    cfg["base"] = os.getenv("GSX_BASE", cfg["base"]).rstrip("/")
    cfg["user"] = os.getenv("GSX_USER", cfg["user"])
    cfg["password"] = os.getenv("GSX_PASS", cfg["password"])
    mac = os.getenv("GSX_MAC", cfg.get("mac", "auto"))
    cfg["mac"] = local_mac() if str(mac).lower() == "auto" else mac
    return cfg


# --------------------------------------------------------------------------- #
# 日期工具
# --------------------------------------------------------------------------- #
def iso_start(d: str) -> str:
    """'2026-08-07' -> '2026-08-07T00:00:00'"""
    return f"{d}T00:00:00"


def iso_end(d: str) -> str:
    """'2026-08-07' -> '2026-08-07T23:59:59'（闭区间末尾）"""
    return f"{d}T23:59:59"


def next_day(d: str) -> str:
    return (date.fromisoformat(d) + timedelta(days=1)).isoformat()


def month_segments(start: str, end: str):
    """按自然月切段，返回 [(tag, seg_start, seg_end_exclusive), ...]（yybb 半开区间用）"""
    s, e = date.fromisoformat(start), date.fromisoformat(end)
    segs, cur = [], s.replace(day=1)
    while cur <= e:
        ny, nm = (cur.year + 1, 1) if cur.month == 12 else (cur.year, cur.month + 1)
        nxt = date(ny, nm, 1)
        seg_s = max(cur, s)
        seg_e = min(nxt, e + timedelta(days=1))  # 半开区间上界
        if seg_s < seg_e:
            segs.append((f"{cur.year}-{cur.month:02d}", seg_s.isoformat(), seg_e.isoformat()))
        cur = nxt
    return segs


# --------------------------------------------------------------------------- #
# 客户端
# --------------------------------------------------------------------------- #
class LoginError(RuntimeError):
    pass


class GSXClient:
    def __init__(self, cfg: dict | None = None, verbose: bool = True):
        self.cfg = cfg or load_config()
        self.api = self.cfg["api"]
        self.verbose = verbose
        self._pw = self._browser = self._ctx = self._page = None

        self.retail_shop_ids = sorted(int(k) for k in self.cfg["shops"])
        self.internal_shop_ids = sorted(int(k) for k in self.cfg.get("internal_shops", {}))
        self.all_shop_ids = self.retail_shop_ids + self.internal_shop_ids
        self.shop_names = {int(k): v for k, v in self.cfg["shops"].items()}
        self.shop_names.update({int(k): v for k, v in self.cfg.get("internal_shops", {}).items()})

    # ---------------- 生命周期 ----------------
    def __enter__(self):
        self.start()
        self.login()
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def _log(self, *a):
        if self.verbose:
            print(*a, flush=True)

    def start(self):
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        args = ["--no-sandbox", "--disable-dev-shm-usage"]
        headless = self.cfg.get("headless", True)
        last = None
        for ch in list(self.cfg.get("browser_channels", [])) + [None]:
            try:
                self._browser = (
                    self._pw.chromium.launch(channel=ch, headless=headless, args=args)
                    if ch else
                    self._pw.chromium.launch(headless=headless, args=args)
                )
                self._log(f"[browser] 使用 {ch or 'playwright-chromium'}")
                break
            except Exception as e:                      # 该通道未安装，试下一个
                last = e
        if self._browser is None:
            raise RuntimeError(
                f"无可用浏览器。请安装 Edge/Chrome，或执行 `python -m playwright install chromium`。原始错误：{last}"
            )

        self._ctx = self._browser.new_context(ignore_https_errors=True, locale="zh-CN")
        mac = self.cfg["mac"]
        # 关键：前端读不到 MAC 会抛错并中断初始化，这里预置好
        self._ctx.add_init_script(
            f'window.__LOCAL_MAC__="{mac}";'
            f'try{{localStorage.setItem("mac","{mac}");'
            f'localStorage.setItem("macAddress","{mac}");}}catch(e){{}}'
        )
        self._page = self._ctx.new_page()
        self._page.on("pageerror", lambda e: None)      # 吞掉无害的 MAC / 埋点报错

    def close(self):
        for obj, m in ((self._ctx, "close"), (self._browser, "close"), (self._pw, "stop")):
            try:
                if obj:
                    getattr(obj, m)()
            except Exception:
                pass
        self._pw = self._browser = self._ctx = self._page = None

    # ---------------- 登录 ----------------
    def login(self, retries: int = 2):
        base = self.cfg["base"]
        for attempt in range(1, retries + 1):
            try:
                self._page.goto(f"{base}/#/login", wait_until="networkidle", timeout=45000)
                self._page.wait_for_timeout(1500)
                self._page.fill("#loginForm_tel", self.cfg["user"])
                self._page.fill("#loginForm_password", self.cfg["password"])
                self._page.wait_for_timeout(300)
                btn = (self._page.query_selector('button:has-text("登录")')
                       or self._page.query_selector("button.ant-btn-primary"))
                if btn:
                    btn.click()
                self._page.wait_for_timeout(4500)
                if self._verify_login():
                    self._log(f"[login] 成功（第 {attempt} 次尝试）")
                    return
                self._log(f"[login] 第 {attempt} 次未通过校验，重试…")
            except Exception as e:
                self._log(f"[login] 第 {attempt} 次异常：{e}")
            self._page.wait_for_timeout(2000)
        raise LoginError(
            "登录失败。排查顺序：①账号密码 ②该机器 MAC 是否已在 SaaS 侧授权"
            "（config.json 的 mac 字段 / 环境变量 GSX_MAC）③网络能否访问 " + base
        )

    def _verify_login(self) -> bool:
        """用一个最轻量的真实业务请求确认会话有效（比看 URL 可靠）"""
        try:
            today = date.today().isoformat()
            r = self.call(
                self.api["yybb"],
                {"shopIds": self.all_shop_ids[:1], "startTime": today,
                 "endTime": next_day(today), "timeType": 1},
                "page=1&size=1",
            )
            return r.get("http") == 200 and r.get("success") is not False
        except Exception:
            return False

    # ---------------- 基础调用 ----------------
    def call(self, url: str, body, qs: str | None = None) -> dict:
        return self._page.evaluate(_JS_FETCH, {"url": url, "body": body, "qs": qs})

    def call_paged(self, url: str, body, size: int = 500, max_pages: int = 200) -> list:
        """自动翻页，返回全部 records"""
        out, page = [], 1
        while page <= max_pages:
            r = self.call(url, body, f"page={page}&size={size}")
            recs = r.get("recs") or []
            if not recs:
                break
            out += recs
            total = r.get("total")
            if total and len(out) >= total:
                break
            if len(recs) < size:      # 无 total 字段时的收尾判据
                break
            page += 1
        return out

    # ---------------- 业务接口 ----------------
    def yybb(self, shop_ids, start: str, end_exclusive: str) -> list:
        """营业报表（逐日逐店）。注意 end 为**半开区间上界**，查 8-07 当天要传 end='2026-08-08'。"""
        return self.call_paged(
            self.api["yybb"],
            {"shopIds": list(shop_ids), "startTime": start,
             "endTime": end_exclusive, "timeType": 1},
        )

    def yybb_range(self, shop_ids, start: str, end_inclusive: str, dedup: bool = True) -> list:
        """跨月安全拉取：按自然月分段 + 按 (date, shopName) 去重。end 为**闭区间**日期。"""
        store, seq = {}, []
        for tag, s, e in month_segments(start, end_inclusive):
            t0 = time.time()
            rows = self.yybb(shop_ids, s, e)
            dup = 0
            for r in rows:
                k = (r.get("date"), r.get("shopName"))
                if dedup:
                    if k in store:
                        dup += 1
                    store[k] = r
                else:
                    seq.append(r)
            self._log(f"  {tag} [{s}~{e}) 拉取={len(rows):5d} "
                      f"累计={len(store) if dedup else len(seq):6d} 重复={dup} ({time.time()-t0:.0f}s)")
        return list(store.values()) if dedup else seq

    def financial_total(self, shop_ids, start: str, end: str) -> dict:
        """财务汇总（系统官方口径，含权威 xjlhjTotal 现金流合计）。⚠️必须 ISO 时间。"""
        st, ed = iso_start(start), iso_end(end)
        r = self.call(self.api["financial_total"], {
            "shopIdList": list(shop_ids),
            "rangeDatetime": [st, ed],
            "startDatetime": st,
            "stopDatetime": ed,
        })
        recs = r.get("recs") or []
        return recs[0] if recs else {}

    def clothes_details(self, shop_ids, start: str, end: str, size: int = 2000) -> list:
        """收件产品明细（件数/高附加值判定的权威数据源）。⚠️必须 ISO 时间。"""
        return self.call_paged(
            self.api["clothes_details"],
            {"startTime": iso_start(start), "endTime": iso_end(end), "shopIds": list(shop_ids)},
            size=size,
        )

    def xfbb(self, shop_ids, start: str, end: str) -> list:
        """消费报表（客户维度）。⚠️必须 ISO 时间。"""
        return self.call_paged(
            self.api["xfbb"],
            {"shopIds": list(shop_ids), "startTime": iso_start(start), "endTime": iso_end(end)},
        )

    def delivery_info(self, shop_ids, start: str, end: str, status: str = "Y") -> list:
        """
        取送/配送信息明细（= 配送信息查询页数据源，字段与导出的「配送信息-*.xls」完全一致）。

        字段映射：门店=shopName, 配送类型=deliveryType(取衣/送衣), 客户= customerName/tel/address,
        流水号=runningNumber, 预约时间=planDeliveryDatetime, 派单人=assignStaffName,
        派单时间=assignDatetime, 衣物数量=clothesCount, 配送人=deliveryStaffName,
        完成时间=deliveryDatetime, 配送状态=deliveryStatus(Y已完成/N未完成), 是否超时=onTime。

        ⚠️ 必须 ISO 时间；deliveryStatus='Y' 已完成（历史），'N' 未完成（待派/在途）。
        实测口径（人南片区7店, 8.1-8.11）：Y 共 1329 单/3519 件，与线下导出的 Excel 完全一致。
        """
        return self.call_paged(
            self.api["delivery_info"],
            {"shopIdList": list(shop_ids), "queryPickup": True, "querySend": True,
             "startDatetime": iso_start(start), "stopDatetime": iso_end(end),
             "deliveryStatus": status},
            size=2000,
        )


# --------------------------------------------------------------------------- #
# 口径计算（已通过与系统官方接口的同刻比对，差 0.00）
# --------------------------------------------------------------------------- #
def _f(x) -> float:
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def cash_flow(row: dict) -> float:
    """
    现金流（≡ 系统 financialtotal.xjlhjTotal，实测 4 个时段差额均为 0.00）

        售卡(现金+POS+微信+支付宝) + 充值(同 4 类)
      + 消费现金类(现金+微信+支付宝+POS)      ← 已含欠款补交 T0504/T0506，勿重复加
      − 退卡(totalTk)

    ⚠️2026-08-09 用户确认：含第三方支付 totalDsfXf（美团/抖音等），对齐系统看板口径；
      对账基准相应改为 官方 xjlhjTotal + consumptionDsf。
    """
    sk = _f(row.get("totalXjSk")) + _f(row.get("totalPosSk")) + _f(row.get("totalWxSk")) + _f(row.get("totalZfbSk"))
    cz = _f(row.get("totalXjCz")) + _f(row.get("totalPosCz")) + _f(row.get("totalWxCz")) + _f(row.get("totalZfbCz"))
    xf = _f(row.get("totalXjXf")) + _f(row.get("totalWxXf")) + _f(row.get("totalZfbXf")) + _f(row.get("totalPosXf"))
    return sk + cz + xf + _f(row.get("totalDsfXf")) - _f(row.get("totalTk"))


def revenue(row: dict) -> float:
    """营收 = 营业额 + 0.7 × 券抵扣（看板口径：营收含券）"""
    return _f(row.get("totalTurnover")) + 0.7 * _f(row.get("totalCoupondeductFee"))


def clothes_num(row: dict) -> int:
    """收件数（yybb totalClothesNum 已验证 == getClothesDetails 的 total）"""
    return int(_f(row.get("totalClothesNum")))


def aggregate(rows) -> dict:
    """把一批 yybb 行聚合成指标字典"""
    return {
        "revenue": round(sum(revenue(r) for r in rows), 2),
        "turnover": round(sum(_f(r.get("totalTurnover")) for r in rows), 2),
        "coupon": round(sum(_f(r.get("totalCoupondeductFee")) for r in rows), 2),
        "cash_flow": round(sum(cash_flow(r) for r in rows), 2),
        "dsf": round(sum(_f(r.get("totalDsfXf")) for r in rows), 2),
        "clothes": sum(clothes_num(r) for r in rows),
        "shop_days": len(rows),
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cfg = load_config()
    print(f"base={cfg['base']}  user={cfg['user']}  mac={cfg['mac']}  (本机真实 MAC={local_mac()})")
    with GSXClient(cfg) as c:
        d = sys.argv[1] if len(sys.argv) > 1 else "2026-08-07"
        rows = c.yybb(c.all_shop_ids, d, next_day(d))
        a = aggregate(rows)
        ft = c.financial_total(c.all_shop_ids, d, d)
        print(f"\n{d} 门店行数={len(rows)}")
        print(f"  营收   {a['revenue']:>14,.2f}")
        print(f"  现金流 {a['cash_flow']:>14,.2f}   官方 xjlhjTotal {_f(ft.get('xjlhjTotal')):>14,.2f}"
              f"   差 {a['cash_flow'] - _f(ft.get('xjlhjTotal')):>+10,.2f}")
        print(f"  件数   {a['clothes']:>14,}")
