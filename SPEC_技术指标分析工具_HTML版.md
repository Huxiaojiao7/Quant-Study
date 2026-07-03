# 交互式技术指标分析工具 — 产品设计规格说明书

> **版本**: v1.0  
> **日期**: 2026-07-04  
> **输出**: 纯前端 HTML 交互工具 + Python 数据获取脚本

---

## 1. 产品概述

### 1.1 产品愿景

构建一个**零依赖、开箱即用**的浏览器端技术指标交互分析工具。用户选择股票 → 工具自动加载近一年日线数据 → 实时计算 RSI / MACD / 布林带 / ATR 四项指标 → 任意调整每个指标的参数即时重绘，所见即所得。

### 1.2 核心价值

| 痛点 | 解决方案 |
|------|---------|
| 每次改参数都要重跑代码 | 滑块拖拽、输入框修改，毫秒级重绘 |
| 只能在单一股票上分析 | 下拉切换 5 只股票，数据秒切 |
| 多指标对比困难 | 四张图纵向堆叠，共用 X 轴时间线 |
| 环境搭建麻烦 | 纯 HTML/JS，浏览器直接打开 |

### 1.3 目标股票池

| 序号 | 股票代码 | 股票名称 | 交易所 | 板块 |
|------|---------|---------|--------|------|
| 1 | 688017.SH | 绿的谐波 | 上交所 | 科创板 |
| 2 | 688256.SH | 寒武纪 | 上交所 | 科创板 |
| 3 | 002896.SZ | 中大力德 | 深交所 | 主板 |
| 4 | 002472.SZ | 双环传动 | 深交所 | 主板 |
| 5 | 688981.SH | 中芯国际 | 上交所 | 科创板 |

### 1.4 四项技术指标

| 指标 | 英文 | 默认参数 | 用途 |
|------|------|---------|------|
| RSI | Relative Strength Index | N=14 | 超买超卖判断 |
| MACD | Moving Average Convergence Divergence | (12,26,9) | 趋势跟踪 |
| BOLL | Bollinger Bands | (20, 2.0) | 波动区间 |
| ATR | Average True Range | N=14 | 波动率衡量 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────┐
│                  HTML 页面                        │
│  ┌───────────────────────────────────────────┐  │
│  │            控制面板 (Control Panel)         │  │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │  │
│  │  │股票  │ │指标  │ │参数  │ │时间  │ ... │  │
│  │  │选择器│ │选择器│ │面板  │ │范围  │     │  │
│  │  └──────┘ └──────┘ └──────┘ └──────┘     │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │            图表区域 (Chart Panel)           │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │  K线 + 布林带 (主图)                 │  │  │
│  │  │          + 成交量                    │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │  RSI 子图                [参数面板]  │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │  MACD 子图               [参数面板]  │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │  ATR 子图                [参数面板]  │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│            Python 数据获取脚本                    │
│  ┌───────────────────────────────────────────┐  │
│  │  fetch_data.py                             │  │
│  │  ├─ Tushare MCP → 获取 5 只股票近1年日线   │  │
│  │  └─ 输出 → data/stocks.json (内嵌数据)     │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

### 2.2 数据流

```
[Tushare MCP]
     │
     ▼
[Python 脚本] ──批量获取 5 只股票近 365 天日线数据
     │
     ▼
[stocks.json] ──每只股票: { dates, open, high, low, close, volume }
     │
     ▼
[HTML 主页面] ──启动时加载 JSON
     │
     ├── 股票选择 → 筛选对应数据
     ├── 参数调整 → 触发 JS 重新计算指标
     └── 图表重绘 → ECharts 增量更新
```

### 2.3 技术选型

| 层级 | 技术 | 选型理由 |
|------|------|---------|
| 数据获取 | Python + Tushare MCP | 工作台已有 MCP 连接，直接复用 |
| 数据载体 | JSON 文件 | 静态文件，浏览器直接 fetch |
| 前端框架 | 纯 HTML + Vanilla JS | 零依赖，双击即用 |
| 图表渲染 | ECharts 5.x (CDN) | 金融图表能力强，支持 K 线、多面板 |
| 样式 | 原生 CSS + CSS Variables | 无框架依赖，主题切换方便 |
| 数学计算 | 手写纯 JS | 不引入 lodash/mathjs，代码可控 |

---

## 3. 功能模块详细设计

### 3.1 数据管理层

#### 3.1.1 数据格式 (stocks.json)

