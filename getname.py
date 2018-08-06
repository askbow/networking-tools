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

# getname.py
# An extension to routep.py
# Scans configs for name resolution lines, i.e. on Cisco ASA where you can have 
# sh route have something like
#  O E1 192.0.2.0/24 [110/202] via some-string-name, 42d42h, GigabitEthernet0/0
#
# MIT license
# (c) Denis Borchev 

CONFIG_LOOKUP_DIR = "./shrun/"

def __listfiles__(mypath="./"):
    #https://stackoverflow.com/a/3207973
    from os import listdir
    from os.path import isfile, join
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    return onlyfiles

def fileImport(mode="file", fName=""):
    # 
    lst = list()
    if mode == "file":
        if fName == "": fName = u'shrun.txt'
        try:
            for line in open(fName):
                nin = 0
                if nin < 1 : lst.append(line[:-1])
        except:
            return lst
    #
    else: pass
    return lst

def getname():
    files = __listfiles__(CONFIG_LOOKUP_DIR)
    names = dict()
    for file in files:
        #print("!",file)
        fl = fileImport(fName=CONFIG_LOOKUP_DIR+file)
        for line in fl:
            if "name" not in line: continue
            elements = line.split()
            le = len(elements)
            if le < 3: continue
            if elements[0]=="name":
               if elements[2] in names.keys():
                   if names[elements[2]] == elements[1]  : continue
                   else: print("!WARNING: possible name conflict:",elements[2],names[elements[2]],elements[1])
               else:
                   names[elements[2]] = elements[1]               
            else:
                continue
    return names
    
    
def main():
    #
    cconfig = list()
    coml = getname( )
    for c in coml:
        print(c, "=>", coml[c])
    
if __name__ == '__main__':
    main()