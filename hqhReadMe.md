<!--
 * @Author: Huang, Quan Hang quanhang.huang@siemens.com
 * @Date: 2024-06-03 16:54:05
 * @LastEditors: Huang, Quan Hang 250901214@qq.com
 * @LastEditTime: 2024-06-15 11:26:14
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

# backtrader 
## 数据类型
self.dataclose = self.datas[0].close
```
print("hqh type self.datas=    %s" % type(self.datas))
print("hqh leng self.datas   = %s" % len(self.datas))

print("hqh type self.datas[0]= %s" % type(self.datas[0]))
print("hqh leng self.datas[0]= %s" % len(self.datas[0]))

print("hqh type self.datas[0].close= %s" % type(self.datas[0].close))
print("hqh leng self.datas[0].close= %s" % len(self.datas[0].close))

print("hqh type self.dataclose= %s" % type(self.dataclose))
print("hqh leng self.dataclose= %s" % len(self.dataclose))

print("hqh type self.datas[0].close[0]= %s" % type(self.datas[0].close[0]))
print("hqh type self.dataclose[0]     = %s" % type(self.dataclose[0]))
```
```
hqh type self.datas=    <class 'list'>
hqh leng self.datas   = 1
hqh type self.datas[0]= <class 'backtrader.feeds.yahoo.YahooFinanceCSVData'>
hqh leng self.datas[0]= 1
hqh type self.datas[0].close= <class 'backtrader.linebuffer.LineBuffer'>
hqh leng self.datas[0].close= 1
hqh type self.dataclose= <class 'backtrader.linebuffer.LineBuffer'>
hqh leng self.dataclose= 1
hqh type self.datas[0].close[0]= <class 'float'>
hqh type self.dataclose[0]     = <class 'float'>
```

# backtrader
[Analyzers](https://blog.csdn.net/Castlehe/article/details/113772133) 指标的公式

## [backtrader源码解读](https://www.zhihu.com/column/c_1604522311041966081)
- [backtrader源码解读 (1)：读懂源码的钥匙——认识元类](https://www.fengstatic.com/archives/2958#4_new)
  ```
  class UpperMetaClass(type):
    def __new__(meta, name, bases, dct):
        print('[1]', dct)
        
        upper_dct = {
            k if k.startswith("__") else k.upper(): v
            for k, v in dct.items()
        }
        return type.__new__(meta, name, bases, upper_dct)

  class MyClass(metaclass = UpperMetaClass):
      var = 1
      def func(self):
          pass

  print('[2]', MyClass.__dict__)

  [1] {'__module__': '__main__', '__qualname__': 'MyClass', 'var': 1, 'func': <function MyClass.func at 0x00000221683B5550>}
  te '__weakref__' of 'MyClass' objects>, '__doc__': None}
  ```
  __new__方法，该方法接受四个参数，分别为：
  - 元类MyMetaClass自身；
  - 创建类的名称；
  - 创建类的父类组成的元组；
  - 创建类的属性名或方法名为键，对应的属性值或函数为值所组成的字典。
- [backtrader源码解读 (2)：读懂源码的钥匙——元类进阶](https://www.fengstatic.com/archives/2961)
  ```
  # example 1
  class MyClass:
    def __call__(self, num):
        print(f'[{num}] {self}')

  myobj = MyClass()

  myobj(1)
  myobj.__call__(2)

  [1] <__main__.MyClass object at 0x0000017DCE6B7790>
  [2] <__main__.MyClass object at 0x0000017DCE6B7790>

  # example 2.1
  class MyMetaClass(type):
      def __call__(cls):
          print('[1]', cls)

  class MyClass(metaclass = MyMetaClass):
      pass

  myobj = MyClass()
  print('[2]', myobj is None)

  [1] <class '__main__.MyClass'>
  [2] True
  ```
  super: 子类中可以使用super调用父类的方法
  - 第二个参数决定调用方法的对象并确定使用哪一条MRO链，第一个参数决定在MRO链中从哪个位置寻找其最近的父类以调用该父类的方法
  __call__
  - __call__方法是Python中特殊的实例方法，它用于对实例对象的"( )"运算符进行设定："实例对象( )"相当于实例对象调用__call__方法，即"实例对象.__call__( )"。
- [backtrader源码解读 (3)：底层基石——metabase模块 (上篇)](https://www.fengstatic.com/archives/2963)
  - doprenew、donew、dopreinit、doinit、dopostinit
- [backtrader源码解读 (4)：底层基石——metabase模块 (下篇)](https://zhuanlan.zhihu.com/p/602906986?ssr_src=heifetz)