```json
{
  "meta": {
    "generated_at": "2026-07-04",
    "date_range": ["2025-07-04", "2026-07-03"],
    "total_stocks": 5
  },
  "stocks": {
    "688017.SH": {
      "name": "绿的谐波",
      "data": [
        {
          "date": "2025-07-04",
          "open": 25.50,
          "high": 26.30,
          "low": 25.10,
          "close": 25.80,
          "volume": 12345600
        }
      ]
    }
  }
}
```

#### 3.1.2 数据加载流程

```
1. 页面 onload → fetch('data/stocks.json')
2. 解析 JSON → 填充股票下拉列表
3. 默认选中第一只股票 → 计算四大指标
4. 渲染四张图表
5. 用户切换股票 → 重新计算 + 重新渲染
6. 用户调整参数 → 仅重新计算该指标 + 单图重绘
```

#### 3.1.3 股票切换优化

- 切换股票时**全量重绘**所有图表（因为数据变了）
- 使用 `echartsInstance.setOption(option, { notMerge: true })` 确保干净重置
- 可考虑添加 loading 动画（实际上 JSON 已在内存中，切换是瞬时的）

### 3.2 控制面板

#### 3.2.1 布局

```
┌──────────────────────────────────────────────────────────────┐
│  🔬 技术指标交互分析工具                                      │
│  ┌──────────┐ ┌──────────────┐ ┌────────────────────────┐   │
│  │ 📊 股票  │ │ 📅 数据范围  │ │ ⚙️ 全局设置           │   │
│  │ [▼ 绿的  │ │ 2025-07-04   │ │ ☐ 显示成交量           │   │
│  │   谐波  ] │ │   ~ 至今     │ │ ☐ 启用十字光标联动     │   │
│  └──────────┘ └──────────────┘ └────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

#### 3.2.2 股票选择器

- 下拉菜单 `<select>`，显示 "股票代码 - 股票名称"
- 选中的股票名称同时显示在主图标题中
- 附带最近收盘价、涨跌幅简况（从数据中计算）

#### 3.2.3 全局设置

| 设置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| 显示成交量 | Checkbox | 勾选 | 控制主图中是否显示成交量副图 |
| 十字光标联动 | Checkbox | 勾选 | 鼠标悬停时四张图同步显示十字线 |
| 日期范围 | 双滑块 / 日期选择 | 全部 | 支持缩放到特定日期区间 |

### 3.3 指标参数面板

每个指标子图**右侧**附带一个紧凑的参数面板，浮动或内嵌在图表旁。

```
┌──────────────────────────────────┬──────────┐
│                                  │ RSI 参数 │
│         RSI 图表区域              │ ──────── │
│                                  │ 周期 N   │
│                                  │ [14] ▸◂  │
│                                  │ 超买阈值 │
│                                  │ [70] ▸◂  │
│                                  │ 超卖阈值 │
│                                  │ [30] ▸◂  │
│                                  │          │
│                                  │ [重置]   │
└──────────────────────────────────┴──────────┘
```

#### 3.3.1 RSI 参数

| 参数 | 控件 | 默认值 | 范围 | 步长 |
|------|------|--------|------|------|
| 周期 N | 数字输入 + 滑块 | 14 | 2 ~ 100 | 1 |
| 超买阈值 | 数字输入 + 滑块 | 70 | 50 ~ 100 | 1 |
| 超卖阈值 | 数字输入 + 滑块 | 30 | 0 ~ 50 | 1 |
| 多线模式 | Checkbox | 关闭 | - | - |

> 多线模式：同时显示 N=6, 14, 24 三条 RSI 线（历史对照）

#### 3.3.2 MACD 参数

| 参数 | 控件 | 默认值 | 范围 | 步长 |
|------|------|--------|------|------|
| 快线周期 | 数字输入 + 滑块 | 12 | 2 ~ 100 | 1 |
| 慢线周期 | 数字输入 + 滑块 | 26 | 3 ~ 200 | 1 |
| 信号线周期 | 数字输入 + 滑块 | 9 | 2 ~ 50 | 1 |

#### 3.3.3 布林带参数

| 参数 | 控件 | 默认值 | 范围 | 步长 |
|------|------|--------|------|------|
| 中轨周期 N | 数字输入 + 滑块 | 20 | 2 ~ 100 | 1 |
| 标准差倍数 K | 数字输入 + 滑块 | 2.0 | 0.5 ~ 5.0 | 0.1 |
| 移动平均类型 | 下拉选择 | SMA | SMA / EMA | - |

> 布林带渲染在主图（K线图）上，而非独立子图

#### 3.3.4 ATR 参数

| 参数 | 控件 | 默认值 | 范围 | 步长 |
|------|------|--------|------|------|
| 周期 N | 数字输入 + 滑块 | 14 | 2 ~ 100 | 1 |
| 平滑方式 | 下拉选择 | EMA | SMA / EMA / Wilder | - |

### 3.4 图表绘制引擎

#### 3.4.1 整体布局（四图纵排）

```
┌─────────────────────────────────────────┐
│  [主图] K线 + 布林带 + 成交量 (60%高度)  │
│  ├─ 蜡烛图 (涨红跌绿)                    │
│  ├─ 布林带三轨叠加                       │
│  └─ 成交量柱状图 (下挂副图)              │
├─────────────────────────────────────────┤
│  [子图1] RSI (约13%高度)                 │
│  ├─ RSI 曲线                             │
│  ├─ 超买线(70) / 超卖线(30)              │
│  ├─ 中轴线(50)                           │
│  └─ 超买/超卖区域半透明填充              │
├─────────────────────────────────────────┤
│  [子图2] MACD (约13%高度)                │
│  ├─ DIF 曲线                             │
│  ├─ DEA 曲线                             │
│  ├─ 柱状图 (正红负绿)                    │
│  └─ 零轴                                  │
├─────────────────────────────────────────┤
│  [子图3] ATR (约13%高度)                 │
│  ├─ ATR 曲线 (深蓝色)                    │
│  └─ 可选: ATR% (ATR/close) 副线         │
└─────────────────────────────────────────┘
```

#### 3.4.2 ECharts 配置要点

| 配置项 | 值 | 说明 |
|--------|-----|------|
| grid 联动 | 四图共用 X 轴 `axisPointer.link` | 鼠标悬停同步 |
| dataZoom | 底部统一滑块 | 缩放 & 平移 |
| tooltip | `trigger: 'axis'` | 坐标轴触发 |
| 配色 | 红 `#DC143C` / 绿 `#228B22` | A股惯例 |

