from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt


# Create a Stratey
class TestStrategy(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)

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

        
        print('%s, %s' % (dt.isoformat(), txt))
    

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])


if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(TestStrategy)

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
        todate=datetime.datetime(2020, 12, 31),
        # Do not pass values after this date
        reverse=False)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())