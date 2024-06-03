<!--
 * @Author: Huang, Quan Hang quanhang.huang@siemens.com
 * @Date: 2024-06-03 16:54:05
 * @LastEditors: Huang, Quan Hang 250901214@qq.com
 * @LastEditTime: 2024-06-03 23:57:18
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