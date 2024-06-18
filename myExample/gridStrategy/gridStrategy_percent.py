# -*- coding: UTF-8 -*-
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
import backtrader.analyzers as btanalyzers
import math
import numpy
import selectETF

from collections import OrderedDict
import yfinance as yf
import pandas as pd
import shutil
import csv
import threading
import msvcrt

# Create a Stratey
# params = {
    # 'isPrint': False
    # 'grid': (
    #     ('share', 0),           # 股票
    #     ('initCash', 0),        # 资金
    #     ('eachBSPos', 0),       # 每次交易份额(股)
    #     ('stepPercent', 0),     # 网格间隔 %
    #     ('totalGridNum', 0),    # 总共格子数(个)
    #     ('benchmarkPrice', 0),  # 基准价(元)
    #     ('lowLimitPrice', 0),   # 最低限价(元)
    #     ('highLimitPrice', 0),  # 最高限价(元)
    # ) }
class TestStrategy(bt.Strategy):
    
    params = (
        ('grid', {} ),
        ('isPrint', False)
    )
    
    def getBuyPos(self, cash, price, position):
        maxPos = math.floor(cash / price / 100) * 100 
        if (maxPos >= position):
            return position
        else:
            return maxPos

    def log(self, txt, dt=None, doPrint=False):
        ''' Logging function fot this strategy'''
        if doPrint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        self.log("------------init----------", doPrint=self.params.isPrint) 
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close
        self.log("样本标准差/均值: %.2f%%" % (numpy.std(self.dataclose, ddof=1)/numpy.mean(self.dataclose)*100), doPrint=self.params.isPrint)
        # To keep track of pending orders and buy price/commission
        self.order = None
        self.totalSell = 0
        self.totalBuy = 0
        self.benchmarkPrice = 0
        
        # Init
        self.broker.setcash(self.params.grid['initCash'])

        self.log('share = %s, initCash = %d, eachBSPos = %d, stepPercent = %.2f%%' % (
                    self.params.grid['share'],
                    self.params.grid['initCash'], self.params.grid['eachBSPos'], 
                    self.params.grid['stepPercent']*100), doPrint=self.params.isPrint)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:

            self.benchmarkPrice = order.executed.price
            if order.isbuy():
                self.totalBuy += 1
                self.log(
                    'BUY EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Comm %.2f, 持仓量: %d(股)' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm,
                     self.broker.getposition(self.datas[0]).size), doPrint=self.params.isPrint)

            else:  # Sell
                self.totalSell += 1
                self.log('SELL EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Net: %.2f, Comm %.2f, 持仓量 %d(股)' %
                         (order.executed.price,
                          - order.executed.size,
                          - (order.executed.price * order.executed.size),
                          (- (order.executed.price * order.executed.size) - order.executed.value),
                          order.executed.comm,
                          self.broker.getposition(self.datas[0]).size), doPrint=self.params.isPrint)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected', doPrint=self.params.isPrint)

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm), doPrint=self.params.isPrint)
        self.log('持仓量  = %d(股), 现价 = %.2f(元), 成本价 = %s(元), 价值 = %.2f(元), 现金 = %.2f(元)' % (
            self.broker.getposition(self.datas[0]).size,
            self.broker.getposition(self.datas[0]).adjbase,
            self.broker.getposition(self.datas[0]).price,
            self.broker.getvalue(),
            self.broker.getcash()
        ), doPrint=self.params.isPrint)

    def start(self):
        pass

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0], doPrint=self.params.isPrint)

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Buy, Buy, Buy
        if (self.benchmarkPrice == 0) and (self.dataclose[0] < ((1-self.params.grid['stepPercent']) * self.params.grid['highLimitPrice'])):
            totalBuyNum = 0
            curPrice = self.dataclose[0]
            for num in range(0, self.params.grid['totalGridNum']):
                if((curPrice * (1+self.params.grid['stepPercent'])) < self.params.grid['highLimitPrice']):
                    totalBuyNum += 1
                    curPrice = curPrice * (1+self.params.grid['stepPercent'])
           
            # BUY, BUY, BUY!!! (with default parameters)
            buyPos = self.getBuyPos(cash=self.broker.getcash(), price=self.dataclose[0], position=(self.params.grid['eachBSPos']*totalBuyNum))
            self.order = self.buy(size=buyPos)
            self.log('BUY CREATE, %.2f, Size:  %d' % (self.dataclose[0], self.params.grid['eachBSPos'] * totalBuyNum), doPrint=self.params.isPrint)
        else:
            if (self.dataclose[0] <= (self.benchmarkPrice * ( 1 - self.params.grid['stepPercent'])) and 
                self.dataclose[0] <= self.params.grid['highLimitPrice']):
                # BUY, BUY, BUY!!! (with default parameters)
                buyPos = self.getBuyPos(cash=self.broker.getcash(), price=self.dataclose[0], position=self.params.grid['eachBSPos'])
                self.order = self.buy(size=buyPos)
                self.log('BUY CREATE, %.2f, benchmarkPrice: %.2f: -%.2f%%, Size:  %d, ' % (self.dataclose[0], 
                            self.benchmarkPrice, (self.benchmarkPrice - self.dataclose[0]) / self.benchmarkPrice * 100, 
                            self.params.grid['eachBSPos']), doPrint=self.params.isPrint)
            
            elif (self.dataclose[0] >= (self.benchmarkPrice * ( 1 + self.params.grid['stepPercent'])) and
                  self.dataclose[0] >= self.params.grid['lowLimitPrice']):
                    remainPos = self.broker.getposition(self.datas[0]).size - self.params.grid['eachBSPos']
                    remainPos = self.params.grid['eachBSPos'] if remainPos >= 0 else self.broker.getposition(self.datas[0]).size
                    if(remainPos > 0):
                        self.order = self.sell(size=remainPos)
                        # SELL, SELL, SELL!!! (with all possible default parameters)
                        self.log('SELL CREATE, %.2f, benchmarkPrice: %.2f: +%.2f%%, Size:  %d' % (self.dataclose[0], 
                                    self.benchmarkPrice, (self.dataclose[0] - self.benchmarkPrice) / self.benchmarkPrice * 100,                                                              
                                    remainPos), doPrint=self.params.isPrint)
            else:
                pass

    def stop(self):

        self.log("------------stop----------", doPrint=self.params.isPrint) 
    
        # Print out the final result
        stepPercent = self.params.grid['stepPercent'] * 100
        MaxDrawDown = self.analyzers.DrawDown.get_analysis()['max']['drawdown']
        MaxMoneydown = self.analyzers.DrawDown.get_analysis()['max']['moneydown']
        Net = self.broker.getvalue()-self.params.grid['initCash']
        NetPecent = Net / self.params.grid['initCash'] * 100
        OpenInterest = self.broker.getposition(self.datas[0]).size
        currentPrice = self.broker.getposition(self.datas[0]).adjbase

        self.params.grid['maxPortfolio'] = f'{self.broker.getvalue():.2f}'
        self.params.grid['Net'] = f'{Net:.2f}'
        self.params.grid['Net(%)'] = f'{NetPecent:.2f}'
        self.params.grid['stepPercent(%)']= f'{stepPercent:.2f}'
        self.params.grid['MaxDrawDown(%)'] = f'{MaxDrawDown:.2f}'
        self.params.grid['MaxMoneydown(RMB)'] = f'{MaxMoneydown:.2f}'
        self.params.grid['OpenInterest(stocks)'] = OpenInterest
        self.params.grid['currentPrice'] = f'{currentPrice:.2f}'
        self.params.grid['totalBuy'] = self.totalBuy
        self.params.grid['totalSell'] = self.totalSell
        
        new_row = pd.DataFrame([self.params.grid])
        appendStepPercentCSV(self.params.grid['share'], new_row)

        # self.log(maxPortfolioPrint, doPrint=self.params.isPrint)
        self.log("==========================", doPrint=self.params.isPrint) 

