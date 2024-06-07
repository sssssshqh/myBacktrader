'''
Author: Huang, Quan Hang 250901214@qq.com
Date: 2024-06-07 23:51:31
LastEditors: Huang, Quan Hang 250901214@qq.com
LastEditTime: 2024-06-08 00:03:38
FilePath: \myBacktrader\myExample\yfinance\downloadETF50.PY
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import pandas as pd
import yfinance as yf


# etf800_5m_1 = yf.download("159652.SS", start="2024-04-08", end="2024-04-15", interval="5m")
# etf800_5m_2 = yf.download("159652.SS", start="2024-04-15", end="2024-04-22", interval="5m")
# etf800_5m_3 = yf.download("159652.SS", start="2024-04-22", end="2024-04-29", interval="5m")
# etf800_5m_4 = yf.download("159652.SS", start="2024-04-29", end="2024-05-06", interval="5m")

# etf800_5m_5 = yf.download("159652.SS", start="2024-05-06", end="2024-05-13", interval="5m")
# etf800_5m_6 = yf.download("159652.SS", start="2024-05-13", end="2024-05-20", interval="5m")
# etf800_5m_7 = yf.download("159652.SS", start="2024-05-20", end="2024-05-27", interval="5m")
# etf800_5m_8 = yf.download("159652.SS", start="2024-05-27", end="2024-06-03", interval="5m")
# etf800_5m_9 = yf.download("159652.SS", start="2024-06-03", end="2024-06-09", interval="5m")

etf50_1d = yf.download("159652.SZ", interval="1d")
etf50_1d.to_csv('./yfDataFeed/159652.SZ/159652_1d.csv')