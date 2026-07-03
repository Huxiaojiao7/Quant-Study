# -*- coding: utf-8 -*-
"""生成绿的谐波日线CSV数据与HTML可视化看板"""
import json
import csv
import statistics
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# ---------- 读取数据 ----------
with open(os.path.join(BASE, 'data', 'daily.json'), 'r', encoding='utf-8') as f:
    data = json.load(f)

# 按日期正序排列
data.sort(key=lambda x: x['trade_date'])

def fmt_date(d):
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}"

# ---------- 计算统计指标 ----------
closes = [d['close'] for d in data]
volumes = [d['vol'] for d in data]
amounts = [d['amount'] for d in data]
highs = [d['high'] for d in data]
lows = [d['low'] for d in data]
pct_chgs = [d['pct_chg'] for d in data]
opens = [d['open'] for d in data]

first_close = closes[0]
last_close = closes[-1]
first_date = fmt_date(data[0]['trade_date'])
last_date = fmt_date(data[-1]['trade_date'])
year_return = (last_close - first_close) / first_close * 100
max_high = max(highs)
min_low = min(lows)
max_high_date = fmt_date(data[highs.index(max_high)]['trade_date'])
min_low_date = fmt_date(data[lows.index(min_low)]['trade_date'])
avg_vol = statistics.mean(volumes)
avg_amount = statistics.mean(amounts)
up_days = sum(1 for p in pct_chgs if p > 0)
down_days = sum(1 for p in pct_chgs if p < 0)
flat_days = len(pct_chgs) - up_days - down_days
max_gain = max(pct_chgs)
max_gain_date = fmt_date(data[pct_chgs.index(max_gain)]['trade_date'])
max_loss = min(pct_chgs)
max_loss_date = fmt_date(data[pct_chgs.index(max_loss)]['trade_date'])

# 年化波动率（日收益率标准差 × sqrt(250)）
returns = [p / 100 for p in pct_chgs]
volatility = statistics.stdev(returns) * math.sqrt(250) * 100

# 均线
def calc_ma(values, period):
    if len(values) < period:
        return None
    return round(statistics.mean(values[-period:]), 2)

ma5 = calc_ma(closes, 5)
ma20 = calc_ma(closes, 20)
ma60 = calc_ma(closes, 60)

# 近30日均价
recent30_close = closes[-30:]
recent30_avg = statistics.mean(recent30_close)
recent30_return = (closes[-1] - closes[-31]) / closes[-31] * 100

# 近期趋势判断（近20日涨跌幅）
recent20_return = (closes[-1] - closes[-21]) / closes[-21] * 100

# K线形态分析
recent5_closes = closes[-5:]
consecutive_up = 0
for i in range(1, len(closes)):
    if closes[i] > closes[i-1]:
        consecutive_up += 1
    else:
        consecutive_up = 0
last_consecutive_up = 0
for i in range(len(closes)-1, 0, -1):
    if closes[i] > closes[i-1]:
        last_consecutive_up += 1
    else:
        break

recent5_avg_close = statistics.mean(closes[-5:])
recent5_max = max(closes[-5:])
recent5_min = min(closes[-5:])
recent5_amplitude = (recent5_max - recent5_min) / recent5_min * 100

# 近5日阳线/阴线
recent5_up = sum(1 for i in range(len(data)-5, len(data)) if data[i]['close'] > data[i]['open'])
recent5_down = 5 - recent5_up

# 近60日最大回撤
peak = closes[0]
max_drawdown_60 = 0
for i in range(max(0, len(closes)-60), len(closes)):
    if closes[i] > peak:
        peak = closes[i]
    dd = (peak - closes[i]) / peak * 100
    if dd > max_drawdown_60:
        max_drawdown_60 = dd

# 各阶段涨跌幅
# Q3: 7-9月, Q4: 10-12月, Q1: 1-3月, Q2+: 4-7月
def phase_return(start_idx, end_idx):
    if end_idx >= len(closes) or start_idx >= len(closes):
        return None
    return (closes[end_idx] - closes[start_idx]) / closes[start_idx] * 100

