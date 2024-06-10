'''
Author: Huang, Quan Hang 250901214@qq.com
Date: 2024-06-11 00:08:32
LastEditors: Huang, Quan Hang 250901214@qq.com
LastEditTime: 2024-06-11 00:50:37
FilePath: \myBacktrader\myExample\gridStrategy\std.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import pandas as pd
import yfinance as yf
import numpy

etf51780_1d = yf.download("517800.SS 159652.SZ", interval="1d", group_by='tickers')
etf51780_1d.to_csv('./yfDataFeed/517800.SS_1d.txt')
print(etf51780_1d)


# toIndex = aa[aa.Date == '2024-04-01'].index.tolist()[0]  
# fromIndex   = aa[aa['Date'] == '2024-06-01'].index.tolist()[0]

# slice = etf51780_1d.loc[fromIndex:toIndex, 'Adj Close']
# print(slice)

# import pandas as pd

# data = {
#     'name': ['Alice', 'Bob', 'Charlie', 'David', 'Eva'],
#     'age': [25, 30, 35, 40, 45]
# }

# df = pd.DataFrame(data)
# print(df)

# index = df.loc[df['name'] == 'Charlie'].index[0]
# print(index)
