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

# minipprefix.py
# Aggressively compresses a list of prefixes into supernets
# Useful when you need to minify a prefix list (e.g. for an ACL)
# Beacuse cidr_merge although more correct, is not aggressive enought for some cases
# 
# MIT license
# (c) Denis Borchev 


def ipSmashMerge(iplist, ipv4len = 24, ipv6len = 64, lengap=0, threshold = 3):
    # 
    superlist = dict()
    maxlen = 128
    minlen = 0
    retlist = []
    for ip in iplist:
        if ip.version == 4: 
            maxlen = ipv4len
            if lengap==0: minlen = 32
            else: minlen = maxlen+lengap
        if ip.version == 6: 
            maxlen = ipv6len
            if lengap==0: minlen = 128
            else: minlen = maxlen+lengap
        if ip.prefixlen > maxlen and minlen>=ip.prefixlen:
            if ip.supernet(maxlen)[0] in superlist:
                superlist[ip.supernet(maxlen)[0]]+=1
            else:
                superlist[ip.supernet(maxlen)[0]]=1
        retlist.append(ip)
    for ipnet in superlist:
        if superlist[ipnet] >= threshold:
            retlist.append(ipnet)
    return cidr_merge(retlist)

def ipv6subnet64(iplist):
    # normilize IPv6 prefix lenght to at most 64
    retlist = []
    for ip in iplist:
        if ip.version == 6:
            if ip.prefixlen >= 64:
                ip.prefixlen = 64
                ip = ip.cidr
        retlist.append(ip)
    return retlist

def main():
    iplist = list()
    try:
        with open (sys.argv[1], "r") as fp:
            iplist = [IPNetwork(q) for q in fp.read().splitlines()]
    iplist.sort()
    iplist = ipv6subnet64(iplist)
    iplist = ipSmashMerge(iplist)
    # turn aggression to 11:
    iplist = ipSmashMerge(iplist, ipv4len = 22, ipv6len = 48, lengap=2)
    iplist = ipSmashMerge(iplist, ipv4len = 20, ipv6len = 44, lengap=2)
    iplist = ipSmashMerge(iplist, ipv4len = 16, ipv6len = 40, lengap=4)
    iplist = ipSmashMerge(iplist, ipv4len = 12, ipv6len = 36, lengap=4)
    iplist = ipSmashMerge(iplist, ipv4len = 10, ipv6len = 34, lengap=2)
    iplist = ipSmashMerge(iplist, ipv4len = 8, ipv6len = 32, lengap=2)
    for i in iplist:
        print i

if __name__ == '__main__':
    main()
# EOF
