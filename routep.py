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

import sys
from netaddr import *

# routep.py
# Creates static routes from dinamicly-learned (e.g. OSPF, EIGRP, BGP, RIP) ones
# Useful when you need to re-do your routing domain with minimum downtime,
# for example, move/renumber/type change OSPF areas
# 
# MIT license
# (c) Denis Borchev 

##############################################################
# code definitions were taken from a Cisco router and might be subject to their copyright
Codes = {"L":"local", "C":"connected", "S":"static", "R":"RIP", "M":"mobile", "B":"BGP",
       "D":"EIGRP", "EX":"EIGRP external", "O":"OSPF", "IA":"OSPF inter area", 
       "N1":"OSPF NSSA external type 1", "N2":"OSPF NSSA external type 2",
       "E1":"OSPF external type 1", "E2":"OSPF external type 2",
       "i":"IS-IS", "su":"IS-IS summary", "L1":"IS-IS level-1", "L2":"IS-IS level-2",
       "ia":"IS-IS inter area", "*":"candidate default", "U":"per-user static route",
       "o":"ODR", "P":"periodic downloaded static route", "H":"NHRP", "l":"LISP",
       "+":"replicated route", "%":"next hop override","via":"nexthop in next token"}


codesInitial = ["O","R","B","D","EX","i","o",]
codesIgnore =  ["S","L",]
ignorelist = ["Codes","external","level","candidate","downloaded","replicated","resort","variably","route","directly",]

def shIPRouteImport(mode="file", fName=""):
    # imports only interesting lines from 'show ip route' output
    lst = list()
    if mode == "file":
        if fName == "": fName = u'shiproute.txt'
        try:
            for line in open(fName):
                nin = 0
                for a in ignorelist:
                   if a in line: nin +=1
                if nin < 1 : lst.append(line)
        except:
            return lst
    #
    else: pass
    return lst

def shIProuteParser():
    # parses 'sh ip routes' into a dictionary of lists, each list containing nexthops for a prefix
    result = dict()
    lst = shIPRouteImport()
    tempNet = IPNetwork("0.0.0.0")
    for l in lst:
        element = l.split()
        le = len(element)
        if le > 0:
            if element[0] in codesIgnore: continue
            if element[0] in codesInitial:
                pos = 1
                if element[pos] in Codes: pos+=1
                if '/' in element[pos]: # we're looking at 192.0.2.0/24
                    nnet = IPNetwork(element[pos])
                else: # we're looking at 192.0.2.0 255.255.255.0
                    nnet = IPNetwork(element[pos] + "/" + element[pos+1])
                    pos += 1
                result[nnet] = list()
                if le > 3: # nexthop on the same line
                    result[nnet].append(IPAddress(element[pos+3][:-1]))
                else: # nexthops are listed on subsequent lines
                    tempNet = nnet
            else:
                #append to prev.route
                pos = 1
                if element[pos] in Codes: pos+=1
                if tempNet in result:
                    result[tempNet].append(IPAddress(element[pos][:-1]))
        else: #len(element) > 0:
            continue
    return result

def routeOptimize(routes=list(), mode="simple"):
    # slightly optimizes route table for lenght
    # trade-off: only one next-hop per prefix, adjacent prefixes are merged
    #            i.e. loss of detailed routing information
    if routes==list(): return routes
    result = dict()
    invertRoutes = dict()
    for r in routes:
        if routes[r][0] not in invertRoutes:
            invertRoutes[routes[r][0]] = list()
        invertRoutes[routes[r][0]].append(r)
    maxNH = IPAddress("0.0.0.0")
    maxR = 0
    for r in invertRoutes:
        invertRoutes[r] = cidr_merge(invertRoutes[r])
        if len(invertRoutes[r]) > maxR: 
            maxNH = r
            maxR = len(invertRoutes[r])
    for r in invertRoutes:    
        if mode == "super": # DANGER! This option may create routing loops
            if r == maxNH: 
                result[IPNetwork("0.0.0.0")] = [r]
                continue
        for rr in invertRoutes[r]:
            if rr not in result:
                result[rr] = list()
            result[rr].append(r)
    return result

def commandSet(mode="short"):
    # prepares a set of commands to instatiate static routes
    # the resulting list can be printed or passed to netmiko [ https://github.com/ktbyers/netmiko ]
    # modes:
    # - short - tries to optimize table lenght by merging adjacent prefixes
    # - long  - one nexthop per original prefix
    # - full  - all known nexthops for each prefix
    result = list()
    if mode == "short": routes = routeOptimize(shIProuteParser())
    elif mode == "long" or mode == "full": routes = shIProuteParser()
    else: return result
    #
    for r in routes:
        if mode == "short" or mode=="long": result.append("ip route %s %s %s 242"%(r.ip, r.netmask, routes[r][0]) )
        if mode == "full":
            for nh in routes[r]:
                result.append("ip route %s %s %s 242"%(r.ip, r.netmask, nh) )
    #
    return result

    
def main():
    #
    cconfig = list()
    coml = commandSet(mode="full")
    for c in coml:
        print(c)
    
if __name__ == '__main__':
    main()