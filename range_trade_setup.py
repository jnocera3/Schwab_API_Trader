#!/usr/bin/python

shares = 10
maxshares = 600
buyprice = 41.21
sellprice = 42.01
buyinc = 0.10

for sharecount in range(shares, maxshares+shares, shares):
    print(str(sharecount) + ", " + str(round(buyprice,2)) + ", " + str(round(sellprice,2)))
    buyprice = buyprice - buyinc
    sellprice = sellprice - buyinc
