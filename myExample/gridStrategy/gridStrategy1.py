from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt

import math
from collections import OrderedDict

# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('initPosition', 0),
        ('benchmarkPrice', 0),
        ('gridPrice', []),
        ('eachBSPos', 0)
    )
    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        cerebro.broker.getposition(self.datas[0]).size = self.params.initPosition
        cerebro.broker.getposition(self.datas[0]).price = self.params.benchmarkPrice

        self.totalBuy = math.floor(self.params.initPosition / self.params.eachBSPos)
        self.totalSell = 0
        
        # 保存各个网格持有的股数 有序字典-从低价到高价
        self.gridMark = OrderedDict()
        _tmpRemainPosition = self.params.initPosition
        for price in self.params.gridPrice:
            if(price>=self.params.benchmarkPrice):
                if((_tmpRemainPosition-self.params.eachBSPos) >= 0):
                    self.gridMark[price]=self.params.eachBSPos
                    _tmpRemainPosition -= self.params.eachBSPos
                else:
                    self.gridMark[price] = _tmpRemainPosition
                    _tmpRemainPosition = 0;
            else:
                self.gridMark[price] = 0

        print('gridMark = %s' % self.gridMark)
        print('posSize  = %s' % cerebro.broker.getposition(self.datas[0]).size)
        print('posPrice = %s' % cerebro.broker.getposition(self.datas[0]).price)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Buy, Buy, Buy
        for key in sorted(self.gridMark, reverse=True):
            # 当价格跌到网格下方，且当前网格没有持仓时则买入份额
            if ((key != self.params.gridPrice[-1]) and (self.dataclose[0] <= key) and (self.gridMark[key] == 0)):
                self.order = self.buy()
                self.gridMark[key] = self.params.eachBSPos
                self.totalBuy += 1
                # BUY, BUY, BUY!!! (with default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

        # Sell, Sell, Sell 
        for num in range(0, len(self.params.gridPrice)-1):
            key = self.params.gridPrice[num]
            keyNext = self.params.gridPrice[num+1]
            value = self.gridMark[key]
            if((self.dataclose[0] >= key) and (value > 0)):
                if(self.dataclose[0] >= keyNext):
                    self.order = self.sell()
                    remainPos = value - self.params.eachBSPos
                    self.gridMark[key] = remainPos if remainPos >= 0 else 0
                    self.totalSell += 1
                     # SELL, SELL, SELL!!! (with all possible default parameters)
                    self.log('SELL CREATE, %.2f' % self.dataclose[0])

    def stop(self):
        print("==========================") 
        print('posSize  = %s' % cerebro.broker.getposition(self.datas[0]).size)
        print('posPrice = %s' % cerebro.broker.getposition(self.datas[0]).price)
        print("==========================") 
        print("Total Buy/Sell: %s/%s initBuy: %s" % (self.totalBuy, self.totalSell, math.floor(self.params.initPosition / self.params.eachBSPos))) 
        for key, value in self.gridMark.items():
            print("gridMark: [%s] - %s" % (key, value)) 
        print("==========================") 


if __name__ == '__main__':

    gridParams = {
        'initCash': 100000,
        'cashUsageRate': 0.7,  # To prevent loss too much in the early stages and cann't buy sufficient positions at the low price level
        'lowLimitPrice': 1.026,
        'highLimitPrice': 1.11,
        'benchmarkPrice': 1.06,
        'stepPrice': 0.01,
        
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

    gridParams['highGridNum'] = math.floor((gridParams['highLimitPrice'] - gridParams['benchmarkPrice'])/gridParams['stepPrice'])
    gridParams['lowGridNum'] = math.floor((gridParams['benchmarkPrice'] - gridParams['lowLimitPrice'])/gridParams['stepPrice'])
    for num in range(1, gridParams['highGridNum']+1):
        gridParams['highGridPrice'].append(gridParams['benchmarkPrice']+num*gridParams['stepPrice'])
    
    for num in range(gridParams['lowGridNum'], 0, -1 ):
        gridParams['lowGridPrice'].append(gridParams['benchmarkPrice']-num*gridParams['stepPrice'])
    
    gridParams['gridPrice'] = gridParams['lowGridPrice'] + [gridParams['benchmarkPrice'],] + gridParams['highGridPrice']
    # 份数， 非股数
    remianPosition = (((gridParams['lowGridPrice'][0] + gridParams['lowGridPrice'][-1]) / 2) / gridParams['benchmarkPrice']) * gridParams['lowGridNum']
    # 每一份 金额
    initPosCash = math.floor(gridParams['initCash'] * gridParams['cashUsageRate'] / (gridParams['highGridNum'] + remianPosition))
    gridParams['eachBSPos'] = math.floor(initPosCash / gridParams['benchmarkPrice'] /100) * 100
    gridParams['initPosition'] = math.floor((gridParams['highGridNum']) * gridParams['eachBSPos'])
    gridParams['initConsumeCash'] = gridParams['benchmarkPrice'] * gridParams['initPosition']
    gridParams['initRemainCash'] = gridParams['initCash'] - gridParams['initConsumeCash']
    gridParams['initReachCash'] = (gridParams['initPosition'] + remianPosition * gridParams['eachBSPos']) * gridParams['benchmarkPrice']

    print(gridParams)
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy, initPosition=gridParams['initPosition'], benchmarkPrice=gridParams['benchmarkPrice'], 
                        gridPrice=gridParams['gridPrice'], eachBSPos=gridParams['eachBSPos'])

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

    # Set our desired cash start
    cerebro.broker.setcash(gridParams['initCash'])

    # # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=gridParams['eachBSPos'])
    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.003)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Plot the result
    cerebro.plot()