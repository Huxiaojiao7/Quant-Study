/**
 * controls.js — 控制面板事件绑定
 * 参数调整 → 防抖 → 重算 → 重绘
 */

// ─────────────────── 参数状态 ───────────────────
const paramState = {
  rsi: { period: 14, overbought: 70, oversold: 30, multiLine: false },
  macd: { fast: 12, slow: 26, signal: 9 },
  boll: { period: 20, multiplier: 2.0, maType: 'SMA' },
  atr: { period: 14, smoothType: 'EMA' },
};

// ─────────────────── DOM 引用缓存 ───────────────────
const dom = {};

function cacheDom() {
  dom.rsiPeriod = document.getElementById('rsi-period');
  dom.rsiOb = document.getElementById('rsi-ob');
  dom.rsiOs = document.getElementById('rsi-os');
  dom.rsiMulti = document.getElementById('rsi-multi');
  dom.macdFast = document.getElementById('macd-fast');
  dom.macdSlow = document.getElementById('macd-slow');
  dom.macdSignal = document.getElementById('macd-signal');
  dom.bollPeriod = document.getElementById('boll-period');
  dom.bollMultiplier = document.getElementById('boll-multiplier');
  dom.bollMaType = document.getElementById('boll-ma-type');
  dom.atrPeriod = document.getElementById('atr-period');
  dom.atrSmooth = document.getElementById('atr-smooth');
  dom.stockSelect = document.getElementById('stock-select');
  dom.showVolume = document.getElementById('show-volume');
  dom.crosshair = document.getElementById('crosshair');
  dom.rsiPeriodVal = document.getElementById('rsi-period-val');
  dom.rsiObVal = document.getElementById('rsi-ob-val');
  dom.rsiOsVal = document.getElementById('rsi-os-val');
  dom.macdFastVal = document.getElementById('macd-fast-val');
  dom.macdSlowVal = document.getElementById('macd-slow-val');
  dom.macdSignalVal = document.getElementById('macd-signal-val');
  dom.bollPeriodVal = document.getElementById('boll-period-val');
  dom.bollMultiplierVal = document.getElementById('boll-multiplier-val');
  dom.atrPeriodVal = document.getElementById('atr-period-val');
}

