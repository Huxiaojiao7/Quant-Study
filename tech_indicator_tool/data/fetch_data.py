"""
fetch_data.py — 使用 Tushare 获取 5 只股票近一年日线数据

用法:
  python fetch_data.py

输出:
  data/stocks.json — 前端可以直接加载的格式

依赖:
  pip install tushare  (或通过 MCP 接口获取)
  
注意:
  本脚本需要 Tushare API Token (请设置 TUSHARE_TOKEN 环境变量)
  如果使用 WorkBuddy 内置的 Tushare MCP，可直接在 AI 对话中调用获取
"""

import os
import json
from datetime import datetime, timedelta

STOCKS = [
    ("688017.SH", "绿的谐波"),
    ("688256.SH", "寒武纪"),
    ("002896.SZ", "中大力德"),
    ("002472.SZ", "双环传动"),
    ("688981.SH", "中芯国际"),
]


def fetch_from_tushare_pro():
    """使用 Tushare Pro SDK 获取数据（备用方案）"""
    import tushare as ts

    token = os.environ.get("TUSHARE_TOKEN")
    if not token:
        print("请设置 TUSHARE_TOKEN 环境变量")
        return None

    ts.set_token(token)
    pro = ts.pro_api()

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

    result = {}
    for ts_code, name in STOCKS:
        print(f"正在获取 {name} ({ts_code}) ...")
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)

        if df.empty:
            print(f"  ⚠️ {name} 无数据")
            continue

        records = []
        for _, row in df.iterrows():
            records.append({
                "date": row["trade_date"][:4] + "-" + row["trade_date"][4:6] + "-" + row["trade_date"][6:],
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": int(row["vol"]),
                "amount": float(row["amount"]),
                "change": float(row["change"]),
                "pct_chg": float(row["pct_chg"]),
            })

        records.sort(key=lambda x: x["date"])
        result[ts_code] = {"name": name, "data": records}
        print(f"  ✓ {len(records)} 条记录")

    return result


def save_to_json(stocks_data, output_path="data/stocks.json"):
    if not stocks_data:
        print("没有数据可保存")
        return

    all_dates = []
    for s in stocks_data.values():
        all_dates.extend([d["date"] for d in s["data"]])
    all_dates.sort()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "date_range": [all_dates[0], all_dates[-1]],
                "total_stocks": len(stocks_data),
            },
            "stocks": stocks_data,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 数据已保存到 {output_path}")
    print(f"  共 {len(stocks_data)} 只股票, {len(all_dates)} 行数据")
    print(f"  时间范围: {all_dates[0]} ~ {all_dates[-1]}")


if __name__ == "__main__":
    stocks_data = fetch_from_tushare_pro()
    if stocks_data:
        save_to_json(stocks_data)
