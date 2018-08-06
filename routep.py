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
import re

# routep.py
# Creates static routes from dinamicly-learned (e.g. OSPF, EIGRP, BGP, RIP) ones
# Useful when you need to re-do your routing domain with minimum downtime,
# for example, move/renumber/type change OSPF areas
# 
# MIT license
# (c) Denis Borchev 

##############################################################
# code definitions were taken from a Cisco router and might be subject to their copyright
# 
Codes = {"L":"local", "C":"connected", "S":"static", "R":"RIP", "M":"mobile", "B":"BGP", "I":"IGRP", "E":"EGP",
       "D":"EIGRP", "EX":"EIGRP external", "O":"OSPF", "IA":"OSPF inter area", 
       "N1":"OSPF NSSA external type 1", "N2":"OSPF NSSA external type 2",
       "E1":"OSPF external type 1", "E2":"OSPF external type 2",
       "i":"IS-IS", "su":"IS-IS summary", "L1":"IS-IS level-1", "L2":"IS-IS level-2",
       "ia":"IS-IS inter area", "*":"candidate default", "U":"per-user static route",
       "o":"ODR", "P":"periodic downloaded static route", "H":"NHRP", "l":"LISP",
       "+":"replicated route", "%":"next hop override","via":"nexthop in next token"}


codesInitial = ("O","R","B","D","EX","i","o","I","E","O*","R*","B*","D*","EX*","i*","o*","I*","E*","O*E1")
codesIgnore =  ("S","L","C","S*")
ignorelist = ("Codes","external","level","candidate","downloaded","replicated","resort","variably","route","directly","summary","[BEGIN]","[END]","sh ip rou",'<---', 'More', '--->','sh rou','foreign','exit')
vrfToken = ("Routing Table:")
emptyLines = ('','\n','\t',' ','  ','   ',)

def shIPRouteImport(mode="file", fName=""):
    # imports only interesting lines from 'show ip route' output
    lst = list()
    if mode == "file":
        if fName == "": fName = u'shiproute.txt'
        try:
            for line in open(fName):
                nin = 0
                if vrfToken[0] in line: lst.append(line[:-1])
                for a in ignorelist:
                   if a in line: nin +=1
                if nin < 1 : lst.append(line[:-1]) # slice to remove linebreaks
        except:
            return lst
    #
    else: pass
    return lst

def shIProuteParser(source=""):
    # parses 'sh ip routes' into a dictionary of lists, each list containing nexthops for a prefix
    result = dict()
    lst = shIPRouteImport(fName=source)
    tempNet = IPNetwork("0.0.0.0")
    mask = '32'
    vrf = ""
    try:
        import getname
        names = getname.getname()
    except ImportError:
        names = dict()
    for l in lst:
        if l in emptyLines: continue
        element = l.split()
        le = len(element)
        if le > 1:
            if element[0] in codesIgnore: continue
            if element[0]=="Routing" and element[1]=="Table": vrf=element[2]
            if element[0] in codesInitial: 
                # we hit a line with a route in it, i.e.
                #  O E1 192.0.2.0/24 [110/202] via 192.0.2.1, 42d42h, GigabitEthernet0/0
                #  B 192.0.2.0/24 [20/0] via 192.0.2.1, 42w42d
                pos = 1
                adj = 0
                if element[pos] in Codes: pos+=1 # for cases like 'O E1'
                # we don't care about the source of the route past this point:
                clear = " ".join(element[pos:])
                # find prefix:
                ca = re.compile('^\d{1,3}(\.\d{1,3}){3}\/\d{1,2}$')
                if ca.match(element[pos]): # we're looking at 192.0.2.0/24
                    nnet = IPNetwork(element[pos])
                else:
                    ca = re.compile('^\d{1,3}(\.\d{1,3}){3} \d{1,3}(\.\d{1,3}){3}')
                    if ca.match(clear): # we're looking for 192.0.2.0 255.255.255.0
                        nnet = IPNetwork(element[pos] + "/" + element[pos+1])
                    ca = re.compile('^\d{1,3}(\.\d{1,3}){3} \[\d{1,3}\/\d+\]')
                    if ca.match(clear): # we're looking at 192.0.2.0 [110/250]
                        # the mask must've been listed on one of the preceeding lines
                        nnet = IPNetwork(element[pos] + "/" + mask)
                        pos -=1
                    pos += 1
                    adj +=1
                #
                # at this point, 'nnet' already stores an IPNetwork object
                result[nnet] = list()
                tempNet = nnet
                # find nexthop:
                # check if nexthop is on the same line:
                # O        192.0.2.0/24 [110/202] via 192.0.2.1, 5w5d, GigabitEthernet0/0
                ca = re.compile('^\d{1,3}(\.\d{1,3}){3}')
                c = ca.match(clear[clear.find("via")+4:])
                if c: 
                    nh = dict()
                    nh['ip'] = IPAddress(c.group())
                    if 'B' in element[0]: nh['iface'] = list()
                    else: nh['iface'] = element[-1:] # interface is always listed last
                    nh['vrf'] = vrf
                    result[nnet].append(nh)
                else: 
                    # let's see if we can resolve a name here:
                    subline = clear[clear.find("via")+4:].split()[0][:-1]
                    if subline in names.keys():
                        #print(nnet, "==> 172.21.255.165")
                        nh = dict()
                        nh['ip'] = IPAddress(names[subline])
                        nh['iface'] = element[-1:] # interface is always listed last
                        if 'B' in element[0]: nh['iface'] = list()
                        nh['vrf'] = vrf
                        #print("+add nexthop",nh)
                        result[nnet].append(nh)
                        continue
                    # nexthops are listed on subsequent lines
                    tempNet = nnet
                    continue
            else:
                # hadle special cases
                #
                # 
                if 'subnetted,' in element:
                    #   192.0.2.0/24 is subnetted, 42 subnets
                    # this line contains the mask for several subsequent lines
                    ca = re.compile('^\d{1,3}(\.\d{1,3}){3}\/\d{1,2}')
                    c = ca.match(" ".join(element)).group() # we're looking at 192.0.2.0/24
                    mask = c[c.find("/")+1:]
                    continue # no more usable info on this line
                #
                # the line contains a nexthop for a previous line, something like this:
                # O        192.0.2.0/24 
                #             [110/2] via 192.0.2.1, 4w5d, GigabitEthernet0/0
                #             [110/2] via 192.0.2.2, 4w5d, GigabitEthernet0/0
                pos = 1
                if element[pos] in Codes: pos+=1
                clear = " ".join(element[pos:])
                if tempNet in result:
                    ca = re.compile('^\d{1,3}(\.\d{1,3}){3}')
                    c = ca.match(clear[clear.find("via")+4:])
                    if c: 
                        nh = dict()
                        nh['ip'] = IPAddress(c.group())
                        if 'B' in element[0]: nh['iface'] = list()
                        else: nh['iface'] = element[-1:] # interface is always listed last
                        nh['vrf'] = vrf
                        result[nnet].append(nh)
                    else:
                        # let's see if we can resolve a name here:
                        subline = clear[clear.find("via")+4:].split()[0][:-1]
                        if subline in names.keys():
                            #print(nnet, "==> 172.21.255.165")
                            nh = dict()
                            nh['ip'] = IPAddress(names[subline])
                            nh['iface'] = element[-1:] # interface is always listed last
                            if 'B' in element[0]: nh['iface'] = list()
                            nh['vrf'] = vrf
                            #print("+add nexthop",nh)
                            result[nnet].append(nh)
                            continue
        else: #len(element) > 0:
            continue
    return result

