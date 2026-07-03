# 绿的谐波 (688017.SH) 技术指标分析 — 项目规格说明书

> **版本**: v1.1  
> **日期**: 2026-07-04  
> **输出**: Jupyter Notebook (.ipynb)

---

## 1. 项目概述

### 1.1 目标
获取绿的谐波（688017.SH）上市以来的全部日线行情数据，计算四项常用技术指标，并通过可视化图形展示结果。全部计算过程以 Jupyter Notebook 形式呈现，确保可复现、可交互。

### 1.2 股票信息

| 字段 | 值 |
|------|-----|
| TS 代码 | 688017.SH |
| 股票代码 | 688017 |
| 股票名称 | 绿的谐波 |
| 上市日期 | 2020-08-28 |
| 交易所 | 上交所 |
| 板块 | 科创板 |
| 行业 | 机械基件 |
| 地区 | 江苏 |

---

## 2. 数据获取

### 2.1 数据源
- **本地 CSV 文件**: `C:\Users\27924\Desktop\QuantStudy\Task1\绿的谐波_日线数据.csv`
- 数据由 Task1 项目预先从 Tushare 拉取，无需重复请求

### 2.2 CSV 字段映射

| CSV 列名 | 含义 | 映射变量 | 用途 |
|----------|------|----------|------|
| `交易日期` | 交易日期 | `date` | X 轴时间刻度 |
| `开盘价` | 开盘价 | `open` | K线 |
| `最高价` | 最高价 | `high` | ATR、布林带 |
| `最低价` | 最低价 | `low` | ATR、布林带 |
| `收盘价` | 收盘价 | `close` | RSI、MACD、布林带、ATR |
| `成交量(手)` | 成交量 | `volume` | 成交量副图 |
| `成交额(千元)` | 成交额 | `amount` | 可选参考 |

### 2.3 加载方式
```python
df = pd.read_csv(r'C:\Users\27924\Desktop\QuantStudy\Task1\绿的谐波_日线数据.csv')
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
```

### 2.4 数据范围
- 起始日期: 2020-08-28（上市日）
- 截止日期: CSV 中最新日期

---

## 3. 技术指标定义

### 3.1 RSI — 相对强弱指标

| 参数 | 值 |
|------|-----|
| 周期 | 6 / 14 / 24 三组 |

#### 计算公式
```
RS = avg_gain(N) / avg_loss(N)
RSI = 100 - 100 / (1 + RS)
```

#### 步骤
1. 计算价格变动 `delta = close_t - close_{t-1}`
2. 将 `delta` 分为 `gain`（正值）和 `loss`（负值的绝对值）
3. 对 `gain` 和 `loss` 分别计算 N 周期的 Wilder 平滑平均（EMA 方式）
4. 代入 RSI 公式

#### 信号阈值
- 超买: RSI > 70
- 超卖: RSI < 30
- 50 中轴线

---

### 3.2 MACD — 指数平滑异同移动平均线

| 参数 | 值 |
|------|-----|
| 快线周期 (fast) | 12 |
| 慢线周期 (slow) | 26 |
| 信号线周期 (signal) | 9 |

#### 计算公式
```
EMA_12 = EMA(close, 12)
EMA_26 = EMA(close, 26)
DIF = EMA_12 - EMA_26
DEA = EMA(DIF, 9)
MACD_hist = DIF - DEA
```

#### 图表元素
- DIF 线（快线）
- DEA 线（信号线）
- 柱状图 (MACD Histogram)：正值红色、负值绿色（A股惯例）
- 零轴参考线

---

### 3.3 布林带 — Bollinger Bands

| 参数 | 值 |
|------|-----|
| 中轨周期 (N) | 20 |
| 标准差倍数 (K) | 2 |

#### 计算公式
```
MID = MA(close, 20)
STD = std(close, 20)
UPPER = MID + 2 × STD
LOWER = MID - 2 × STD
```

#### 辅助指标
- 带宽 `(UPPER - LOWER) / MID × 100%`
- %B 位置 `(close - LOWER) / (UPPER - LOWER)`

---

### 3.4 ATR — 平均真实波幅

| 参数 | 值 |
|------|-----|
| 周期 | 14 |

#### 计算公式
```
TR_t = max(
    high_t - low_t,
    |high_t - close_{t-1}|,
    |low_t - close_{t-1}|
)
ATR = EMA(TR, 14)  // 使用 EMA 平滑
```

#### 用途
- 衡量市场波动性
- 用于止损/止盈设定参考

---

## 4. 可视化设计

### 4.1 整体布局
使用 `matplotlib` + `mplfinance` 组合，Notebook 中分板块展示。

### 4.2 图表清单

