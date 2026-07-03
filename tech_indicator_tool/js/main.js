/**
 * main.js — 入口文件
 * 加载 JSON 数据 → 初始化图表 → 绑定事件
 */

let stockDataMap = {};
let currentStockCode = null;

// ─────────────────── 数据加载 ───────────────────
async function loadStockData() {
  try {
    const resp = await fetch('data/stocks.json');
    const json = await resp.json();

    const stocks = json.stocks;
    for (const [tsCode, info] of Object.entries(stocks)) {
      const d = info.data;
      stockDataMap[tsCode] = {
        name: info.name,
        tsCode: tsCode,
        dates: d.map(r => r.date),
        opens: d.map(r => r.open),
        highs: d.map(r => r.high),
        lows: d.map(r => r.low),
        closes: d.map(r => r.close),
        volumes: d.map(r => r.volume),
        amounts: d.map(r => r.amount),
      };
    }

    // 填充股票下拉列表
    const select = document.getElementById('stock-select');
    select.innerHTML = '';
    for (const [tsCode, info] of Object.entries(stocks)) {
      const opt = document.createElement('option');
      opt.value = tsCode;
      opt.textContent = `${tsCode}  ${info.name}`;
      select.appendChild(opt);
    }

    // 默认选中第一只股票
    currentStockCode = Object.keys(stocks)[0];
    select.value = currentStockCode;

    return json.meta;
  } catch (err) {
    console.error('加载股票数据失败:', err);
    document.getElementById('app').innerHTML = `
      <div style="text-align:center;padding:4rem;color:#999;">
        <h2>数据加载失败</h2>
        <p>请确保 data/stocks.json 文件存在且格式正确。</p>
        <p style="font-size:12px;color:#DC143C;">${err.message}</p>
      </div>
    `;
    throw err;
  }
}

// ─────────────────── 参数变化回调 ───────────────────
function onParamChange() {
  const data = stockDataMap[currentStockCode];
  if (!data) return;
  updateHeader(data);
  renderAll(data, paramState);
  updateSummary(data, paramState);
}

// ─────────────────── 更新标头信息 ───────────────────
function updateHeader(data) {
  const badge = document.getElementById('stock-badge');
  const dateRange = document.getElementById('date-range');
  const priceLast = document.getElementById('price-last');
  const priceChange = document.getElementById('price-change');

  badge.textContent = `${data.name} ${data.tsCode}`;

  const dates = data.dates;
  dateRange.textContent = `${dates[0]} ~ ${dates[dates.length - 1]}`;

  const lastClose = data.closes[data.closes.length - 1];
  const prevClose = data.closes[data.closes.length - 2] || lastClose;
  const change = (lastClose - prevClose).toFixed(2);
  const pctChg = ((lastClose - prevClose) / prevClose * 100).toFixed(2);

  priceLast.textContent = lastClose.toFixed(2);
  const isUp = change >= 0;
  priceChange.textContent = `${isUp ? '+' : ''}${change} (${isUp ? '+' : ''}${pctChg}%)`;
  priceChange.className = `change ${isUp ? 'up' : 'down'}`;
  priceLast.style.color = isUp ? '#DC143C' : '#228B22';
}

// ─────────────────── 启动 ───────────────────
async function main() {
  // 缓存 DOM
  cacheDom();

  // 加载数据
  const meta = await loadStockData();
  console.log(`数据已加载: ${meta.date_range[0]} ~ ${meta.date_range[1]}, ${meta.total_stocks} 只股票`);

  // 初始化图表
  initCharts({
    main: 'chart-main',
    rsi: 'chart-rsi',
    macd: 'chart-macd',
    atr: 'chart-atr',
  });

  // 绑定事件
  bindParamEvents(onParamChange);
  bindStockSelect(onParamChange);

  // 绑定重置按钮
  ['rsi', 'macd', 'boll', 'atr'].forEach(type => {
    const btn = document.getElementById(`reset-${type}`);
    if (btn) {
      btn.addEventListener('click', () => {
        resetParams(type);
        onParamChange();
      });
    }
  });

  // 首次渲染
  currentStockCode = document.getElementById('stock-select').value;
  const data = stockDataMap[currentStockCode];
  if (data) {
    renderAll(data, paramState);
    updateSummary(data, paramState);
  }
}

// DOM 就绪后启动
document.addEventListener('DOMContentLoaded', main);