// ─────────────────── 防抖 ───────────────────
function debounce(fn, delay = 200) {
  let timer = null;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// ─────────────────── 同步数值显示 ───────────────────
function syncValue(inputId, displayId) {
  const input = document.getElementById(inputId);
  const display = document.getElementById(displayId);
  if (input && display) {
    input.addEventListener('input', () => {
      let val = input.value;
      if (input.step && input.step === '0.1') {
        val = parseFloat(val).toFixed(1);
      }
      display.textContent = val;
    });
  }
}

// ─────────────────── 绑定参数事件 ───────────────────
function bindParamEvents(onChange) {
  const onChangeDebounced = debounce(onChange, 200);

  // RSI
  dom.rsiPeriod.addEventListener('input', () => {
    paramState.rsi.period = parseInt(dom.rsiPeriod.value);
    dom.rsiPeriodVal.textContent = dom.rsiPeriod.value;
    onChangeDebounced();
  });
  dom.rsiOb.addEventListener('input', () => {
    paramState.rsi.overbought = parseInt(dom.rsiOb.value);
    dom.rsiObVal.textContent = dom.rsiOb.value;
    onChangeDebounced();
  });
  dom.rsiOs.addEventListener('input', () => {
    paramState.rsi.oversold = parseInt(dom.rsiOs.value);
    dom.rsiOsVal.textContent = dom.rsiOs.value;
    onChangeDebounced();
  });
  dom.rsiMulti.addEventListener('change', () => {
    paramState.rsi.multiLine = dom.rsiMulti.checked;
    onChange();
  });

  // MACD
  dom.macdFast.addEventListener('input', () => {
    paramState.macd.fast = parseInt(dom.macdFast.value);
    dom.macdFastVal.textContent = dom.macdFast.value;
    onChangeDebounced();
  });
  dom.macdSlow.addEventListener('input', () => {
    paramState.macd.slow = parseInt(dom.macdSlow.value);
    dom.macdSlowVal.textContent = dom.macdSlow.value;
    onChangeDebounced();
  });
  dom.macdSignal.addEventListener('input', () => {
    paramState.macd.signal = parseInt(dom.macdSignal.value);
    dom.macdSignalVal.textContent = dom.macdSignal.value;
    onChangeDebounced();
  });

  // 布林带
  dom.bollPeriod.addEventListener('input', () => {
    paramState.boll.period = parseInt(dom.bollPeriod.value);
    dom.bollPeriodVal.textContent = dom.bollPeriod.value;
    onChangeDebounced();
  });
  dom.bollMultiplier.addEventListener('input', () => {
    paramState.boll.multiplier = parseFloat(dom.bollMultiplier.value);
    dom.bollMultiplierVal.textContent = parseFloat(dom.bollMultiplier.value).toFixed(1);
    onChangeDebounced();
  });
  dom.bollMaType.addEventListener('change', () => {
    paramState.boll.maType = dom.bollMaType.value;
    onChange();
  });

  // ATR
  dom.atrPeriod.addEventListener('input', () => {
    paramState.atr.period = parseInt(dom.atrPeriod.value);
    dom.atrPeriodVal.textContent = dom.atrPeriod.value;
    onChangeDebounced();
  });
  dom.atrSmooth.addEventListener('change', () => {
    paramState.atr.smoothType = dom.atrSmooth.value;
    onChange();
  });

  // 全局控制
  dom.showVolume.addEventListener('change', onChange);
  dom.crosshair.addEventListener('change', () => {
    const connected = dom.crosshair.checked;
    if (connected) {
      echarts.connect([charts.main, charts.rsi, charts.macd, charts.atr]);
    } else {
      echarts.disconnect();
    }
  });
}

// ─────────────────── 重置参数 ───────────────────
function resetParams(type) {
  const defaults = {
    rsi: { period: 14, overbought: 70, oversold: 30, multiLine: false },
    macd: { fast: 12, slow: 26, signal: 9 },
    boll: { period: 20, multiplier: 2.0, maType: 'SMA' },
    atr: { period: 14, smoothType: 'EMA' },
  };

  const p = defaults[type];
  if (!p) return;

  switch (type) {
    case 'rsi':
      dom.rsiPeriod.value = p.period; dom.rsiPeriodVal.textContent = p.period;
      dom.rsiOb.value = p.overbought; dom.rsiObVal.textContent = p.overbought;
      dom.rsiOs.value = p.oversold; dom.rsiOsVal.textContent = p.oversold;
      dom.rsiMulti.checked = p.multiLine;
      break;
    case 'macd':
      dom.macdFast.value = p.fast; dom.macdFastVal.textContent = p.fast;
      dom.macdSlow.value = p.slow; dom.macdSlowVal.textContent = p.slow;
      dom.macdSignal.value = p.signal; dom.macdSignalVal.textContent = p.signal;
      break;
    case 'boll':
      dom.bollPeriod.value = p.period; dom.bollPeriodVal.textContent = p.period;
      dom.bollMultiplier.value = p.multiplier; dom.bollMultiplierVal.textContent = p.multiplier.toFixed(1);
      dom.bollMaType.value = p.maType;
      break;
    case 'atr':
      dom.atrPeriod.value = p.period; dom.atrPeriodVal.textContent = p.period;
      dom.atrSmooth.value = p.smoothType;
      break;
  }
  Object.assign(paramState[type], p);
}

// ─────────────────── 股票选择 ───────────────────
function bindStockSelect(onChange) {
  dom.stockSelect.addEventListener('change', () => {
    const tsCode = dom.stockSelect.value;
    const stockData = stockDataMap[tsCode];
    if (!stockData) return;
    renderAll(stockData, paramState);
    updateSummary(stockData, paramState);
  });
}

// ─────────────────── 更新汇总卡片 ───────────────────
function updateSummary(data, params) {
  const closes = data.closes;
  const lastClose = closes[closes.length - 1];

  // RSI
  const rsiVals = computeRSI(closes, params.rsi.period);
  const lastRSI = rsiVals[rsiVals.length - 1];
  document.getElementById('summary-rsi-val').textContent = isNaN(lastRSI) ? '--' : lastRSI.toFixed(1);
  const rsiText = lastRSI >= params.rsi.overbought ? '超买' : (lastRSI <= params.rsi.oversold ? '超卖' : '中性区间');
  document.getElementById('summary-rsi-desc').textContent = rsiText;
  document.getElementById('summary-rsi-val').style.color = lastRSI >= params.rsi.overbought ? '#DC143C' : (lastRSI <= params.rsi.oversold ? '#228B22' : 'inherit');

  // MACD 信号
  const macd = computeMACD(closes, params.macd.fast, params.macd.slow, params.macd.signal);
  const difLast = macd.dif[macd.dif.length - 1];
  const deaLast = macd.dea[macd.dea.length - 1];
  const difPrev = macd.dif[macd.dif.length - 2] || 0;
  const deaPrev = macd.dea[macd.dea.length - 2] || 0;
  let macdSignal = '--', macdDetail = '--';
  if (!isNaN(difLast) && !isNaN(deaLast)) {
    if (difPrev < deaPrev && difLast >= deaLast) {
      macdSignal = '金叉'; macdDetail = 'DIF 上穿 DEA';
    } else if (difPrev > deaPrev && difLast <= deaLast) {
      macdSignal = '死叉'; macdDetail = 'DIF 下穿 DEA';
    } else if (difLast > deaLast) {
      macdSignal = '多头'; macdDetail = 'DIF > DEA';
    } else {
      macdSignal = '空头'; macdDetail = 'DIF < DEA';
    }
  }
  document.getElementById('summary-macd-val').textContent = macdSignal;
  document.getElementById('summary-macd-desc').textContent = macdDetail;
  document.getElementById('summary-macd-val').style.color = macdSignal === '死叉' || macdSignal === '空头' ? '#228B22' : '#DC143C';

  // 布林带
  const boll = computeBollinger(closes, params.boll.period, params.boll.multiplier, params.boll.maType);
  const bollMid = boll.mid[boll.mid.length - 1];
  const bollUpper = boll.upper[boll.upper.length - 1];
  const bollLower = boll.lower[boll.lower.length - 1];
  if (!isNaN(bollMid) && !isNaN(bollUpper)) {
    const percentB = (lastClose - bollLower) / (bollUpper - bollLower);
    const posText = lastClose >= bollUpper ? '突破上轨' : (lastClose <= bollLower ? '跌破下轨' : '中轨上方');
    document.getElementById('summary-boll-val').textContent = lastClose >= bollMid ? '中轨上方' : '中轨下方';
    document.getElementById('summary-boll-desc').textContent = `%B = ${percentB.toFixed(2)}`;
  }

  // ATR
  const { atr } = computeATR(data.highs, data.lows, closes, params.atr.period, params.atr.smoothType);
  const lastATR = atr[atr.length - 1];
  document.getElementById('summary-atr-val').textContent = isNaN(lastATR) ? '--' : lastATR.toFixed(2);
  const atrPct = (lastATR / lastClose * 100);
  document.getElementById('summary-atr-desc').textContent = isNaN(atrPct) ? '--' : `ATR% = ${atrPct.toFixed(1)}%`;
}