def routeOptimize(routes=list(), mode="simple"):
    # slightly optimizes route table for lenght
    # trade-off: only one next-hop per prefix, adjacent prefixes are merged
    #            i.e. loss of detailed routing information and load-sharing
    if routes==list(): return routes
    result = dict()
    invertRoutes = dict()
    nhiface = dict()
    for r in routes:
        if len(routes[r]) < 1: continue # weird case
        if routes[r][0]["vrf"] not in invertRoutes:
            invertRoutes[routes[r][0]["vrf"]] = dict()
        if routes[r][0]["ip"] not in invertRoutes[routes[r][0]["vrf"]]:
            invertRoutes[routes[r][0]["vrf"]][routes[r][0]["ip"]] = list()
        invertRoutes[routes[r][0]["vrf"]][routes[r][0]["ip"]].append(r)
        nhiface[routes[r][0]["ip"]] = routes[r][0]["iface"]
    maxNH = IPAddress("0.0.0.0")
    maxR = 0
    for vrf in invertRoutes:
        for r in invertRoutes[vrf]:
            invertRoutes[r] = cidr_merge(invertRoutes[vrf][r])
            if len(invertRoutes[vrf][r]) > maxR: 
                maxNH = r
                maxR = len(invertRoutes[vrf][r])
    for vrf in invertRoutes:
        for r in invertRoutes[vrf]: 
            for rr in invertRoutes[r]:
                if rr not in result:
                    result[rr] = list()
                result[rr].append({"vrf":vrf,"ip":r, "iface":nhiface[r]})
    return result



def commandSet(mode="full", syntax="ciscoios"):
    # prepares a set of commands to instatiate static routes
    # the resulting list can be printed or passed to netmiko [ https://github.com/ktbyers/netmiko ]
    # modes:
    # - short - tries to optimize table lenght by merging adjacent prefixes in a safe way
    # - long  - one nexthop per original prefix
    # - full  - all known nexthops for each prefix'./sh ip route asadown.log','./sh ip route asainet.log',
    result = list()
    filelist = ["router.txt",]
    for f in filelist:
        #
        if 'asa' in f.lower(): syntax = 'ciscoasa'
        else: syntax="ciscoios"
        routes = shIProuteParser(source=f)
        if mode == "short": routes = routeOptimize(routes)
        elif mode == "long" or mode == "full": pass
        else: return result
        #
        str = "ip route "
        if syntax == "ciscoios":
            str = "ip route"
        elif syntax == "ciscoasa":
            str = "route"
        result.append("! Create static routes")
        result.append("! based on %s"%f)
        i = " "
        for r in routes:
            for nh in routes[r]:
                i = ""
                if nh['vrf'] > "":       i = i + "vrf " + nh['vrf']
                if syntax == "ciscoasa": i = i + nh['iface'][0]
            result.append(str +i+ " %s %s %s 253"%(r.ip, r.netmask, nh["ip"]) )
        result.append("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n")
    return result

def compareRT(fileA,fileB):
    #
    routingtableA = shIProuteParser(source=fileA)
    routingtableB = shIProuteParser(source=fileB)
    lra = len(routingtableA.keys())
    lrb = len(routingtableB.keys())
    if lra > lrb or lrb > lra: print("Number of prefixes differs")
    for pa in routingtableA:
        if pa not in routingtableB:
            for r in routingtableA[pa]:
                print("not in B",r)
            continue
        for r in routingtableA[pa]:
            if r not in routingtableB[pa]:
                print("not in A",r)
    for pb in routingtableB:
        if pb not in routingtableA:
            for r in routingtableB[pb]:
                print("not in A",r)
            continue
        for r in routingtableB[pb]:
            if r not in routingtableA[pb]:
                print("not in A",r)
    
        
    
def main():
    #
    cconfig = list()
    coml = commandSet(mode="short")
    for c in coml:
        print(c)
    
if __name__ == '__main__':
    main()