#### 3.4.3 十字光标联动实现

```javascript
// 核心思路：四张图都连接同一个 axisPointer group
echarts.connect([chartKline, chartRSI, chartMACD, chartATR]);
// 或在各自 option 中设置：
axisPointer: { link: [{ xAxisIndex: 'all' }] }
```

### 3.5 参数调整 → 重绘机制

```
用户拖拽滑块 / 修改输入框
        │
        ▼
    onChange 事件 (防抖 200ms)
        │
        ▼
    重新计算该指标 (纯 JS 运算)
        │
        ▼
    chart.setOption(新option)
    (仅更新对应图表，不重绘整页)
```

#### 3.5.1 性能考虑

- 近一年数据约 250 条日线，四条指标计算 < 5ms
- 防抖延迟 200ms，避免拖动滑块时频繁重绘
- 使用 `setOption` 的增量更新模式（默认行为，速度极快）

#### 3.5.2 重置按钮

每个参数面板附带一个「**重置默认值**」按钮，一键恢复出厂参数。

---

## 4. 指标计算规范（JavaScript 实现参考）

### 4.1 RSI

```javascript
function computeRSI(closes, period = 14) {
  const gains = [], losses = [], rsi = [];
  for (let i = 1; i < closes.length; i++) {
    const delta = closes[i] - closes[i - 1];
    gains.push(delta > 0 ? delta : 0);
    losses.push(delta < 0 ? -delta : 0);
  }
  // Wilder's smoothed average
  let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
  let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;
  rsi.push(100 - 100 / (1 + avgGain / Math.max(avgLoss, 1e-10)));
  for (let i = period; i < gains.length; i++) {
    avgGain = (avgGain * (period - 1) + gains[i]) / period;
    avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
    rsi.push(100 - 100 / (1 + avgGain / Math.max(avgLoss, 1e-10)));
  }
  return rsi; // 长度 = closes.length - period
}
```

### 4.2 MACD

```javascript
function computeEMA(values, period) {
  const k = 2 / (period + 1);
  const ema = [values[0]];
  for (let i = 1; i < values.length; i++) {
    ema.push(values[i] * k + ema[i - 1] * (1 - k));
  }
  return ema;
}

function computeMACD(closes, fast = 12, slow = 26, signal = 9) {
  const emaFast = computeEMA(closes, fast);
  const emaSlow = computeEMA(closes, slow);
  const dif = emaFast.map((v, i) => v - emaSlow[i]);
  const dea = computeEMA(dif, signal);
  const histogram = dif.map((v, i) => v - dea[i]);
  return { dif, dea, histogram };
}
```

