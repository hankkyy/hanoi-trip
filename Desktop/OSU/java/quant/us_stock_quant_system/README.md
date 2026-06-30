# us_stock_quant_system

## 项目目的

`us_stock_quant_system` 是一个本地化、模块化、以美股日线低频交易为核心的量化系统。第一阶段目标不是追求最优策略，而是优先跑通完整工程闭环，包括数据获取、缓存、校验、指标计算、扫描、风控、回测、订单计划、dry-run、IBKR Paper Trading 对接和日常自动化。

## 风险声明

- 本系统不是投资建议。
- 默认不会进行真实交易。
- 回测收益不代表未来收益。
- 免费数据源可能存在延迟、缺失、复权差异和准确性问题。
- 真正实盘前必须使用更可靠的数据源。
- 真正实盘前必须进行长时间 paper trading 验证。
- IBKR Paper Trading 和 Live Trading 必须严格分开。
- 端口不能配错。
- 不要在 Live 账户里测试下单。
- 程序错误、网络错误、行情错误、滑点、跳空、TWS 断线、订单重复提交都可能导致真实亏损。

## 安装方法

项目要求 Python 3.11 或更高。当前工程已在 Python 3.14 环境下验证通过。

## 创建虚拟环境

```bash
cd us_stock_quant_system
python3 -m venv .venv
source .venv/bin/activate
```

## 安装依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 配置 `.env`

先复制模板：

```bash
cp .env.example .env
```

默认安全配置如下：

```env
DRY_RUN=true
PAPER_TRADING=true
LIVE_TRADING=false
CONFIRM_LIVE_TRADING=

IBKR_HOST=127.0.0.1
IBKR_PORT=7497
IBKR_CLIENT_ID=101
IBKR_ACCOUNT_ID=

AUTO_SUBMIT_PAPER_ORDERS=false
ALLOW_MARKET_ORDERS=false
ALLOW_FRACTIONAL_SHARES=true
```

## 配置 `universe.yaml`

股票池在 [config/universe.yaml](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/config/universe.yaml) 中，默认包含：

- `SPY`
- `QQQ`
- `AAPL`
- `MSFT`
- `NVDA`
- `AMD`
- `MU`
- `AVGO`
- `GOOGL`
- `AMZN`
- `META`

## 配置 `risk.yaml`

风险参数在 [config/risk.yaml](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/config/risk.yaml) 中，默认账户净值是 `20000 USD`，单笔风险是 `0.5%`，单票上限是 `15%`，总持仓上限是 `4` 只，半导体同时最多 `2` 只。

## 如何下载数据

```bash
python -m src.main download-data
```

功能：

- 读取 `config/universe.yaml`
- 优先用 `yfinance` 下载日线 OHLCV
- 失败时自动 fallback 到 mock 数据
- 每个 ticker 单独保存到 `data/cache/<ticker>.csv`
- 自动做数据校验

## 如何计算指标

```bash
python -m src.main compute-indicators
```

已实现：

- `SMA20` `SMA50` `SMA200`
- `EMA12` `EMA26`
- `MACD` `MACD Signal` `MACD Histogram`
- `RSI14`
- `Bollinger Middle` `Bollinger Upper` `Bollinger Lower`
- `ATR14`
- Ichimoku 全套核心列
- `20D High` `20D Low`
- `60D High` `60D Low`
- `Fib 38.2` `Fib 50` `Fib 61.8`
- `20D Return` `60D Return`

## 如何运行扫描

```bash
python -m src.main scan
```

输出：

- 终端表格
- [reports/daily](</Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/reports/daily>)
- `YYYY-MM-DD_scan.csv`
- `YYYY-MM-DD_scan.md`

## 如何运行风险检查

```bash
python -m src.main risk-check
```

会基于当日扫描结果计算：

- 建议入场价
- 建议止损
- 止损距离
- 单笔风险金额
- 仓位金额上限
- 股数
- 是否允许下单
- 阻止原因

## 如何运行回测

```bash
python -m src.main backtest --start 2018-01-01 --end 2026-01-01
```

输出：

- `reports/backtests/YYYY-MM-DD_backtest_summary.md`
- `reports/backtests/YYYY-MM-DD_trades.csv`
- `reports/backtests/YYYY-MM-DD_equity_curve.csv`
- `reports/charts/YYYY-MM-DD_equity_curve.png`

报告会明确写出：

- 最大回撤
- 总收益率
- 年化收益率
- 交易次数
- 胜率
- 盈亏比
- 与 `QQQ`、`SPY`、`50% QQQ + 50% cash`、等权股票池基准的对比

如果策略跑输 `QQQ`，报告会直接写明。

## 如何运行 dry-run

```bash
python -m src.main dry-run
```

特点：

- 不连接真实券商
- 不发送真实订单
- 只生成模拟订单日志
- 控制台明确打印 `DRY RUN ONLY - NO LIVE ORDERS SENT`

## 如何运行 daily

```bash
python -m src.main daily
```

`daily` 流程会依次执行：

1. 下载或更新行情
2. 校验数据
3. 计算指标
4. 扫描股票池
5. 风险检查
6. 生成订单计划
7. 根据 broker 模式选择 dry-run 或 IBKR paper 流程
8. 生成日报

