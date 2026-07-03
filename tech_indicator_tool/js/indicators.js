/**
 * indicators.js — 四大技术指标纯前端计算
 * RSI / MACD / Bollinger Bands / ATR
 */

// ─────────────────────── Helper: EMA ───────────────────────
function computeEMA(values, period) {
  const k = 2 / (period + 1);
  const ema = [values[0]];
  for (let i = 1; i < values.length; i++) {
    ema.push(values[i] * k + ema[i - 1] * (1 - k));
  }
  return ema;
}

// ─────────────────────── Helper: SMA ───────────────────────
function computeSMA(values, period) {
  const sma = [];
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      sma.push(NaN);
      continue;
    }
    let sum = 0;
    for (let j = i - period + 1; j <= i; j++) sum += values[j];
    sma.push(sum / period);
  }
  return sma;
}

// ─────────────────────── 1. RSI ───────────────────────
function computeRSI(closes, period) {
  if (closes.length < period + 1) return closes.map(() => NaN);

  const gains = [], losses = [];
  for (let i = 1; i < closes.length; i++) {
    const delta = closes[i] - closes[i - 1];
    gains.push(delta > 0 ? delta : 0);
    losses.push(delta < 0 ? -delta : 0);
  }

  // Wilder's smoothed average
  let avgGain = gains.slice(0, period).reduce((a, b) => a + b, 0) / period;
  let avgLoss = losses.slice(0, period).reduce((a, b) => a + b, 0) / period;

  const rsiArr = new Array(closes.length).fill(NaN);
  rsiArr[period] = 100 - 100 / (1 + avgGain / Math.max(avgLoss, 1e-10));

  for (let i = period; i < gains.length; i++) {
    avgGain = (avgGain * (period - 1) + gains[i]) / period;
    avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
    rsiArr[i + 1] = 100 - 100 / (1 + avgGain / Math.max(avgLoss, 1e-10));
  }
  return rsiArr;
}

// ─────────────────────── 2. MACD ───────────────────────
function computeMACD(closes, fastPeriod, slowPeriod, signalPeriod) {
  const emaFast = computeEMA(closes, fastPeriod);
  const emaSlow = computeEMA(closes, slowPeriod);
  const dif = emaFast.map((v, i) => v - emaSlow[i]);
  const dea = computeEMA(dif, signalPeriod);
  const histogram = dif.map((v, i) => v - dea[i]);
  return { dif, dea, histogram };
}

// ─────────────────────── 3. Bollinger Bands ───────────────────────
function computeBollinger(closes, period, multiplier, maType) {
  const mid = maType === 'EMA' ? computeEMA(closes, period) : computeSMA(closes, period);
  const upper = [], lower = [];

  for (let i = 0; i < closes.length; i++) {
    if (isNaN(mid[i])) {
      upper.push(NaN);
      lower.push(NaN);
      continue;
    }
    const start = Math.max(0, i - period + 1);
    const slice = closes.slice(start, i + 1);
    const mean = mid[i];
    const variance = slice.reduce((s, v) => s + (v - mean) ** 2, 0) / slice.length;
    const std = Math.sqrt(variance);
    upper.push(mean + multiplier * std);
    lower.push(mean - multiplier * std);
  }
  return { mid, upper, lower };
}

// ─────────────────────── 4. ATR ───────────────────────
function computeATR(highs, lows, closes, period, smoothType) {
  const tr = [highs[0] - lows[0]];
  for (let i = 1; i < closes.length; i++) {
    tr.push(Math.max(
      highs[i] - lows[i],
      Math.abs(highs[i] - closes[i - 1]),
      Math.abs(lows[i] - closes[i - 1])
    ));
  }

  let result;
  if (smoothType === 'EMA') {
    result = computeEMA(tr, period);
  } else if (smoothType === 'Wilder') {
    const atrArr = new Array(closes.length).fill(NaN);
    const firstAvg = tr.slice(0, period).reduce((a, b) => a + b, 0) / period;
    atrArr[period - 1] = firstAvg;
    for (let i = period; i < tr.length; i++) {
      atrArr[i] = (atrArr[i - 1] * (period - 1) + tr[i]) / period;
    }
    result = atrArr;
  } else {
    result = computeSMA(tr, period);
  }
  return { atr: result, tr };
}
