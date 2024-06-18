'''
Author: Huang, Quan Hang 250901214@qq.com
Date: 2024-06-04 23:02:10
LastEditors: Huang, Quan Hang quanhang.huang@siemens.com
LastEditTime: 2024-06-18 11:29:29
FilePath: \myBacktrader\myExample\pandas\test.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
import msvcrt
import csv

with open('./11.csv', 'a+', encoding='UTF-8', newline='') as csvfile:
    csv_write = csv.writer(csvfile)
    fileNo:int = csvfile.fileno()
    msvcrt.locking(fileNo, msvcrt.LK_LOCK, 10)
    csvfile.seek(0, 0)
    csv_write.writerow([1,3])

    msvcrt.locking(fileNo, msvcrt.LK_UNLCK, 10)
    csvfile.close()