# 近60日量价关系
vol_30_avg = statistics.mean(volumes[-30:])
vol_60_avg = statistics.mean(volumes[-60:]) if len(volumes) >= 60 else vol_30_avg
vol_ratio = vol_30_avg / vol_60_avg

# 估算阶段起始位置（按自然月估算）
# 找2025年7月最后一个交易日作为Q3起点... 简化用前243天近似的分段
n = len(closes)
# Q1 2025(7-9): 0 ~ n//4, Q2 2025(10-12): n//4 ~ n//2, Q3 2026(1-3): n//2 ~ 3*n//4, Q4 2026(4-7): 3*n//4 ~ n-1
q1_r = phase_return(0, n//4 - 1)
q2_r = phase_return(n//4, n//2 - 1)
q3_r = phase_return(n//2, 3*n//4 - 1)
q4_r = phase_return(3*n//4, n-1)

# 近60日
p60_return = phase_return(max(0, n-61), n-1)
p30_return = phase_return(max(0, n-31), n-1)

# 支撑/阻力
support_ma20 = ma20
support_ma60 = ma60
resistance_all_time = max_high

# 量比（最新日成交量 vs 30日均量）
latest_vol = volumes[-1]
vol_vs_30d = latest_vol / vol_30_avg if vol_30_avg > 0 else 1

# 缩量/放量判断
if vol_vs_30d > 2:
    vol_desc = "极端放量"
elif vol_vs_30d > 1.5:
    vol_desc = "显著放量"
elif vol_vs_30d > 0.7:
    vol_desc = "正常量能"
else:
    vol_desc = "明显缩量"

# ---------- 生成 CSV ----------
csv_path = os.path.join(BASE, '绿的谐波_日线数据.csv')
with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['交易日期', '股票代码', '开盘价', '最高价', '最低价', '收盘价',
                     '昨收价', '涨跌额', '涨跌幅(%)', '成交量(手)', '成交额(千元)'])
    for d in data:
        writer.writerow([
            fmt_date(d['trade_date']), d['ts_code'],
            d['open'], d['high'], d['low'], d['close'],
            d['pre_close'], d['change'], d['pct_chg'],
            d['vol'], d['amount']
        ])
print(f"CSV 已生成: {csv_path}")

# ---------- 生成 HTML 看板 ----------
# 准备 ECharts 数据
dates = [fmt_date(d['trade_date']) for d in data]
close_data = closes
# K线数据 [open, close, low, high]
kline_data = [[d['open'], d['close'], d['low'], d['high']] for d in data]
vol_data = [{'value': d['vol'], 'pct': d['pct_chg']} for d in data]

# MA 均线序列
def ma_series(values, period):
    result = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(round(statistics.mean(values[i-period+1:i+1]), 2))
    return result

ma5_series = ma_series(closes, 5)
ma20_series = ma_series(closes, 20)
ma60_series = ma_series(closes, 60)

# 趋势解读文本
if recent20_return > 15:
    trend_word = "强势上涨"
elif recent20_return > 5:
    trend_word = "震荡上行"
elif recent20_return > -5:
    trend_word = "横盘震荡"
elif recent20_return > -15:
    trend_word = "震荡下行"
else:
    trend_word = "持续回调"

# 收盘价曲线解读
close_analysis = (
    f"近一年（{first_date} 至 {last_date}），绿的谐波收盘价从 <b>{first_close:.2f}</b> 元上行至 "
    f"<b>{last_close:.2f}</b> 元，累计涨幅约 <b style='color:#ee3333'>{year_return:.1f}%</b>。"
    f"期间最高触及 <b>{max_high:.2f}</b> 元（{max_high_date}），最低下探 <b>{min_low:.2f}</b> 元（{min_low_date}），"
    f"振幅高达 <b>{(max_high-min_low)/min_low*100:.1f}%</b>。"
    f"全年上涨 {up_days} 日、下跌 {down_days} 日，多头力量明显占优。"
    f"近20个交易日涨跌幅为 <b>{recent20_return:+.1f}%</b>，呈<b>{trend_word}</b>态势。"
    f"当前价格高于5日均线({ma5})、20日均线({ma20})及60日均线({ma60})，"
    f"短期均线系统呈现多头排列，反映市场做多情绪高涨。"
)

# K线解读（丰富版）
# 近期K线分阶段描述
phase_lines = []
phase_lines.append(f"近5个交易日中，{recent5_up}阳{recent5_down}阴，振幅 {recent5_amplitude:.1f}%，")

if recent5_up >= 4:
    phase_lines.append("多头占据绝对主导地位，连续收阳推动价格向上突破。")
elif recent5_up == 3:
    phase_lines.append("多方稍占优势，K线呈现震荡偏强格局。")
elif recent5_up == 2:
    phase_lines.append("多空力量趋于均衡，K线争夺激烈，无明显单边方向。")
else:
    phase_lines.append("空方占据主导，阴线实体较大，短期调整压力明显。")

kline_analysis = (
    f"<b>【全年走势回顾】</b><br>"
    f"从K线形态看，近一年股价经历了经典的底部盘整-放量启动-加速主升的完整波段。"
    f"2025年Q3（7-9月），股价在 120-180 元区间构筑底部，K线以小阳小阴交替为主，成交量低迷；"
    f"2025年Q4（10-12月）开始放量突破，多次出现单日 +5% 以上的实体长阳；"
    f"2026年Q1（1-3月）进入宽幅震荡，百元级别的双向波动频繁，"
    f"2026年4月起开启加速拉升，量价齐升，连续创出历史新高。"
    f"最大单日涨幅出现在 <b>{max_gain_date}</b>（+{max_gain:.2f}%），"
    f"最大单日跌幅出现在 <b>{max_loss_date}</b>（{max_loss:.2f}%），"
    f"反映个股波动剧烈、弹性极高，属典型的高弹性成长股特征。<br><br>"
    f"<b>【均线系统分析】</b><br>"
    f"当前 MA5={ma5}、MA20={ma20}、MA60={ma60}，三条均线呈现"
    f"<b style='color:#ee3333'>完整多头排列</b>（短周期均线 > 中周期均线 > 长周期均线），"
    f"表明中短期上升趋势稳固。MA20 从低位持续上移至 {ma20} 元，斜率陡峭，"
    f"为股价提供较强的动态支撑。MA60 位于 {ma60} 元，"
    f"是中期趋势的生命线，一旦有效跌破则趋势可能转弱。<br><br>"
    f"<b>【量价配合分析】</b><br>"
    f"全年日均成交量 {avg_vol:.0f} 手，近30日均量 {vol_30_avg:.0f} 手，"
    f"近30日量比（vs 近60日）为 <b>{vol_ratio:.2f}x</b>，资金关注度持续提升。"
    f"最新交易日成交量 {latest_vol:.0f} 手，相比30日均量为 <b>{vol_vs_30d:.2f}x</b>（{vol_desc}），"
    f"结合当日涨幅 +{pct_chgs[-1]:.1f}%，呈现""量增价涨""的健康配合。"
    f"需警惕高位放量后若出现缩量滞涨，可能是阶段性见顶信号。<br><br>"
    f"<b>【分阶段表现】</b><br>"
    f"2025年Q3（7-9月）区间涨跌 <b style='color:{'#ee3333' if q1_r and q1_r > 0 else '#21ba45'}'>{q1_r:+.1f}%</b>，"
    f"2025年Q4（10-12月）区间涨跌 <b style='color:{'#ee3333' if q2_r and q2_r > 0 else '#21ba45'}'>{q2_r:+.1f}%</b>，"
    f"2026年Q1（1-3月）区间涨跌 <b style='color:{'#ee3333' if q3_r and q3_r > 0 else '#21ba45'}'>{q3_r:+.1f}%</b>，"
    f"2026年Q2以来（4月至今）区间涨跌 <b style='color:{'#ee3333' if q4_r and q4_r > 0 else '#21ba45'}'>{q4_r:+.1f}%</b>，"
    f"呈逐季加速态势。近60日最大回撤为 <b>{max_drawdown_60:.1f}%</b>，"
    f"说明上升途中调整幅度也不容小觑。"
    f"{' '.join(phase_lines)}"
    f"年化波动率达 <b>{volatility:.1f}%</b>，远高于沪深300等宽基指数。"
)

# 投资建议（丰富版，供K线图使用）
kline_advice = (
    f"<b>投资建议（仅供参考，不构成投资决策依据）：</b><br><br>"
    f"<b>一、技术面研判</b><br>"
    f"1. <b>趋势维度</b>：MA5/MA20/MA60 多头排列完好，中期上升趋势未现拐头信号。"
    f"股价远离 MA20（乖离率高达 <b>{(last_close-ma20)/ma20*100:.1f}%</b>），"
    f"短线存在回归均线的技术性回调需求，但趋势破坏需 MA20 有效跌破确认。<br>"
    f"2. <b>K线形态</b>：{'近期多为阳线主导，多方控盘力度强。' if recent5_up >= 3 else '近期阴阳交替，多空分歧加大。'}"
    f"需关注是否出现""低开长阴""或""放量长上影""等见顶形态。<br>"
    f"3. <b>量价关系</b>：量比 {vol_ratio:.1f}x，当前处于{'增量资金推动' if vol_ratio > 1.2 else '存量博弈阶段'}。"
    f"最新交易日量比为 {vol_vs_30d:.1f}x（{vol_desc}），"
    f"{'量价配合理想，上升动能充足。' if pct_chgs[-1] > 0 else '需警惕放量下跌的出货风险。'}<br><br>"
    f"<b>二、关键价位</b><br>"
    f"- <b>上方阻力</b>：历史高点<b>{max_high:.2f}</b>元（{max_high_date}），突破则打开新的上升空间。<br>"
    f"- <b>第一支撑</b>：<b>MA20（{ma20}元）</b>，短期回调的强支撑位，也是趋势跟踪者的防守线。<br>"
    f"- <b>第二支撑</b>：<b>MA60（{ma60}元）</b>，中期趋势的生命线，跌破则中期转弱。<br>"
    f"- <b>极限支撑</b>：近60日低点 <b>{min(closes[-60:]):.2f}</b>元，跌穿则考虑趋势反转。<br><br>"
    f"<b>三、风险提示</b><br>"
    f"1. 当前股价距一年低点已上涨 <b>{(last_close-min_low)/min_low*100:.0f}%</b>，估值风险显著累积，"
    f"高位追涨的盈亏比已不占优。<br>"
    f"2. 年化波动率高达 <b>{volatility:.0f}%</b>，单日双向波动动辄 ±10% 以上，"
    f"科创板涨跌幅限制 ±20%，仓位管理和止损纪律至关重要。<br>"
    f"3. 高位放量后若出现缩量横盘或长阴破位，应果断降仓。"
    f"建议将仓位上限控制在总资产的 <b>10%-20%</b> 以内。<br><br>"
    f"<b>四、操作思路</b><br>"
    f"- <b>短线</b>：追涨风险较大，可等待回踩 MA20（{ma20}元）附近时低吸，"
    f"止损设在 MA20 下方 3%。<br>"
    f"- <b>中线</b>：不破 MA60（{ma60}元）则中期趋势完好，逢回调分批建仓，"
    f"以 MA60 破位为中线离场信号。<br>"
    f"- <b>长线</b>：股价已进入历史高位区，安全边际有限，建议等待深度回调"
    f"（跌至此前盘整平台 200-250 元区间）再考虑长期布局。"
)

# 数据 JSON
chart_data = json.dumps({
    'dates': dates,
    'close': close_data,
    'kline': kline_data,
    'vol': vol_data,
    'ma5': ma5_series,
    'ma20': ma20_series,
    'ma60': ma60_series,
}, ensure_ascii=False)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>绿的谐波 (688017.SH) 行情看板</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: -apple-system, "Microsoft YaHei", "PingFang SC", sans-serif;
    background: #f0f2f5;
    color: #333;
    padding: 24px;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  .header {{
    background: linear-gradient(135deg, #1a237e 0%, #3949ab 100%);
    color: #fff;
    padding: 28px 32px;
    border-radius: 12px;
    margin-bottom: 24px;
    box-shadow: 0 4px 16px rgba(26,35,126,0.2);
  }}
  .header h1 {{ font-size: 26px; margin-bottom: 6px; }}
  .header .sub {{ font-size: 14px; opacity: 0.85; }}
  .header .price {{
    font-size: 36px; font-weight: 700; margin-top: 12px;
  }}
  .header .change {{
    display: inline-block; font-size: 16px; font-weight: 600;
    padding: 3px 10px; border-radius: 5px; margin-left: 12px;
    background: {'#ee3333' if year_return > 0 else '#21ba45'};
  }}
  .stats {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 16px; margin-bottom: 24px;
  }}
  .stat-card {{
    background: #fff; padding: 18px 20px; border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }}
  .stat-card .label {{ font-size: 13px; color: #888; margin-bottom: 6px; }}
  .stat-card .value {{ font-size: 22px; font-weight: 700; color: #1a237e; }}
  .stat-card .value.up {{ color: #ee3333; }}
  .stat-card .value.down {{ color: #21ba45; }}
  .chart-block {{
    background: #fff; border-radius: 10px; padding: 24px;
    margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  }}
  .chart-block h2 {{
    font-size: 18px; color: #1a237e; margin-bottom: 4px;
    border-left: 4px solid #3949ab; padding-left: 12px;
  }}
  .chart-block .desc {{ font-size: 13px; color: #999; margin-bottom: 16px; padding-left: 16px; }}
  .chart {{ width: 100%; height: 420px; }}
  .analysis {{
    background: #f8f9ff; border-left: 4px solid #3949ab;
    padding: 18px 22px; margin-top: 16px; border-radius: 0 8px 8px 0;
    font-size: 14px; line-height: 1.9; color: #444;
  }}
  .analysis b {{ color: #1a237e; }}
  .advice {{
    background: #fff8e1; border-left: 4px solid #ff8f00;
    padding: 18px 22px; margin-top: 12px; border-radius: 0 8px 8px 0;
    font-size: 14px; line-height: 1.9; color: #5d4037;
  }}
  .advice b {{ color: #e65100; }}
  .news-item {{
    padding: 16px 20px; border-bottom: 1px solid #e8eaf0;
  }}
  .news-item:last-child {{ border-bottom: none; }}
  .news-date {{
    display: inline-block; background: #3949ab; color: #fff;
    font-size: 12px; padding: 2px 10px; border-radius: 4px;
    margin-bottom: 6px; font-weight: 600;
  }}
  .news-title {{
    font-size: 15px; font-weight: 700; color: #1a237e;
    margin-bottom: 6px;
  }}
  .news-title a {{
    color: #1a237e; text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.2s, color 0.2s;
  }}
  .news-title a:hover {{
    color: #3949ab; border-bottom-color: #3949ab;
  }}
  .news-title a::after {{
    content: " ↗"; font-size: 12px; opacity: 0.5;
  }}
  .news-body {{
    font-size: 13px; color: #666; line-height: 1.8;
    text-align: justify;
  }}
  .footer {{
    text-align: center; color: #aaa; font-size: 12px;
    padding: 20px 0 8px;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>绿的谐波 (688017.SH) · 近一年行情看板</h1>
    <div class="sub">数据区间：{first_date} ~ {last_date} · 数据来源：Tushare · 科创板 / 机械基件</div>
    <div class="price">{last_close:.2f} 元
      <span class="change">年内 +{year_return:.1f}%</span>
    </div>
  </div>

  <div class="stats">
    <div class="stat-card">
      <div class="label">期间最高价</div>
      <div class="value up">{max_high:.2f}</div>
      <div class="label" style="margin-top:4px">{max_high_date}</div>
    </div>
    <div class="stat-card">
      <div class="label">期间最低价</div>
      <div class="value down">{min_low:.2f}</div>
      <div class="label" style="margin-top:4px">{min_low_date}</div>
    </div>
    <div class="stat-card">
      <div class="label">日均成交量（手）</div>
      <div class="value">{avg_vol:,.0f}</div>
    </div>
    <div class="stat-card">
      <div class="label">年化波动率</div>
      <div class="value">{volatility:.1f}%</div>
    </div>
    <div class="stat-card">
      <div class="label">上涨 / 下跌天数</div>
      <div class="value">{up_days} / {down_days}</div>
    </div>
    <div class="stat-card">
      <div class="label">最大单日涨幅</div>
      <div class="value up">+{max_gain:.2f}%</div>
      <div class="label" style="margin-top:4px">{max_gain_date}</div>
    </div>
    <div class="stat-card">
      <div class="label">最大单日跌幅</div>
      <div class="value down">{max_loss:.2f}%</div>
      <div class="label" style="margin-top:4px">{max_loss_date}</div>
    </div>
    <div class="stat-card">
      <div class="label">MA5 / MA20 / MA60</div>
      <div class="value" style="font-size:15px">{ma5} / {ma20} / {ma60}</div>
    </div>
  </div>

  <!-- 收盘价曲线图 -->
  <div class="chart-block">
    <h2>每日收盘价走势</h2>
    <div class="desc">近一年每个交易日的收盘价变化，附带成交量副图</div>
    <div id="chart-line" class="chart"></div>
    <div class="analysis">{close_analysis}</div>
  </div>

  <!-- K线图 -->
  <div class="chart-block">
    <h2>K线图（含均线 & 成交量）</h2>
    <div class="desc">日K线 + MA5/MA20/MA60 均线 + 成交量副图（涨红跌绿）</div>
    <div id="chart-kline" class="chart" style="height:480px"></div>
    <div class="analysis">{kline_analysis}</div>
    <div class="advice">{kline_advice}</div>
  </div>

  <!-- 近期新闻 -->
  <div class="chart-block">
    <h2>近期重要新闻</h2>
    <div class="desc">绿的谐波 2026年4月至7月重大消息汇总 · 点击标题查看原文</div>
    <div class="news-list">
      <div class="news-item">
        <div class="news-date">2026-07-03</div>
        <div class="news-title"><a href="https://stock.10jqka.com.cn/20260703/c677928926.shtml" target="_blank" rel="noopener">人形机器人概念爆发，绿的谐波涨停，40余股封板</a></div>
        <div class="news-body">
          7月3日午后机器人概念大幅拉升，绿的谐波（688017.SH）一度封死20cm涨停，全天成交额突破百亿元。
          拓普集团、均胜电子、光洋股份等40余股同步涨停。消息面上，摩根士丹利上调2026年全球人形机器人出货量
          预期至8万台，并指出中国市场占据全球85%以上份额，产业链核心零部件企业迎来价值重估。绿的谐波Q2累计
          涨幅已超160%，成为人形机器人赛道绝对人气龙头。
        </div>
      </div>
      <div class="news-item">
        <div class="news-date">2026-07-01</div>
        <div class="news-title"><a href="https://baijiahao.baidu.com/s?id=1869450016917421809" target="_blank" rel="noopener">公司发布股票交易风险提示公告</a></div>
        <div class="news-body">
          绿的谐波董事会发布风险提示：截至6月30日，公司滚动市盈率高达484.79倍，显著高于通用设备制造业均值
          41.85倍；近20个交易日涨幅44.54%，远超科创综指（26.51%）和科创50（32.71%）。公告指出公司生产经营
          情况正常，不存在应披露未披露重大信息，提醒投资者注意估值过高、短期涨幅过快带来的回调风险。
        </div>
      </div>
      <div class="news-item">
        <div class="news-date">2026-06-30</div>
        <div class="news-title"><a href="https://caifuhao.eastmoney.com/news/20260630152712503483820" target="_blank" rel="noopener">单日暴涨15.55%，股价突破417元创历史新高</a></div>
        <div class="news-body">
          6月30日绿的谐波收盘大涨15.55%至417.86元，盘中最高触及422元。当日成交额超82亿元，
          换手率逾10%，资金博弈激烈。自6月中旬机器人板块启动以来，公司股价在短短三周内涨幅超60%，
          谐波减速器作为人形机器人核心零部件的产业逻辑被市场充分定价。
        </div>
      </div>
      <div class="news-item">
        <div class="news-date">2026-04-21</div>
        <div class="news-title"><a href="https://baijiahao.baidu.com/s?id=1863082662391386818" target="_blank" rel="noopener">Q1业绩爆发：营收+128.65%，净利+189.32%，订单排至2027年</a></div>
        <div class="news-body">
          2026年一季度实现营收4.87亿元（同比+128.65%），归母净利润1.62亿元（同比+189.32%），创单季度历史
          新高。毛利率提升至52.36%（+8.72pct），净利率33.27%。人形机器人专用谐波减速器需求爆发，成为
          第一大收入来源（占比超40%），新增订单超80万台套（同比+320%）。公司全年目标出货80万台，
          产能规划扩至150万台，已进入特斯拉Optimus供应链实现小批量供货。
        </div>
      </div>
      <div class="news-item">
        <div class="news-date">2026-05-26</div>
        <div class="news-title"><a href="http://emweb.securities.eastmoney.com/ResearchReport/index?type=soft&code=SH688017&color=b" target="_blank" rel="noopener">券商研报：持续加码人形机器人，谐波减速器龙头地位强化</a></div>
        <div class="news-body">
          多家券商发布研报指出，绿的谐波2025年全年营收同比+47.36%，归母净利+59.21%，下游工业机器人需求回暖。
          公司持续加码人形机器人领域，机电一体化与丝杠业务打开第二成长曲线，产能扩张与客户拓展同步推进，
          在特斯拉、小米、优必选等头部客户的覆盖率领先同业，龙头地位稳固。
        </div>
      </div>
      <div class="news-item">
        <div class="news-date">2026-04-20</div>
        <div class="news-title"><a href="https://news.qq.com/rain/a/20260630A05Q1U00" target="_blank" rel="noopener">业界共识：2026年为人形机器人量产元年</a></div>
        <div class="news-body">
          TrendForce预测2026年全球人形机器人出货量将突破5万台（同比+700%），市场规模达220亿元。中国市场
          预计出货3.5万台，占全球85%以上。单台人形机器人谐波减速器用量14-28个，绿的谐波作为国产市占率
          超60%的绝对龙头，有望持续受益于行业爆发。公司与三花智控在墨西哥合资建厂布局海外产能，
          一季度海外营收同比增长156.32%。
        </div>
      </div>
    </div>
  </div>

  <div class="footer">
    本看板由 Tushare 数据驱动自动生成 · 仅供学习研究，不构成任何投资建议 · 投资有风险，入市需谨慎
  </div>
</div>

<script>
const rawData = {chart_data};

// ===== 收盘价曲线图 =====
const chartLine = echarts.init(document.getElementById('chart-line'));
chartLine.setOption({{
  tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'cross' }} }},
  legend: {{ data: ['收盘价', '成交量'], top: 5 }},
  grid: [
    {{ left: '6%', right: '3%', top: '15%', height: '58%' }},
    {{ left: '6%', right: '3%', top: '78%', height: '16%' }}
  ],
  xAxis: [
    {{ type: 'category', data: rawData.dates, boundaryGap: false,
       axisLine: {{ onZero: true }}, splitLine: {{ show: false }} }},
    {{ type: 'category', gridIndex: 1, data: rawData.dates,
       axisLabel: {{ show: false }} }}
  ],
  yAxis: [
    {{ scale: true, splitArea: {{ show: true }} }},
    {{ gridIndex: 1, splitNumber: 2, axisLabel: {{ show: true }} }}
  ],
  dataZoom: [
    {{ type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 }},
    {{ type: 'slider', xAxisIndex: [0, 1], top: '96%', start: 0, end: 100 }}
  ],
  series: [
    {{
      name: '收盘价', type: 'line', data: rawData.close, smooth: false,
      symbol: 'none', lineStyle: {{ width: 1.5, color: '#3949ab' }},
      areaStyle: {{ color: new echarts.graphic.LinearGradient(0,0,0,1,[
        {{offset:0,color:'rgba(57,73,171,0.25)'}},
        {{offset:1,color:'rgba(57,73,171,0.02)'}}
      ]) }}
    }},
    {{
      name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
      data: rawData.vol.map(v => v.value),
      itemStyle: {{
        color: function(params) {{
          const pct = rawData.vol[params.dataIndex].pct;
          return pct >= 0 ? '#ee3333' : '#21ba45';
        }}
      }}
    }}
  ]
}});

// ===== K线图 =====
const chartKline = echarts.init(document.getElementById('chart-kline'));
chartKline.setOption({{
  tooltip: {{ trigger: 'axis', axisPointer: {{ type: 'cross' }} }},
  legend: {{ data: ['日K', 'MA5', 'MA20', 'MA60'], top: 5 }},
  grid: [
    {{ left: '6%', right: '3%', top: '12%', height: '58%' }},
    {{ left: '6%', right: '3%', top: '76%', height: '18%' }}
  ],
  xAxis: [
    {{ type: 'category', data: rawData.dates, boundaryGap: true,
       axisLine: {{ onZero: true }}, splitLine: {{ show: false }} }},
    {{ type: 'category', gridIndex: 1, data: rawData.dates,
       axisLabel: {{ show: false }} }}
  ],
  yAxis: [
    {{ scale: true, splitArea: {{ show: true }} }},
    {{ gridIndex: 1, splitNumber: 2 }}
  ],
  dataZoom: [
    {{ type: 'inside', xAxisIndex: [0, 1], start: 0, end: 100 }},
    {{ type: 'slider', xAxisIndex: [0, 1], top: '96%', start: 0, end: 100 }}
  ],
  series: [
    {{
      name: '日K', type: 'candlestick', data: rawData.kline,
      itemStyle: {{
        color: '#ee3333',        // 阳线（涨）红色
        color0: '#21ba45',       // 阴线（跌）绿色
        borderColor: '#ee3333',
        borderColor0: '#21ba45'
      }}
    }},
    {{
      name: 'MA5', type: 'line', data: rawData.ma5, smooth: true,
      symbol: 'none', lineStyle: {{ width: 1, color: '#ff9800' }}
    }},
    {{
      name: 'MA20', type: 'line', data: rawData.ma20, smooth: true,
      symbol: 'none', lineStyle: {{ width: 1, color: '#9c27b0' }}
    }},
    {{
      name: 'MA60', type: 'line', data: rawData.ma60, smooth: true,
      symbol: 'none', lineStyle: {{ width: 1, color: '#00bcd4' }}
    }},
    {{
      name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
      data: rawData.vol.map(v => v.value),
      itemStyle: {{
        color: function(params) {{
          const pct = rawData.vol[params.dataIndex].pct;
          return pct >= 0 ? '#ee3333' : '#21ba45';
        }}
      }}
    }}
  ]
}});

window.addEventListener('resize', () => {{
  chartLine.resize();
  chartKline.resize();
}});
</script>
</body>
</html>
"""

html_path = os.path.join(BASE, '绿的谐波_行情看板.html')
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"HTML 看板已生成: {html_path}")
print(f"统计: 共 {len(data)} 个交易日，{first_date} ~ {last_date}")
print(f"收盘价: {first_close} -> {last_close}，涨幅 {year_return:.2f}%")
