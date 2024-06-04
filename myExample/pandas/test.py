'''
Author: Huang, Quan Hang 250901214@qq.com
Date: 2024-06-04 23:02:10
LastEditors: Huang, Quan Hang 250901214@qq.com
LastEditTime: 2024-06-04 23:16:20
FilePath: \myBacktrader\myExample\pandas\test.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import pandas as pd

df2 = pd.DataFrame([['b', 20], ['a', 10], ['c', 30]], columns= ["let","num"], index=["A1", "B2", "C"])

print(df2)

# print(df2.reset_index(drop=True))

print(df2.reset_index(drop=False, inplace=True))

#print(df2)