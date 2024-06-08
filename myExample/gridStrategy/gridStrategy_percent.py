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
import yfinance as yf

# Global
maxPortfolio = 0
isPrint = True
# isPrint = False
share="159652.SZ"
interval="1d"
# Create a Stratey
class TestStrategy(bt.Strategy):
    
    params = (
        ('grid', {} ),
    )
    # params = (
    #     ('initCash', 0),        # 资金
    #     ('eachBSPos', 0),       # 每次交易份额(股)
    #     ('stepPercent', 0),     # 网格间隔 %
    #     ('totalGridNum', 0),    # 总共格子数(个)
    #     ('benchmarkPrice', 0),  # 基准价(元)
    #     ('lowLimitPrice', 0),   # 最低限价(元)
    #     ('highLimitPrice', 0),  # 最高限价(元)
    # )

    
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

        self.log("------------init----------", doPrint=isPrint) 
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.totalSell = 0
        self.totalBuy = 0
        self.benchmarkPrice = 0
        
        # Init
        self.broker.setcash(self.params.grid['initCash'])

        self.log('initCash = %d, eachBSPos = %d, stepPercent = %.2f%%' % (self.params.grid['initCash'], self.params.grid['eachBSPos'], 
                    self.params.grid['stepPercent']*100), doPrint=isPrint)


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
                     self.broker.getposition(self.datas[0]).size), doPrint=isPrint)

            else:  # Sell
                self.totalSell += 1
                self.log('SELL EXECUTED, Price: %.2f, Size: %d, Cost: %.2f, Net: %.2f, Comm %.2f, 持仓量 %d(股)' %
                         (order.executed.price,
                          - order.executed.size,
                          - (order.executed.price * order.executed.size),
                          (- (order.executed.price * order.executed.size) - order.executed.value),
                          order.executed.comm,
                          self.broker.getposition(self.datas[0]).size), doPrint=isPrint)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected', doPrint=isPrint)

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' % (trade.pnl, trade.pnlcomm), doPrint=isPrint)
        self.log('持仓量  = %d(股), 现价 = %.2f(元), 成本价 = %s(元), 价值 = %.2f(元), 现金 = %.2f(元)' % (
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
            self.log('BUY CREATE, %.2f, Size:  %d' % (self.dataclose[0], self.params.grid['eachBSPos'] * totalBuyNum), doPrint=isPrint)
        else:
            if (self.dataclose[0] <= (self.benchmarkPrice * ( 1 - self.params.grid['stepPercent'])) and 
                self.dataclose[0] <= self.params.grid['highLimitPrice']):
                # BUY, BUY, BUY!!! (with default parameters)
                buyPos = self.getBuyPos(cash=self.broker.getcash(), price=self.dataclose[0], position=self.params.grid['eachBSPos'])
                self.order = self.buy(size=buyPos)
                self.log('BUY CREATE, %.2f, benchmarkPrice: %.2f: -%.2f%%, Size:  %d, ' % (self.dataclose[0], 
                            self.benchmarkPrice, (self.benchmarkPrice - self.dataclose[0]) / self.benchmarkPrice * 100, 
                            self.params.grid['eachBSPos']), doPrint=isPrint)
            
            elif (self.dataclose[0] >= (self.benchmarkPrice * ( 1 + self.params.grid['stepPercent'])) and
                  self.dataclose[0] >= self.params.grid['lowLimitPrice']):
                    remainPos = self.broker.getposition(self.datas[0]).size - self.params.grid['eachBSPos']
                    remainPos = self.params.grid['eachBSPos'] if remainPos >= 0 else self.broker.getposition(self.datas[0]).size
                    if(remainPos > 0):
                        self.order = self.sell(size=remainPos)
                        # SELL, SELL, SELL!!! (with all possible default parameters)
                        self.log('SELL CREATE, %.2f, benchmarkPrice: %.2f: +%.2f%%, Size:  %d' % (self.dataclose[0], 
                                    self.benchmarkPrice, (self.dataclose[0] - self.benchmarkPrice) / self.benchmarkPrice * 100,                                                              
                                    remainPos), doPrint=isPrint)
            else:
                pass

    def stop(self):

        global maxPortfolio
        if (self.broker.getvalue() > maxPortfolio):
            maxPortfolio = self.broker.getvalue()
            self.log("------------stop----------", doPrint=isPrint) 
            # Print out the final result
            self.log('Final Portfolio Value: %.2f, Net: %.2f, Percent: %.2f%%, eachBSPos: %d(股), stepPercent: %.2f%%, benchmarkPrice: %.2f(元) totalGridNum: %d(个), Buy/Sell: %s/%s, 持仓量  = %d(股), 现价 = %.2f(元)' % (
                self.broker.getvalue(),
                self.broker.getvalue()-self.params.grid['initCash'],
                (self.broker.getvalue()-self.params.grid['initCash']) / self.params.grid['initCash'] * 100,
                self.params.grid['eachBSPos'],
                self.params.grid['stepPercent'] * 100,
                self.params.grid['benchmarkPrice'],
                self.params.grid['totalGridNum'],
                self.totalBuy,
                self.totalSell,
                self.broker.getposition(self.datas[0]).size,
                self.broker.getposition(self.datas[0]).adjbase
            ), doPrint=True)
            self.log("==========================", doPrint=isPrint) 

if __name__ == '__main__':

    # Create a cerebro entity
    cerebro = bt.Cerebro(optreturn=False)

    strageParams = {'initCash': 35000, 'cashUsageRate': 0.9, 'lowLimitPrice': 0.88, 'highLimitPrice': 1, 'benchmarkPrice': '1'}
    grids = []

    percent = round(((strageParams['highLimitPrice'] / strageParams['lowLimitPrice']) - 1), 4)
    stepPercents = numpy.arange(0.0001, percent, 0.0001)
    stepPercents = numpy.around(stepPercents, decimals=4)
    if isPrint:
        stepPercents = [0.0414]
    for stepPercent in stepPercents:
        
        gridParams = {
            'initCash': strageParams['initCash'],
            'cashUsageRate': strageParams['cashUsageRate'],  # To prevent loss too much in the early stages and cann't buy sufficient positions at the low price level
            'lowLimitPrice': strageParams['lowLimitPrice'],
            'highLimitPrice': strageParams['highLimitPrice'],
            
            'stepPercent': 0.0001,   # 唯一变量
            
            # 计算得出值 
            'totalGridNum': 0,       # 总共格子数
            'eachBSPos': 0,          #  每次交易股数(股) 整100股/1手交易
            'benchmarkPrice': 1,     # 取中间值， 这里没用到
        }
        
        gridParams['stepPercent'] = stepPercent
        gridParams['benchmarkPrice'] = round(((gridParams['highLimitPrice'] + gridParams['lowLimitPrice']) / 2), 3)
        
        lowPrice = gridParams['lowLimitPrice']
        highPrice = gridParams['highLimitPrice']
        priceGrid = []
        cashGride = []

        # 最多上下10格
        if (lowPrice * math.pow((1+stepPercent), 11) < highPrice):
            continue
        else:
            curPrice = lowPrice
            for num in range(0, 10):
                curPrice = round(curPrice*(1+stepPercent), 3)
                if(curPrice > gridParams['highLimitPrice']):
                    break
                else:
                    gridParams['totalGridNum'] += 1
                    highPrice = curPrice
                    priceGrid.append(curPrice)
        # 最少2格
        if(gridParams['totalGridNum']<2):
            continue 


        # 每一份 金额
        useCash = gridParams['initCash'] * gridParams['cashUsageRate']
        aveagePrice = (lowPrice + highPrice) / 2
        gridNumAdj = (( aveagePrice / lowPrice) * gridParams['totalGridNum'])
        gridParams['eachBSPos'] = math.floor( useCash / gridNumAdj / aveagePrice / 100 ) * 100
        
        if(gridParams['eachBSPos']==0):
            continue

        for price in priceGrid:
            cash = round(price * gridParams['eachBSPos'], 3)
            if(len(cashGride)==0):
                cashGride.append(cash)
            else:
                cashGride.append(cash+cashGride[len(cashGride)-1])

        cashGride = numpy.around(cashGride, decimals=3)
    
        grid = {}
        grid['eachBSPos'] = gridParams['eachBSPos']
        grid['stepPercent'] = gridParams['stepPercent']
        grid['totalGridNum'] = gridParams['totalGridNum']
        grid['initCash'] = gridParams['initCash']
        grid['benchmarkPrice'] = gridParams['benchmarkPrice']
        grid['lowLimitPrice'] = gridParams['lowLimitPrice']
        grid['highLimitPrice'] = gridParams['highLimitPrice']
        grids.append(grid)
    
    # Add a strategy
    cerebro.optstrategy(TestStrategy, grid=grids)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    csvpath='..\\..\\yfDataFeed\\' + share + '_' + interval + '.csv'
    datapath = os.path.join(modpath, csvpath)
    data = None
    # download
    if (not isPrint):
        data = yf.download(share, interval="1d")
        data.to_csv(datapath)

    # Create a Data Feed
    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2024, 4, 1),
        # Do not pass values before this date
        todate=datetime.datetime(2024, 6, 9),
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

    