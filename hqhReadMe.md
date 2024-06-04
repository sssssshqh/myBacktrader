<!--
 * @Author: Huang, Quan Hang quanhang.huang@siemens.com
 * @Date: 2024-06-03 16:54:05
 * @LastEditors: Huang, Quan Hang 250901214@qq.com
 * @LastEditTime: 2024-06-04 23:36:58
 * @FilePath: \myBacktrader\hqhReadMe.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
# 环境
```
python -m venv myEnv
myEnv\Scripts\activate.bat

pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

python -m pip install --upgrade pip

pip install backtrader
pip install pandas
pip install yfinance          --upgrade --no-cache-dir
pip install yfinance[nospam]  --upgrade --no-cache-dir
pip install yfinance[repair]  --upgrade --no-cache-dir
pip install matplotlib        --upgrade --no-cache-dir
pip install jupyter notebook

```

# yfinance
在 yfinance 中，中国 A 股的股票代码需要加上交易所的后缀，上海证券交易所（SSE）的后缀是 .SS，深圳证券交易所（SZSE）的后缀是 .SZ。
- [yfinance Library – 完整指南](https://algotrading101.com/learn/yfinance-guide/)
- [Python菜鸟教程 获取金融数据](https://www.runoob.com/python-qt/qt-get-data.html)
  
The layout itself is also really simple, there are just three modules:
- yf.Tickers: Almost all the methods are in the Tickers module.
- yf.download: The download module is for rapidly downloading the historical data of multiple tickers at once.
- yf.pandas_datareader: is for back compatibility with legacy code, 没用

## Tickers
-  [history()](https://github.com/ranaroussi/yfinance/wiki/Ticker) method, which is the most “complicated” method in the yfinance library.It takes the following parameters as input:
    - period: data period to download (either use period parameter or use start and end) Valid periods are: “1d”, “5d”, “1mo”, “3mo”, “6mo”, “1y”, “2y”, “5y”, “10y”, “ytd”, “max”
   - interval: data interval (1m data is only for available for last 7 days, and data interval <1d for the last 60 days) Valid intervals are: “1m”, “2m”, “5m”, “15m”, 30m”, “60m”, “90m”, “1h”, “1d”, “5d”, “1wk”, “1mo”, “3mo”
   - start: If not using period – in the format (yyyy-mm-dd) or datetime.
   - end: If not using period – in the format (yyyy-mm-dd) or datetime.
   - prepost: Include Pre and Post regular market data in results? (Default is False)- no need usually to change this from False
   - auto_adjust: Adjust all OHLC (Open/High/Low/Close prices) automatically? (Default is True)- just leave this always as true and don’t worry about it
   - actions: Download stock dividends and stock splits events? (Default is True)
   ```
   import yfinance as yf

   aapl= yf.Ticker("aapl")
   aapl_historical = aapl.history(start="2020-06-02", end="2020-06-07", interval="1m")
   ```
- info() returns a dictionary with a wide range of information about a ticker, including such things as a summary description, employee count, marketcap, volume, P/E ratios, dividends etc.
- dividends() if you want a breakdown of each dividend payout as it occurred and on what date

## Tickers
- [download()](https://github.com/ranaroussi/yfinance/wiki/Tickers)
   - group_by: group by column or ticker (‘column’/’ticker’, default is ‘column’)
   - threads: use threads for mass downloading? (True/False/Integer)
   - proxy: proxy URL if you want to use a proxy server for downloading the data (optional, default is None)
   ```
   data = yf.download("AMZN AAPL GOOG", start="2017-01-01", end="2017-04-30", group_by='tickers')
   ```

## 替代品
- If you want to build algorithms trading real money, we absolutely recommend you use an official data source/API, preferably one connected directly to exchange data and with low latency. Something like 
  - Polygon.io or 
  - IEX might suit you better.
- If you absolutely HAVE to use the Yahoo Finance data specifically, we recommend at least paying for an unofficial API like 
  - RapidAPI, where you stand a good bet there is an active team of developers constantly maintaining the API. Remember RapidAPI does still have a limited usage free tier!