## 如何查看报告

主要输出目录：

- [reports/daily](</Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/reports/daily>)
- [reports/backtests](</Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/reports/backtests>)
- [reports/charts](</Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/reports/charts>)
- [reports/account](</Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/reports/account>)
- [reports/orders](</Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/reports/orders>)

## 如何添加自己的策略

你可以在 [src/strategies](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/src/strategies) 中新增策略类，并在扫描或回测入口中接入。建议做法：

- 继承 `StrategyBase`
- 把买入和退出条件写成可测试的纯逻辑
- 通过 `config/strategy.yaml` 切换激活策略名

## 如何切换数据源

数据源入口在 [src/data](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/src/data)：

- `YFinanceProvider`
- `MockProvider`

后续要换成 Polygon、Tiingo、IBKR 历史数据或本地数据库，只需要新增 provider 并沿用 `DataProviderBase` 接口。

## 如何使用 mock 数据

当 `yfinance` 下载失败时，系统会自动生成 mock OHLCV 数据继续运行。当前环境下已经验证过：当 Yahoo Finance 因网络或限流失败时，`download-data`、`scan`、`backtest`、`daily` 仍然可以完整跑通。

## 如何连接 IBKR Paper Trading

先准备好 TWS 或 IB Gateway，然后参考下面的专门章节。

## 如何同步 IBKR 账户

```bash
python -m src.main ibkr-sync
```

成功时会写入：

- `reports/account/YYYY-MM-DD_account.json`
- `reports/account/YYYY-MM-DD_positions.csv`
- `reports/account/YYYY-MM-DD_open_orders.csv`

如果 TWS 或 Gateway 没开，程序会明确提示原因，并保持本地 dry-run 流程可用。

## 如何测试 IBKR Paper order

```bash
python -m src.main ibkr-paper-test-order --ticker AAPL --quantity 1 --limit-price 100
```

规则：

- 只能在 `PAPER_TRADING=true`
- `DRY_RUN=false`
- `LIVE_TRADING=false`
- 且连接 paper 端口时允许真实 paper 测试

如果当前仍是 `DRY_RUN=true`，命令不会发单，只会写入模拟日志。

## 为什么默认禁止 Live Trading

因为这套系统当前优先目标是工程闭环和 paper 流程验证，而不是实盘收益。Live 与 Paper 最大的不同不是接口，而是错误成本。任何端口配错、风控缺口、重复提交、行情异常、网络闪断、脚本 bug，都可能直接变成真实亏损，所以默认永久关闭 Live 是必要的安全底线。

## 常见错误排查

- `YFRateLimitError`：Yahoo Finance 限流，系统会自动 fallback 到 mock 数据。
- `Couldn't connect to TWS`：确认 TWS 或 Gateway 已启动、API 已启用、端口正确。
- `PAPER_TRADING=true requires paper port 7497 or 4002`：你配置到了 live 端口。
- `Market orders are disabled`：默认禁止市价单。
- `Order value exceeds max_order_value_usd`：订单金额超过风控阈值。
- `No BUY_CANDIDATE rows for risk check`：说明当前市场过滤器或个股规则没有放出买点，这不是程序错误。

## IBKR Paper Trading Setup

1. 安装并登录 Trader Workstation 或 IB Gateway。
2. 新手优先使用 TWS Paper Trading。
3. 在 TWS 中打开 `Global Configuration -> API -> Settings`。
4. 启用 `Enable ActiveX and Socket Clients`。
5. 确认端口：
   - `TWS Paper` 默认 `7497`
   - `TWS Live` 默认 `7496`
   - `IB Gateway Paper` 默认 `4002`
   - `IB Gateway Live` 默认 `4001`
6. 第一阶段可以保持 Read-Only，只测试连接和读取账户。
7. 如果要发送 Paper Trading 订单，需要在 Paper 环境关闭 Read-Only，但仍然禁止 Live。
8. 运行：

```bash
python -m src.main ibkr-test-connection
```

9. 运行：

```bash
python -m src.main ibkr-sync
```

10. 运行：

```bash
python -m src.main daily
```

11. 只有确认 dry-run 和 paper 都正常后，才考虑后续实盘。
12. 实盘配置必须手动开启，默认永久关闭。

## 支持的命令

```bash
python -m src.main download-data
python -m src.main compute-indicators
python -m src.main scan
python -m src.main risk-check
python -m src.main backtest --start 2018-01-01 --end 2026-01-01
python -m src.main dry-run
python -m src.main ibkr-test-connection
python -m src.main ibkr-sync
python -m src.main ibkr-paper-test-order --ticker AAPL --quantity 1 --limit-price 100
python -m src.main daily
pytest
```

## 目录说明

关键代码位置：

- [src/main.py](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/src/main.py)
- [src/data](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/src/data)
- [src/indicators](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/src/indicators)
- [src/scanner](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/src/scanner)
- [src/risk](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/src/risk)
- [src/backtest](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/src/backtest)
- [src/brokers](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/src/brokers)
- [tests](/Users/hankzhang/Documents/Codex/2026-06-29/python-ibkr-api-ibkr-paper-trading/us_stock_quant_system/tests)