| 编号 | 图表名称 | 类型 | 内容 |
|------|---------|------|------|
| Fig 1 | K线 + 布林带 + 成交量 | 主图 | 蜡烛图 + 布林带三轨叠加 + 成交量柱状图 |
| Fig 2 | RSI 三线图 | 副图 | RSI-6 / RSI-14 / RSI-24 三线 + 超买超卖区间 |
| Fig 3 | MACD 图 | 副图 | DIF / DEA / 柱状图 + 零轴 |
| Fig 4 | ATR 图 | 副图 | ATR-14 曲线 |
| Fig 5 | 综合仪表盘 | 多面板 | 四合一总览（可选） |

### 4.3 配色方案
- **A股惯例**: 涨红跌绿
- 蜡烛图: 阳线红色 `#DC143C`，阴线绿色 `#228B22`
- 布林带: 中轨蓝色，上下轨灰色半透明填充
- RSI: 超买区红色半透明 `70-100`，超卖区绿色半透明 `0-30`
- MACD 柱: 正值红色，负值绿色
- ATR: 深蓝色曲线

### 4.4 图表尺寸与风格
- 默认 `figsize = (16, 10)`，根据内容调整
- 使用 `seaborn-v0_8-darkgrid` 或自定义 style
- 中文字体支持（SimHei / Microsoft YaHei）

---

## 5. Notebook 结构设计

```
绿的谐波_688017_技术指标分析.ipynb

├── Cell 1:  标题、项目简介
├── Cell 2:  环境配置（import + 中文字体设置）
├── Cell 3:  数据加载与预处理（读取 CSV + 列名映射 + 日期解析）
│
├── Cell 4:  【指标说明】RSI — 计算方法 + 作用
├── Cell 5:  【指标计算】RSI 6/14/24
│
├── Cell 6:  【指标说明】MACD — 计算方法 + 作用
├── Cell 7:  【指标计算】MACD
│
├── Cell 8:  【指标说明】布林带 — 计算方法 + 作用
├── Cell 9:  【指标计算】布林带
│
├── Cell 10: 【指标说明】ATR — 计算方法 + 作用
├── Cell 11: 【指标计算】ATR
│
├── Cell 12: 【可视化】K线 + 布林带 + 成交量
├── Cell 13: 【可视化】RSI 三线
├── Cell 14: 【可视化】MACD
├── Cell 15: 【可视化】ATR
├── Cell 16: 综合统计摘要
└── Cell 17: 总结与备注
```

> **说明 Cell 内容规范**（以 RSI 为例）:
> - **计算方法**: 逐步骤描述公式推导过程
> - **作用**: 解释该指标的实战含义（超买/超卖判断、趋势确认、背离信号等）

---

## 6. 技术依赖

### 6.1 Python 环境
| 包 | 版本要求 | 用途 |
|----|---------|------|
| `pandas` | ≥2.0 | 数据处理 |
| `numpy` | ≥1.24 | 数值计算 |
| `matplotlib` | ≥3.7 | 基础绑图 |
| `mplfinance` | ≥0.12 | K线/金融图表 |
| `jupyter` | latest | Notebook 运行环境 |

### 6.2 安装命令
```bash
pip install pandas numpy matplotlib mplfinance jupyter
```

---

## 7. 文件结构

```
Task2/
├── SPEC_格林谐波_技术指标分析.md      # 本文件（规格说明书）
├── 绿的谐波_688017_技术指标分析.ipynb  # Jupyter Notebook（主产出）
└── outputs/
    ├── kline_bollinger.png            # K线 + 布林带
    ├── rsi.png                         # RSI
    ├── macd.png                        # MACD
    └── atr.png                         # ATR
```

> 数据文件位于 `../Task1/绿的谐波_日线数据.csv`，Notebook 通过相对路径或绝对路径直接读取。

---

## 8. 验收标准

- [x] 数据完整性: 覆盖上市以来所有交易日
- [ ] 指标计算正确: RSI 范围 [0,100]，MACD 与通用平台一致
- [ ] 可视化清晰: 图表标题、坐标轴标签、图例完整
- [ ] 中文字体正常显示，无乱码
- [ ] Notebook 从头到尾可顺序执行，无报错
- [ ] A股惯例: 涨红跌绿，颜色一致性

---

## 9. 执行计划

| 步骤 | 内容 | 预计 |
|------|------|------|
| Step 1 | 创建目录结构 + 安装依赖 | ✓ |
| Step 2 | 从 Task1 加载 CSV 并预处理 | ✓ |
| Step 3 | 逐项编写指标说明 + 计算代码 | ✓ |
| Step 4 | 生成四张可视化图表 | ✓ |
| Step 5 | 组装 Jupyter Notebook | ✓ |
| Step 6 | 全量测试执行 | ✓ |
