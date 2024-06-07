from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

import math
import numpy

from collections import OrderedDict
import threading

# Global
maxPortfolio = 0
isPrint = False
# Create a Stratey
class TestStrategy(bt.Strategy):
    
    params = (
        ('grid', {} ),
    )
    # params = (
    #     ('initPosition', 0),    # 初始持仓
    #     ('benchmarkPrice', 0),  # 成本价
    #     ('gridPrice', []),      # 网格
    #     ('eachBSPos', 0),       # 每次交易份额(股)
    #     ('stepPrice', 0),       # 网格间隔(元)
    #     ('initCash', 0),        # 资金
    # )

    def log(self, txt, dt=None, doPrint=False):
        ''' Logging function fot this strategy'''
        if doPrint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        self.log("------------init----------", doPrint=isPrint) 
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.totalSell = 0
        self.totalBuy = 0
        
        # Init
        self.broker.setcash(self.params.grid['initCash'])
        # Overwritten
        self.params.grid['initPosition'] = 0
        self.params.grid['gridPrice'] = numpy.around(self.params.grid['gridPrice'], decimals=3)
        self.params.grid['benchmarkPrice'] = self.params.grid['gridPrice'][-1]

        # 保存各个网格持有的股数 有序字典-从低价到高价  未兼容原先做法，原先有初始持仓
        self.gridMark = OrderedDict()
        _tmpRemainPosition = self.params.grid['initPosition']
        for price in self.params.grid['gridPrice']:
            if(price>=self.params.grid['benchmarkPrice']):
                if((_tmpRemainPosition-self.params.grid['eachBSPos']) >= 0):
                    self.gridMark[price]=self.params.grid['eachBSPos']
                    _tmpRemainPosition -= self.params.grid['eachBSPos']
                else:
                    self.gridMark[price] = _tmpRemainPosition
                    _tmpRemainPosition = 0;
            else:
                self.gridMark[price] = 0

        self.log('eachBSPos = %s, %s' % (self.params.grid['eachBSPos'], self.gridMark), doPrint=isPrint)


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.size,
                     order.executed.value,
                     order.executed.comm), doPrint=isPrint)

            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Net: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.size,
                          - (order.executed.price * order.executed.size),
                          (- (order.executed.price * order.executed.size) - order.executed.value),
                          order.executed.comm), doPrint=isPrint)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected', doPrint=isPrint)

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm), doPrint=isPrint)
        self.log('持仓量  = %d(股), 现价 = %.2f(元), 成本价 = %s(元), 价值 = %.2f(元), 现金 = %s(元)' % (
            self.broker.getposition(self.datas[0]).size,
            self.broker.getposition(self.datas[0]).adjbase,
            self.broker.getposition(self.datas[0]).price,
            self.broker.getvalue(),
            self.broker.getcash()
        ), doPrint=isPrint)

    def start(self):
        pass

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0], doPrint=isPrint)

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Buy, Buy, Buy
        buyPos = 0
        for key in sorted(self.gridMark, reverse=True):
            # 当价格跌到网格下方，且当前网格没有持仓时则买入份额
            if ((key != self.params.grid['gridPrice'][-1]) and (self.dataclose[0] <= key) and (self.gridMark[key] == 0)):
                buyPos += self.params.grid['eachBSPos']
                self.gridMark[key] = self.params.grid['eachBSPos']
                self.totalBuy += 1
        
        if(buyPos>0):
            self.order = self.buy(size=buyPos)
            # BUY, BUY, BUY!!! (with default parameters)
            self.log('BUY CREATE, %.2f, Size:  %d, %s' % (self.dataclose[0], buyPos, self.gridMark), doPrint=isPrint)
        else:
            # Sell, Sell, Sell 
            sellPos = 0
            for num in range(0, len(self.params.grid['gridPrice'])-1):
                key = self.params.grid['gridPrice'][num]
                keyNext = self.params.grid['gridPrice'][num+1]
                value = self.gridMark[key]
                if((self.dataclose[0] >= key) and (value > 0)):
                    if(self.dataclose[0] >= keyNext):
                        remainPos = value - self.params.grid['eachBSPos']
                        if(remainPos >= 0):
                            sellPos += self.params.grid['eachBSPos']
                            self.gridMark[key] = remainPos
                            self.totalSell += 1
                        elif(value>0):
                            sellPos += value
                            self.gridMark[key] = 0
                            self.totalSell += 1
                        else:
                            pass

            if(sellPos>0):
                self.order = self.sell(size=sellPos)
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f, Size:  %d, %s' % (self.dataclose[0], sellPos, self.gridMark), doPrint=isPrint)

    def stop(self):

        global maxPortfolio
        if (self.broker.getvalue() > maxPortfolio):
            maxPortfolio = self.broker.getvalue()
            self.log("------------stop----------", doPrint=isPrint) 
            # Print out the final result
            self.log("Total Buy/Sell: %s/%s, 持仓量  = %d(股), 现价 = %.2f(元), %s" % (
                self.totalBuy,
                self.totalSell,
                self.broker.getposition(self.datas[0]).size,
                self.broker.getposition(self.datas[0]).adjbase,
                self.gridMark
            ), doPrint=isPrint) 
            self.log('Final Portfolio Value: %.2f, Net: %.2f, eachBSPos: %d(股), stepPrice: %.3f(元)' % (
                self.broker.getvalue(),
                self.broker.getvalue()-self.params.grid['initCash'],
                self.params.grid['eachBSPos'],
                self.params.grid['stepPrice']
            ), doPrint=True)
            self.log("==========================", doPrint=isPrint) 