### 4.3 布林带

```javascript
function computeSMA(values, period) {
  const sma = [];
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) { sma.push(null); continue; }
    const slice = values.slice(i - period + 1, i + 1);
    sma.push(slice.reduce((a, b) => a + b, 0) / period);
  }
  return sma;
}

function computeBollinger(closes, period = 20, multiplier = 2.0, maType = 'SMA') {
  const mid = maType === 'SMA' ? computeSMA(closes, period) : computeEMA(closes, period);
  const upper = [], lower = [], bandwidth = [], percentB = [];
  for (let i = 0; i < closes.length; i++) {
    if (mid[i] === null || mid[i] === undefined) {
      upper.push(null); lower.push(null); bandwidth.push(null); percentB.push(null);
      continue;
    }
    const slice = closes.slice(Math.max(0, i - period + 1), i + 1);
    const std = Math.sqrt(slice.reduce((s, v) => s + (v - mid[i]) ** 2, 0) / slice.length);
    upper.push(mid[i] + multiplier * std);
    lower.push(mid[i] - multiplier * std);
    bandwidth.push(((upper[i] - lower[i]) / mid[i]) * 100);
    percentB.push((closes[i] - lower[i]) / (upper[i] - lower[i]));
  }
  return { mid, upper, lower, bandwidth, percentB };
}
```

### 4.4 ATR

```javascript
function computeATR(highs, lows, closes, period = 14, smoothType = 'EMA') {
  const tr = [highs[0] - lows[0]];
  for (let i = 1; i < closes.length; i++) {
    tr.push(Math.max(
      highs[i] - lows[i],
      Math.abs(highs[i] - closes[i - 1]),
      Math.abs(lows[i] - closes[i - 1])
    ));
  }
  if (smoothType === 'EMA') return computeEMA(tr, period);
  if (smoothType === 'Wilder') {
    // Wilder: ATR[period-1] = avg(first period TRs),
    // then ATR[i] = (ATR[i-1] * (period-1) + TR[i]) / period
    const atr = tr.slice(0, period).reduce((a, b) => a + b, 0) / period;
    const result = Array(period - 1).fill(null);
    result.push(atr);
    for (let i = period; i < tr.length; i++) {
      result.push((result[result.length - 1] * (period - 1) + tr[i]) / period);
    }
    return result;
  }
  return computeSMA(tr, period);
}
```

---

## 5. 界面设计详述

### 5.1 配色方案

| 颜色角色 | 色值 | 用途 |
|---------|------|------|
| 阳线上涨 | `#DC143C` (Crimson) | K线阳线、MACD 正柱 |
| 阴线下跌 | `#228B22` (ForestGreen) | K线阴线、MACD 负柱 |
| 布林上/下轨 | `rgba(128,128,128,0.3)` | 半透明填充带 |
| 布林中轨 | `#FF8C00` (DarkOrange) | 移动平均线 |
| RSI 曲线 | `#6A5ACD` (SlateBlue) | RSI 主线 |
| RSI 超买带 | `rgba(220,20,60,0.08)` | 半透明红 |
| RSI 超卖带 | `rgba(34,139,34,0.08)` | 半透明绿 |
| MACD DIF | `#FF6347` (Tomato) | 快线 |
| MACD DEA | `#4169E1` (RoyalBlue) | 信号线 |
| ATR 曲线 | `#2F4F4F` (DarkSlateGray) | 波动率 |
| 背景 | `#FFFFFF` | 白色（白天主题） |
| 网格线 | `#E8E8E8` | 浅灰 |
| 面板背景 | `#F8F9FA` | 浅灰白 |

### 5.2 字体

- 标题: 'PingFang SC', 'Microsoft YaHei', sans-serif, 18px bold
- 图表内文字: 12px
- 参数标签: 13px
- 数据标签（tooltip）: 12px monospace

### 5.3 响应式设计

- 最小宽度：1024px（不建议更小，金融图表需要空间）
- 图表宽度：100% 容器宽度
- 参数面板：固定 220px 宽，或在小屏幕折叠为悬浮面板

### 5.4 交互细节

| 交互 | 行为 |
|------|------|
| 鼠标悬停 K线 | 十字光标同步出现在四张图上 |
| 底部 dataZoom 拖拽 | 四张图同步缩放 & 平移 |
| 参数滑块拖拽 | 松开后 200ms 防抖触发重算 |
| 数字输入框失焦 | 立即触发重算 |
| 切换股票 | 全部图表 + 标题更新 |
| 重置按钮 | 恢复默认参数 + 重绘 |