# 根据输入自动计算每次买入和卖出份额的数值, 返回
#     eachBSPos 
#     totalGridNum
#     benchmarkPrice
#     priceGrides  []
#     cashGrides   []
#     由输入补全
#     initCash
#     stepPercent
#     lowLimitPrice
#     highLimitPrice
#     cashUsageRate
def getEachBSPos(share, lowLimitPrice, highLimitPrice, stepPercent, initCash, cashUsageRate):
    grid = {}
        
    # 计算得出值 
    totalGridNum = 0        # 总共格子数
    eachBSPos = 0           #  每次交易股数(股) 整100股/1手交易

    # 临时变量
    lowPrice = lowLimitPrice
    highPrice = highLimitPrice
    priceGrides = []
    cashGrides = []

    # 最多上下10格
    if (lowPrice * math.pow((1+stepPercent), 11) < highPrice):
        return grid
    else:
        curPrice = lowPrice
        for num in range(0, 10):
            curPrice = round(curPrice*(1+stepPercent), 3)
            if(curPrice > highLimitPrice):
                break
            else:
                totalGridNum += 1
                highPrice = curPrice
                priceGrides.append(curPrice)
    # 最少2格
    if(totalGridNum < 2):
        return grid 


    # 每一份 金额
    useCash = initCash * cashUsageRate
    aveagePrice = (lowPrice + highPrice) / 2
    gridNumAdj = (( aveagePrice / lowPrice) * totalGridNum)
    eachBSPos = math.floor( useCash / gridNumAdj / aveagePrice / 100 ) * 100
    
    if(eachBSPos == 0):
        return grid 

    for price in priceGrides:
        cash = round(price * eachBSPos, 3)
        if(len(cashGrides)==0):
            cashGrides.append(cash)
        else:
            cashGrides.append(cash+cashGrides[len(cashGrides)-1])

    cashGrides = numpy.around(cashGrides, decimals=3)
    
    grid['eachBSPos'] = eachBSPos
    grid['totalGridNum'] = totalGridNum
    grid['benchmarkPrice'] = round(((priceGrides[0] + priceGrides[-1]) / 2), 3)

    grid['priceGrides'] = ' '.join([str(priceGride) for priceGride in priceGrides])
    grid['cashGrides'] = ' '.join([str(cashGride) for cashGride in cashGrides])
    # 由输入补全
    grid['share'] = share
    grid['initCash'] = initCash
    grid['stepPercent'] = stepPercent
    grid['lowLimitPrice'] = lowLimitPrice
    grid['highLimitPrice'] = highLimitPrice
    grid['cashUsageRate'] = cashUsageRate
    return grid

