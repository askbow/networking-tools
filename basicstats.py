#!/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
try:
    from future_builtins import *
except ImportError:
    pass

import csv
from statistics import mean, median, stdev
import numpy as np

# basicstats.py
# Computes basic statistics over time-series data exported from network monitoring system
# Useful when you need to baseline your network load (e.g. interface load, CPU)
# 
# MIT license
# (c) Denis Borchev 


infiles = ["node-day-in.csv",
"node-month-in.csv",
"node-quarter-in.csv",
"node-year-in.csv",
]

node = ["node",] # i.e. corea-nyc, access-ams
period = ["day", "month", "quarter", "year"]

def LoadData():
    # parses input files
    datad = dict()
    for ff in infiles:
        label = ""
        for n in node:
            if n in ff: label+=n
        label+="-"
        for p in period:
            if p in ff: label+=p
        dataReader = csv.DictReader(open(ff))
        for row in dataReader:
            for rr in row:
                if rr=='value': # this is specific to export format of our network monitoring system
                    if label in datad:
                        datad[label].append(float(row[rr]))
                    else:
                        l = list()
                        l.append(float(row[rr]))
                        datad[label] = l        
    return datad

def computeStats(datalist=list(),name=""):
    # compute and print out basic statistics
    d = dict()
    d['name'] = name
    d['mean'] = mean(datalist)
    d['median'] = median(datalist)
    d['stdev'] = stdev(datalist)
    a = np.array(datalist)
    d['percentile95'] = np.percentile(a, 95)
    d['min'] = min(datalist)
    d['max'] = max(datalist)
    for k in d:
       print(k, d[k])
    return d
    
def main():
    #
    netinput = LoadData()
    for oname in netinput:
        print(oname)
        computeStats(datalist=netinput[oname],name=oname)
    # EOF
if __name__ == '__main__':
    main()