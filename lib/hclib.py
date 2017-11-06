#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import csv
import psutil
from collections import namedtuple
from hostconf import *
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

def get_value_after_sep(str_line):
    value = str_line.split(":")[-1].strip()
    return value

class BondStatus(object):
    __slots__ = ('mode', 'active', 'slave_iface', 'intState', 'strState', 'slave_iface_status')
    def __init__(self):
        self.mode = ""
        self.active = ""
        self.slave_iface = []
        self.slave_iface_status = []
        self.intState = 0
        self.strState = ""

def get_between_parentheses(str):
    return (str.split('('))[1].split(')')[0]

def check_bond_status(strBondName): 
    bondStatus = BondStatus()
    mii_status = []
    slave_iface = []
    n = 0 

    strBondPath = "/proc/net/bonding/%s" % strBondName 
    for line in open(strBondPath).readlines(): 
        if "Bonding Mode" in line:
#            mode = get_value_after_sep(line)
            mode = get_between_parentheses(line)
            bondStatus.mode = mode 
        if "Currently Active Slave" in line:
            active = get_value_after_sep(line)
            bondStatus.active = active 
        if "MII Status" in line: 
            strState = get_value_after_sep(line)
            mii_status.append(strState)
            n = n + 1 
        if "Slave Interface" in line:
            iface = get_value_after_sep(line)
            slave_iface.append(iface)
            bondStatus.slave_iface = slave_iface 

    if mii_status[0] != "up": 
        # bond nok 
        intState = 1 
        strState = mii_status[0]
        bondStatus.intState = intState 
        bondStatus.strState = strState
        # we stop at first error 
        return bondStatus 
    else: 
        # bond ok 
        intState = 0 
        strState = mii_status[0]
        bondStatus.intState = intState 
        bondStatus.strState = strState

    bondStatus.slave_iface_status = mii_status[1:]

    # we expect to find 3 "up" in our typical bond, trigg error if not 
    if n != 3: 
        intState = 1 
        strState = "One NIC is missing in bond" 
        bondStatus.intState = intState 
        bondStatus.strState = strState 

    return bondStatus 

def get_IP_list():
    ''' return IP address list
    '''
    IP_list = []
    for nic, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == 2 :
                IP_list.append(addr.address)
#                   print(" address   : %s" % addr.address)
#               print(" family :  : %s" % addr.family)
    return IP_list

def get_ha_status():
    ha_status = []

    IP_list = get_IP_list()
    logger.info('%s : IP address : %s', GetCurFunc(), IP_list)

    st_ha_operating_mode = 'STANDBY'
    for IP in IP_list:
        for hostlist in HostConf:
            if IP in hostlist:
                host_class = hostlist[2]
                if hostlist[1] == 'VIP':
                    st_ha_operating_mode = 'ACTIVE'
                    logger.info('%s : This host is Active', GetCurFunc())
                    break
    for hostlist in HostConf:
        if host_class in hostlist:
            if hostlist[1] == 'VIP':
                ha_installed = 1
                logger.info('%s : This %s is HA', GetCurFunc(), host_class)
                break
            else:
                ha_installed = 0
                if st_ha_operating_mode == 'STANDBY' and ha_installed == 0:
                    st_ha_operating_mode = 'ACTIVE'

    ha_status.append(st_ha_operating_mode)
    ha_status.append(ha_installed)

    return ha_status, IP_list

def get_host_info():
    ATTR_HOST_INFO = 'system_name hostname hostclass ip_address ha_operating_mode ha_installed'
    host_info_tpl = namedtuple('host_info_tpl', ATTR_HOST_INFO)

#    IP_list = get_IP_list()
    ha_status_list, IP_list = get_ha_status()

    for IP in IP_list:
        for hostlist in HostConf:
            if IP in hostlist:
                if hostlist[1] == 'VIP':
                    continue
                logger.info('%s : hostname is %s', GetCurFunc(), hostlist[1])
                HOST_INFO = hostlist + ha_status_list
                host_info = host_info_tpl._make(HOST_INFO)

                return host_info   # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE,'1'],

    logger.info('%s :: unknown IP address, check HostConf List',GetCurFunc())
    sys.exit()