if __name__ == '__main__':

    # Create a cerebro entity
    cerebro = bt.Cerebro(optreturn=False)

    strageParams = {'initCash': 100000, 'cashUsageRate': 0.7, 'lowLimitPrice': 1.026, 'highLimitPrice': 1.11, 'benchmarkPrice': 1.06}
    grids = []

    stepPrices = numpy.arange(0.001, 0.04, 0.001)
    # stepPrices = [0.03]
    stepPrices = numpy.around(stepPrices, decimals=3)
    for stepPrice in stepPrices:
        
        gridParams = {
            'initCash': strageParams['initCash'],
            'cashUsageRate': strageParams['cashUsageRate'],  # To prevent loss too much in the early stages and cann't buy sufficient positions at the low price level
            'lowLimitPrice': strageParams['lowLimitPrice'],
            'highLimitPrice': strageParams['highLimitPrice'],
            'benchmarkPrice': strageParams['benchmarkPrice'],

            'stepPrice': 0.01,   # 唯一变量
            
            'lowGridPrice': [],  # 最低限价
            'highGridPrice': [], # 最高限价
            'gridPrice': [],     # 每个网格的价格    从低价到高价
            'lowGridNum': 0,     # 低网格的价格
            'highGridNum': 0,    # 高网格的价格
            'initPosition': 0,   # 初始仓位(股)     整100股/1手交易
            'eachBSPos': 0,      # 每次交易股数(股) 整100股/1手交易
            'initConsumeCash': 0,
            'initRemainCash': 0,
            'initReachCash': 0,
        }
        
        gridParams['stepPrice'] = stepPrice
        gridParams['highGridNum'] = math.floor((gridParams['highLimitPrice'] - gridParams['benchmarkPrice'])/gridParams['stepPrice'])
        gridParams['lowGridNum'] = math.floor((gridParams['benchmarkPrice'] - gridParams['lowLimitPrice'])/gridParams['stepPrice'])
        for num in range(1, gridParams['highGridNum']+1):
            gridParams['highGridPrice'].append(gridParams['benchmarkPrice']+num*gridParams['stepPrice'])
        
        for num in range(gridParams['lowGridNum'], 0, -1 ):
            gridParams['lowGridPrice'].append(gridParams['benchmarkPrice']-num*gridParams['stepPrice'])
        
        gridParams['gridPrice'] = gridParams['lowGridPrice'] + [gridParams['benchmarkPrice'],] + gridParams['highGridPrice']
        if(len(gridParams['gridPrice']) < 3):
            next
        # 份数， 非股数
        remianPosition = 0
        if (gridParams['lowGridNum'] >= 2):
            remianPosition = (((gridParams['lowGridPrice'][0] + gridParams['lowGridPrice'][-1]) / 2) / gridParams['benchmarkPrice']) * gridParams['lowGridNum']
        elif (gridParams['lowGridNum'] == 1):
            remianPosition = gridParams['lowGridPrice'][0] / gridParams['benchmarkPrice']
        else:
            remianPosition = 0
        
        # 每一份 金额
        initPosCash = math.floor(gridParams['initCash'] * gridParams['cashUsageRate'] / (gridParams['highGridNum'] + remianPosition))
        gridParams['eachBSPos'] = math.floor(initPosCash / gridParams['benchmarkPrice'] /100) * 100
        gridParams['initPosition'] = math.floor((gridParams['highGridNum']) * gridParams['eachBSPos'])
        gridParams['initConsumeCash'] = gridParams['benchmarkPrice'] * gridParams['initPosition']
        gridParams['initRemainCash'] = gridParams['initCash'] - gridParams['initConsumeCash']
        gridParams['initReachCash'] = (gridParams['initPosition'] + remianPosition * gridParams['eachBSPos']) * gridParams['benchmarkPrice']
        
        grid = {}
        grid['initPosition'] = gridParams['initPosition']
        grid['benchmarkPrice'] = gridParams['benchmarkPrice']
        grid['gridPrice'] = numpy.around(gridParams['gridPrice'], decimals=3)
        grid['eachBSPos'] = gridParams['eachBSPos']
        grid['stepPrice'] = gridParams['stepPrice']
        grid['initCash'] = gridParams['initCash']
        grids.append(grid)
    
    # Add a strategy
    cerebro.optstrategy(TestStrategy, grid=grids)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '..\\..\\yfDataFeed\\515800.SS\\515800_1d.csv')

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2020, 6, 4),
        # Do not pass values before this date
        todate=datetime.datetime(2020, 8, 22),
        # Do not pass values after this date
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.003)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.SizerFix, stake=1)
    
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the Max Portfolio Value
    # global maxPortfolio
    # print('Max Portfolio Value: %.2f' % maxPortfolio)

    # Plot the result
    # if isPrint:
    #     cerebro.plot()