def getYFcsvData(share, interval, fromDate, toDate):

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.abspath(os.path.join(modpath, f'..\\..\\yfDataFeed\\{share}_{interval}.csv'))

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime.strptime(fromDate, '%Y-%m-%d'),
        # Do not pass values before this date
        todate=datetime.datetime.strptime(toDate, '%Y-%m-%d'),
        # Do not pass values after this date
        reverse=False)

    return data

def getCsvData(share, interval, fromDate, toDate):
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    sharPath = os.path.abspath(os.path.join(modpath, f'..\\..\\yfDataFeed\\{share}_{interval}.csv'))
    shareData = pd.read_csv(sharPath)
    
    formIndexs=shareData[shareData.Date==fromDate].index.tolist()
    toIndexs=shareData[shareData.Date==toDate].index.tolist()

    shareDataSlice = pd.DataFrame()
    if((len(formIndexs)!=0) and len(toIndexs)!=0):
        formIndex = formIndexs[0]
        toIndex = toIndexs[0]

        if((not math.isnan(formIndex)) and (not math.isnan(toIndex))):
            shareDataSlice = shareData.loc[formIndex:toIndex].reset_index(drop=True)

    return shareDataSlice

def rmFilesUnderFolder(folderPath):
    if(os.path.exists(folderPath)):
        shutil.rmtree(folderPath)
        os.mkdir(folderPath)
    else:
        os.mkdir(folderPath)

def rmStepPercentFolder():
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    folder = os.path.abspath(os.path.join(modpath, f'..\\..\\execl\\stepPercent'))
    if(os.path.exists(folder)):
        rmFilesUnderFolder(folder)

threadLock = threading.Lock()
def appendStepPercentCSV(share, pd_row):
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    dataPath = os.path.abspath(os.path.join(modpath, f'..\\..\\execl\\stepPercent\\{share}.csv'))
    if(len(pd_row)==0):
        return
    
    header = pd_row.columns.values
    content = pd_row.loc[0].values

    if((len(header)==0) or (len(content)==0)):
        return
    
    header = ', '.join([str(headerData) for headerData in header]) + '\n'
    content = ', '.join([str(contentData) for contentData in content]) + '\n'

    new_row = ''
    addTitle = False
    if(not os.path.exists(dataPath)):
        addTitle = True
        new_row = header + content
    else:
        addTitle = False
        new_row = content

    global threadLock
    threadLock.acquire_lock()
    with open(dataPath, 'a', encoding='UTF-8') as csvfile: 
        if(addTitle):
            csvfile.seek(0, 0)
        csvfile.write(new_row)
        csvfile.flush()
        csvfile.close()
    threadLock.release_lock()

