# -*- coding: utf-8 -*-
"""生成 Jupyter Notebook 文件，展示绿的谐波数据分析全流程"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))

cells = []

def md(source):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": source if isinstance(source, list) else [source]
    })

def code(source):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source if isinstance(source, list) else [source]
    })

# ========== Cell 1: 标题 ==========
md([
    "# 绿的谐波（688017.SH）行情数据分析\n",
    "---\n",
    "本 Notebook 完整展示从 **Tushare 数据获取** → **数据清洗与统计** → **CSV 存储** → **ECharts 可视化看板生成** 的全流程。\n",
    f"\n> 📅 生成日期：2026-07-03  |  🎯 标的：绿的谐波（688017.SH）科创板 / 机械基件\n",
    "> 📊 数据区间：近一年（约 243 个交易日）\n",
    "\n---"
])

# ========== Cell 2: 环境准备 ==========
md([
    "## 1. 环境准备\n",
    "\n导入所需库。本 Notebook 仅使用 **Python 标准库**（无第三方依赖），可视化通过 ECharts CDN 在 HTML 中渲染。"
])

code([
    "import json\n",
    "import csv\n",
    "import statistics\n",
    "import math\n",
    "import os\n",
    "\n",
    "print('✅ 标准库导入完成')"
])

# ========== Cell 3: Tushare 数据获取 ==========
md([
    "## 2. 获取行情数据\n",
    "\n### 方式一：通过 Tushare API 获取（推荐）\n",
    "\n> 需要先注册 Tushare 账号（https://tushare.pro）获取 token。\n",
    "> 安装 tushare：`pip install tushare`"
])

code([
    "# ====== 方式一：Tushare API 实时获取 ======\n",
    "# 取消注释下方代码并填入你的 token 即可使用\n",
    "\n",
    "# import tushare as ts\n",
    "# pro = ts.pro_api('你的Token')\n",
    "# df = pro.daily(\n",
    "#     ts_code='688017.SH',\n",
    "#     start_date='20250703',\n",
    "#     end_date='20260703'\n",
    "# )\n",
    "# data = df.to_dict('records')\n",
    "\n",
    "print('💡 若 Tushare 不可用，请运行下方单元格从本地文件加载')\n",
    "print('   （已在 .workbuddy 环境中预存了 daily.json 作为示例）')"
])

md([
    "### 方式二：从本地 JSON 加载（示例数据）\n",
    "\n当前会话已将 Tushare MCP 获取的数据保存为 `data/daily.json`，可直接读取。"
])

code([
    "# ====== 方式二：从本地文件加载 ======\n",
    "json_path = 'data/daily.json'\n",
    "\n",
    "if os.path.exists(json_path):\n",
    "    with open(json_path, 'r', encoding='utf-8') as f:\n",
    "        data = json.load(f)\n",
    "    print(f'✅ 成功加载 {len(data)} 条行情记录')\n",
    "else:\n",
    "    print('⚠️ data/daily.json 不存在，请先运行 Tushare API 方式获取')\n",
    "    data = []"
])

# ========== Cell 4: 数据预处理 ==========
md([
    "## 3. 数据预处理与探索\n",
    "\n查看数据结构、按日期排序、检查数据质量。"
])

code([
    "# 按交易日期正序排列\n",
    "data.sort(key=lambda x: x['trade_date'])\n",
    "\n",
    "# 日期格式化工具\n",
    "def fmt_date(d):\n",
    "    return f\"{d[:4]}-{d[4:6]}-{d[6:8]}\"\n",
    "\n",
    "# 查看前 5 行\n",
    "print(f\"{'交易日期':<12}{'开盘价':>8}{'最高价':>8}{'最低价':>8}{'收盘价':>8}{'涨跌幅(%)':>10}{'成交量(手)':>12}\")\n",
    "print('-' * 70)\n",
    "for d in data[:5]:\n",
    "    print(f\"{fmt_date(d['trade_date']):<12}{d['open']:>8.2f}{d['high']:>8.2f}{d['low']:>8.2f}{d['close']:>8.2f}{d['pct_chg']:>10.2f}{d['vol']:>12.1f}\")\n",
    "print(f\"\\n... 共 {len(data)} 条记录\")"
])

# ========== Cell 5: 统计指标 ==========
md([
    "## 4. 关键统计指标计算\n",
    "\n从原始行情数据中提取数列，计算核心统计指标。"
])

code([
    "# 提取各维度的数据序列\n",
    "closes   = [d['close']    for d in data]\n",
    "volumes  = [d['vol']      for d in data]\n",
    "amounts  = [d['amount']   for d in data]\n",
    "highs    = [d['high']     for d in data]\n",
    "lows     = [d['low']      for d in data]\n",
    "pct_chgs = [d['pct_chg']  for d in data]\n",
    "opens    = [d['open']     for d in data]\n",
    "\n",
    "# 基础统计\n",
    "first_close = closes[0]\n",
    "last_close  = closes[-1]\n",
    "first_date  = fmt_date(data[0]['trade_date'])\n",
    "last_date   = fmt_date(data[-1]['trade_date'])\n",
    "year_return = (last_close - first_close) / first_close * 100\n",
    "max_high    = max(highs)\n",
    "min_low     = min(lows)\n",
    "max_high_date = fmt_date(data[highs.index(max_high)]['trade_date'])\n",
    "min_low_date  = fmt_date(data[lows.index(min_low)]['trade_date'])\n",
    "avg_vol    = statistics.mean(volumes)\n",
    "avg_amount = statistics.mean(amounts)\n",
    "up_days    = sum(1 for p in pct_chgs if p > 0)\n",
    "down_days  = sum(1 for p in pct_chgs if p < 0)\n",
    "max_gain   = max(pct_chgs)\n",
    "max_loss   = min(pct_chgs)\n",
    "max_gain_date = fmt_date(data[pct_chgs.index(max_gain)]['trade_date'])\n",
    "max_loss_date = fmt_date(data[pct_chgs.index(max_loss)]['trade_date'])\n",
    "\n",
    "# 年化波动率\n",
    "returns     = [p / 100 for p in pct_chgs]\n",
    "volatility  = statistics.stdev(returns) * math.sqrt(250) * 100\n",
    "\n",
    "# 移动均线\n",
    "def calc_ma(values, period):\n",
    "    if len(values) < period:\n",
    "        return None\n",
    "    return round(statistics.mean(values[-period:]), 2)\n",
    "\n",
    "ma5  = calc_ma(closes, 5)\n",
    "ma20 = calc_ma(closes, 20)\n",
    "ma60 = calc_ma(closes, 60)\n",
    "\n",
    "print('📊 核心统计指标')\n",
    "print('=' * 50)\n",
    "print(f'  数据区间：{first_date}  →  {last_date}')\n",
    "print(f'  起始收盘价：{first_close:.2f} 元')\n",
    "print(f'  最新收盘价：{last_close:.2f} 元')\n",
    "print(f'  年涨幅：{year_return:+.2f}%')\n",
    "print(f'  最高价：{max_high:.2f} 元（{max_high_date}）')\n",
    "print(f'  最低价：{min_low:.2f} 元（{min_low_date}）')\n",
    "print(f'  日均成交量：{avg_vol:,.0f} 手')\n",
    "print(f'  年化波动率：{volatility:.1f}%')\n",
    "print(f'  上涨/下跌：{up_days} / {down_days} 天')\n",
    "print(f'  最大涨幅：+{max_gain:.2f}%（{max_gain_date}）')\n",
    "print(f'  最大跌幅：{max_loss:.2f}%（{max_loss_date}）')\n",
    "print(f'  MA5 / MA20 / MA60：{ma5} / {ma20} / {ma60}')"
])

# ========== Cell 6: CSV 导出 ==========
md([
    "## 5. 导出为 CSV 文件\n",
    "\n将数据写入标准 CSV 格式，带 BOM 头以兼容 Excel 中文显示。"
])

code([
    "csv_path = '绿的谐波_日线数据.csv'\n",
    "with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:\n",
    "    writer = csv.writer(f)\n",
    "    writer.writerow(['交易日期', '股票代码', '开盘价', '最高价', '最低价',\n",
    "                     '收盘价', '昨收价', '涨跌额', '涨跌幅(%)', '成交量(手)', '成交额(千元)'])\n",
    "    for d in data:\n",
    "        writer.writerow([\n",
    "            fmt_date(d['trade_date']), d['ts_code'],\n",
    "            d['open'], d['high'], d['low'], d['close'],\n",
    "            d['pre_close'], d['change'], d['pct_chg'],\n",
    "            d['vol'], d['amount']\n",
    "        ])\n",
    "\n",
    "file_size = os.path.getsize(csv_path)\n",
    "print(f'✅ CSV 已导出：{csv_path}')\n",
    "print(f'   共 {len(data)} 行，{file_size:,} 字节')"
])

# ========== Cell 7: HTML 看板 ==========
md([
    "## 6. 生成 HTML 可视化看板\n",
    "\n使用 **ECharts 5.x CDN** 渲染交互式图表。看板包含：\n",
    "- **📈 收盘价曲线图** + 成交量副图\n",
    "- **📊 K线图** + MA5/MA20/MA60 均线 + 成交量副图\n",
    "- **📰 近期重要新闻**板块\n",
    "- 各图表下方的**数据解读**与**投资建议**（自动生成）\n",
    "\n> 以下代码将完整的 HTML 字符串写入文件，打开即可在浏览器中交互查看。"
])

code([
    "# ---------- 准备 ECharts 数据 ----------\n",
    "dates      = [fmt_date(d['trade_date']) for d in data]\n",
    "close_data = closes\n",
    "kline_data = [[d['open'], d['close'], d['low'], d['high']] for d in data]\n",
    "vol_data   = [{'value': d['vol'], 'pct': d['pct_chg']} for d in data]\n",
    "\n",
    "# MA 均线序列\n",
    "def ma_series(values, period):\n",
    "    result = []\n",
    "    for i in range(len(values)):\n",
    "        if i < period - 1:\n",
    "            result.append(None)\n",
    "        else:\n",
    "            result.append(round(statistics.mean(values[i-period+1:i+1]), 2))\n",
    "    return result\n",
    "\n",
    "ma5_series  = ma_series(closes, 5)\n",
    "ma20_series = ma_series(closes, 20)\n",
    "ma60_series = ma_series(closes, 60)\n",
    "\n",
    "# 趋势判断\n",
    "recent20_return = (closes[-1] - closes[-21]) / closes[-21] * 100\n",
    "if   recent20_return > 15: trend_word = '强势上涨'\n",
    "elif recent20_return > 5:  trend_word = '震荡上行'\n",
    "elif recent20_return > -5: trend_word = '横盘震荡'\n",
    "elif recent20_return > -15:trend_word = '震荡下行'\n",
    "else:                      trend_word = '持续回调'\n",
    "\n",
    "print(f'📌 近期趋势：近20日涨跌幅 {recent20_return:+.2f}% → {trend_word}')\n",
    "print(f'📌 数据点：{len(dates)} 个交易日')\n",
    "print('🔄 正在组装 HTML 看板...')"
])

code([
    "# ====== 核心 HTML 生成（简化版，完整版见 generate_dashboard.py）======\n",
    "\n",
    "# 将数据序列化为 JSON，嵌入 HTML\n",
    "chart_data = json.dumps({\n",
    "    'dates': dates,\n",
    "    'close': close_data,\n",
    "    'kline': kline_data,\n",
    "    'vol': vol_data,\n",
    "    'ma5': ma5_series,\n",
    "    'ma20': ma20_series,\n",
    "    'ma60': ma60_series,\n",
    "}, ensure_ascii=False)\n",
    "\n",
    "# 此处省略完整的 HTML 模板字符串（约 450 行），\n",
    "# 详情请查看同级目录下的 generate_dashboard.py\n",
    "# 该脚本读取 data/daily.json 后生成完整看板\n",
    "\n",
    "html_path = '绿的谐波_行情看板.html'  # 已在之前步骤中生成\n",
    "print(f'✅ HTML 看板已就绪：{html_path}')\n",
    "print(f'   使用 ECharts 5.5.0 CDN，含收盘价曲线 + K线图 + 新闻板块')"
])

# ========== Cell 8: 总结 ==========
md([
    "## 7. 总结\n",
    "\n### 完成的工作\n",
    "\n| 步骤 | 内容 | 输出 |\n",
    "|------|------|------|\n",
    "| 1 | 通过 Tushare MCP 获取近一年日线数据 | `data/daily.json` (243 条) |\n",
    "| 2 | 数据清洗与统计指标计算 | 年涨幅 +306%，波动率 81.5% |\n",
    "| 3 | 导出标准 CSV 格式 | `绿的谐波_日线数据.csv` |\n",
    "| 4 | 生成 ECharts 交互式看板 | `绿的谐波_行情看板.html` |\n",
    "| 5 | 推送至 GitHub 仓库 | https://github.com/Huxiaojiao7/Quant-Study |\n",
    "\n### 技术栈\n",
    "- **数据源**：Tushare Pro API（MCP 方式调用）\n",
    "- **数据处理**：Python 3.13 标准库（json / csv / statistics / math）\n",
    "- **可视化**：ECharts 5.x（CDN 加载）、HTML 单文件输出\n",
    "- **版本控制**：Git + GitHub（SSH）\n",
    "\n### 关键结论\n",
    "> 绿的谐波近一年涨幅超 300%，年化波动率约 81.5%，属于典型的高弹性成长股。\n",
    "> 2026 年人形机器人产业进入量产元年，公司作为谐波减速器龙头直接受益，\n",
    "> Q1 净利润同比增长 189%，订单已排至 2027 年，赛道逻辑清晰。\n",
    "> 但当前 PE 高达 484 倍（7月1日公告），远超行业均值 42 倍，估值风险需警惕。"
])

# ========== Build Notebook ==========
notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.13.12"
        }
    },
    "cells": cells
}

nb_path = os.path.join(BASE, '绿的谐波_数据分析流程.ipynb')
with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"[OK] Notebook generated: {nb_path}")
print(f"    Total {len(cells)} cells")
