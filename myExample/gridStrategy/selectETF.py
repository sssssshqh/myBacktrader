'''
Author: Huang, Quan Hang 250901214@qq.com
Date: 2024-06-14 20:44:18
LastEditors: Huang, Quan Hang 250901214@qq.com
LastEditTime: 2024-06-15 15:22:28
FilePath: \myBacktrader\myExample\pandas\test2.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

import pandas as pd
import yfinance as yf
from collections import OrderedDict
import math

shares = []
# shares = ['517800.SS', '159652.SZ']
interval = '1d'
sharesPath = OrderedDict()

modpath = os.path.dirname(os.path.abspath(sys.argv[0]))

etfListPath = os.path.abspath(os.path.join(modpath, f'..\\..\\execl\\ETF.xlsx'))
etfListData = pd.read_excel(etfListPath, sheet_name=['上海交易所ETF列表', '深圳交易所ETF列表'])
ssList = etfListData['上海交易所ETF列表'].loc[:, ('StockCode', 'StockABB')]
ssList['Exchange'] = '上海'
ssList['StockCode'] = ssList.StockCode.map(lambda code: str(code)+".SS")

szList = etfListData['深圳交易所ETF列表'].loc[:, ('StockCode', 'StockABB')]
szList['Exchange'] = '深圳'
szList['StockCode'] = szList.StockCode.map(lambda code: str(code)+".SZ")

shareList = pd.concat([ssList, szList], axis=0, ignore_index=True)

shares = shareList['StockCode'].values.tolist()
sharesData = yf.download(shares, group_by='tickers', threads='Integer')

for share in shares:
    sharesPath[share] = os.path.abspath(os.path.join(modpath, f'..\\..\\yfDataFeed\\{share}_{interval}.csv'))
    sharesData[share].to_csv(sharesPath[share])
    adjClose = sharesData.loc['2024-04-01':'2024-06-14' , [(share, 'Adj Close')]]
    std = adjClose.std().values[0]
    mean = adjClose.mean().values[0]
    index = shareList[shareList.StockCode==share].index.tolist()[0]
    if ( math.isnan(std) or math.isnan(mean)):
        shareList.loc[index, 'stdMean'] = 0
    else:
        stdMean = round(((std / mean) * 100), 2)
        shareList.loc[index, 'stdMean'] = stdMean

stdMeanPath = os.path.abspath(os.path.join(modpath, f'..\\..\\execl\\ETF_stdMean.xlsx'))
shareList.to_excel(stdMeanPath, sheet_name='ETF', index=False)

# data = pd.read_csv(datapath)

# print(data.loc[[0, 1, 2]])