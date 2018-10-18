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

from scapy.all import *
from datetime import datetime
from time import sleep
import os
import signal
import sys

# foxhunt.py
# Prints out RSSI to selected client MAC on WiFi iface
# Useful with this commit
# https://github.com/askbow/BakeBit/commit/dc4027b6c8a66302691d329806b6a9d05007e8a8
# for example, to play foxhunt radio game with wlanpi ( https://www.wlanpi.com/ ), 
# or do some more practical things during radio survey or WiFi operations day-to-day tasks
# 
# MIT license
# (c) Denis Borchev, idea by Kirill Schekuteev

def PacketHandler(pkt) :
  os.putenv("FIND_DEVICE", "1")
  if pkt.haslayer(Dot11) :
    #print(pkt.addr2)
    #
    if pkt.addr2 and sys.argv[2] in pkt.addr2:
        extra = pkt.notdecoded
        rssi = str(-(256 - ord(extra[-4:-3])))
        f = open(u'/tmp/foxhunt.dat','w')
        print(rssi,"\t", pkt.addr2[-6:])
        f.write("F>"+pkt.addr2[-6:]+" "+rssi)
        #f.write(rssi)
        f.close()

def Usage():
    print("\n Usage:\n")
    print("\t%s {interface} [client_mac]\n"%sys.argv[0])
    exit()
        
def main():
    if len(sys.argv)<3: Usage()
    sniff(iface=sys.argv[1], prn = PacketHandler)

def exit_gracefully(signum, frame): #https://stackoverflow.com/a/18115530
    # restore the original signal handler as otherwise evil things will happen
    # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
    signal.signal(signal.SIGINT, original_sigint)

    try:
        os.remove(u'/tmp/foxhunt.dat') 
        sys.exit(1)

    except KeyboardInterrupt:
        print("Ok ok, quitting")
        sys.exit(1)

    # restore the exit gracefully handler here    
    signal.signal(signal.SIGINT, exit_gracefully)

original_sigint = signal.getsignal(signal.SIGINT)
if __name__ == '__main__':
    # store the original SIGINT handler
    #original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)
    main()
    
