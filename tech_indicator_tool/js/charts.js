/**
 * charts.js — ECharts 图表初始化与渲染逻辑
 * 四图纵排：K线+布林带(主) / RSI / MACD / ATR
 * 十字光标联动、dataZoom 同步
 */

// A股配色: 涨红跌绿
const COLORS = {
  up: '#DC143C',
  down: '#228B22',
  bollMid: '#FF8C00',
  bollBand: 'rgba(128,128,128,0.25)',
  rsi: '#6A5ACD',
  rsiOverbought: 'rgba(220,20,60,0.06)',
  rsiOversold: 'rgba(34,139,34,0.06)',
  macdDif: '#FF6347',
  macdDea: '#4169E1',
  macdPos: '#DC143C',
  macdNeg: '#228B22',
  atr: '#2F4F4F',
  volumeUp: 'rgba(220,20,60,0.35)',
  volumeDown: 'rgba(34,139,34,0.30)',
  gridLine: '#E8E8E8',
};

// ─────────────────── 初始化 ───────────────────
let charts = {};
let currentData = null;

function initCharts(domIds) {
  charts.main = echarts.init(document.getElementById(domIds.main));
  charts.rsi = echarts.init(document.getElementById(domIds.rsi));
  charts.macd = echarts.init(document.getElementById(domIds.macd));
  charts.atr = echarts.init(document.getElementById(domIds.atr));

  // 十字光标联动
  echarts.connect([charts.main, charts.rsi, charts.macd, charts.atr]);

  // 窗口自适应
  window.addEventListener('resize', () => {
    Object.values(charts).forEach(c => c.resize());
  });
}

// ─────────────────── 通用 dataZoom ───────────────────
function getDataZoom(totalLen) {
  return [
    {
      type: 'slider',
      xAxisIndex: [0],
      realtime: false,
      start: Math.max(0, 100 - 120 / totalLen * 100),
      end: 100,
      bottom: 0,
      height: 16,
      borderColor: '#ddd',
      backgroundColor: 'transparent',
      fillerColor: 'rgba(83,74,183,0.1)',
      handleStyle: { color: '#534AB7' },
      textStyle: { fontSize: 10 },
    },
    {
      type: 'inside',
      xAxisIndex: [0],
    },
  ];
}

// ─────────────────── Grid 工具 ───────────────────
function makeGrid(height, top, leftExtra) {
  return {
    left: (leftExtra || 56),
    right: 16,
    top: top || 8,
    height: height,
    backgroundColor: '#FFFFFF',
  };
}

// ─────────────────── 1. 主图: K线 + 布林带 + 成交量 ───────────────────
function renderMainChart(data, bollParams) {
  const { dates, opens, highs, lows, closes, volumes } = data;
  const bollBand = computeBollinger(closes, bollParams.period, bollParams.multiplier, bollParams.maType);

  // K线数据
  const klineData = dates.map((_, i) => [opens[i], closes[i], lows[i], highs[i]]);

  // 成交量颜色
  const volColors = [];
  for (let i = 0; i < volumes.length; i++) {
    const isUp = i === 0 ? true : closes[i] >= closes[i - 1];
    volColors.push(isUp ? COLORS.volumeUp : COLORS.volumeDown);
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      makeGrid('70%', 6),       // K-line + Bollinger
      makeGrid('22%', '72%'),   // Volume
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { show: false }, splitLine: { show: false } },
      { type: 'category', data: dates, gridIndex: 1, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { show: false }, splitLine: { show: false } },
    ],
    yAxis: [
      { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: COLORS.gridLine, type: 'dashed' } }, axisLabel: { fontSize: 11 } },
      {
        scale: true, gridIndex: 1, splitLine: { show: false }, axisLabel: { show: true, fontSize: 10, color: '#999' },
        position: 'right', name: 'Vol', nameTextStyle: { fontSize: 10, color: '#999' },
      },
    ],
    dataZoom: getDataZoom(dates.length),
    series: [
      {
        name: 'K线', type: 'candlestick', xAxisIndex: 0, yAxisIndex: 0,
        data: klineData,
        itemStyle: { color: COLORS.up, color0: COLORS.down, borderColor: COLORS.up, borderColor0: COLORS.down },
      },
      {
        name: 'BOLL UPPER', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: bollBand.upper, smooth: true, symbol: 'none',
        lineStyle: { width: 1, color: 'rgba(128,128,128,0.45)', type: 'dashed' }, z: 2,
      },
      {
        name: 'BOLL MID', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: bollBand.mid, smooth: true, symbol: 'none',
        lineStyle: { width: 1.5, color: COLORS.bollMid }, z: 2,
      },
      {
        name: 'BOLL LOWER', type: 'line', xAxisIndex: 0, yAxisIndex: 0,
        data: bollBand.lower, smooth: true, symbol: 'none',
        lineStyle: { width: 1, color: 'rgba(128,128,128,0.45)', type: 'dashed' },
        areaStyle: {
          color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [{ offset: 0, color: COLORS.bollBand }, { offset: 1, color: 'rgba(128,128,128,0.02)' }] },
        }, z: 1,
      },
      {
        name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1,
        data: volumes.map((v, i) => ({ value: v, itemStyle: { color: volColors[i], borderColor: 'transparent' } })),
        barWidth: '50%', z: 0,
      },
    ],
  };

  charts.main.setOption(option, { notMerge: true });
}