---

## 6. 文件结构

```
Task2/
├── SPEC_技术指标分析工具_HTML版.md      # 本文档（设计规格书）
├── tech_indicator_tool/
│   ├── index.html                       # 主页面（核心产出）
│   ├── css/
│   │   └── style.css                    # 样式文件
│   ├── js/
│   │   ├── indicators.js                # 四大指标计算函数
│   │   ├── charts.js                    # ECharts 初始化和渲染逻辑
│   │   ├── controls.js                  # 控制面板事件绑定
│   │   └── main.js                      # 入口 + 数据加载
│   └── data/
│       ├── stocks.json                  # 预获取的股票数据
│       └── fetch_data.py                # Tushare 数据获取脚本
└── outputs/                             # （可选）导出图表截图
```

---

## 7. 数据获取脚本设计

### 7.1 fetch_data.py 流程

```python
# 使用 Tushare MCP 逐个获取 5 只股票的日线数据
# 时间范围：近 365 个自然日（约 250 个交易日）
# 输出：tech_indicator_tool/data/stocks.json

STOCKS = [
    ("688017.SH", "绿的谐波"),
    ("688256.SH", "寒武纪"),
    ("002896.SZ", "中大力德"),
    ("002472.SZ", "双环传动"),
    ("688981.SH", "中芯国际"),
]

# 步骤：
# 1. 计算起始日期（当前日期 - 365天）
# 2. 逐个调用 Tushare daily 接口
# 3. 字段映射：ts_code, trade_date → date, open, high, low, close, vol → volume
# 4. 按日期升序排列
# 5. 合并输出 JSON
```

### 7.2 数据更新策略

- **首次使用**：运行 `fetch_data.py` 生成 `stocks.json`
- **数据过旧**（> 1周）：重新运行脚本刷新
- **可扩展性**：添加新股只需在脚本的 `STOCKS` 列表追加一行

---

## 8. 验收标准

### 8.1 功能验收

- [ ] 5 只股票均可通过下拉菜单切换，数据正确加载
- [ ] RSI 图表正确渲染，超买/超卖线、半透明区域正常显示
- [ ] MACD 图表正确渲染，DIF/DEA/柱状图 + 零轴
- [ ] 布林带在主图 K 线上正确叠加，三轨可见
- [ ] ATR 图表正确渲染
- [ ] 四张图十字光标联动正常（鼠标悬停同步）
- [ ] 底部 dataZoom 拖拽四图同步缩放
- [ ] RSI 参数（周期/阈值）调整后图表正确重绘
- [ ] MACD 参数（快/慢/信号周期）调整后图表正确重绘
- [ ] 布林带参数（周期/倍数）调整后图表正确重绘
- [ ] ATR 参数（周期/平滑方式）调整后图表正确重绘
- [ ] 每个指标的「重置默认值」按钮正常工作
- [ ] 浏览器直接双击 `index.html` 即可运行（不需要 HTTP 服务器）

### 8.2 视觉验收

- [ ] A股惯例：涨红跌绿，全图颜色一致
- [ ] 中文字体正常显示，无乱码
- [ ] 图例清晰，各线条可区分
- [ ] 整体布局紧凑但不拥挤
- [ ] 参数面板与图表区域比例协调

### 8.3 性能验收

- [ ] 页面首次加载 < 2 秒
- [ ] 股票切换响应 < 200ms
- [ ] 参数调整后图表重绘 < 100ms

---

## 9. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| JSON 文件过大（5只 × 250行） | 首次加载慢 | 约 200KB，可接受；如需优化用 gzip |
| ECharts CDN 不可用 | 无法渲染 | 提供本地 fallback echarts.min.js |
| 浏览器兼容性 | 部分用户用 IE | 提示使用 Chrome/Edge/Firefox |
| 十字光标联动不同步 | 影响体验 | 使用 `echarts.connect()` API |
| Tushare 接口限流 | 获取数据慢 | 数据预获取，不实时调用 |

---

## 10. 后续扩展规划

| 阶段 | 内容 |
|------|------|
| Phase 2 | 增加 KDJ、OBV、CCI 指标 |
| Phase 3 | 支持自定义股票（输入代码查询） |
| Phase 4 | 多股票同指标对比模式 |
| Phase 5 | 导出分析报告（PDF/PNG） |
| Phase 6 | 暗色主题切换 |
| Phase 7 | PWA 离线支持 |

---

> **本文档为产品设计阶段产出，开发将在设计确认后启动。**
