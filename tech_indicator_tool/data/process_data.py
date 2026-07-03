import json
from datetime import datetime, timedelta

STOCK_NAMES = {
    "688017.SH": "绿的谐波",
    "688256.SH": "寒武纪",
    "002896.SZ": "中大力德",
    "002472.SZ": "双环传动",
    "688981.SH": "中芯国际",
}

with open("raw_data.json", "r", encoding="utf-8") as f:
    raw = json.load(f)

stocks = {}
for item in raw:
    ts_code = item["ts_code"]
    if ts_code not in stocks:
        stocks[ts_code] = {
            "name": STOCK_NAMES.get(ts_code, ts_code),
            "data": []
        }
    stocks[ts_code]["data"].append({
        "date": f"{item['trade_date'][:4]}-{item['trade_date'][4:6]}-{item['trade_date'][6:]}",
        "open": item["open"],
        "high": item["high"],
        "low": item["low"],
        "close": item["close"],
        "volume": int(item["vol"]),
        "amount": item["amount"],
        "change": item["change"],
        "pct_chg": item["pct_chg"]
    })

for ts_code in stocks:
    stocks[ts_code]["data"].sort(key=lambda x: x["date"])

# Compute min/max dates
all_dates = []
for s in stocks.values():
    all_dates.extend([d["date"] for d in s["data"]])
all_dates.sort()

with open("stocks.json", "w", encoding="utf-8") as f:
    json.dump({
        "meta": {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date_range": [all_dates[0], all_dates[-1]],
            "total_stocks": len(stocks)
        },
        "stocks": stocks
    }, f, ensure_ascii=False, indent=2)

print(f"Done! Processed {len(stocks)} stocks, date range: {all_dates[0]} ~ {all_dates[-1]}")
for ts_code, s in stocks.items():
    print(f"  {ts_code} {s['name']}: {len(s['data'])} rows")
