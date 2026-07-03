# 项目记忆 - QuantStudy/Task1

## 项目概述
量化学习项目，当前任务聚焦于通过 Tushare 获取 A 股个股行情数据并进行可视化分析。

## 技术栈与约定
- 数据源：Tushare MCP（通过 DeferExecuteTool 调用 mcp__tushareMcp__daily 等）
- 可视化：ECharts 5.x（CDN），HTML 单文件输出
- Python：3.13.12 (managed)，仅用标准库处理数据
- 中国股市配色：涨红(#ee3333) 跌绿(#21ba45)
- Tushare 日期格式：YYYYMMDD（如 20250703）

## 已完成任务
- 2026-07-03：绿的谐波(688017.SH)近一年日线数据获取与 HTML 看板生成
