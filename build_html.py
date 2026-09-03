import json

with open('analysis_data.json', encoding='utf-8') as f:
    DATA = json.load(f)

DATA_JSON = json.dumps(DATA, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>人南片区取送情况分析</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@3.0.1/dist/chartjs-plugin-annotation.min.js"></script>
<style>
  :root{
    --bg:#f4f6fb; --card:#ffffff; --ink:#1f2733; --sub:#6b7686;
    --line:#e7ebf2; --blue:#2f6df0; --teal:#13b6a4; --orange:#f59229;
    --purple:#8b5cf6; --pink:#ec4899; --green:#22a06b; --red:#e5484d;
  }
  *{box-sizing:border-box;}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
       background:var(--bg);color:var(--ink);}
  header{position:sticky;top:0;z-index:20;background:rgba(255,255,255,.92);backdrop-filter:blur(8px);
         border-bottom:1px solid var(--line);padding:14px 22px;}
  .htitle{font-size:19px;font-weight:700;display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
  .hsub{color:var(--sub);font-size:13px;margin-top:3px;}
  .wrap{max-width:1180px;margin:0 auto;padding:20px 22px 60px;}
  .tabs{display:flex;gap:8px;margin:6px 0 22px;flex-wrap:wrap;}
  .tabs button{border:1px solid var(--line);background:var(--card);padding:9px 18px;border-radius:10px;cursor:pointer;
               font-size:14px;font-weight:600;color:var(--sub);}
  .tabs button.active{background:var(--ink);color:#fff;border-color:var(--ink);}
  .sec{display:none;}
  .sec.active{display:block;}
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:14px;margin-bottom:22px;}
  .kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;box-shadow:0 1px 3px rgba(20,30,60,.04);}
  .kpi .lbl{color:var(--sub);font-size:12.5px;margin-bottom:6px;}
  .kpi .val{font-size:25px;font-weight:750;letter-spacing:.3px;}
  .kpi .val small{font-size:13px;color:var(--sub);font-weight:600;margin-left:3px;}
  .kpi .sub{font-size:12px;color:var(--sub);margin-top:5px;}
  /* 改革后对比排：橙色顶边区分于改革前基线排 */
  .kpi.after{border-top:3px solid var(--orange);background:#fffdf8;}
  .rowtag{display:flex;align-items:center;gap:8px;margin:2px 0 12px;font-size:13px;font-weight:700;}
  .rowtag small{font-weight:600;color:var(--sub);font-size:12px;}
  .rowtag.after{color:var(--orange);}
  .panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin-bottom:20px;box-shadow:0 1px 3px rgba(20,30,60,.04);}
  .panel h3{margin:0 0 4px;font-size:15.5px;}
  .panel .desc{color:var(--sub);font-size:12.5px;margin:0 0 14px;}
  .grid2{display:grid;grid-template-columns:1.5fr 1fr;gap:20px;}
  @media(max-width:820px){.grid2{grid-template-columns:1fr;}}
  /* 手机自适应 */
  @media(max-width:640px){
    header{padding:12px 14px;}
    .htitle{font-size:16px;gap:8px;}
    .hsub{font-size:11.5px;}
    .wrap{padding:14px 12px 48px;}
    .tabs{margin:4px 0 16px;gap:6px;flex-wrap:nowrap;overflow-x:auto;padding-bottom:4px;-webkit-overflow-scrolling:touch;scrollbar-width:none;}
    .tabs::-webkit-scrollbar{display:none;}
    .tabs button{padding:8px 13px;font-size:13px;white-space:nowrap;flex:0 0 auto;}
    .cards{grid-template-columns:repeat(2,1fr);gap:10px;}
    .kpi{padding:12px 13px;box-shadow:none;}
    .kpi .val{font-size:20px;}
    .kpi .lbl{font-size:11.5px;}
    .panel{padding:14px;margin-bottom:14px;}
    .panel h3{font-size:14.5px;}
    .panel .desc,.base-note,.ptn-base{font-size:11.5px;}
    .chartbox{height:260px;}
    .chartbox.sm{height:230px;}
    .selrow{flex-direction:column;align-items:stretch;gap:8px;}
    .selrow select{width:100%;}
    .ptn-hd{gap:6px;}
    .ptn-chip{font-size:10.5px;padding:2px 7px;}
    .ptn-name{font-size:14.5px;}
    .rank .nm{width:70px;font-size:12.5px;}
    .rank .v{width:52px;font-size:11.5px;}
    table,.cmp-tbl{font-size:11.5px;}
    th,td{padding:6px 7px;}
    .note{font-size:11.5px;padding:11px 13px;}
    .reformtag{font-size:11px;}
  }
  @media(max-width:380px){
    .cards{grid-template-columns:repeat(2,1fr);}
    .kpi .val{font-size:18px;}
    .chartbox{height:240px;}
  }
  .chartbox{position:relative;height:320px;}
  .chartbox.sm{height:280px;}
  .selrow{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:16px;}
  select{padding:9px 14px;border:1px solid var(--line);border-radius:9px;font-size:14px;background:var(--card);color:var(--ink);font-weight:600;}
  table{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px;}
  th,td{padding:8px 10px;text-align:center;border-bottom:1px solid var(--line);}
  th{background:#f7f9fc;color:var(--sub);font-weight:600;position:sticky;top:0;}
  td.st{font-weight:600;}
  tr:hover td{background:#fafbfe;}
  .legend{display:flex;gap:16px;font-size:12.5px;color:var(--sub);margin-top:8px;flex-wrap:wrap;}
  .legend i{width:11px;height:11px;border-radius:3px;display:inline-block;margin-right:5px;vertical-align:-1px;}
  .note{color:var(--sub);font-size:12.5px;line-height:1.7;background:#fbfcfe;border:1px dashed var(--line);border-radius:12px;padding:14px 16px;margin-top:8px;}
  .rank{display:flex;align-items:center;gap:10px;margin:8px 0;}
  .rank .nm{width:92px;flex:none;font-weight:600;font-size:13.5px;white-space:nowrap;}
  .rank .track{flex:1;min-width:0;display:flex;align-items:center;}
  .rank .bar{height:22px;border-radius:6px;background:var(--blue);min-width:4px;max-width:100%;}
  .rank .v{flex:none;width:62px;text-align:right;font-size:12.5px;color:var(--sub);white-space:nowrap;}
  .flexhd{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;}
  .ptn-grid{display:grid;grid-template-columns:1fr;gap:20px;margin-top:6px;}
  .ptn{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px 18px;box-shadow:0 1px 3px rgba(20,30,60,.04);}
  .ptn-hd{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:12px;}
  .ptn-name{font-size:16px;font-weight:700;}
  .ptn-chip{font-size:11.5px;color:var(--sub);background:#f4f6fb;border:1px solid var(--line);padding:3px 9px;border-radius:20px;font-weight:600;white-space:nowrap;}
  .ptn .panel{margin-bottom:0;}
  .reformtag{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--orange);font-weight:600;background:#fff4e6;border:1px solid #ffe0b8;padding:3px 10px;border-radius:20px;margin-top:8px;}
  .reformtag i{width:10px;height:10px;border-radius:50%;background:var(--orange);display:inline-block;}
  .up{color:#22a06b;font-weight:700;}
  .down{color:#e5484d;font-weight:700;}
  .flat{color:var(--sub);font-weight:700;}
  .cmp-tbl{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px;}
  .cmp-tbl th,.cmp-tbl td{padding:9px 10px;text-align:center;border-bottom:1px solid var(--line);}
  .cmp-tbl th{background:#f7f9fc;color:var(--sub);font-weight:600;position:sticky;top:0;white-space:nowrap;}
  .cmp-tbl td.st{font-weight:700;white-space:nowrap;}
  .base-note{font-size:12.5px;color:var(--sub);margin:4px 0 14px;}
  .ptn-base{font-size:12.5px;color:var(--sub);margin:-4px 0 12px;line-height:1.6;}
  .ptn-base b{color:var(--ink);}
  .pdet{background:#fbfcfe;border:1px dashed var(--line);border-radius:12px;margin-top:14px;}
  .pdet summary{cursor:pointer;padding:11px 16px;font-weight:700;font-size:13.5px;color:var(--ink);
                list-style:none;display:flex;align-items:center;gap:8px;user-select:none;}
  .pdet summary::-webkit-details-marker{display:none;}
  .pdet summary::before{content:'▸';color:var(--blue);transition:transform .15s;font-size:12px;}
  .pdet[open] summary::before{transform:rotate(90deg);}
  .pdet .pdet-body{padding:2px 16px 16px;overflow:auto;max-height:460px;}
  .pdet .cmp-tbl th{position:static;}
  /* 伙伴改革后单日明细 · 日期筛选按钮 */
  .datefilter{display:flex;gap:8px;flex-wrap:wrap;margin:4px 0 14px;align-items:center;}
  .datefilter .df-lbl{font-size:12.5px;color:var(--sub);font-weight:600;margin-right:2px;}
  .datefilter button{border:1px solid var(--line);background:var(--card);padding:6px 14px;border-radius:20px;cursor:pointer;font-size:13px;font-weight:600;color:var(--sub);transition:all .12s;white-space:nowrap;}
  .datefilter button:hover{border-color:var(--orange);color:var(--orange);}
  .datefilter button.active{background:var(--orange);color:#fff;border-color:var(--orange);}
  @media(max-width:640px){
    .datefilter button{padding:5px 11px;font-size:12px;}
  }
</style>
</head>
<body>
<header>
  <div class="htitle">📦 人南片区取送情况分析
    <span class="hsub" id="period"></span>
  </div>
</header>

<div class="wrap">
  <div class="tabs" id="tabs">
    <button data-tab="reform" class="active">改革效果</button>
    <button data-tab="overview">片区总览</button>
    <button data-tab="stores">门店分析</button>
    <button data-tab="partners">伙伴分析</button>
  </div>

  <!-- OVERVIEW -->
  <section class="sec" id="sec-overview"></section>

  <!-- STORES -->
  <section class="sec" id="sec-stores"></section>

  <!-- PARTNERS -->
  <section class="sec" id="sec-partners"></section>

  <!-- REFORM (默认展示) -->
  <section class="sec active" id="sec-reform"></section>

  <div class="note" id="footnote"></div>
</div>

<script>
const DATA = __DATA__;
const C = {blue:'#2f6df0',teal:'#13b6a4',orange:'#f59229',purple:'#8b5cf6',pink:'#ec4899',green:'#22a06b',red:'#e5484d',gray:'#9aa6b8'};
const charts = {};
if(window.ChartDataLabels) Chart.register(window.ChartDataLabels);
const AnnotationPlugin = window.ChartAnnotation || window['chartjs-plugin-annotation'];
if(AnnotationPlugin) Chart.register(AnnotationPlugin);
// 全局默认：在柱/线上直接显示数值
Chart.defaults.plugins.datalabels = {
  display:true, color:'#1f2733', font:{size:10,weight:'700'},
  anchor:'end', align:'end', clamp:true, offset:2,
  formatter:(v)=> (v==null?'':v)
};
const dates = DATA.dates.map(d=>d.slice(5).replace('-','/'));

// 改革启动标记线（8.12 起取送机制改革）
function reformLabel(){
  const i = DATA.meta.reform_index;
  return (i!=null && i>=0) ? dates[i] : null;
}
function reformAnno(){
  const lbl = reformLabel();
  if(!lbl) return {};
  // 注意：annotation v3 + Chart.js4 在 category 轴上必须用 value 定位；
  // 实测 xMin/xMax 传字符串标签不绘制（静默失败），value 正常。
  return {annotations:{reformLine:{
    type:'line', scaleID:'x', value:lbl,
    borderColor:'#f59229', borderWidth:2, borderDash:[6,4],
    label:{display:true, content:'取送机制改革启动', position:'start',
      backgroundColor:'#f59229', color:'#fff', font:{size:11,weight:'700'}, padding:4, borderRadius:4}
  }}};
}
function kpiCard(lbl,val,unit,sub,cls){
  return `<div class="kpi${cls?` ${cls}`:''}"><div class="lbl">${lbl}</div><div class="val">${val}${unit?`<small>${unit}</small>`:''}</div>${sub?`<div class="sub">${sub}</div>`:''}</div>`;
}

// 改革后区间（reform_date 起）日均指标 —— 与改革前基线同维度，供上下两排卡片对比
function reformPeriodAvg(){
  const i = DATA.meta.reform_index;
  const d = DATA.overall.daily;
  const days = DATA.dates.length - i;
  const sum = a=> a.slice(i).reduce((x,y)=>x+y,0);
  const qo=sum(d['取衣_orders']), so=sum(d['送衣_orders']), to=sum(d['orders']);
  const tp=sum(d['pieces']);
  return {days, qo, so, to, tp,
    dqo:+(qo/days).toFixed(2), dso:+(so/days).toFixed(2),
    dto:+(to/days).toFixed(2), dtp:+(tp/days).toFixed(2),
    apo: to? +(tp/to).toFixed(2):0};
}

function renderOverview(){
  const o = DATA.overall, s=o.summary, d=o.daily;
  const ndays = DATA.meta.days;
  const sec=document.getElementById('sec-overview');
  sec.innerHTML = `
    <div class="cards">
      ${kpiCard('总订单量', s.total_orders,'单','取衣 '+s.quyi_orders+' · 送衣 '+s.songyi_orders)}
      ${kpiCard('总件数', s.total_pieces,'件','取衣 '+s.quyi_pieces+' · 送衣 '+s.songyi_pieces)}
      ${kpiCard('日均单量', s.daily_avg_orders,'单/天',ndays+'天累计均值')}
      ${kpiCard('日均件数', s.daily_avg_pieces,'件/天',ndays+'天累计均值')}
      ${kpiCard('单均件数', s.avg_pieces_per_order,'件/单','总件数 ÷ 总订单')}
    </div>
    <div class="panel">
      <h3>片区总单量逐日趋势</h3>
      <p class="desc">柱体=订单量（蓝=取衣，绿=送衣，叠加为合计）。🟧 虚线为 ${reformLabel()} 取送机制改革启动节点，用于观察改革前后变化。</p>
      <div class="chartbox"><canvas id="ovOrders"></canvas></div>
    </div>
    <div class="panel">
      <h3>片区总件数逐日趋势</h3>
      <p class="desc">柱体=件数（蓝=取衣，绿=送衣，叠加为合计）。</p>
      <div class="chartbox"><canvas id="ovPieces"></canvas></div>
    </div>
    <div class="panel">
      <h3>各门店订单量排名</h3>
      <p class="desc">按 ${ndays} 天累计总订单排序。</p>
      <div id="ovRank"></div>
    </div>`;
  document.getElementById('period').textContent = ' · '+DATA.meta.period+' · 共 '+DATA.meta.total_rows_in_window+' 单';
  drawStacked('ovOrders', d, 'orders');
  drawStacked('ovPieces', d, 'pieces');
  drawRank('ovRank', DATA.meta.stores, 'stores');
}

function drawTrend(id, daily, label){
  if(charts[id]) charts[id].destroy();
  const ds=[];
  const barDL={anchor:'center',align:'center',color:'#fff',clamp:true,font:{size:9,weight:'700'},formatter:v=>v||''};
  ds.push({type:'bar',label:'取衣订单',data:daily['取衣_orders'],backgroundColor:C.blue,stack:'o',borderRadius:4,order:3,datalabels:barDL});
  ds.push({type:'bar',label:'送衣订单',data:daily['送衣_orders'],backgroundColor:C.teal,stack:'o',borderRadius:4,order:3,datalabels:barDL});
  ds.push({type:'line',label:'件数(件)',data:daily['pieces'],yAxisID:'y1',borderColor:C.purple,backgroundColor:C.purple,
    tension:.35,borderWidth:2.5,pointRadius:3,order:1,
    datalabels:{color:C.purple,font:{size:9,weight:'600'},anchor:'end',align:'end',clamp:true,offset:3}});
  charts[id]=new Chart(document.getElementById(id),{
    data:{labels:dates,datasets:ds},
    options:{maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{labels:{boxWidth:14,font:{size:12}}},datalabels:{display:true},
        annotation:reformAnno()},
      scales:{
        y:{position:'left',stacked:true,title:{display:true,text:'订单(单)'},grid:{color:'#eef1f6'},beginAtZero:true},
        y1:{position:'right',title:{display:true,text:'件数(件)'},grid:{drawOnChartArea:false},beginAtZero:true}
      }}
  });
}

function drawDonut(id, s){
  if(charts[id]) charts[id].destroy();
  charts[id]=new Chart(document.getElementById(id),{
    type:'doughnut',
    data:{labels:['取衣','送衣'],datasets:[
      {data:[s.quyi_orders,s.songyi_orders],backgroundColor:[C.blue,C.teal],borderWidth:2,borderColor:'#fff'}]},
    options:{maintainAspectRatio:false,cutout:'58%',
      plugins:{legend:{position:'bottom',labels:{boxWidth:13,font:{size:12}}},
        title:{display:true,text:'订单量占比',font:{size:13,weight:'600'}},
        datalabels:{
          color:'#fff', font:{size:13,weight:'700'},
          formatter:(v,ctx)=>{const t=ctx.dataset.data.reduce((a,b)=>a+b,0); return (v/t*100).toFixed(1)+'%';},
          anchor:'center', align:'center', clamp:false
        }}}
  });
}

// 逐日堆叠柱（取衣/送衣）+ 改革启动标记线。metric: orders | pieces
function drawStacked(id, daily, metric){
  if(charts[id]) charts[id].destroy();
  const ds=[];
  const barDL={anchor:'center',align:'center',color:'#fff',clamp:true,font:{size:9,weight:'700'},formatter:v=>v||''};
  ds.push({type:'bar',label:'取衣',data:daily['取衣_'+metric],backgroundColor:C.blue,stack:'a',borderRadius:4,order:3,datalabels:barDL});
  ds.push({type:'bar',label:'送衣',data:daily['送衣_'+metric],backgroundColor:C.teal,stack:'a',borderRadius:4,order:3,datalabels:barDL});
  charts[id]=new Chart(document.getElementById(id),{
    data:{labels:dates,datasets:ds},
    options:{maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{labels:{boxWidth:14,font:{size:12}}},datalabels:{display:true},
        annotation:reformAnno()},
      scales:{y:{stacked:true,title:{display:true,text: metric==='orders'?'订单(单)':'件数(件)'},grid:{color:'#eef1f6'},beginAtZero:true}}
    }
  });
}

function drawRank(id, keys, kind){
  const map={};
  keys.forEach(k=>map[k]=DATA[kind][k].summary.total_orders);
  const arr=Object.entries(map).sort((a,b)=>b[1]-a[1]);
  const max=arr[0][1];
  document.getElementById(id).innerHTML = arr.map(([n,v])=>
    `<div class="rank"><div class="nm">${n}</div>
     <div class="track"><div class="bar" style="width:${(v/max*100).toFixed(1)}%"></div></div>
     <div class="v">${v} 单</div></div>`).join('');
}

function detailSection(kind, keys, overallObj){
  const selId = kind+'Sel';
  return `
  <div class="selrow">
    <label style="font-weight:600;color:var(--sub);font-size:13.5px;">选择${kind==='stores'?'门店':'伙伴'}：</label>
    <select id="${selId}">${keys.map(k=>`<option value="${k}">${k}</option>`).join('')}</select>
  </div>
  <div class="cards" id="${kind}Cards"></div>
  <div class="panel">
    <h3>逐日趋势（取衣/送衣 订单 + 件数）</h3>
    <p class="desc">柱体=订单量（蓝=取衣，绿=送衣，叠加为合计）；折线=件数。</p>
    <div class="chartbox"><canvas id="${kind}TrendO"></canvas></div>
  </div>
  <div class="panel">
    <h3>${DATA.meta.days}天每日明细</h3>
    <p class="desc">逐日 取衣/送衣 订单与件数（合计=取衣+送衣）。</p>
    <div style="max-height:340px;overflow:auto;"><table id="${kind}Table"></table></div>
  </div>`;
}

function renderStores(){
  const sec=document.getElementById('sec-stores');
  sec.innerHTML = `
    <div class="panel">
      <h3>各门店累计对比</h3>
      <p class="desc">柱体=订单量（蓝=取衣，绿=送衣，堆叠），线=件数。</p>
      <div class="chartbox"><canvas id="storeCmp"></canvas></div>
    </div>
    <div id="storeDetail"></div>`;
  document.getElementById('storeDetail').innerHTML = detailSection('stores', DATA.meta.stores, DATA.overall);
  drawCompare('storeCmp','stores');
  bindDetail('stores', DATA.meta.stores);
}

function renderPartners(){
  const sec=document.getElementById('sec-partners');
  const keys=DATA.meta.partners;
  const ndays=DATA.meta.days;
  const cards = keys.map((k,i)=>{
    const s=DATA.partners[k].summary;
    const bp=DATA.baseline.partners[k];
    const rd=reformDayMetrics(DATA.partners[k]);
    const af=DATA.meta.partner_active_from||{};
    const late = af[k] && af[k] > DATA.meta.reform_date;  // 任职晚于改革日（如梁几斗 9.1 接替）
    const lateNote = late ? `· ${af[k].slice(5).replace('-','/')} 起接替杨龙任职（晚于改革启动，暂无改革前基线）` : '';
    return `<div class="ptn">
      <div class="ptn-hd">
        <span class="ptn-name">${k}${late?' <small style="font-weight:600;color:var(--orange);font-size:12px;">接替杨龙</small>':''}</span>
        <span class="ptn-chip">总单 ${s.total_orders}</span>
        <span class="ptn-chip">总件 ${s.total_pieces}</span>
        <span class="ptn-chip">出勤 ${s.active_days} 天${s.rest_days>0?' · 休'+s.rest_days+' 天':''}</span>
        <span class="ptn-chip">日均 ${s.daily_avg_orders} 单</span>
        <span class="ptn-chip">日均 ${s.daily_avg_pieces} 件</span>
        <span class="ptn-chip">单均 ${s.avg_pieces_per_order} 件/单</span>
      </div>
      <div class="ptn-base">改革前日均单量 <b>${bp.daily_avg_orders}</b> 单/天（出勤${bp.active_days}天） · 改革首日(${reformLabel()}) <b>${rd.to}</b> 单（日环比 ${pctHtml(rd.to, bp.daily_avg_orders)}）；日均件数基线 <b>${bp.daily_avg_pieces}</b> 件 → 首日 <b>${rd.tp}</b> 件（${pctHtml(rd.tp, bp.daily_avg_pieces)}）${lateNote}</div>
      <div class="grid2">
        <div class="panel">
          <h3>订单量逐日趋势</h3>
          <p class="desc">蓝=取衣，绿=送衣。🟧 为改革启动节点。</p>
          <div class="chartbox sm"><canvas id="pO_${i}"></canvas></div>
        </div>
        <div class="panel">
          <h3>件数逐日趋势</h3>
          <p class="desc">蓝=取衣，绿=送衣。🟧 为改革启动节点。</p>
          <div class="chartbox sm"><canvas id="pP_${i}"></canvas></div>
        </div>
      </div>
    </div>`;
  }).join('');
  sec.innerHTML = `
    <div class="panel">
      <h3>${DATA.meta.partners.length}位伙伴累计对比</h3>
      <p class="desc">仅统计现役伙伴 ${DATA.meta.partners.join('、')}（杨龙 2026-09-01 起离职，岗位由梁几斗接替；梁几斗自 9.1 起纳入伙伴统计）。柱体=订单量（蓝=取衣，绿=送衣，堆叠），线=件数。</p>
      <div class="chartbox"><canvas id="partnerCmp"></canvas></div>
    </div>
    <p class="desc" style="margin:10px 2px 4px;">以下为 ${DATA.meta.partners.length} 位伙伴各自逐日趋势（单量 + 件数），直接平铺展示，无需切换：</p>
    <div class="ptn-grid">${cards}</div>`;
  drawCompare('partnerCmp','partners');
  keys.forEach((k,i)=>{
    drawStacked('pO_'+i, DATA.partners[k].daily, 'orders');
    drawStacked('pP_'+i, DATA.partners[k].daily, 'pieces');
  });
}

function pctHtml(cur, base){
  if(base==null || base===0) return '<span class="flat">—</span>';
  const p = (cur-base)/base*100;
  if(Math.abs(p)<0.05) return '<span class="flat">0.0%</span>';
  const cls = p>0?'up':'down';
  const sign = p>0?'+':'';
  return `<span class="${cls}">${sign}${p.toFixed(1)}%</span>`;
}
// 取某实体在首个改革日的单日指标
function reformDayMetrics(ent){
  const i = DATA.meta.reform_index;
  const d = ent.daily;
  const qo=d['取衣_orders'][i], so=d['送衣_orders'][i], to=d['orders'][i];
  const tp=d['pieces'][i];
  const ap = to? (tp/to).toFixed(2):'0.00';
  return {i,qo,so,to,tp,ap};
}

function renderReform(){
  const b = DATA.baseline.overall;
  const preN = DATA.baseline.pre_days;
  const o = DATA.overall;
  const rd = reformDayMetrics(o);
  const rm = reformPeriodAvg();
  const reformDates = DATA.dates.filter(d=> d >= DATA.meta.reform_date);
  // 6位伙伴改革后单日明细：行=伙伴×日期，列=姓名/日期/取衣送衣合计单量/取衣送衣合计件数/单量及件数日环比
  const pks = DATA.meta.partners;
  const afMap = DATA.meta.partner_active_from||{};
  const pRows = pks.map(k=>{
    const ent = DATA.partners[k].daily;
    const bp = DATA.baseline.partners[k];
    const af = afMap[k];  // 任职起始日（如梁几斗 2026-09-01）
    return reformDates.map(d=>{
      if(af && d < af) return '';  // 尚未任职（接替前任前）——不纳入该伙伴明细
      const i = DATA.dates.indexOf(d);
      const qo=ent['取衣_orders'][i], so=ent['送衣_orders'][i], to=ent['orders'][i];
      const qp=ent['取衣_pieces'][i], sp=ent['送衣_pieces'][i], tp=ent['pieces'][i];
      // 当天休息（0 单）：不算人头、不算日环比，合计单量标记「休」
      const rest = to===0;
      return `<tr data-date="${d}"${rest?' style="color:#9aa6b8;"':''}>
        <td class="st">${k}</td>
        <td>${d.slice(5).replace('-','/')}</td>
        <td>${qo}</td><td>${so}</td><td>${rest?'<b>休</b>':`<b>${to}</b>`}</td>
        <td>${qp}</td><td>${sp}</td><td>${rest?'—':`<b>${tp}</b>`}</td>
        <td>${rest?'—':pctHtml(to, bp.daily_avg_orders)}</td>
        <td>${rest?'—':pctHtml(tp, bp.daily_avg_pieces)}</td></tr>`;
    }).join('');
  }).join('');
  const pHead = `<tr><th>姓名</th><th>日期</th><th>取衣单量</th><th>送衣单量</th><th>合计单量</th><th>取衣件数</th><th>送衣件数</th><th>合计件数</th><th>单量日环比</th><th>件数日环比</th></tr>`;
  const sec=document.getElementById('sec-reform');
  sec.innerHTML = `
    <div class="panel">
      <h3>改革前基线 vs 改革后日均（同维度对比）</h3>
      <p class="base-note">上一排为改革前基线（${DATA.baseline.pre_period}，${preN} 天均值固化）；下一排为改革后（${reformLabel()} 起，共 ${rm.days} 天）同维度日均指标，两排逐列对应，可直接对比改革前后变化。</p>
      <div class="rowtag">▶ 改革前基线 <small>${DATA.baseline.pre_period} · ${preN} 天均值</small></div>
      <div class="cards">
        ${kpiCard('日均取衣单量', (b.quyi_orders/preN).toFixed(2),'单/天',preN+'天均值')}
        ${kpiCard('日均送衣单量', (b.songyi_orders/preN).toFixed(2),'单/天',preN+'天均值')}
        ${kpiCard('日均合计单量', b.daily_avg_orders,'单/天',preN+'天均值')}
        ${kpiCard('日均件数', b.daily_avg_pieces,'件/天',preN+'天均值')}
        ${kpiCard('单均件数', b.avg_pieces_per_order,'件/单',preN+'天均值')}
      </div>
      <div class="rowtag after">▼ 改革后日均 <small>${reformLabel()} 起 · ${rm.days} 天</small></div>
      <div class="cards">
        ${kpiCard('日均取衣单量', rm.dqo,'单/天',rm.days+'天均值 · '+reformLabel()+' 起', 'after')}
        ${kpiCard('日均送衣单量', rm.dso,'单/天',rm.days+'天均值 · '+reformLabel()+' 起', 'after')}
        ${kpiCard('日均合计单量', rm.dto,'单/天',rm.days+'天均值 · '+reformLabel()+' 起', 'after')}
        ${kpiCard('日均件数', rm.dtp,'件/天',rm.days+'天均值 · '+reformLabel()+' 起', 'after')}
        ${kpiCard('单均件数', rm.apo,'件/单','总件数 ÷ 总订单', 'after')}
      </div>
    </div>
    <div class="panel">
      <h3>改革前基线 vs 改革后单日</h3>
      <p class="base-note">柱体对比：改革前日均（${preN} 天）与改革后每一天的单量/件数（含最新日），可逐日观察改革效果。注：改革初期数据量尚少，数值偏低属正常，随数据累积对比将更准确。</p>
      <div class="chartbox"><canvas id="reformCmp"></canvas></div>
    </div>
    <div class="panel">
      <h3>改革后单日数据 vs 基线（日环比）</h3>
      <p class="base-note">日环比 = (当日值 − 改革前基线) ÷ 改革前基线。绿色=高于基线，红色=低于基线。</p>
      <div style="overflow:auto;">
      <table class="cmp-tbl">
        <thead><tr>
          <th>日期</th><th>取衣单量</th><th>送衣单量</th><th>合计单量</th>
          <th>件数</th><th>单均件数</th><th>合计单量日环比</th><th>件数日环比</th>
        </tr></thead>
        <tbody>${reformDates.map(d=>{
          const i = DATA.dates.indexOf(d);
          const dd=o.daily;
          const qo=dd['取衣_orders'][i], so=dd['送衣_orders'][i], to=dd['orders'][i];
          const tp=dd['pieces'][i];
          const ap = to? (tp/to).toFixed(2):'0.00';
          return `<tr><td class="st">${d.slice(5).replace('-','/')}</td>
            <td>${qo}</td><td>${so}</td><td><b>${to}</b></td>
            <td>${tp}</td><td>${ap}</td>
            <td>${pctHtml(to, b.daily_avg_orders)}</td>
            <td>${pctHtml(tp, b.daily_avg_pieces)}</td></tr>`;
        }).join('')}</tbody>
      </table></div>
      <details class="pdet" open>
        <summary>${DATA.meta.partners.length}位伙伴 · 改革后单日明细（单量/件数 vs 个人改革前日均，日环比；梁几斗 9.1 起接替杨龙，此前不展示）</summary>
        <div class="pdet-body">
          <div class="datefilter" id="pdetDateFilter">
            <span class="df-lbl">按日期筛选：</span>
          </div>
          <table class="cmp-tbl" id="pdetTable">
            <thead>${pHead}</thead>
            <tbody>${pRows}</tbody>
          </table>
        </div>
      </details>
    </div>`;
  // 对比图：改革前日均 vs 改革后各单日（双轴：单量/件数）。改革后每一天均为独立柱体，随窗口滚动自动增加。
  const cmpDates = reformDates.map(d=>d.slice(5).replace('-','/'));
  const cmpOrders = [b.daily_avg_orders, ...reformDates.map(d=>o.daily['orders'][DATA.dates.indexOf(d)])];
  const cmpPieces = [b.daily_avg_pieces, ...reformDates.map(d=>o.daily['pieces'][DATA.dates.indexOf(d)])];
  if(charts['reformCmp']) charts['reformCmp'].destroy();
  charts['reformCmp']=new Chart(document.getElementById('reformCmp'),{
    type:'bar',
    data:{labels:['改革前日均('+preN+'天)', ...cmpDates],
      datasets:[
        {label:'合计单量(单)',data:cmpOrders,backgroundColor:[C.gray, ...reformDates.map(()=>C.orange)],borderRadius:6,yAxisID:'y',order:2,
          datalabels:{anchor:'end',align:'end',color:'#1f2733',font:{size:11,weight:'700'},formatter:v=>v==null?'':v}},
        {label:'件数(件)',data:cmpPieces,type:'line',borderColor:C.purple,backgroundColor:C.purple,
          tension:.3,borderWidth:2.5,pointRadius:4,yAxisID:'y1',order:1,
          datalabels:{anchor:'end',align:'end',color:C.purple,font:{size:11,weight:'700'},formatter:v=>v==null?'':v}}
      ]},
    options:{maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{labels:{boxWidth:14,font:{size:12}}},datalabels:{display:true}},
      scales:{y:{position:'left',title:{display:true,text:'合计单量(单)'},grid:{color:'#eef1f6'},beginAtZero:true},
              y1:{position:'right',title:{display:true,text:'件数(件)'},grid:{drawOnChartArea:false},beginAtZero:true}}}
  });
  // 6位伙伴改革后单日明细 · 日期筛选按钮
  setupPdetFilter();
}

// 6位伙伴改革后单日明细 日期筛选：全部 / 各改革日（按钮标注当日实际出勤人数，休息伙伴不算人头）
function setupPdetFilter(){
  const wrap = document.getElementById('pdetDateFilter');
  const tbody = document.querySelector('#pdetTable tbody');
  if(!wrap || !tbody) return;
  const filterDates = DATA.dates.filter(d=> d >= DATA.meta.reform_date);
  const pks = DATA.meta.partners;
  const labels = filterDates.map(d=>{
    const i = DATA.dates.indexOf(d);
    const on = pks.filter(k=> DATA.partners[k].daily['orders'][i] > 0).length;
    return d.slice(5).replace('-','/') + '·出勤' + on + '人';
  });
  const btns = ['全部', ...labels];
  wrap.insertAdjacentHTML('beforeend', btns.map((t,i)=>
    `<button type="button" data-i="${i}" class="${i===0?'active':''}">${t}</button>`).join(''));
  const rows = Array.from(tbody.querySelectorAll('tr'));
  wrap.querySelectorAll('button').forEach(b=>{
    b.addEventListener('click', ()=>{
      wrap.querySelectorAll('button').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      const idx = +b.dataset.i;
      const sel = idx===0 ? null : filterDates[idx-1];
      rows.forEach(r=>{
        r.style.display = (sel===null || r.dataset.date===sel) ? '' : 'none';
      });
    });
  });
}

function drawCompare(id, kind){
  if(charts[id]) charts[id].destroy();
  const keys = kind==='stores'?DATA.meta.stores:DATA.meta.partners;
  const sum=a=>a.reduce((x,y)=>x+y,0);
  const qO=keys.map(k=>sum(DATA[kind][k].daily['取衣_orders']));
  const sO=keys.map(k=>sum(DATA[kind][k].daily['送衣_orders']));
  const tP=keys.map(k=>sum(DATA[kind][k].daily['pieces']));
  const ds=[];
  const barDL={anchor:'center',align:'center',color:'#fff',clamp:true,font:{size:10,weight:'700'},formatter:v=>v||''};
  ds.push({type:'bar',label:'取衣订单',data:qO,backgroundColor:C.blue,stack:'o',borderRadius:6,order:3,datalabels:barDL});
  ds.push({type:'bar',label:'送衣订单',data:sO,backgroundColor:C.teal,stack:'o',borderRadius:6,order:3,datalabels:barDL});
  ds.push({type:'line',label:'件数(件)',data:tP,yAxisID:'y1',borderColor:C.purple,backgroundColor:C.purple,
    tension:.3,borderWidth:2.5,pointRadius:4,order:1,
    datalabels:{color:C.purple,font:{size:10,weight:'600'},anchor:'end',align:'end',clamp:true,offset:3}});
  charts[id]=new Chart(document.getElementById(id),{
    data:{labels:keys,datasets:ds},
    options:{maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
      plugins:{legend:{labels:{boxWidth:14,font:{size:12}}},datalabels:{display:true}},
      scales:{y:{position:'left',stacked:true,title:{display:true,text:'订单(单)'},grid:{color:'#eef1f6'},beginAtZero:true},
              y1:{position:'right',title:{display:true,text:'件数(件)'},grid:{drawOnChartArea:false},beginAtZero:true}}}
  });
}

function bindDetail(kind, keys){
  const sel=document.getElementById(kind+'Sel');
  const upd=()=>updateDetail(kind, sel.value);
  sel.addEventListener('change', upd);
  upd();
}

function updateDetail(kind, key){
  const ent=DATA[kind][key];
  const s=ent.summary, d=ent.daily;
  document.getElementById(kind+'Cards').innerHTML = `
    ${kpiCard('总订单', s.total_orders,'单',`取衣 ${s.quyi_orders} · 送衣 ${s.songyi_orders}`)}
    ${kpiCard('总件数', s.total_pieces,'件',`取衣 ${s.quyi_pieces} · 送衣 ${s.songyi_pieces}`)}
    ${kpiCard('日均单量', s.daily_avg_orders,'单/天',DATA.meta.days+'天累计')}
    ${kpiCard('日均件数', s.daily_avg_pieces,'件/天',DATA.meta.days+'天累计')}
    ${kpiCard('单均件数', s.avg_pieces_per_order,'件/单','总件数÷总订单')}
  `;
  drawTrend(kind+'TrendO', d, key);
  // table (ent.daily 存的是按列对齐的数组，用索引取逐日值)
  let rows = DATA.dates.map((dt,i)=>{
    const qo=d['取衣_orders'][i], so=d['送衣_orders'][i], to=d['orders'][i];
    const qp=d['取衣_pieces'][i], sp=d['送衣_pieces'][i], tp=d['pieces'][i];
    return `<tr><td class="st">${dt.slice(5).replace('-','/')}</td>
      <td>${qo}</td><td>${so}</td><td><b>${to}</b></td>
      <td>${qp}</td><td>${sp}</td><td><b>${tp}</b></td></tr>`;
  }).join('');
  document.getElementById(kind+'Table').innerHTML =
    `<thead><tr><th>日期</th><th>取衣订单</th><th>送衣订单</th><th>合计订单</th>
     <th>取衣件数</th><th>送衣件数</th><th>合计件数</th></tr></thead><tbody>${rows}</tbody>`;
}

// tabs
document.getElementById('tabs').addEventListener('click',e=>{
  const b=e.target.closest('button'); if(!b)return;
  const t=b.dataset.tab;
  document.querySelectorAll('#tabs button').forEach(x=>x.classList.toggle('active',x===b));
  document.querySelectorAll('.sec').forEach(s=>s.classList.toggle('active',s.id==='sec-'+t));
  // 图表已随 renderAll 初始化；显示隐藏的标签页时无需重绘（Chart.js ResizeObserver 会自动适配尺寸）
});

function renderAll(){
  renderOverview();
  try{ renderStores(); }catch(e){ console.error('renderStores failed:',e); }
  try{ renderPartners(); }catch(e){ console.error('renderPartners failed:',e); }
  try{ renderReform(); }catch(e){ console.error('renderReform failed:',e); }
  document.getElementById('footnote').innerHTML =
    `📌 口径说明：① 数据来源：国色星洗 SaaS 系统接口（/api/zhcx/deliveryinfo/query，配送信息查询页数据源，取已完成 deliveryStatus=Y），订单日期取「预约时间」，分析窗口为 ${DATA.meta.period}（共 ${DATA.meta.total_rows_in_window} 单；${reformLabel()} 为取送机制改革启动日，纳入以观察改革前后变化）。`+
    `②「改革效果」页将 ${DATA.baseline.pre_period}（${DATA.baseline.pre_days} 天）日均值固化为改革前基线节点（合计日均单量 ${DATA.baseline.overall.daily_avg_orders} 单、日均件数 ${DATA.baseline.overall.daily_avg_pieces} 件），与 ${reformLabel()} 起单日数据做日环比对比；并同排展示改革后（${reformLabel()} 起至最新日）同维度日均指标，改革后日均 = 改革后区间累计单量/件数 ÷ 区间天数。`+
    `③ 门店维度覆盖全部 7 家门店（人南片区）；伙伴维度统计现役 ${DATA.meta.partners.length} 位（${DATA.meta.partners.join('、')}）。杨龙 2026-09-01 起离职，其岗位由梁几斗接替；梁几斗自 9.1 起纳入伙伴统计，其 9 月前的顶班记录不计入伙伴维度。`+
    `④ 伙伴日均单量/日均件数 = 该伙伴累计单量/件数 ÷ 实际出勤天数（当天休息的伙伴不纳入计算：不算天数，出勤天数=窗口内当日有派单记录的天数）；「单均件数」= 总件数 ÷ 总订单。`+
    `⑤ 伙伴改革后单日明细中，当日 0 单的伙伴按「休」处理，不占出勤人头、不参与该日环比；接替前任任职前的日期不展示；日期筛选按钮标注每日实际出勤人数。⑥ 所有订单状态均为「已完成」。⑦ 逐日趋势图上的 🟧 虚线为改革启动节点(${reformLabel()})。`;
  document.title = `人南片区取送情况分析 (${DATA.meta.period.replace('2026-','').replace(' ~ ',' ~ ')})`;
}
renderAll();
</script>
</body>
</html>
"""

HTML = HTML.replace('__DATA__', DATA_JSON)
# 输出文件名按分析窗口动态生成，如 人南片区取送情况分析_8.1-8.12.html
def _mmdd(dt):
    return dt[5:7].lstrip('0') + '.' + dt[8:10].lstrip('0')
_out_name = f"人南片区取送情况分析_{_mmdd(DATA['meta']['period'].split(' ~ ')[0])}-{_mmdd(DATA['meta']['period'].split(' ~ ')[1])}.html"
with open(_out_name, 'w', encoding='utf-8') as f:
    f.write(HTML)
print("HTML written:", _out_name, "size:", len(HTML))
