#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成 绿的谐波 技术指标分析 Jupyter Notebook
"""

import json
import os
import sys

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 非交互后端，适合脚本生成
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
import mplfinance as mpf
import nbformat as nbf

# ============================================================
# 0. 中文字体检测与设置
# ============================================================
def setup_chinese_font():
    """自动检测系统中文字体，并返回 (font_name, rc_params)"""
    from matplotlib.font_manager import fontManager
    candidates = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong', 'STSong']
    available = {f.name for f in fontManager.ttflist}
    for c in candidates:
        if c in available:
            rc = {
                'font.family': 'sans-serif',
                'font.sans-serif': [c, 'DejaVu Sans'],
                'axes.unicode_minus': False,
            }
            plt.rcParams.update(rc)
            return c, rc
    # fallback
    rc = {
        'font.family': 'sans-serif',
        'font.sans-serif': ['DejaVu Sans'],
        'axes.unicode_minus': False,
    }
    plt.rcParams.update(rc)
    return None, rc

FONT_NAME, FONT_RC = setup_chinese_font()
print(f"[INFO] 中文字体: {FONT_NAME}")

# ============================================================
# 1. 数据加载
# ============================================================
CSV_PATH = r'C:\Users\27924\Desktop\QuantStudy\Task1\绿的谐波_日线数据.csv'
OUTPUT_DIR = r'C:\Users\27924\Desktop\QuantStudy\Task2\outputs'
os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(CSV_PATH)
df.rename(columns={
    '交易日期': 'date',
    '开盘价': 'open',
    '最高价': 'high',
    '最低价': 'low',
    '收盘价': 'close',
    '成交量(手)': 'volume',
    '成交额(千元)': 'amount'
}, inplace=True)
df['date'] = pd.to_datetime(df['date'])
df.sort_values('date', inplace=True)
df.reset_index(drop=True, inplace=True)

DATE_MIN = df['date'].min().strftime('%Y-%m-%d')
DATE_MAX = df['date'].max().strftime('%Y-%m-%d')
ROW_COUNT = len(df)

print(f"[INFO] 数据加载完成: {ROW_COUNT} 行, {DATE_MIN} ~ {DATE_MAX}")

# ============================================================
# 2. 指标计算
# ============================================================

# --- RSI ---
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

df['rsi_6'] = compute_rsi(df['close'], 6)
df['rsi_14'] = compute_rsi(df['close'], 14)
df['rsi_24'] = compute_rsi(df['close'], 24)

# --- MACD ---
def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    hist = dif - dea  # 不乘2
    return dif, dea, hist

df['dif'], df['dea'], df['macd_hist'] = compute_macd(df['close'])

# --- 布林带 ---
def compute_bollinger(series, period=20, k=2):
    mid = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = mid + k * std
    lower = mid - k * std
    bandwidth = (upper - lower) / mid * 100
    pct_b = (series - lower) / (upper - lower)
    return upper, mid, lower, bandwidth, pct_b

df['bb_upper'], df['bb_mid'], df['bb_lower'], df['bb_bandwidth'], df['bb_pct_b'] = \
    compute_bollinger(df['close'])

# --- ATR ---
def compute_atr(df, period=14):
    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

df['atr'] = compute_atr(df, 14)

# 日收益率
df['return'] = df['close'].pct_change() * 100

print("[INFO] 指标计算完成")

# ============================================================
# 3. 可视化生成
# ============================================================

# 选取最近 200 个交易日做可视化聚焦（数据量大时更清晰）
DISPLAY_N = min(200, ROW_COUNT)
df_disp = df.tail(DISPLAY_N).copy()

# 图表配色
RED = '#DC143C'
GREEN = '#228B22'
BLUE = '#1f77b4'
ORANGE = '#ff7f0e'
PURPLE = '#9467bd'

# ---- Fig 1: K线 + 布林带 + 成交量 ----
print("[INFO] 生成 Fig 1: K线 + 布林带...")
fig1_df = df_disp.set_index('date')
mc = mpf.make_marketcolors(
    up=RED, down=GREEN,
    edge='inherit', wick='inherit',
    volume='inherit'
)
s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False, rc=FONT_RC)

apds = [
    mpf.make_addplot(fig1_df['bb_upper'], color='gray', linestyle='--', width=0.8, label='上轨'),
    mpf.make_addplot(fig1_df['bb_mid'], color=BLUE, width=1.2, label='中轨'),
    mpf.make_addplot(fig1_df['bb_lower'], color='gray', linestyle='--', width=0.8, label='下轨'),
]

fig1, axes = mpf.plot(
    fig1_df,
    type='candle',
    style=s,
    addplot=apds,
    volume=True,
    title='\n绿的谐波 (688017.SH) — K线 + 布林带 (20,2)',
    ylabel='价格 (元)',
    ylabel_lower='成交量 (手)',
    figsize=(16, 9),
    returnfig=True,
    warn_too_much_data=10000,
)

axes[0].legend(loc='upper left', fontsize=9)

fig1.savefig(os.path.join(OUTPUT_DIR, 'kline_bollinger.png'), dpi=150, bbox_inches='tight')
plt.close(fig1)

# ---- Fig 2: RSI 三线 ----
print("[INFO] 生成 Fig 2: RSI...")
fig2, ax_rsi = plt.subplots(figsize=(16, 5))
ax_rsi.plot(df_disp['date'], df_disp['rsi_6'], color=ORANGE, linewidth=1, label='RSI-6')
ax_rsi.plot(df_disp['date'], df_disp['rsi_14'], color=BLUE, linewidth=1.2, label='RSI-14')
ax_rsi.plot(df_disp['date'], df_disp['rsi_24'], color=PURPLE, linewidth=1, label='RSI-24')
ax_rsi.axhline(y=70, color=RED, linestyle='--', alpha=0.5, linewidth=0.8)
ax_rsi.axhline(y=30, color=GREEN, linestyle='--', alpha=0.5, linewidth=0.8)
ax_rsi.axhline(y=50, color='gray', linestyle=':', alpha=0.4, linewidth=0.6)
ax_rsi.fill_between(df_disp['date'], 70, 100, alpha=0.08, color=RED)
ax_rsi.fill_between(df_disp['date'], 0, 30, alpha=0.08, color=GREEN)
ax_rsi.set_ylim(0, 100)
ax_rsi.set_ylabel('RSI')
ax_rsi.set_title('绿的谐波 (688017.SH) — RSI (6 / 14 / 24)', fontsize=13, fontweight='bold')
ax_rsi.legend(loc='upper left', fontsize=9)
ax_rsi.grid(True, alpha=0.3)
fig2.tight_layout()
fig2.savefig(os.path.join(OUTPUT_DIR, 'rsi.png'), dpi=150, bbox_inches='tight')
plt.close(fig2)

# ---- Fig 3: MACD ----
print("[INFO] 生成 Fig 3: MACD...")
fig3, ax_macd = plt.subplots(figsize=(16, 5))
colors_hist = [RED if v >= 0 else GREEN for v in df_disp['macd_hist'].values]
ax_macd.bar(df_disp['date'], df_disp['macd_hist'], color=colors_hist, width=0.8, alpha=0.6)
ax_macd.plot(df_disp['date'], df_disp['dif'], color=BLUE, linewidth=1.2, label='DIF')
ax_macd.plot(df_disp['date'], df_disp['dea'], color=ORANGE, linewidth=1, label='DEA')
ax_macd.axhline(y=0, color='gray', linestyle='-', linewidth=0.6)
ax_macd.set_ylabel('MACD')
ax_macd.set_title('绿的谐波 (688017.SH) — MACD (12, 26, 9)', fontsize=13, fontweight='bold')
ax_macd.legend(loc='upper left', fontsize=9)
ax_macd.grid(True, alpha=0.3)
fig3.tight_layout()
fig3.savefig(os.path.join(OUTPUT_DIR, 'macd.png'), dpi=150, bbox_inches='tight')
plt.close(fig3)

# ---- Fig 4: ATR ----
print("[INFO] 生成 Fig 4: ATR...")
fig4, ax_atr = plt.subplots(figsize=(16, 5))
ax_atr.fill_between(df_disp['date'], df_disp['atr'], alpha=0.25, color=BLUE)
ax_atr.plot(df_disp['date'], df_disp['atr'], color=BLUE, linewidth=1.2)
ax_atr.set_ylabel('ATR')
ax_atr.set_title('绿的谐波 (688017.SH) — ATR (14)', fontsize=13, fontweight='bold')
ax_atr.grid(True, alpha=0.3)
fig4.tight_layout()
fig4.savefig(os.path.join(OUTPUT_DIR, 'atr.png'), dpi=150, bbox_inches='tight')
plt.close(fig4)

print("[INFO] 可视化生成完成")

# ============================================================
# 4. 组装 Notebook
# ============================================================
nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "name": "python",
        "version": "3.13.12"
    }
}

cells = []

# -- Cell 1: 标题 --
cells.append(nbf.v4.new_markdown_cell(
    "# 绿的谐波 (688017.SH) 技术指标分析\n\n"
    f"**股票代码**：688017.SH | **板块**：科创板 | **行业**：机械基件  \n"
    f"**数据范围**：{DATE_MIN} ~ {DATE_MAX} | **交易日数**：{ROW_COUNT}  |\n"
    f"**分析指标**：RSI / MACD / 布林带 / ATR\n\n"
    "---"
))

# -- Cell 2: 环境配置 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# 环境配置\n"
    "# ============================================================\n"
    "import pandas as pd\n"
    "import numpy as np\n"
    "import matplotlib.pyplot as plt\n"
    "import matplotlib.dates as mdates\n"
    "import mplfinance as mpf\n"
    "import warnings\n"
    "warnings.filterwarnings('ignore')\n\n"
    "# ---- 中文字体设置 ----\n"
    "from matplotlib.font_manager import fontManager\n"
    "candidates = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong', 'STSong']\n"
    "available = {f.name for f in fontManager.ttflist}\n"
    "font_name = None\n"
    "for c in candidates:\n"
    "    if c in available:\n"
    "        font_name = c\n"
    "        break\n"
    "if font_name:\n"
    "    FONT_RC = {\n"
    "        'font.family': 'sans-serif',\n"
    "        'font.sans-serif': [font_name, 'DejaVu Sans'],\n"
    "        'axes.unicode_minus': False,\n"
    "    }\n"
    "    plt.rcParams.update(FONT_RC)\n"
    "    print(f'中文字体: {font_name}')\n"
    "else:\n"
    "    print('⚠ 未找到中文字体，可能显示乱码')\n"
    "    FONT_RC = {\n"
    "        'font.family': 'sans-serif',\n"
    "        'font.sans-serif': ['DejaVu Sans'],\n"
    "        'axes.unicode_minus': False,\n"
    "    }\n"
    "    plt.rcParams.update(FONT_RC)\n\n"
    "# 图表默认配置\n"
    "plt.rcParams['figure.dpi'] = 100\n"
    "%matplotlib inline\n"
    'print("环境配置完成 ✓")'
))

# -- Cell 3: 数据加载 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# 数据加载与预处理\n"
    "# ============================================================\n"
    "CSV_PATH = r'C:\\Users\\27924\\Desktop\\QuantStudy\\Task1\\绿的谐波_日线数据.csv'\n\n"
    "df = pd.read_csv(CSV_PATH)\n"
    "df.rename(columns={\n"
    "    '交易日期': 'date',\n"
    "    '开盘价': 'open',\n"
    "    '最高价': 'high',\n"
    "    '最低价': 'low',\n"
    "    '收盘价': 'close',\n"
    "    '成交量(手)': 'volume',\n"
    "    '成交额(千元)': 'amount'\n"
    "}, inplace=True)\n\n"
    "df['date'] = pd.to_datetime(df['date'])\n"
    "df.sort_values('date', inplace=True)\n"
    "df.reset_index(drop=True, inplace=True)\n\n"
    "print(f'数据行数: {len(df)}')\n"
    "print(f'日期范围: {df[\"date\"].min().date()} ~ {df[\"date\"].max().date()}')\n"
    "print(f'列名: {list(df.columns)}')\n"
    "df.head(8)"
))

# -- Cell 4: RSI 说明 --
cells.append(nbf.v4.new_markdown_cell(
    "## RSI — 相对强弱指标 (Relative Strength Index)\n\n"
    "### 📐 计算方法\n"
    "1. 计算每日价格变动：$\\Delta_t = close_t - close_{t-1}$\n"
    "2. 将 $\\Delta$ 分解为涨幅和跌幅：\n"
    "   - $gain_t = \\max(\\Delta_t, 0)$\n"
    "   - $loss_t = \\max(-\\Delta_t, 0)$\n"
    "3. 对 gain 和 loss 分别做 EMA 平滑（Wilder's smoothing, $\\alpha = 1/N$）：\n"
    "   - $avg\\_gain_t = \\alpha \\cdot gain_t + (1-\\alpha) \\cdot avg\\_gain_{t-1}$\n"
    "   - $avg\\_loss_t = \\alpha \\cdot loss_t + (1-\\alpha) \\cdot avg\\_loss_{t-1}$\n"
    "4. 计算 RS 和 RSI：\n"
    "   - $RS = \\frac{avg\\_gain}{avg\\_loss}$\n"
    "   - $RSI = 100 - \\frac{100}{1 + RS}$\n\n"
    "### 🎯 作用\n"
    "- **超买/超卖判断**：RSI > 70 为超买区（可能回调），RSI < 30 为超卖区（可能反弹）\n"
    "- **50 中轴**：RSI > 50 偏多，RSI < 50 偏空\n"
    "- **背离信号**：价格创新高而 RSI 未创新高 → 顶背离（看空）；价格创新低而 RSI 未创新低 → 底背离（看多）\n"
    "- **周期选择**：短周期(6)敏感、中周期(14)稳健、长周期(24)平滑\n\n"
    "> 本次计算三组 RSI（6 / 14 / 24），便于对比不同周期的灵敏度。"
))

# -- Cell 5: RSI 计算 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# RSI 计算 (6 / 14 / 24)\n"
    "# ============================================================\n"
    "def compute_rsi(series, period=14):\n"
    '    """使用 EMA 方式 (Wilder smoothing) 计算 RSI"""\n'
    "    delta = series.diff()\n"
    "    gain = delta.where(delta > 0, 0.0)\n"
    "    loss = (-delta).where(delta < 0, 0.0)\n"
    "    # α = 1/period 的 EMA\n"
    "    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()\n"
    "    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()\n"
    "    rs = avg_gain / avg_loss.replace(0, np.nan)\n"
    "    rsi = 100.0 - (100.0 / (1.0 + rs))\n"
    "    return rsi\n\n"
    "df['rsi_6']  = compute_rsi(df['close'], 6)\n"
    "df['rsi_14'] = compute_rsi(df['close'], 14)\n"
    "df['rsi_24'] = compute_rsi(df['close'], 24)\n\n"
    "print('RSI 计算完成 ✓')\n"
    "print(f'RSI-6  最新值: {df[\"rsi_6\"].iloc[-1]:.2f}')\n"
    "print(f'RSI-14 最新值: {df[\"rsi_14\"].iloc[-1]:.2f}')\n"
    "print(f'RSI-24 最新值: {df[\"rsi_24\"].iloc[-1]:.2f}')\n"
    "df[['date', 'close', 'rsi_6', 'rsi_14', 'rsi_24']].tail(8)"
))

# -- Cell 6: MACD 说明 --
cells.append(nbf.v4.new_markdown_cell(
    "## MACD — 指数平滑异同移动平均线\n\n"
    "### 📐 计算方法\n"
    "1. 计算快慢 EMA：\n"
    "   - $EMA_{12} = EMA(close, 12)$\n"
    "   - $EMA_{26} = EMA(close, 26)$\n"
    "2. 计算 DIF（差离值）：\n"
    "   - $DIF = EMA_{12} - EMA_{26}$\n"
    "3. 计算 DEA（信号线）：\n"
    "   - $DEA = EMA(DIF, 9)$\n"
    "4. 计算柱状图（Histogram）：\n"
    "   - $MACD\\_hist = DIF - DEA$\n\n"
    "### 🎯 作用\n"
    "- **金叉/死叉**：DIF 上穿 DEA → 金叉（看多信号）；DIF 下穿 DEA → 死叉（看空信号）\n"
    "- **零轴参考**：DIF/DEA > 0 多头区域，< 0 空头区域\n"
    "- **柱状图**：红柱（正值）表示多头动能增强，绿柱（负值）表示空头动能增强\n"
    "- **背离信号**：价格与 MACD 走势相反时，预示趋势可能反转\n\n"
    "> 参数采用经典设置 (12, 26, 9)，柱状图 = DIF - DEA（红涨绿跌，A股惯例）。"
))

# -- Cell 7: MACD 计算 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# MACD 计算 (12, 26, 9)\n"
    "# ============================================================\n"
    "def compute_macd(series, fast=12, slow=26, signal=9):\n"
    '    """计算 MACD — 返回 DIF, DEA, Histogram（不乘2）"""\n'
    "    ema_fast = series.ewm(span=fast, adjust=False).mean()\n"
    "    ema_slow = series.ewm(span=slow, adjust=False).mean()\n"
    "    dif = ema_fast - ema_slow\n"
    "    dea = dif.ewm(span=signal, adjust=False).mean()\n"
    "    hist = dif - dea\n"
    "    return dif, dea, hist\n\n"
    "df['dif'], df['dea'], df['macd_hist'] = compute_macd(df['close'])\n\n"
    "print('MACD 计算完成 ✓')\n"
    "print(f'DIF  最新值: {df[\"dif\"].iloc[-1]:.4f}')\n"
    "print(f'DEA  最新值: {df[\"dea\"].iloc[-1]:.4f}')\n"
    "print(f'Hist 最新值: {df[\"macd_hist\"].iloc[-1]:.4f}')\n"
    "# 金叉/死叉检测\n"
    "cross = np.where(\n"
    "    (df['dif'] > df['dea']) & (df['dif'].shift(1) <= df['dea'].shift(1)), 1,\n"
    "    np.where(\n"
    "        (df['dif'] < df['dea']) & (df['dif'].shift(1) >= df['dea'].shift(1)), -1, 0\n"
    "    )\n"
    ")\n"
    "golden = (cross == 1).sum()\n"
    "death  = (cross == -1).sum()\n"
    "print(f'金叉次数: {golden}  |  死叉次数: {death}')\n"
    "df[['date', 'close', 'dif', 'dea', 'macd_hist']].tail(8)"
))

# -- Cell 8: 布林带说明 --
cells.append(nbf.v4.new_markdown_cell(
    "## 布林带 — Bollinger Bands\n\n"
    "### 📐 计算方法\n"
    "1. 计算中轨（N 日均线）：\n"
    "   - $MID = MA(close, 20)$\n"
    "2. 计算 N 日标准差：\n"
    "   - $STD = \\sigma(close, 20)$\n"
    "3. 计算上下轨：\n"
    "   - $UPPER = MID + K \\times STD$ （K=2）\n"
    "   - $LOWER = MID - K \\times STD$\n"
    "4. 辅助指标：\n"
    "   - 带宽 $BandWidth = \\frac{UPPER - LOWER}{MID} \\times 100\\%$\n"
    "   - %B 位置 $\\%B = \\frac{close - LOWER}{UPPER - LOWER}$\n\n"
    "### 🎯 作用\n"
    "- **波动率可视化**：布林带收窄 → 低波动（酝酿突破），布林带扩张 → 高波动（趋势进行中）\n"
    "- **超买/超卖参考**：价格触及上轨 → 短线偏强，价格触及下轨 → 短线偏弱\n"
    "- **中轨趋势**：价格在中轨上方 → 多头趋势，中轨下方 → 空头趋势\n"
    "- **%B 指标**：>1 突破上轨，<0 跌破下轨，0.5 刚好在中轨附近\n\n"
    "> 参数采用经典设置 (20, 2)。"
))

# -- Cell 9: 布林带计算 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# 布林带计算 (20, 2)\n"
    "# ============================================================\n"
    "def compute_bollinger(series, period=20, k=2):\n"
    '    """计算布林带 — 返回 Upper, Mid, Lower, BandWidth, %B"""\n'
    "    mid = series.rolling(window=period).mean()\n"
    "    std = series.rolling(window=period).std(ddof=0)\n"
    "    upper = mid + k * std\n"
    "    lower = mid - k * std\n"
    "    bandwidth = (upper - lower) / mid * 100\n"
    "    pct_b = (series - lower) / (upper - lower)\n"
    "    return upper, mid, lower, bandwidth, pct_b\n\n"
    "df['bb_upper'], df['bb_mid'], df['bb_lower'], df['bb_bandwidth'], df['bb_pct_b'] = \\\n"
    "    compute_bollinger(df['close'])\n\n"
    "print('布林带计算完成 ✓')\n"
    "print(f'上轨 最新值: {df[\"bb_upper\"].iloc[-1]:.2f}')\n"
    "print(f'中轨 最新值: {df[\"bb_mid\"].iloc[-1]:.2f}')\n"
    "print(f'下轨 最新值: {df[\"bb_lower\"].iloc[-1]:.2f}')\n"
    "print(f'带宽 最新值: {df[\"bb_bandwidth\"].iloc[-1]:.2f}%')\n"
    "print(f'%B   最新值: {df[\"bb_pct_b\"].iloc[-1]:.4f}')\n"
    "df[['date', 'close', 'bb_upper', 'bb_mid', 'bb_lower', 'bb_bandwidth']].tail(8)"
))

# -- Cell 10: ATR 说明 --
cells.append(nbf.v4.new_markdown_cell(
    "## ATR — 平均真实波幅 (Average True Range)\n\n"
    "### 📐 计算方法\n"
    "1. 计算真实波幅 (True Range)：\n"
    "   $$\n"
    "   TR_t = \\max\\begin{cases}\n"
    "   high_t - low_t \\\\\n"
    "   |high_t - close_{t-1}| \\\\\n"
    "   |low_t - close_{t-1}|\n"
    "   \\end{cases}\n"
    "   $$\n"
    "2. 对 TR 做 EMA 平滑（Wilder's smoothing）：\n"
    "   - $ATR_t = \\alpha \\cdot TR_t + (1-\\alpha) \\cdot ATR_{t-1}$，其中 $\\alpha = 1/14$\n\n"
    "### 🎯 作用\n"
    "- **衡量波动性**：ATR 值越大 → 市场波动越剧烈；ATR 值越小 → 市场越平静\n"
    "- **止损/止盈设定**：常见用法是止损价 = 入场价 ± 2×ATR\n"
    "- **仓位管理**：ATR 高时减小仓位，ATR 低时适当加大仓位\n"
    "- **突破确认**：价格突破关键位超过 1×ATR 往往更具可靠性\n\n"
    "> ATR 不指示方向，只衡量波动幅度。参数采用经典设置 (14)。"
))

# -- Cell 11: ATR 计算 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# ATR 计算 (14)\n"
    "# ============================================================\n"
    "def compute_atr(df, period=14):\n"
    '    """计算 ATR (Average True Range) — EMA 平滑方式"""\n'
    "    high, low, close = df['high'], df['low'], df['close']\n"
    "    prev_close = close.shift(1)\n"
    "    tr1 = high - low\n"
    "    tr2 = (high - prev_close).abs()\n"
    "    tr3 = (low - prev_close).abs()\n"
    "    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)\n"
    "    atr = tr.ewm(alpha=1/period, adjust=False).mean()\n"
    "    return atr\n\n"
    "df['atr'] = compute_atr(df, 14)\n\n"
    "print('ATR 计算完成 ✓')\n"
    "print(f'ATR(14) 最新值: {df[\"atr\"].iloc[-1]:.4f}')\n"
    "print(f'ATR(14) 均值:   {df[\"atr\"].mean():.4f}')\n"
    "print(f'当前收盘价:     {df[\"close\"].iloc[-1]:.2f}')\n"
    "print(f'ATR/Close:     {df[\"atr\"].iloc[-1] / df[\"close\"].iloc[-1] * 100:.2f}%')\n"
    "df[['date', 'high', 'low', 'close', 'atr']].tail(8)"
))

# -- Cell 12: K线 + 布林带 + 成交量 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# 可视化 1: K线 + 布林带 + 成交量\n"
    "# ============================================================\n"
    "plt.rcParams.update(FONT_RC)  # 确保中文字体生效\n\n"
    "# 选取最近 200 个交易日展示\n"
    "DISPLAY_N = min(200, len(df))\n"
    "df_disp = df.tail(DISPLAY_N).copy().set_index('date')\n\n"
    "# 配色: A股惯例 涨红跌绿\n"
    "RED   = '#DC143C'\n"
    "GREEN = '#228B22'\n"
    "BLUE  = '#1f77b4'\n\n"
    "mc = mpf.make_marketcolors(up=RED, down=GREEN, edge='inherit', wick='inherit', volume='inherit')\n"
    "s  = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False, rc=FONT_RC)\n\n"
    "apds = [\n"
    "    mpf.make_addplot(df_disp['bb_upper'], color='gray', linestyle='--', width=0.8, label='上轨'),\n"
    "    mpf.make_addplot(df_disp['bb_mid'],   color=BLUE, width=1.2, label='中轨'),\n"
    "    mpf.make_addplot(df_disp['bb_lower'], color='gray', linestyle='--', width=0.8, label='下轨'),\n"
    "]\n\n"
    "fig1, axes = mpf.plot(\n"
    "    df_disp, type='candle', style=s, addplot=apds, volume=True,\n"
    "    title='\\n绿的谐波 (688017.SH) — K线 + 布林带 (20,2)',\n"
    "    ylabel='价格 (元)', ylabel_lower='成交量 (手)',\n"
    "    figsize=(16, 9), returnfig=True, warn_too_much_data=10000,\n"
    ")\n"
    "axes[0].legend(loc='upper left', fontsize=9)\n"
    "plt.show()"
))

# -- Cell 13: RSI 可视化 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# 可视化 2: RSI 三线\n"
    "# ============================================================\n"
    "plt.rcParams.update(FONT_RC)\n"
    "fig2, ax = plt.subplots(figsize=(16, 5))\n\n"
    "ax.plot(df_disp.index, df['rsi_6'].tail(DISPLAY_N),  color='#ff7f0e', linewidth=1,   label='RSI-6')\n"
    "ax.plot(df_disp.index, df['rsi_14'].tail(DISPLAY_N), color=BLUE,        linewidth=1.2, label='RSI-14')\n"
    "ax.plot(df_disp.index, df['rsi_24'].tail(DISPLAY_N), color='#9467bd',   linewidth=1,   label='RSI-24')\n\n"
    "# 超买超卖区间\n"
    "ax.axhline(y=70, color=RED,   linestyle='--', alpha=0.5, linewidth=0.8)\n"
    "ax.axhline(y=30, color=GREEN, linestyle='--', alpha=0.5, linewidth=0.8)\n"
    "ax.axhline(y=50, color='gray', linestyle=':',  alpha=0.4, linewidth=0.6)\n"
    "ax.fill_between(df_disp.index, 70, 100, alpha=0.08, color=RED)\n"
    "ax.fill_between(df_disp.index, 0,  30,  alpha=0.08, color=GREEN)\n"
    "ax.set_ylim(0, 100)\n"
    "ax.set_ylabel('RSI')\n"
    "ax.set_title('绿的谐波 (688017.SH) — RSI (6 / 14 / 24)', fontsize=13, fontweight='bold')\n"
    "ax.legend(loc='upper left', fontsize=9)\n"
    "ax.grid(True, alpha=0.3)\n"
    "fig2.tight_layout()\n"
    "plt.show()"
))

# -- Cell 14: MACD 可视化 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# 可视化 3: MACD\n"
    "# ============================================================\n"
    "plt.rcParams.update(FONT_RC)\n"
    "fig3, ax = plt.subplots(figsize=(16, 5))\n\n"
    "# 柱状图：正值红色，负值绿色\n"
    "hist_vals = df['macd_hist'].tail(DISPLAY_N).values\n"
    "colors = [RED if v >= 0 else GREEN for v in hist_vals]\n"
    "ax.bar(df_disp.index, hist_vals, color=colors, width=0.8, alpha=0.6)\n\n"
    "ax.plot(df_disp.index, df['dif'].tail(DISPLAY_N), color=BLUE,        linewidth=1.2, label='DIF')\n"
    "ax.plot(df_disp.index, df['dea'].tail(DISPLAY_N), color='#ff7f0e',   linewidth=1,   label='DEA')\n"
    "ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.6)\n"
    "ax.set_ylabel('MACD')\n"
    "ax.set_title('绿的谐波 (688017.SH) — MACD (12, 26, 9)', fontsize=13, fontweight='bold')\n"
    "ax.legend(loc='upper left', fontsize=9)\n"
    "ax.grid(True, alpha=0.3)\n"
    "fig3.tight_layout()\n"
    "plt.show()"
))

# -- Cell 15: ATR 可视化 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# 可视化 4: ATR\n"
    "# ============================================================\n"
    "plt.rcParams.update(FONT_RC)\n"
    "fig4, ax = plt.subplots(figsize=(16, 5))\n\n"
    "atr_vals = df['atr'].tail(DISPLAY_N).values\n"
    "ax.fill_between(df_disp.index, atr_vals, alpha=0.25, color=BLUE)\n"
    "ax.plot(df_disp.index, atr_vals, color=BLUE, linewidth=1.2)\n"
    "ax.set_ylabel('ATR')\n"
    "ax.set_title('绿的谐波 (688017.SH) — ATR (14)', fontsize=13, fontweight='bold')\n"
    "ax.grid(True, alpha=0.3)\n"
    "fig4.tight_layout()\n"
    "plt.show()"
))

# -- Cell 16: 统计摘要 --
cells.append(nbf.v4.new_code_cell(
    "# ============================================================\n"
    "# 综合统计摘要\n"
    "# ============================================================\n"
    "latest = df.iloc[-1]\n"
    "close_series = df['close']\n"
    "\n"
    "summary = pd.DataFrame({\n"
    "    '指标': [\n"
    "        '收盘价',\n"
    "        'N日最高', 'N日最低',\n"
    "        '20日均价', '60日均价',\n"
    "        '日波动率(年化)',\n"
    "        'RSI-6', 'RSI-14', 'RSI-24',\n"
    "        'DIF', 'DEA', 'MACD Hist',\n"
    "        '布林上轨', '布林中轨', '布林下轨',\n"
    "        '布林带宽(%)', '%B',\n"
    "        'ATR(14)',\n"
    "        'ATR/Close(%)',\n"
    "    ],\n"
    "    '最新值': [\n"
    "        f\"{latest['close']:.2f}\",\n"
    "        f\"{close_series.max():.2f}\", f\"{close_series.min():.2f}\",\n"
    "        f\"{close_series.tail(20).mean():.2f}\", f\"{close_series.tail(60).mean():.2f}\",\n"
    "        f\"{close_series.pct_change().std() * np.sqrt(252) * 100:.2f}%\",\n"
    "        f\"{latest['rsi_6']:.2f}\", f\"{latest['rsi_14']:.2f}\", f\"{latest['rsi_24']:.2f}\",\n"
    "        f\"{latest['dif']:.4f}\", f\"{latest['dea']:.4f}\", f\"{latest['macd_hist']:.4f}\",\n"
    "        f\"{latest['bb_upper']:.2f}\", f\"{latest['bb_mid']:.2f}\", f\"{latest['bb_lower']:.2f}\",\n"
    "        f\"{latest['bb_bandwidth']:.2f}%\", f\"{latest['bb_pct_b']:.4f}\",\n"
    "        f\"{latest['atr']:.4f}\",\n"
    "        f\"{latest['atr'] / latest['close'] * 100:.2f}%\",\n"
    "    ]\n"
    "})\n"
    "print(f'数据日期: {df[\"date\"].iloc[-1].date()}   股票: 绿的谐波 688017.SH\\n')\n"
    "summary"
))

# -- Cell 17: 总结 --
cells.append(nbf.v4.new_markdown_cell(
    "## 总结与备注\n\n"
    "### 分析结论\n"
    "以上四项技术指标从不同维度刻画了绿的谐波的走势特征：\n"
    "- **RSI** 反映价格运动的内在强弱，辅以超买/超卖信号\n"
    "- **MACD** 追踪趋势方向与动能变化，通过金叉/死叉给出交易信号\n"
    "- **布林带** 衡量价格偏离均线的程度，识别波动率变化\n"
    "- **ATR** 量化市场波动幅度，辅助仓位管理与止损设定\n\n"
    "### 注意事项\n"
    "- 技术指标仅供参考，不构成投资建议\n"
    "- 单一指标存在局限性，建议结合基本面与市场环境综合判断\n"
    "- ATR 不指示方向，应配合趋势类指标（如 MACD）共同使用\n"
    "- 布林带在横盘市场参考价值较高，强趋势中价格可能持续贴边运行\n\n"
    "### 指标参数汇总\n"
    "| 指标 | 参数 |\n"
    "|------|------|\n"
    "| RSI | 6 / 14 / 24 |\n"
    "| MACD | Fast=12, Slow=26, Signal=9, Hist=DIFF-DEA |\n"
    "| 布林带 | Period=20, K=2 |\n"
    "| ATR | Period=14 |\n"
    f"\n---\n*生成日期: 2026-07-04 | 数据来源: Tushare*"
))

# 设置 cell ID
for i, cell in enumerate(cells):
    cell.id = f"cell-{i+1:02d}"

nb.cells = cells

# 写入
NOTEBOOK_PATH = r'C:\Users\27924\Desktop\QuantStudy\Task2\绿的谐波_688017_技术指标分析.ipynb'
nbf.write(nb, NOTEBOOK_PATH)
print(f"\n[SUCCESS] Notebook 已生成: {NOTEBOOK_PATH}")
print(f"[SUCCESS] 共 {len(cells)} 个 Cell")
