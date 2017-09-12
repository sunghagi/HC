#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import csv
from lib.log import *

logger = HcLogger()

def bytes2human(n):
    # http://code.activestate.com/recipes/578019 
    # >>> bytes2human(10000) 
    # '9.8K' 
    # >>> bytes2human(100001221) 
    # '95.4M' 
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n

def comment_remove(ConfigValueWithComment):
    ConfigValue=ConfigValueWithComment.split('#', 1)[0].strip()
    return ConfigValue

def disk_node_usage(path):
    disk = {}
    disk['total_no_of_nodes'] = os.statvfs(path).f_files
    disk['total_no_of_free_nodes'] = os.statvfs(path).f_ffree

    return disk

#def GetCurFunc():
#   return inspect.stack()[1][3]

def oneline_print(str):
    return str[:75] + '...' + '\n'

def split2len(s, n):
    def _f(s, n):
        while s:
            yield s[:n]
            s = s[n:]
    return list(_f(s,n))

def string_concate(a, b):
    if not isinstance(b, str):
        b = str(b)

    string_list = []
    string_list.append(a)
    string_list.append(b)

    try:
        return ''.join(string_list)
    except Exception as e:
        logger.exception('%s :: error : %s', GetCurFunc(), e)

def SaveResultCsv(CsvFileName, ResultList):
    try :
        with open(CsvFileName, 'a') as f:
            writer = csv.writer(f)
            writer.writerows(ResultList)
            logger.info('%s : Write to csv file result : success', GetCurFunc())
    except Exception as e:
        logger.exception('%s :: CSV file handle error : %s', GetCurFunc(), e)

def get_dashes(perc):
    dashes = "|" * int((float(perc) / 10 * 4))
    empty_dashes = " " * (40 - len(dashes)) 
    return dashes, empty_dashes 
   
def pprint_ntuple(nt):
    for name in nt._fields:
        value = getattr(nt, name)
        if name != 'percent': 
            value = bytes2human(value)
        print('%-10s : %7s' % (name.capitalize(), value))
      
def single_grep(STR, FILE_PATH):
    for line in open(FILE_PATH):
        if STR in line:
            line_without_crlf = ''.join(line.splitlines())
            return line_without_crlf
         
def netmask2cidr(NETMASK):
    cidr = sum([bin(int(x)).count("1") for x in NETMASK.split(".")])
    return str(cidr)

def get_bond(): 
    try: 
        path = "/proc/net/bonding/" 
        bondList = os.listdir(path) 
        return bondList 
    except Exception: 
        return 

def check_bond_status(strBondName): 
    try: 
        bondStatus = {} 
        slave_iface = []
        n = 0 
        strBondPath = "/proc/net/bonding/%s" % strBondName 
        for line in open(strBondPath).readlines(): 
            if "Currently Active Slave" in line:
                active = line.split(":")
                active = active[1].strip()
                bondStatus['active'] = active 
            if "MII Status" in line: 
                if n >= 1:
                    n = n + 1 
                    continue
                strState = line.split(":") 
                strState = strState[1].strip() 
                if strState != "up": 
                    # bond nok 
                    intState = 1 
                    bondStatus['intState'] = intState 
                    bondStatus['strState'] = strState 
                    # we stop at first error 
                    return bondStatus 
                else: 
                    # bond ok 
                    n = n + 1 
                    intState = 0 
                    bondStatus['intState'] = intState 
                    bondStatus['strState'] = strState 
            if "Slave Interface" in line:
                iface = line.split(":")
                iface = iface[1].strip()
                slave_iface.append(iface)
                bondStatus['slave_iface'] = slave_iface 

        # we expect to find 3 "up" in our typical bond, trigg error if not 
        if n != 3: 
            intState = 1 
            strState = "One NIC is missing in bond" 
            bondStatus['intState'] = intState 
            bondStatus['strState'] = strState 
        return bondStatus 
    except Exception: 
        return 