// ─────────────────── 2. RSI ───────────────────
function renderRSI(data, params) {
  const { dates, closes } = data;
  const period = params.period || 14;
  const overbought = params.overbought || 70;
  const oversold = params.oversold || 30;
  const multiLine = params.multiLine || false;

  const rsiValues = computeRSI(closes, period);

  const series = [
    {
      name: `RSI(${period})`,
      type: 'line',
      data: rsiValues,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 1.5, color: COLORS.rsi },
      markLine: {
        silent: true,
        symbol: 'none',
        data: [
          { yAxis: overbought, label: { formatter: `${overbought} 超买`, color: '#DC143C', fontSize: 10, position: 'insideEndTop' }, lineStyle: { color: 'rgba(220,20,60,0.4)', type: 'dashed', width: 1 } },
          { yAxis: oversold, label: { formatter: `${oversold} 超卖`, color: '#228B22', fontSize: 10, position: 'insideEndBottom' }, lineStyle: { color: 'rgba(34,139,34,0.4)', type: 'dashed', width: 1 } },
          { yAxis: 50, label: { formatter: '50', color: '#999', fontSize: 9, position: 'insideEndTop' }, lineStyle: { color: COLORS.gridLine, width: 0.5 } },
        ],
      },
      markArea: {
        silent: true,
        data: [
          [{ yAxis: overbought }, { yAxis: 100, itemStyle: { color: COLORS.rsiOverbought } }],
          [{ yAxis: 0 }, { yAxis: oversold, itemStyle: { color: COLORS.rsiOversold } }],
        ],
      },
    },
  ];

  // 多线模式
  if (multiLine) {
    [6, 24].forEach((p) => {
      if (p === period) return;
      const vals = computeRSI(closes, p);
      series.push({
        name: `RSI(${p})`,
        type: 'line',
        data: vals,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1, type: 'dotted', color: p === 6 ? '#FFB6C1' : '#DDA0DD' },
      });
    });
  }

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
    },
    grid: [makeGrid('85%', 6)],
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      min: 0,
      max: 100,
      splitLine: { lineStyle: { color: COLORS.gridLine, type: 'dashed' } },
      axisLabel: { fontSize: 11 },
    },
    dataZoom: getDataZoom(dates.length),
    series: series,
  };

  charts.rsi.setOption(option, { notMerge: true });
}

// ─────────────────── 3. MACD ───────────────────
function renderMACD(data, params) {
  const { dates, closes } = data;
  const fast = params.fast || 12;
  const slow = params.slow || 26;
  const signal = params.signal || 9;

  const macd = computeMACD(closes, fast, slow, signal);

  const barColors = macd.histogram.map(v => v >= 0 ? COLORS.macdPos : COLORS.macdNeg);

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
    },
    grid: [makeGrid('85%', 6)],
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { show: false },
      splitLine: { show: false },
    },
    yAxis: {
      scale: true,
      splitLine: { lineStyle: { color: COLORS.gridLine, type: 'dashed' } },
      axisLabel: { fontSize: 11 },
    },
    dataZoom: getDataZoom(dates.length),
    series: [
      {
        name: 'DIF',
        type: 'line',
        data: macd.dif,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1.5, color: COLORS.macdDif },
      },
      {
        name: 'DEA',
        type: 'line',
        data: macd.dea,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1.5, color: COLORS.macdDea },
      },
      {
        name: 'MACD柱',
        type: 'bar',
        data: macd.histogram.map((v, i) => ({ value: v, itemStyle: { color: barColors[i] } })),
        barWidth: '55%',
      },
    ],
  };

  charts.macd.setOption(option, { notMerge: true });
}

// ─────────────────── 4. ATR ───────────────────
function renderATR(data, params) {
  const { dates, highs, lows, closes } = data;
  const period = params.period || 14;
  const smoothType = params.smoothType || 'EMA';

  const { atr } = computeATR(highs, lows, closes, period, smoothType);

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', label: { backgroundColor: '#6a7985' } },
    },
    grid: [makeGrid('85%', 6)],
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { fontSize: 11, interval: Math.max(1, Math.floor(dates.length / 8)) },
      splitLine: { show: false },
    },
    yAxis: {
      scale: true,
      splitLine: { lineStyle: { color: COLORS.gridLine, type: 'dashed' } },
      axisLabel: { fontSize: 11 },
    },
    dataZoom: getDataZoom(dates.length),
    series: [
      {
        name: `ATR(${period})`,
        type: 'line',
        data: atr,
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 1.5, color: COLORS.atr },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(47,79,79,0.15)' },
              { offset: 1, color: 'rgba(47,79,79,0.02)' },
            ],
          },
        },
      },
    ],
  };

  charts.atr.setOption(option, { notMerge: true });
}

// ─────────────────── 全量渲染入口 ───────────────────
function renderAll(data, params) {
  currentData = data;
  renderMainChart(data, params.boll);
  renderRSI(data, params.rsi);
  renderMACD(data, params.macd);
  renderATR(data, params.atr);
}