# 获取最优的每次买入和卖出百分比值
def getBestStepPercent(share, lowLimitPrice, highLimitPrice, fromDate, toDate,
                        interval='1d', initCash=35000, cashUsageRate=0.9, commission=0.003):
    
    percent = round(((highLimitPrice / lowLimitPrice) - 1), 4)
    stepPercents = numpy.arange(0.0001, percent, 0.0001)
    stepPercents = numpy.around(stepPercents, decimals=4)
    
    grids = []
    for stepPercent in stepPercents:
        grid = getEachBSPos(share=share, lowLimitPrice=lowLimitPrice, highLimitPrice=highLimitPrice, stepPercent=stepPercent, initCash=initCash, cashUsageRate=cashUsageRate)
        if(len(grid) != 0):
            grids.append(grid)
    
    # Create a cerebro entity
    cerebro = bt.Cerebro(optreturn=False)

    # Add a strategy
    # if(isPrint):
    #     cerebro.addstrategy(TestStrategy, grid=grids[0], isPrint=True)
    # else:
    cerebro.optstrategy(TestStrategy, grid=grids, isPrint=False)

    data = getYFcsvData(share=share, interval=interval, fromDate=fromDate, toDate=toDate)
    
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=commission)
  
    # Analyzer
    # cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='mysharpe')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='DrawDown')
    # cerebro.addanalyzer(btanalyzers.transactions, _name='transactions')

    # if(isPrint):
    #     thestrats = cerebro.run()
    #     # Run over everything
    #     thestrat = thestrats[0]
    #     print('DrawDown, max.drawdown: %.2f, max.moneydown: %.2f%%, max.len: %s' %(
    #           thestrat.analyzers.DrawDown.get_analysis()['max']['drawdown'], 
    #           thestrat.analyzers.DrawDown.get_analysis()['max']['moneydown'],
    #           thestrat.analyzers.DrawDown.get_analysis()['max']['len']))

    # else:
    cerebro.run()

    # Plot the result
    # if isPrint:
    #     cerebro.plot()

# TODO:
def getBSinfo(share, lowLimitPrice, highLimitPrice, fromDate, toDate,
                interval='1d', initCash=35000, cashUsageRate=0.9, commission=0.003):

    percent = round(((highLimitPrice / lowLimitPrice) - 1), 4)
    stepPercents = numpy.arange(0.0001, percent, 0.0001)
    stepPercents = numpy.around(stepPercents, decimals=4)
    
    grids = []
    for stepPercent in stepPercents:
        grid = getEachBSPos(share=share, lowLimitPrice=lowLimitPrice, highLimitPrice=highLimitPrice, stepPercent=stepPercent, initCash=initCash, cashUsageRate=cashUsageRate)
        if(len(grid) != 0):
            grids.append(grid)
    
    # Create a cerebro entity
    cerebro = bt.Cerebro(optreturn=False)

    # Add a strategy
    # if(isPrint):
    #     cerebro.addstrategy(TestStrategy, grid=grids[0], isPrint=True)
    # else:
    cerebro.optstrategy(TestStrategy, grid=grids, isPrint=False)

    data = getYFcsvData(share=share, interval=interval, fromDate=fromDate, toDate=toDate)
    
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=commission)
  
    # Analyzer
    # cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='mysharpe')
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='DrawDown')
    # cerebro.addanalyzer(btanalyzers.transactions, _name='transactions')

    # if(isPrint):
    #     # Run over everything
    #     thestrats = cerebro.run()
    #     thestrat = thestrats[0]
    #     print('DrawDown, max.drawdown: %.2f, max.moneydown: %.2f%%, max.len: %s' %(
    #           thestrat.analyzers.DrawDown.get_analysis()['max']['drawdown'], 
    #           thestrat.analyzers.DrawDown.get_analysis()['max']['moneydown'],
    #           thestrat.analyzers.DrawDown.get_analysis()['max']['len']))


    # else:
    cerebro.run()
    # cerebro.plot()

def readETFResult():
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    etfResultPath = os.path.abspath(os.path.join(modpath, f'..\\..\\execl\\ETF_result.xlsx'))
    etfData = pd.read_excel(etfResultPath, sheet_name='ETF')
    return etfData


if __name__ == '__main__':

    _fromDate = '2024-04-01'
    _toDate = '2024-06-14'
    _interval = '1d'
    
    rmStepPercentFolder()
    etfData = readETFResult()
    for share in etfData['StockCode']:
        shareData = getCsvData(share=share, interval=_interval, fromDate=_fromDate, toDate=_toDate)
        if (len(shareData) == 0):
            continue
        adjClose = shareData.loc[:, 'Adj Close']
        lowPrice = adjClose.min()
        highPrice = adjClose.max()
        lowLimitPrice = round((lowPrice * 1), 3)
        highLimitPrice = round((highPrice * 1), 3)

        getBestStepPercent(share=share, lowLimitPrice=lowLimitPrice, highLimitPrice=highLimitPrice, fromDate=_fromDate, toDate=_toDate, interval=_interval)
        break

    print('Exiting Main Thread')

