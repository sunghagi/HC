#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
from __future__ import division
import sys
import psutil
import subprocess
import re
import datetime
import time
import socket
import os.path
import ConfigParser
import math
from lib.log import *
#from lib.hostconf import *
from lib.hclib import *
from collections import namedtuple


class HcResult(object):
   ''' Health check status

   Attributes:
      result: the health check result as a string
      output: the health check running status as a string
    '''

   def __init__(self):
      self.result = 'OK'
      self.reason = ""
      self.output = ""
#      self.width = width
#   ResultList = [index, CheckDate, TodayCheckPeriod, SystemNumber, HostName, ItemDesc, CmdResult, ReturnString]

   def _insert_status_endline(self, column_width):
      if self.output.endswith('\n'):
         status_end = '=' * column_width + '\n'
      else:
         status_end = '\n' + '=' * column_width + '\n'
      self.output = string_concate(self.output, status_end)

class OdbcQuery(object):
   yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
   today = datetime.date.today().strftime("%Y-%m-%d %H:%M:%S")
   stattime = (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")

   def __init__(self, item_name, dbname_config):
      self.hc_item_name = item_name
      self.db_column_name = []
      self.db_column_width = []
      self.db_query = ""
      self.db_parameter = ""
      self.set_vertical = "off"

      config = ConfigLoad()
      self.omc_type = config.get_item_from_section('omc type', 'type')
      dsn_from_config = config.get_item_from_section('DB DSN', dbname_config)
      self.dsn_string = 'DSN=%s' % (dsn_from_config)
      logger.info('%s :: DB DSN : %s', GetCurFunc(), self.dsn_string)

   def make_output(self):
      hc_result = HcResult()

      if self.set_vertical == "on":
         column_width = 80
      else:
         column_width = sum(abs(int(CW)) for CW in self.db_column_width)

      hc_result_table = HcCmdResultTable(self.hc_item_name, column_width)
      if self.set_vertical == "on":
         output_buf = hc_result_table.hc_header
         direction = "vertical"
      else:
         title_table_row = print_column_name(self.db_column_name, self.db_column_width)
         output_buf = string_concate(hc_result_table.hc_header, title_table_row)
         direction = "Horizontal"

      unicode_db_query =  unicode(self.db_query,"euc-kr")
      logger.debug('%s :: Unicode DB Query : %s', GetCurFunc(), unicode_db_query)
      output_table_row, result = odbc_query_execute_fetchall(self.dsn_string, unicode_db_query, self.db_param, self.db_column_name, self.db_column_width, direction)
      if result.result == "OK":
         hc_result.output = string_concate(output_buf, output_table_row)
         hc_result.result = "OK"
      else:
         logger.info('%s :: result.reason : %s', GetCurFunc(), result.reason)
         hc_result.header = hc_result_table.hc_header
         hc_result.output = string_concate(output_buf, oneline_print(result.reason))
         hc_result.output += "=" * column_width + '\n'
         hc_result.result = "NOK"
         hc_result.reason = result.reason

      return hc_result


class HcCmdResultTable(object):
   ''' Health check contents

   Attributes:
      column_name: the column name as a string
      column_width: the column width as a string
      output: command execute result  as a string
      status_end: the health check result end as a string
   '''
   def __init__(self, column_name, column_width):
      self.column_name = column_name
      self.column_width = column_width

      output_single_line  = "-" * abs(self.column_width) + '\n'

      output_header = '\n' + output_single_line
      output_header += '  %-*s' % (self.column_width, self.column_name) + '\n'
      output_header += output_single_line

      self.hc_header = output_header
      self.hc_content = ""
      self.output = ""

   def _insert_tail(self):
      if self.output.endswith('\n'):
         status_end = '=' * self.column_width + '\n'
      else:
         status_end = '\n' + '=' * self.column_width + '\n'
      self.output = string_concate(self.output, status_end)

   def _concate(self, content):
      self.hc_content = content
      self.output = string_concate(self.hc_header, self.hc_content)
      self._insert_tail()

def get_alarm_checkday():
   ''' return one month ago and today '''
   today =  datetime.datetime.today()
   today_Ymd = today.strftime("%Y-%m-%d")
   lastMonthday = today - datetime.timedelta(days=30)
   lastMonthday_Ymd = lastMonthday.strftime("%Y-%m-%d")
   two_month_ago_day = today - datetime.timedelta(days=60)
   two_month_ago_day_Ymd = two_month_ago_day.strftime("%Y-%m-%d")
   alarm_checkday = [lastMonthday_Ymd, today_Ymd, two_month_ago_day_Ymd]

   return alarm_checkday

class HcItem:
    def __init__(self, host_info):
        logger.info('%s :: HcItem class init start', GetCurFunc())
        self.config = ConfigLoad()
        self.host_info = host_info

    def cpu_usage(self):
        cpu_usage_result = HcResult()
        
        CPU_THRESHOLD = self.config.getint_item_from_section('threshold', 'cpu')

        tot_percs = psutil.cpu_percent(interval=0, percpu=False)
        percs = psutil.cpu_percent(interval=0, percpu=True) 
        buf = ""
        for cpu_num, perc in enumerate(percs): 
            dashes, empty_dashes = get_dashes(perc) 
            templ = " CPU%-2s [%s%s] %5s%%"
            buf += templ % (cpu_num, dashes, empty_dashes, perc) + '\n'

        if (tot_percs > CPU_THRESHOLD):
            cpu_usage_result.result = "NOK"
            cpu_usage_result.reason = "CPU usage(%s) over THRESHOLD(%s)" % ( tot_percs, CPU_THRESHOLD )

        hc_result_table = HcCmdResultTable('CPU 사용률('+str(tot_percs)+'%)',78)
        hc_result_table._concate(buf)
        cpu_usage_result.output = hc_result_table.output
        logger.debug('%s :: hc_result_table.output : %s', 
                     GetCurFunc(), hc_result_table.output)

        return cpu_usage_result

    def memory_usage(self):
        memory_usage_result = HcResult()

        MEM_THRESHOLD = self.config.getint_item_from_section('threshold', 'mem')
        SWAP_THRESHOLD = self.config.getint_item_from_section('threshold', 'swap_memory')

        mem = psutil.virtual_memory()
        total_mem = bytes2human(mem.total)
        avail_mem = bytes2human(mem.available)
        '''
        percent_mem = mem.percent
        templ = "%10s      %10s   %10s%%"
        buf = '     Total           Available     Use(%)\n'
        buf += "-" * 65 + '\n'
        buf += templ % (total_mem, avail_mem, percent_mem) + '\n'
        '''
        dashes, empty_dashes = get_dashes(mem.percent)
        templ = " Mem   [%s%s] %5s%% %6s / %s \n"
        buf = templ % (  dashes, empty_dashes, 
                 mem.percent, 
                 str(int(mem.used / 1024 / 1024)) + "M", 
                 str(int(mem.total / 1024 / 1024)) + "M" )

        if (mem.percent > MEM_THRESHOLD):
            memory_usage_result.result = "NOK"

        swap = psutil.swap_memory()
        dashes, empty_dashes = get_dashes(swap.percent)
        templ = " Swap  [%s%s] %5s%% %6s / %s"
        buf += templ % ( dashes, empty_dashes, 
                 swap.percent, 
                 str(int(swap.used / 1024 / 1024)) + "M", 
                 str(int(swap.total / 1024 / 1024)) + "M") 

        if (swap.percent > SWAP_THRESHOLD):
            memory_usage_result.result = "NOK"

        hc_result_table = HcCmdResultTable('(SWAP)MEMORY 사용률(%)',78)
        hc_result_table._concate(buf)
        memory_usage_result.output = hc_result_table.output

        return memory_usage_result


    def disk_usage(self):
        disk_usage_result = HcResult()
        usageover_mountpoint = []

        DISK_THRESHOLD = self.config.getint_item_from_section('threshold', 'disk')

        list_partitions = psutil.disk_partitions(all=True)
        buf = ' Filesystem             Size    Used   Avail    Use%     Mounted on\n'
        NON_PHYSICAL_DEVICE = ['', 'proc', 'sysfs', 'devpts', 'tmpfs', 'sunrpc', 'nfsd']
        for part in list_partitions:
            if part.device in NON_PHYSICAL_DEVICE:
                continue
            fs = part.device
            fstype = part.fstype
            if fstype == 'iso9660':
                continue
            size = psutil.disk_usage(part.mountpoint).total
            used = psutil.disk_usage(part.mountpoint).used
            avail = psutil.disk_usage(part.mountpoint).free
            usage = psutil.disk_usage(part.mountpoint).percent
            mounton = part.mountpoint
            if (usage > DISK_THRESHOLD):
                usageover_mountpoint.append(mounton)
            if len(fs) > 20:
                templ = "% -20s \n %27s %7s %7s %7s     %-20s"
            else:
                templ = "% -20s %7s %7s %7s %7s     %-20s"

            buf += templ % (fs, bytes2human(size), bytes2human(used), \
                          bytes2human(avail), usage, mounton) + '\n'

        if len(usageover_mountpoint) > 0:
            disk_usage_result.result = "NOK"
            reason_text = "Disk(%s) usage over %s%% " % \
				             (', '.join(usageover_mountpoint), DISK_THRESHOLD)

        hc_result_table = HcCmdResultTable('DISK 사용률', 78)
        hc_result_table._concate(buf)
        disk_usage_result.output = hc_result_table.output
        try:
            disk_usage_result.reason = reason_text
        except:
            pass

        return disk_usage_result


    def disk_inode_usage(self):
        disk_node_usage_result = HcResult()

        DISK_THRESHOLD = self.config.getint_item_from_section('threshold', 'disk')

        list_partitions = psutil.disk_partitions(all=True)
        buf = ' Filesystem           Inodes   IUsed   IFree   IUse%     Mounted on\n'
        NON_PHYSICAL_DEVICE = ['', 'proc', 'sysfs', 'devpts', 'tmpfs', 'sunrpc', 'nfsd']
        for part in list_partitions:
            if part.device in NON_PHYSICAL_DEVICE:
                continue
            fs = part.device
            dict_node_usage = disk_node_usage(part.mountpoint)
            nodes = dict_node_usage['total_no_of_nodes']
            free = dict_node_usage['total_no_of_free_nodes']
            used = nodes - free
            try:
                usage = math.ceil((used/nodes)*100)
            except Exception as e:
                usage = 0
            mounton = part.mountpoint

            if (usage > DISK_THRESHOLD):
                disk_usage_result.result = "NOK"
                reason_text = " Disk(%s) inode usage over %s%% " % (mounton, DISK_THRESHOLD )
            if len(fs) > 20:
                templ = "% -20s \n %27s %7s %7s %7s     %-20s"
            else:
                templ = "% -20s %7s %7s %7s %7s     %-20s"

            buf += templ % (fs, bytes2human(nodes), bytes2human(used), \
                           bytes2human(free), usage, mounton) + '\n'

        hc_result_table = HcCmdResultTable('DISK inode 사용률', 78)
        hc_result_table._concate(buf)
        disk_node_usage_result.output = hc_result_table.output
        try:
            disk_node_usage_result.reason = reason_text
        except:
            pass
 
        return disk_node_usage_result


    def uptime_status(self):
        uptime_status_result = HcResult()
        hc_result_table = HcCmdResultTable('시스템 Uptime 확인', 78)

        UPTIME_THRESHOLD = self.config.getint_item_from_section('threshold', 'uptime')

        float_boot_time = psutil.boot_time()
        BootTime = datetime.datetime.fromtimestamp(float_boot_time).strftime("%Y-%m-%d %H:%M:%S")
        t = time.localtime()
        current_time = time.mktime(t)
        uptime = current_time - float_boot_time
        day = uptime / 60 / 60 / 24

        templ = " %20s        %3s days "

        buf = '      Booting 일자          Uptime 일자\n'
        buf += "-" * hc_result_table.column_width + '\n'
        buf += templ % (BootTime, int(day)) + '\n'

        if (day > UPTIME_THRESHOLD):
            uptime_status_result.result = "NOK"
            reason_text = "uptime(%s)이 %를 초과" % (day, UPTIME_THRESHOLD)

        hc_result_table._concate(buf)
        uptime_status_result.output = hc_result_table.output
        try:
            uptime_status_result.reason = reason_text
        except:
            pass
 
        return uptime_status_result

    def etc_backup(self):
        backup_result = HcResult()
        hc_result_table = HcCmdResultTable('/etc Backup',78)

        hc_home_path = self.config.get_item_from_section('main', 'path')
        backup_shell=os.path.join(hc_home_path,'etc_backup.sh')

        sudo_backup_shell='sudo ' + backup_shell
#        backup_status = os_execute(sudo_backup_shell)

        BackupDate = datetime.date.today().strftime("%Y%m%d")
        BackupHost = socket.gethostname()

        etc_backup_path = self.config.get_item_from_section('path', 'etc_backup')
        BackupFileName = os.path.join(etc_backup_path, 'etc_bkup_'+BackupHost+'_'+BackupDate+'.tar.gz')
        logger.info('%s :: BackupFileName : %s', GetCurFunc(), BackupFileName)

        backup_file_chk_cmd = '/usr/bin/file '+BackupFileName
        os_exec_result = os_execute(backup_file_chk_cmd)

        if not os.path.exists(BackupFileName):
            backup_result.result = "NOK"
            reason_text = "/etc backup file does not exits"
 
        hc_result_table._concate(os_exec_result.output)
        backup_result.output = hc_result_table.output
        backup_result.reason = reason_text

        return backup_result


    def sipa_fdump_status(self):
        sipa_fdump_status_result = HcResult()
        hc_result_table = HcCmdResultTable('sipa full dump 설정 확인', 78)

        sipa_trace_path = self.config.get_item_from_section('main', 'sipa_trace')

        sipa_config = ConfigParser.RawConfigParser()
        sipa_config.read(sipa_trace_path)
        dump = sipa_config.getint('MAIN','dump')
        full_dump = sipa_config.getint('MAIN','full_dump')

        sipa_fdump_status_output = "    dump : %s , full_dump : %s" % ( dump, full_dump )
        logger.info('%s :: sipa_fdump_status_output : %s', GetCurFunc(), sipa_fdump_status_output)

        if dump:
            if full_dump:
                sipa_fdump_status_result.result = "NOK"
        else:
            sipa_fdump_status_result.result = "OK"

        hc_result_table._concate(sipa_fdump_status_output)
        sipa_fdump_status_result.output = hc_result_table.output

        return sipa_fdump_status_result


    def corefile_status(self):
        corefile_status_result = HcResult()
        hc_result_table = HcCmdResultTable('CORE 파일 생성 확인 : file CORE_FILE',78)

        core_file_path = self.config.get_item_from_section('path', 'core')
        logger.info('%s :: core_file_path : %s', GetCurFunc(), core_file_path)

        import fnmatch, os
        try:
            files = fnmatch.filter(os.listdir(core_file_path), "core.*")
        except Exception as e:
            logger.exception('%s :: %s', GetCurFunc(), e)
            corefile_status_result.reason = e
            corefile_status_result.result = "NOK"
            buf = e
        else:
            buf = ''
            for CoreFileName in files:
                # OMA 는 root 권한 필요
                CMD = 'sudo /usr/bin/file '+core_file_path+'/'+CoreFileName
                os_exec_result = os_execute(CMD)
                buf += os_exec_result.output
            if files:
                logger.info('%s :: core file : %s', GetCurFunc(), files)
                corefile_status_result.result = "NOK"
                reason_text = "Core file exists"

        hc_result_table._concate(buf)
        corefile_status_result.output = hc_result_table.output
        try:
            corefile_status_result.reason = reason_text
        except:
            pass

        return corefile_status_result


    def process_display(self):
        process_display_result = HcResult()
        hc_result_table = HcCmdResultTable('PROCESS 확인', 78)

        hc_home_path = self.config.get_item_from_section('main', 'path')

        process_display_command = os.path.join(hc_home_path,'DIS-PRCS.py')
        os_exec_result = os_execute(process_display_command)

        hc_result_table._concate(os_exec_result.output)
        process_display_result.output = hc_result_table.output

        return process_display_result

    def ping_status(self):
        ping_status_result = HcResult()
        hc_result_table = HcCmdResultTable('Ping 확인 : ping -s 1500 -c 60 gateway_ip',78)

        hc_home_path = self.config.get_item_from_section('main', 'path')
        HC_CONFIG_PING_PATH= os.path.join(hc_home_path, 'config/ping')

        ping_config_file = self.host_info.hostname + '.cfg'
        ping_config_file_path = os.path.join(HC_CONFIG_PING_PATH, ping_config_file)

        config = ConfigLoad(ping_config_file_path)
        gateway_ip = config.get_item_from_section('default', 'GW')

        ping_command='ping -s 1500 -c 6 ' + gateway_ip
        ping_result = os_execute(ping_command)
        ping_result_list = ping_result.output.split('\n')

        for line in ping_result_list:
            if 'packet loss' in line:
                PingResult = line.split(',')
        PacketLoss = re.findall(r'\d', PingResult[2])
        logger.info('%s : parsing packet loss from ping result : %s', GetCurFunc(), PacketLoss[0])

        if int(PacketLoss[0]) > 0:
            ping_status_result.result = "NOK"
            reason_text = "packet loss from ping result %s" % ( PacketLoss[0] )

        hc_result_table._concate(ping_result.output)
        ping_status_result.output = hc_result_table.output
        try:
            ping_status_result.reason = reason_text
        except:
            pass

        return ping_status_result


    def bond_status_check(self):
        ''' bond interface check
        '''
        bond_check_result = HcResult()
        hc_result_table = HcCmdResultTable('bond interface 확인',78)

        hc_home_path = self.config.get_item_from_section('main', 'path')

        HC_CONFIG_NETIF_PATH= os.path.join(hc_home_path, 'config/netif')

        netif_config_file = self.host_info.hostname + '.cfg'
        netif_config_file_path = os.path.join(HC_CONFIG_NETIF_PATH, netif_config_file)

        config = ConfigLoad(netif_config_file_path)
        netif = config.get_item_from_section('check nic', 'nic')
        netif_nowhitespace = netif.replace(" ","")
        logger.info('%s : read checking netif list from config : %s', 
                     GetCurFunc(), netif_nowhitespace)

        netif_list = netif_nowhitespace.split(',')

        bondList = get_bond() 
        logger.info('%s : get bonding interface list : %s', GetCurFunc(), bondList)
        buf = ""
        if bondList: 
            for bond in bondList: 
                if bond in netif_list:
                    bond_status = check_bond_status(bond) 
                    logger.info('%s : bond_status intState : %s', 
                                 GetCurFunc(),  bond_status.intState)
                    if bond_status: 
                        buf += " %s :\n" % ( bond )
                        buf += "    mode  : %s" % bond_status.mode + '\n'
                        buf += "    stats : up=%s, slave Iface=%4s(%6s,%4s), %4s(%6s,%4s)" % \
                               ("yes" if bond_status.intState == 0 else "no", 
                               bond_status.slave_iface[0], 
                               "ACTIVE" if bond_status.active in bond_status.slave_iface[0] else "STDBY", 
                               bond_status.slave_iface_status[0],
                               bond_status.slave_iface[1], 
                               "ACTIVE" if bond_status.active in bond_status.slave_iface[1] else "STDBY",
                               bond_status.slave_iface_status[1]) + '\n'
                        if bond_status.intState == 1:
                            buf += "Bond %s error:%s" % (bond, bond_status.strState)
                else:
                    continue
            if "down" in bond_status.slave_iface_status:
                bond_check_result.reason = "slave interface is down"
                bond_check_result.result = "NOK"
                buf += bond_check_result.reason
        else: 
            bond_check_result.reason = "bonding interface not found"
            bond_check_result.result = "NOK"
            buf += bond_check_result.reason

        hc_result_table._concate(buf)
        bond_check_result.output = hc_result_table.output

        return bond_check_result


    def route_status(self):
        route_status_result = HcResult()
        hc_result_table = HcCmdResultTable('route 확인',78)

        hc_home_path = self.config.get_item_from_section('main', 'path')

        HC_CONFIG_ROUTE_PATH= os.path.join(hc_home_path, 'config/route')

        route_command='/bin/netstat -rn'
        route_command_result = os_execute(route_command)
        route_command_result_list = route_command_result.output.split('\n')

        route_result = ''
        route_result += "Kernel IP routing table\n"
        route_result += "Destination     Gateway         Genmask         Flags   MSS Window  irtt Iface "
        route_result += "Netconf파일정보유무               비고\n"

        route_config_file = self.host_info.hostname + '.cfg'
        route_config_file_path = os.path.join(HC_CONFIG_ROUTE_PATH, route_config_file)
        logger.info('%s :: route_config_file_path : %s', GetCurFunc(), route_config_file_path)

        route_config = ConfigLoad(route_config_file_path)
        route_dest_sections_from_config = route_config.get_sections()

        for route_dest_section in route_dest_sections_from_config:
            DEST = route_config.get_item_from_section(route_dest_section, 'DEST')
            GW = route_config.get_item_from_section(route_dest_section, 'GW')
            DESC = route_config.get_item_from_section(route_dest_section, 'DESC')

            search_result = "NOK"
            for route_command_result_line in route_command_result_list:
                if DEST in route_command_result_line and GW in route_command_result_line:
                    if DEST == '0.0.0.0':
                        netconf_file_info = 'Default Gateway'
                    else :
                        Iface = route_command_result_line.split()
                        NETMASK = Iface[2]
                        cidr = netmask2cidr(NETMASK)
                        NIC = Iface[7]
                        network_scripts_file = '/etc/sysconfig/network-scripts/'+'route-'+NIC
                        logger.info('%s :: network_scripts_file : %s', GetCurFunc(), network_scripts_file)
                        dest_with_cidr = DEST + '/' + cidr
                        if GW == '0.0.0.0':
                            netconf_file_info = '자체 네트워크'
                        else :
                            netconf_file_info = single_grep(DEST, network_scripts_file)
                            logger.info('%s :: %s in netconf_file_info ?: %s', \
                                         GetCurFunc(), dest_with_cidr, netconf_file_info)
                            if netconf_file_info == None:
                                netconf_file_info = '미존재'
                                route_status_result.result = "NOK"
                    route_result += "%-78s %-33s %s\n" % \
                                    ( route_command_result_line, netconf_file_info, DESC)
                    search_result = "OK"
                    break
            if search_result != "OK":
                route_result += " %-10s : %-s " % ( DEST, GW)
                route_result += ' routing table에 없음\n'
                route_status_result.result = "NOK"

        hc_result_table._concate(route_result)
        route_status_result.output = hc_result_table.output
 
        return route_status_result


    def net_io_counters(self):
        ''' Check Net io counters 
        '''
        net_io_counters_result = HcResult()
        hc_result_table = HcCmdResultTable('NET IO 확인',78)

        hc_home_path = self.config.get_item_from_section('main', 'path')
        HC_CONFIG_NETIF_PATH= os.path.join(hc_home_path, 'config/netif')

        netif_config_file = self.host_info.hostname + '.cfg'
        netif_config_file_path = os.path.join(HC_CONFIG_NETIF_PATH, netif_config_file)

        config = ConfigLoad(netif_config_file_path)
        netif = config.get_item_from_section('check nic', 'nic')
        netif_nowhitespace = netif.replace(" ","")
        logger.info('%s :: check netif list : %s', GetCurFunc(), netif_nowhitespace)

        netif_list = netif_nowhitespace.split(',')


        buf = ""
        for nic, netio_counters in psutil.net_io_counters(pernic=True).items():
            if nic == 'lo' or nic == 'sit0':
                continue
            if nic in netif_list:
                buf += " %s :\n" % ( nic )
                buf += "    errin : %3s, errout : %3s" % \
                            (netio_counters.errin, netio_counters.errout)  + '\n'
                if netio_counters.errin >= 100 or netio_counters.errout >= 100:
                    net_io_counters_result.result = "NOK"
            else:
                continue

        hc_result_table._concate(buf)
        net_io_counters_result.output = hc_result_table.output

        return net_io_counters_result

    def net_if_stats(self):
       ''' Check Net if stats 
       '''
       duplex_map = {
          psutil.NIC_DUPLEX_FULL: "full",
          psutil.NIC_DUPLEX_HALF: "half",
          psutil.NIC_DUPLEX_UNKNOWN: "?",
       }

       net_if_stats_result = HcResult()
       hc_result_table = HcCmdResultTable('NET interface 확인',78)

       hc_home_path = self.config.get_item_from_section('main', 'path')
       HC_CONFIG_NETIF_PATH= os.path.join(hc_home_path, 'config/netif')

       netif_config_file = self.host_info.hostname + '.cfg'
       netif_config_file_path = os.path.join(HC_CONFIG_NETIF_PATH, netif_config_file)

       config = ConfigLoad(netif_config_file_path)
       netif = config.get_item_from_section('check nic', 'nic')
       netif_nowhitespace = netif.replace(" ","")
       logger.info('%s :: check netif list : %s', GetCurFunc(), netif_nowhitespace)

       netif_list = netif_nowhitespace.split(',')

       buf = ""
       for nic, nic_stats in psutil.net_if_stats().items():
          if nic in netif_list:
             if nic == 'lo' or nic == 'sit0':
                continue
          
             if type(nic) == unicode:
                nic = nic.encode("utf-8")

             try:
                if nic_stats.isup != True or nic_stats.duplex != 2:
                   net_if_stats_result.result = "NOK"
                buf += " %s :\n" % ( nic )
                buf += "    stats : up=%s, duplex=%s, speed=%s" % \
                       ("yes" if nic_stats.isup else "no", duplex_map[nic_stats.duplex], nic_stats.speed)  + '\n'
             except Exception as e:
                pass
          else:
             continue

       hc_result_table._concate(buf)
       net_if_stats_result.output = hc_result_table.output

       return net_if_stats_result

    def net_if_address(self):
       ''' Check Net if address 
       '''
       net_if_addrs_result = HcResult()
       hc_result_table = HcCmdResultTable('Net interface address 확인',78)

       ipa_dic = {}
       for nic_name, addrs in psutil.net_if_addrs().items():
          if nic_name == 'lo' or nic_name == 'sit0':
             continue
          for addr in addrs:
             if addr.family == socket.AF_INET:
                ip_addrs = addr.address
                ipa_dic[nic_name] = ip_addrs

       hc_home_path = self.config.get_item_from_section('main', 'path')
       HC_CONFIG_IPADDR_PATH= os.path.join(hc_home_path, 'config/ipaddr')

       ipaddr_config_file = self.host_info.hostname + '.cfg'
       ipaddr_config_file_path = os.path.join(HC_CONFIG_IPADDR_PATH, ipaddr_config_file)

       config = ConfigLoad(ipaddr_config_file_path)
       net_if_addrs_from_config = config.get_items_from_section('ipaddr')

       buf = ""
       for nic_name_conf, ip_addrs_conf in net_if_addrs_from_config:
          search_result = "OK"
          ip_addrs_sys = ipa_dic.get(nic_name_conf)
          if ip_addrs_sys != ip_addrs_conf:
             net_if_addrs_result.result = "NOK"
             search_result = "NOK"

          buf += "  %5s : %15s                                 [ %3s ]" \
               % (nic_name_conf, ip_addrs_conf, search_result  )  + '\n'

       hc_result_table._concate(buf)
       net_if_addrs_result.output = hc_result_table.output

       return net_if_addrs_result


    def crontab_status(self):
        crontab_status_result = HcResult()
        hc_result_table = HcCmdResultTable('crontab 확인 : crontab -l',78)

        crontab_from_config = self.config.get_items_from_section('crontab')
        logger.info('%s :: crontab_from_config  : %s', GetCurFunc(), crontab_from_config)

        crontab_command='sudo crontab -l'
        crontab_command_result = os_execute(crontab_command)
        crontab_command_result_list = crontab_command_result.output.split('\n')

        crontab_result = ''
        for crontab_entry,crontab_command in crontab_from_config:
            search_result = "NOK"
            for crontab_command_result_line in crontab_command_result_list:
                if crontab_command in crontab_command_result_line:
                    crontab_result += " %-10s : " % ( crontab_entry )
                    crontab_result += crontab_command_result_line + '\n'
                    search_result = "OK"            
                    break
            if search_result != "OK":
                crontab_result += crontab_entry + ' : ' + crontab_command
                crontab_result += ' crontab 목록에 없음\n'
                crontab_status_result.result = "NOK"
                crontab_status_result.reason = "crontab 목록에 없음"

        hc_result_table._concate(crontab_result)
        crontab_status_result.output = hc_result_table.output
     
        return crontab_status_result

    def sip_env_status(self):
        '''MAX_SES|CHK_SES|MAX_MSG|CHK_MSG|MAX_CPS|CHK_CPS|MAX_CPU|CHK_CPU|MAX_MEM|CHK_MEM|MAX_TPS|CHK_TPS|EMER|AUDIO|VIDEO|CLASS'''
        sip_env_status_result = HcResult()
        hc_result_table = HcCmdResultTable('SIP ENV 확인',78)

        sip_env_from_config = self.config.get_item_from_section('main', 'sip_env')
        logger.info('%s :: sip_env config path : %s', GetCurFunc(), sip_env_from_config)

        try:
            with open(sip_env_from_config, "r") as f:
                sip_env_list = []
                for line in f:
                    if "db - environment" in line:
                        continue
                    if "#" in line:
                        line = line.lstrip('#')
                    sip_env_list.append(line)
        except Exception as e:
            if os.path.exists(sip_env_from_config)==False:
                logger.info('No such sip_env config file in hc.cfg : %s', sip_env_from_config)
            logger.info('Read sip_env config error : %s', e)
            sip_env_status_result.result = "NOK"
            sip_env_status_result.reason = e
            return sip_env_status_result 

        ENV = sip_env_list[0].split("|")
        VALUE = sip_env_list[1].split("|")
        SIP_ENV = dict(zip(ENV, VALUE))

        MAX_CPS = SIP_ENV["MAX_CPS"]
        if SIP_ENV["CHK_CPS"] == '1':
            CHK_CPS = "ON"
        else:
            CHK_CPS = "OFF"
            reason_text = "CHK_CPS OFF"
            sip_env_status_result.result = "NOK"

        cps_result = " 정책적용 : %-3s, CPS 설정값 : %-5s " % (CHK_CPS, MAX_CPS)

        hc_result_table._concate(cps_result)
        sip_env_status_result.output = hc_result_table.output
        try:
            sip_env_status_result.reason = reason_text
        except:
            pass

        return sip_env_status_result


def ntp_status():
   ntp_status_result = HcResult()
   hc_result_table = HcCmdResultTable('NTP 연동확인 � : ntpq -p',78)

   os_exec_result = os_execute("/usr/sbin/ntpq -p")

   sync_char = re.findall("\*.*", os_exec_result.output)

   if not sync_char:
      ntp_status_result.result = "NOK"
      ntp_status_result.reason = os_exec_result.output

   hc_result_table._concate(os_exec_result.output)
   ntp_status_result.output = hc_result_table.output

   return ntp_status_result


def process_status():
   process_status_result = HcResult()
   hc_result_table = HcCmdResultTable('좀비프로세스 확인', 78)

   buf = 'Process Name     PID   PPID   USER  %MEM    PATH                      CREATE TIME\n'
   buf += "-" * hc_result_table.column_width + '\n'

   pid_list = psutil.pids()

   RunningProcessList = []

   for pl in pid_list:
      try:
         p = psutil.Process(pl)
      except:
         pass
      else:
         if p.status() == psutil.STATUS_ZOMBIE:
            if p.name() == "Xsession":
               pass
            else :
               process_status_result.result = "NOK"
               cmdline = '['+p.name()+'] <defunct>'
               create_time=datetime.datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S")
               templ = "%-13s %6s %6s   %-5s %-4s %-25s %-s\n"
               buf += templ % (p.name(), p.pid, p.ppid(), p.username(), round(p.memory_percent(),1), cmdline, create_time)

   hc_result_table._concate(buf)
   process_status_result.output = hc_result_table.output

   return process_status_result


def disk_mirror_status():
   disk_mirror_status_result = HcResult()
   SYS_MANUF = GetSystemManufacturer()

   if SYS_MANUF == 'HP':
      if os.path.exists("/usr/sbin/hpssacli"):
         hp_storage_admin_tool = "hpssacli"
      else :
         hp_storage_admin_tool = "hpacucli"
      os_command = hp_storage_admin_tool + " ctrl all show config"
   elif SYS_MANUF == 'Advantech':
      os_command = "SKIP (Console Cable 연결 필요)"
   elif SYS_MANUF == 'Red Hat':
      os_command = "SKIP (KVM Host)"
   else :
      os_command = 'mpt-status -i SCSI_ID'

   hc_result_table = HcCmdResultTable('디스크 이중화 상태 확인 : '+os_command, 78)

   if SYS_MANUF == 'HP':
      ps_cmd = 'ps -ef | /bin/grep ' + hp_storage_admin_tool + ' | /bin/grep -v grep | cat'
      ps_cmd_result = os_execute(ps_cmd)
      logger.info('%s :: hp_storage_admin_tool status : \n%s', GetCurFunc(), ps_cmd_result.output)
      find_ps_cmd_result = re.findall(hp_storage_admin_tool, ps_cmd_result.output)
      if find_ps_cmd_result:
         logger.info('%s :: Another instance of %s is running! waiting 3 seconds',\
                      GetCurFunc(), hp_storage_admin_tool)
         time.sleep(3)
      hptool_run_cmd='sudo /usr/sbin/'+ os_command + '| /bin/egrep "logicaldrive"'
      hptool_run_cmd_result = os_execute(hptool_run_cmd)
      logger.info('%s :: %s ctrl slot=0 show config result : \n%s', \
                    GetCurFunc(), hp_storage_admin_tool, hptool_run_cmd_result.output)
      buf = hptool_run_cmd_result.output
      OK = re.findall("OK", hptool_run_cmd_result.output)
   elif SYS_MANUF == 'Advantech':
      buf = "SKIP"
      OK = True
   elif SYS_MANUF == 'Red Hat':
      buf = "SKIP"
      OK = True
   else:
      mpt_status_result = os_execute("sudo mpt-status -p | /bin/grep Found")
      logger.info('%s :: std_out : |%s| ', GetCurFunc(), mpt_status_result.output)
      Buf = re.sub(",.*",'', mpt_status_result.output)
      SCSI_ID = re.sub("\D",'', Buf)

      CMD='sudo mpt-status -i '+SCSI_ID+' | /bin/grep state'
      logger.info('%s :: CMD : %s ', GetCurFunc(), CMD)
      mpt_status_result = os_execute(CMD)
      buf = mpt_status_result.output
      OK = re.findall("OPTIMAL", mpt_status_result.output)

   if OK:
      disk_mirror_status_result.result = "OK"
   else:
      disk_mirror_status_result.result = "NOK"

   hc_result_table._concate(buf)
   disk_mirror_status_result.output = hc_result_table.output

   return disk_mirror_status_result

def vms_subscribers():
   vms_subscribers_sps = OdbcQuery('소리샘 총가입자','altibase')
   vms_subscribers_sps.db_column_name = ['SUBSCRIBERS']
   vms_subscribers_sps.db_column_width = ['78']
   vms_subscribers_sps.db_query = """
   select count(*) from subscribers
   """
   vms_subscribers_sps.db_param = ''
   vms_subscribers_result = vms_subscribers_sps.make_output()
   return vms_subscribers_result

def vic_subscribers():
   vic_subscribers_sps = OdbcQuery('VIC 총가입자','altibase')
   vic_subscribers_sps.db_column_name = ['SUBSCRIBERS']
   vic_subscribers_sps.db_column_width = ['78']
   vic_subscribers_sps.set_vertical = "on"
   vic_subscribers_sps.db_query = """
   select count(*) from subscribers
   """
   vic_subscribers_sps.db_param = ''
   vic_subscribers_result = vic_subscribers_sps.make_output()
   return vic_subscribers_result

def tars_subscribers():
   column_name = 'T-ARS 총가입자'

   db_column_name = ['SUBSCRIBERS']
   db_column_width = ['78']
   column_width = sum(int(CW) for CW in db_column_width)
   hc_result_table = HcCmdResultTable(column_name, column_width)

   vms_subscribers_result = HcResult()

   config = ConfigLoad()
   dsn_from_config = config.get_item_from_section('DB DSN', 'altibase')
   dsn_string = 'DSN=%s' % ( dsn_from_config)
   logger.info('%s :: DB DSN : %s', GetCurFunc(), dsn_string)

   db_query = """
   select count(*) from subscribers where usertype=?
   """
   db_param = 1
   ac_subscribers, result = odbc_query_execute_fetchone(dsn_string, db_query, db_param, hc_result_table.column_width)
   ac_subscribers_cnt = ac_subscribers.split("\n")[0].strip(" ")
   db_param = 2
   cf_subscribers, result = odbc_query_execute_fetchone(dsn_string, db_query, db_param, hc_result_table.column_width)
   cf_subscribers_cnt = cf_subscribers.split("\n")[0].strip(" ")
   total_cnt = int(ac_subscribers_cnt) + int(cf_subscribers_cnt)

#   db_column_name = lib.vms_hc.print_column_name(db_column_name, db_column_width)
   db_column_name = hc_result_table.hc_header
   output_buf = string_concate(hc_result_table.output, db_column_name)

#   tars_subscribers = "자동연결 : %10s 명 \n착신전환 : %10s 명\n합    계 : %10s" % \
#                      (ac_subscribers.split("\n")[0].strip(" "), cf_subscribers.split("\n")[0].strip(" "), )
   tars_subscribers = "자동연결 : %10s 명 \n착신전환 : %10s 명\n합    계 : %10s 명\n" % \
                                (ac_subscribers_cnt, cf_subscribers_cnt, total_cnt )
   vms_subscribers_result.output = string_concate(output_buf, tars_subscribers)

   if result.result == "OK":
#      vms_subscribers_result.output = string_concate(output_buf, vms_subscribers)
      vms_subscribers_result.result = "OK"

   result_templ = "   %-10s %3s %-30s "
   if result.result == "NOK":
      vms_subscribers_result.output = string_concate(output_buf, result.reason)
      vms_subscribers_result.result = "NOK"
#      print(result_templ % ("REASON", "=", result.reason))
#      print(result_templ % ("HELP","=","Subscribers count is available in SPS01/02"))

   return vms_subscribers_result

def isup_stat():
   isup_stat_omp = OdbcQuery('ISUP 통계 확인','mysql')
   isup_stat_omp.db_column_name=['통계시간','IAM','CPS','사용량(%)']
   isup_stat_omp.db_column_width=['-20','-20','-20', '-20']
   if isup_stat_omp.omc_type == '1' or isup_stat_omp.omc_type == '2' :
      isup_stat_omp.db_query = """
      select DATE_FORMAT(collectTime, '%Y-%m-%d %H:%i') AS collectTime,
      SUM(iam_rx) IAM,
      ROUND(SUM(iam_rx)/5/60,1) CPS,
      ROUND(ROUND(SUM(iam_rx)/5/60,1)/250,3)*100 USAGE_RATIO
      from tmr_st_isup_min
      where ( collectTime between ? and ? )
      group by collectTime
      order by sum(iam_rx) desc limit 0,1;
      """
   elif isup_stat_omp.omc_type == '3' :
      isup_stat_omp.db_query = """
      select DATE_FORMAT(STATTIME, '%Y-%m-%d %H:%i') AS STATTIME,
      SUM(IAM_COUNT) IAM,
      ROUND(SUM(IAM_COUNT)/5/60,1) CPS,
      ROUND(ROUND(SUM(IAM_COUNT)/5/60,1)/30,3)*100 USAGE_RATIO
      from ST_ISUP_5MIN
      where ( STATTIME between ? and ? ) and CALLTYPE=0
      group by STATTIME
      order by sum(IAM_COUNT) desc limit 0,1;
      """
   isup_stat_omp.db_param = [isup_stat_omp.yesterday,isup_stat_omp.today]
   isup_stat_result = isup_stat_omp.make_output()
   return isup_stat_result

def scp_stat():
   scp_stat_omp = OdbcQuery('SCP 통계 확인','mysql')
   scp_stat_omp.db_column_name=['통계시간','TotalCount','CPS','사용량(%)/250 CPS']
   scp_stat_omp.db_column_width=['-20','-20','-20', '-20']
   scp_stat_omp.db_query = """
   select DATE_FORMAT(collectTime, '%Y-%m-%d %H:%i') AS collectTime,
   SUM(totalCount) totalCount,
   ROUND(SUM(totalCount)/5/60,1) CPS,
   ROUND(ROUND(SUM(totalCount)/5/60,1)/250,3)*100 USAGE_RATIO
   from tmr_st_scp_min
   where ( collectTime between ? and ? )
   group by collectTime
   order by sum(totalCount) desc limit 0,1;
   """
   scp_stat_omp.db_param = [scp_stat_omp.yesterday,scp_stat_omp.today]
   scp_stat_result = scp_stat_omp.make_output()
   return scp_stat_result

def cpu_stat():
   cpu_stat_omp = OdbcQuery('CPU 통계확인','mysql')
   cpu_stat_omp.db_column_name = ['시스템','Peak 값','평균값']
   cpu_stat_omp.db_column_width = ['20','10','10']

   if cpu_stat_omp.omc_type == '1' or cpu_stat_omp.omc_type == '2' :
      cpu_stat_omp.db_query = """
      SELECT B.SYSNAME, max(A.usages) as max_usages , round(avg(A.usages),1) as avg_usages
      FROM SAM_ST_CPU_HOUR A INNER JOIN SAM_SYSTEM B
      ON A.SYSTEMID = B.SYSTEMID
      group by sysname;
      """
      cpu_stat_omp.db_param = ''
   elif cpu_stat_omp.omc_type == '3' :
      cpu_stat_omp.db_query = """
      SELECT B.SERVERNAME, maxcpu, cpu
      FROM ST_SYS_MON A INNER JOIN SERVER B
      ON A.SERVERID = B.SERVERID
      WHERE A.STATTIME  BETWEEN ? AND ?;
      """
      checkday = get_alarm_checkday()
      alarm_start_time=checkday[2] + ' ' + '00:00:00'
      alarm_end_time=checkday[1] + ' ' + '23:59:59'
      cpu_stat_omp.db_param = [alarm_start_time, alarm_end_time]

   cpu_stat_result = cpu_stat_omp.make_output()
   return cpu_stat_result

def vic_sip_stat():
   sip_stat_omp = OdbcQuery('SIP 통계 확인','mysql')
   sip_stat_omp.db_column_name=['통계수집시간','TOTAL','CPS','USAGE']
   sip_stat_omp.db_column_width=['-25','-15','-15', '-15']
   sip_stat_omp.db_query = """
   SELECT *
   FROM (
      SELECT index5Min AS STATTIME,
          SUM(total) AS TOTAL,
          ROUND(SUM(total)/300, 1) AS CPS,
          ROUND(ROUND(SUM(total)/300, 1)/30,3)*100 AS USAGEPET
      FROM VIC_ST_SIPCALL_MIN
      GROUP BY STATTIME
      ORDER BY TOTAL DESC
   )A
   """
   sip_stat_omp.db_param = ""
   sip_stat_result = sip_stat_omp.make_output()
   return sip_stat_result

def tars_sip_stat():
   sip_stat_omp = OdbcQuery('SIP 통계 확인','mysql')
   sip_stat_omp.db_column_name=['통계수집시간','TOTAL','SUCCESS','FAIL','HT']
   sip_stat_omp.db_column_width=['-25','-15','-15', '-15','-15']
   sip_stat_omp.db_query = """
   SELECT collectTime, SUM(totalCount) totalCount,
   SUM(IF(endCode IN (0, 403), totalCount, 0)) successCount,
   SUM(IF(endCode NOT IN (0, 403), totalCount, 0)) failCount,
   ROUND(SUM(holdingTime * totalCount)/SUM(totalCount)) holdingTime
   FROM SAM_ST_SIPRM_HOUR
   WHERE collectTime = ?
   GROUP BY collectTime
   """
   sip_stat_omp.db_param = [sip_stat_omp.stattime]
   sip_stat_result = sip_stat_omp.make_output()
   return sip_stat_result

def dis_alarm():
   dis_alarm_omp = OdbcQuery('MONTHLY ALARM INFORMATION','mysql')
   dis_alarm_omp.db_column_name=['FIRST_TIME','SOURCE','MESSAGE']
   dis_alarm_omp.db_column_width=['-21','-25','-40']

   checkday = get_alarm_checkday()
#   alarm_checkday = [lastMonthday_Ymd, today_Ymd, two_month_ago_day_Ymd]
   alarm_start_time=checkday[0] + ' ' + '00:00:00'
   alarm_end_time=checkday[1] + ' ' + '23:59:59'

#   print("알람 조회 기간 : %s ~ %s " % ( alarm_start_time, alarm_end_time ))
#   print("작업시간(02:00 ~ 05:59) 알람은 제외")
   if dis_alarm_omp.omc_type == '1' or dis_alarm_omp.omc_type == '2' :
      dis_alarm_omp.db_query = """
      select A.firstTime,
   #  B.sysname,
      A.source,
      A.alarmMessage
      from SAM_ALARM A inner join SAM_SYSTEM B
      on A.systemid = B.systemid
      where A.firstTime between ? and ?
      and A.firstTime not regexp '.*\ 0[2-5].*'
      and A.severity = 1;
      """
   elif dis_alarm_omp.omc_type == '3':
      dis_alarm_omp.db_query = """
      SELECT DATE_FORMAT(EVENTTIME, '%Y-%m-%d %H:%i:%S') AS EVENTTIME,
         SOURCE,
         CAUSE
      FROM ALARM
      WHERE EVENTTIME BETWEEN ? AND ?
      AND EVENTTIME NOT regexp '.*\ 0[1-5].*'
      AND SEVERITY = 2
      AND ALARMCODE != "A0037"  # AvrHoldingtime is too low
      AND ALARMCODE != "A0054"  # E1 Sync Error
      AND ALARMCODE != "A0017"  # sync error
      AND ALARMCODE != "A9203"  # ARS User Cert ERROR[
      ORDER BY EVENTTIME ASC;
      """
   dis_alarm_omp.db_param = [alarm_start_time, alarm_end_time]
   dis_alarm_result = dis_alarm_omp.make_output()
   return dis_alarm_result

def sip_stat():
   sip_stat_omp = OdbcQuery('SIP 통계 확인', 'mysql')
   sip_stat_omp.db_column_name=['통계시간','TotalCount','CPS','사용량(%)/300 CPS']
   sip_stat_omp.db_column_width=['-20','-20','-20', '-20']
   sip_stat_omp.db_query = """
   select DATE_FORMAT(collectTime, '%Y-%m-%d %H:%i') AS collectTime,
   SUM(invite) invite,
   ROUND(SUM(invite)/5/60,1) CPS,
   ROUND(ROUND(SUM(invite)/5/60,1)/300,3)*100 USAGE_RATIO
   from SAM_ST_SIPMSG_MIN
   where ( collectTime between ? and ? )
   group by collectTime
   order by sum(invite) desc limit 0,1;
   """
   sip_stat_omp.db_param = [sip_stat_omp.yesterday,sip_stat_omp.today]
   sip_stat_result = sip_stat_omp.make_output()
   return sip_stat_result

def altibase_tablespace():
   altibase_tablespace_sps = OdbcQuery('알티베이스 메모리 사용률', 'altibase')
   altibase_tablespace_sps.db_column_name=['MAX(M)','TOTAL(M)','ALLOC(M)','USED(M)','USAGE(%)']
   altibase_tablespace_sps.db_column_width=['-16','-16','-16','-16','-16']
   altibase_tablespace_sps.set_vertical="on"

   altibase_tablespace_sps.db_query = """
   SELECT mem_max_db_size/1024/1024 'MAX(M)',
      round(mem_alloc_page_count*32/1024, 2) 'TOTAL(M)',
      trunc((mem_alloc_page_count-mem_free_page_count)*32/1024, 2) 'ALLOC(M)',
      (SELECT round(sum((fixed_used_mem + var_used_mem))/(1024*1024),3) FROM v$memtbl_info) 'USED(M)',
      trunc(((mem_alloc_page_count-mem_free_page_count)*32*1024)/mem_max_db_size, 4)*100 'USAGE(%)'
   FROM v$database ;
   """
   altibase_tablespace_sps.db_param = ''
   altibase_tablespace_result = altibase_tablespace_sps.make_output()
   return altibase_tablespace_result

def print_column_name(column_name, column_width):
   total_width = sum(abs(int(CW)) for CW in column_width)
   
   buf = "\n"
   buf += "-" * abs(total_width) + '\n'
   for name, width in zip(column_name, column_width):
      buf += '%*s' % (int(width), name)
   buf += "\n"
   buf += "-" * abs(total_width) + '\n'

   return buf

def odbc_query_execute_fetchone(DSN,db_query,db_param, column_width):
   from lib.odbc_conn import odbcConn
   fetch_result = HcResult()

   output_buf = ""
   if type(column_width) is not list:
      column_width = [column_width]

   total_width = sum(abs(int(CW)) for CW in column_width)

   db = odbcConn(DSN)
   try:
      db._GetConnect()
      logger.info('%s :: DB connection success ', GetCurFunc())
   except Exception as e:
      logger.exception('%s :: error : %s', GetCurFunc(), e)
#      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = db.error
      return output_buf, fetch_result

   try:
      if db_param == '':
         db.cursor.execute(db_query)
      else :
         db.cursor.execute(db_query, db_param)
      logger.debug('%s :: DB execute : query : %s', GetCurFunc(), db_query)
   except Exception as e:
      logger.exception('%s :: error : %s', GetCurFunc(), e[1])
      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = e[1]
      return output_buf, fetch_result

   while 1:
      row = db.cursor.fetchone()
      if not row:
         output_buf += "-" * abs(total_width) + '\n'
         break
      for value, width in zip(row, column_width):
         output_buf += '%*s' % (int(width), value)
      output_buf += "\n"

   return output_buf, fetch_result

def odbc_query_execute_fetchall(DSN, db_query, db_param, column_name, column_width, direction):
   fetch_result = HcResult()

   output_buf = ""
   if type(column_width) is not list:
      column_width = [column_width]

   if direction == "vertical":
      total_width = 80
   else:
      total_width = sum(abs(int(CW)) for CW in column_width)
#   try:
#      total_width = sum(int(CW) for CW in column_width)
#   except:
#      total_width = column_width

   try:
      from lib.odbc_conn import odbcConn
   except ImportError as e:
      logger.exception('%s :: Import Error : %s', GetCurFunc(), e)
      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = e
      return output_buf, fetch_result

   db = odbcConn(DSN)
   try:
      db._GetConnect()
      logger.info('%s :: DB connection success ', GetCurFunc())
   except Exception as e:
      logger.exception('%s :: error : %s', GetCurFunc(), e)
      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = db.error
      return output_buf, fetch_result

   try:
      logger.info('%s :: DB execute : query type: %s', GetCurFunc(), type(db_query))
      if db_param == '':
         db.cursor.execute(db_query)
      else :
         db.cursor.execute(db_query, db_param)
   except Exception as e:
      logger.exception('%s :: Execute Error : %s', GetCurFunc(), e[1])
      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = e[1] + '\n' + output_buf
      return output_buf, fetch_result

   rows = db.cursor.fetchall()
   
   if len(rows) == 0:
      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = "NOT_EXIST: empty list is returned"
      return output_buf, fetch_result

   logger.info('%s :: output direction : %s', GetCurFunc(), direction)
   if direction == "vertical":
      max_column_name_width = len(max(column_name, key=len))
      logger.info('%s : initializing variable : max_column_name_width to %s', 
                            GetCurFunc(), max_column_name_width)
      for row in rows:
         str_row = unicode2str(row)
         t = zip(column_name, str_row)
         logger.debug('%s :: column_name, str_rows : %s', GetCurFunc(), t)
         for x in t:
            output_buf += " %*s : %-20s\n" % (max_column_name_width, x[0], x[1])
         output_buf += "\n"
      output_buf += "=" * abs(total_width) + '\n'
   else:
      for row in rows:
         str_row = unicode2str(row)
         for value, width in zip(str_row, column_width):
            output_buf += '%*s' % (int(width), value)
         output_buf += "\n"
      output_buf += "=" * abs(total_width) + '\n'
#      output_buf += "\n"

   return output_buf, fetch_result

def unicode2str(unicode_list):
   '''
   unicodestring = u"Hello world"
   # Convert Unicode to plain Python string: "encode"
   utf8string = unicodestring.encode("utf-8")
   # Convert plain Python string to Unicode: "decode"
   plainstring1 = unicode(utf8string, "utf-8")

   '''
   str_list = []
   for x in unicode_list:
      if type(x) == unicode:
         byte_str = x.encode("euc-kr")
      else:
         byte_str = x
      str_list.append(byte_str)

   return str_list


def GetSystemManufacturer():
   os_exec_result = os_execute('sudo /usr/sbin/dmidecode -s system-manufacturer | tail -1')
   SystemManufacturer = re.sub('\n','', os_exec_result.output)
   logger.info('%s :: System Manufacturer : %s', GetCurFunc(), SystemManufacturer)
   return SystemManufacturer

def os_execute(OS_COMMAND):
   ATTR_OS_EXEC_RESULT = 'output, exit_code'
   result_exec_tpl = namedtuple('result_exec_tpl', ATTR_OS_EXEC_RESULT)
   try:
      std_out = subprocess.check_output(OS_COMMAND, stderr=subprocess.STDOUT, shell=True)
      exit_code = 0
   except subprocess.CalledProcessError as e:
      logger.exception('%s :: error return code : %s', GetCurFunc(), e.returncode)
      std_out = e.output
      exit_code = 1
   logger.debug('%s :: std_out : \n%s', GetCurFunc(), std_out)
   result_exec = result_exec_tpl._make([std_out, exit_code])
   
	# logging result from os command
   logger.info('%s : result from os command : %s', GetCurFunc(), OS_COMMAND)
   output = result_exec.output.split('\n')
   for line in output:	
       logger.info('%s',  line)

   return result_exec



def sshd_status():
   ''' Check sshd status
   '''
   sshd_status_result = HcResult()
   hc_result_table = HcCmdResultTable('sshd running 확인',78)

   SSHD_PID = "/var/run/sshd.pid"
   try:
      f = open(SSHD_PID, 'r')
   except IOError as e:
      sshd_status_result.result = "NOK"
      hc_result_table._concate(e)
      sshd_status_result.output = hc_result_table.output
      return sshd_status_result

   pid = int(f.read())

   buf = 'Process Name     PID   PPID   USER  %MEM  PATH                 CREATE TIME\n'
   buf += "-" * hc_result_table.column_width + '\n'

   p = psutil.Process(pid)

   create_time=datetime.datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S")
   templ = "%-13s %6s %6s   %-5s %-5s %-20s %-s\n"
   buf += templ % (p.name(), p.pid, p.ppid(), p.username(), round(p.memory_percent(),1),"".join(p.cmdline()), create_time)

#   if p.name() == 'sshd':
#      sshd_status_result.result = "OK"

   hc_result_table._concate(buf)
   sshd_status_result.output = hc_result_table.output

   return sshd_status_result

def nas_status():
   ''' Check NAS status
   '''
   nas_status_result = HcResult()
   hc_result_table = HcCmdResultTable('NAS Fault 확인',78)

   NAS_CLI = "/opt/Navisphere/bin/naviseccli"

   config = ConfigLoad()
   nas_sp_ipaddr = config.get_item_from_section('ip address', 'nas_sp')
   logger.debug('%s :: nas_sp_ipaddr  : %s', GetCurFunc(), nas_sp_ipaddr)

   nascli_command='sudo ' + NAS_CLI + ' ' \
                   '-User sysadmin -Password sysadmin -Scope 0 -h ' + \
                   nas_sp_ipaddr + ' ' + \
                   'faults -list'
   nascli_command_result = os_execute(nascli_command)
       
   nascli_command_result_list = nascli_command_result.output.split('\n')
   logger.debug('%s :: nascli_command_result  : %s', GetCurFunc(), nascli_command_result)
   fault_msg = re.findall("Faulted", nascli_command_result.output)

   if fault_msg or nascli_command_result.exit_code:
      nas_status_result.result = "NOK"

   hc_result_table._concate(nascli_command_result.output)
   nas_status_result.output = hc_result_table.output

   return nas_status_result

def messages_check():
   ''' /var/log/messages check
   '''
   messages_check_result = HcResult()
   hc_result_table = HcCmdResultTable('/var/log/messages 확인',78)

   search_pattern = '"erro|down|fault|fail"'
   logger.info('%s : assign search pattern : %s', GetCurFunc(), search_pattern)

   messages_check_command = "/bin/egrep -i "+search_pattern+" /var/log/messages | cat"
   messages_check_command_result = os_execute(messages_check_command)
       
#   messages_check_command_result_list = messages_check_command_result.output.split('\n')
#   fault_msg = re.findall("Faulted", messages_check_result.output)
#   if fault_msg or nascli_command_result.exit_code:
   if messages_check_command_result.output != '':
      messages_check_result.result = "NOK"

   hc_result_table._concate(messages_check_command_result.output)
   messages_check_result.output = hc_result_table.output

   return messages_check_result

