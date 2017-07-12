#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import psutil
import datetime
import time
import re
import ConfigParser
import subprocess
import inspect
from log import *
from hostconf import *
from collections import namedtuple
from lib.vms_hc import *

#logger = hcLogger('root')
logger = HcLogger()

#class HealthCheckCommand(object):
#def __init__():
#   pass

def GetCurFunc():
    return inspect.stack()[1][3]

def PrintDashLine():
    print "-" * 93

def PrintEqualLine():
    print "=" * 93

def IP_address_List():
    ''' return IP address list
    '''
    retlist = []
    for nic, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == 2 :
                retlist.append(addr.address)
#                   print(" address   : %s" % addr.address)
#               print(" family :  : %s" % addr.family)
    return retlist

def korean_weekday():
    DayOfTheWeek = datetime.datetime.today().weekday()
    #       Mon = 0, Tue = 1, Wed = 2, Thu = 3, Fri = 4, Sat = 5, Sun = 6
    if DayOfTheWeek == 0:
        return "월"
    elif DayOfTheWeek == 1:
        return "화"
    elif DayOfTheWeek == 2:
        return "수"
    elif DayOfTheWeek == 3:
        return "목"
    elif DayOfTheWeek == 4:
        return "금"
    elif DayOfTheWeek == 5:
        return "토"
    elif DayOfTheWeek == 6:
        return "일"

def ha_status():
    ha_status = []

    IPs = IP_address_List()
    logger.info('%s :: ip address : %s', GetCurFunc(),IPs )

    for IP in IPs:
        for hostlist in HostConf:
            if IP in hostlist:
                host_class = hostlist[2]
                if hostlist[1] == 'VIP':
                    st_ha_operating_mode = 'ACTIVE'
                    logger.info('%s : This host is Active', GetCurFunc())
                    break
                else:
                    st_ha_operating_mode = 'STANDBY'
    for hostlist in HostConf:
        if host_class in hostlist:
            if hostlist[1] == 'VIP':
                ha_installed = 1
                logger.info('%s : This %s is HA', GetCurFunc(), host_class)
                break
            else:
                ha_installed = 0
                
    ha_status.append(st_ha_operating_mode)
    ha_status.append(ha_installed)

    return ha_status

def host_info():
    ATTR_HOST_INFO = 'system_name hostname hostclass ip_address ha_operating_mode ha_installed'
    host_info_tpl = namedtuple('host_info_tpl', ATTR_HOST_INFO)

    IPs = IP_address_List()
    ha_status_list = ha_status()

    for IP in IPs:
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

def os_execute(OsCommand):
    try:
        std_out = subprocess.check_output(OsCommand, stderr=subprocess.STDOUT, shell=True)
    except Exception as e:
        logger.exception('%s :: error return code : %s', GetCurFunc(), e.returncode)
        std_out = e.output
    logger.debug('%s :: std_out : \n%s', GetCurFunc(), std_out)

    return std_out

def poll(interval):
    """Retrieve raw stats within an interval window."""
    tot_before = psutil.net_io_counters()
    pnic_before = psutil.net_io_counters(pernic=True)
    # sleep some time
    time.sleep(interval)
    tot_after = psutil.net_io_counters()
    pnic_after = psutil.net_io_counters(pernic=True)
    return (tot_before, tot_after, pnic_before, pnic_after)

def display_dellog_cron():
    cmd = 'sudo crontab -l| grep -i dellog'
    result = os_execute(cmd)

    if result == '':
        result = 'DELLOG is not setup in crontab\n'

    print 'DELLOG_CRON                root        %-s' % (result),

def display_dellog_cron_tomcat():
    config = ConfigLoad()
    userid = config.get_item_from_section('main', 'userid')
    cmd = 'sudo crontab -u %s -l| grep -i Delete_tomcat_logs' % userid
    result = os_execute(cmd)

    if result == '':
        result = 'DELLOG for tomcat is not setup in crontab\n'

    print 'DELLOG_CRON_TOMCAT         %-5s   %-s' % (userid, result),

def DisplayProcess(ProcessName, longcmd):
    RESULT = "OK"
    PrintEqualLine()
#   print 'Prcs Name     PID  PPID  USER   %CPU %MEM PATH                               CREATE TIME'
    print 'Prcs_Name       PID  PPID  USER   %MEM PATH                               START TIME'
    PrintDashLine()

    pid_list = psutil.pids()
                         
    RunningProcessList = []
    AppendRunningProcessList = []

    for pl in pid_list:
        try:
            p = psutil.Process(pl)
        except:
            pass
        else:
            PidProcessName = p.name()
            if PidProcessName == 'java':
                for cmdline in p.cmdline():
                    if re.search('true',cmdline):
                        PidProcessName = cmdline.split('=', 1)[0].strip()
#                       print cmdline
                        if re.search('java|file',PidProcessName):
                            continue
                        else:
                            PidProcessName = PidProcessName[2:]
                            break
                logger.debug('%s ::  PidProcessName : %s ',GetCurFunc(), PidProcessName)
#               if PidProcessName.upper() in map(str.upper, ProcessName) :
#               if filter(lambda x:PidProcessName in x, ProcessName)  :
            matcher = re.compile(PidProcessName, re.IGNORECASE)
            if filter(matcher.match, ProcessName):
                create_time=datetime.datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S")
                if p.cmdline():
                    if longcmd:
                        cmdline =  " ".join(p.cmdline())
                    else:
                        cmdline = " ".join(p.cmdline())[:34]
                        if len(cmdline) > 32:
                            cmdline = " ".join(p.cmdline())[:30] + '...'
                    logger.debug('%s ::  cmdline : %s ',GetCurFunc(), cmdline)
                else:
                    if p.status() == psutil.STATUS_ZOMBIE:
                        cmdline = '['+p.name()+'] <defunct>'
                    else:
                        cmdline = 'STATUS_UNKNOWN'
# CPU disable
                cpu_percent = p.cpu_percent(interval=None)
#                templ = "%-11s %5s %5s  %-5s %-4s %-4s %-34s %-s"
#                AppendRunningProcessList.append(templ % (PidProcessName, p.pid, p.ppid(), p.username(), cpu_percent, round(p.memory_percent(),1), cmdline, create_time))

                templ = "%-13s %5s %5s  %-6s %4s %-34s %-s"
                AppendRunningProcessList.append(templ % (PidProcessName, p.pid, p.ppid(), p.username(), round(p.memory_percent(),1), cmdline, create_time))
    logger.debug('%s :: Running process list : \n%s ', GetCurFunc(), '\n'.join(AppendRunningProcessList))
    
    for pl2 in ProcessName:
        if pl2 == '--':
            PrintDashLine()
            continue
        if pl2 == 'DELLOG_CRON':
            display_dellog_cron()
            continue
        if pl2 == 'DELLOG_CRON_TOMCAT':
            display_dellog_cron_tomcat()
            continue
        for pl3 in AppendRunningProcessList:
#               if filter(lambda x:pl2 in x, pl3):
#               if pl2 in pl3:
            if re.search(pl2, pl3, re.IGNORECASE):
                process_status = "Running"
                print pl3
                break
        else:
            process_status = "Not Running"
            RESULT = "NOK"
            print '%-60s %-s' % (pl2, process_status)

    PrintEqualLine()
    return RESULT

def print_column_name(column_name, column_width):
    total_width = sum(int(CW) for CW in column_width)

    print "-" * abs(total_width)
    for name, width in zip(column_name, column_width):
        print '%*s' % (int(width), name),
    print ""
    print "-" * abs(total_width)


def ConfigFileCheck(ConfigPath):
    import os.path
    if not os.path.isfile(ConfigPath):
        print "Failed to open config file !!"
        print "Check Server type !!"
        logger.info('%s :: Config File : %s', GetCurFunc(), ConfigPath)
        sys.exit()

def CommentRemove(ConfigValueWithComment):
    ConfigValue=ConfigValueWithComment.split('#', 1)[0].strip()
    return ConfigValue

def ha_process_name(HOST_INFO):
    if HOST_INFO.ha_operating_mode == 'ACTIVE':
        AppendProcessNameList = ['--','HA','MONITOR']
    else:
        AppendProcessNameList = ['--','HA']
    return AppendProcessNameList

def omc_process_name(HOST_INFO):
    omc_config = ConfigParser.RawConfigParser()
    omc_config.read('/nas/HC/config/hc.cfg')
    omc_type = omc_config.get('omc type','type')
    logger.info('%s :: omc_type : %s', GetCurFunc(), omc_type)
    AppendProcessNameList = []

    if omc_type == '1':
        if HOST_INFO.hostclass == 'OMP':
            if HOST_INFO.ha_operating_mode == 'ACTIVE' or HOST_INFO.ha_installed == 0:
                AppendProcessNameList = ['WEB','COLLECTOR','snmpd','--','mysqld']
            else:
                AppendProcessNameList = ['WEB','snmpd','--','mysqld']
        else:
            AppendProcessNameList = ['snmpd']
    elif omc_type == '2':
        if HOST_INFO.hostclass == 'OMP':
            if HOST_INFO.ha_operating_mode == 'ACTIVE' or HOST_INFO.ha_installed == 0:
                AppendProcessNameList = ['snmpd','--','mysqld']
        else:
            AppendProcessNameList = ['snmpd']
    elif omc_type == '3':  # delphi version
        if HOST_INFO.hostclass == 'OMP':
            AppendProcessNameList = ['OMA','--','mysqld']
        else:
            AppendProcessNameList = ['OMA']
        
    logger.debug('%s :: AppendProcessNameList : %s', GetCurFunc(), AppendProcessNameList)
    return AppendProcessNameList

def pnr_process_name(HOST_INFO, PNR_CONFIG_PATH):
#   if HOST_INFO.system_name == 'tmr01' and HOST_INFO.hostclass == 'OMP':
#       AppendProcessNameList = []
#       return AppendProcessNameList
    ConfigFileCheck(PNR_CONFIG_PATH)

    PnrConfig = ConfigParser.RawConfigParser()
    PnrConfig.read(PNR_CONFIG_PATH)
    PnrSectionNameList = PnrConfig.sections()

    HaStatus = HOST_INFO.ha_operating_mode
    logger.info('%s :: HaStatus : %s', GetCurFunc(), HaStatus)
    AppendProcessNameList = ['PNR']
    # PNR fork process list

    try:
        valid_process=PnrConfig.getint('main','processes')
    except:
        valid_process=PnrConfig.getint(' main ','processes')
    logger.debug('%s :: PNR valid process : %s', GetCurFunc(), valid_process)

    for SectionName in PnrSectionNameList:
        if SectionName == 'main' or SectionName == 'logger.main' or \
            SectionName == ' main ' or SectionName == 'PATH' or \
            SectionName == 'sink.ConsoleSink' or SectionName == 'sink.RollingFileSink' :
            continue

        logger.debug('%s :: PNR config Section Name : %s', GetCurFunc(), SectionName)
        valid_process_checker = re.compile("\d{1,2}")
        valid_process_counter = valid_process_checker.findall(SectionName)
        logger.debug('%s :: valid_process_counter : %s', GetCurFunc(), valid_process_counter)
        if int(valid_process_counter[0]) > valid_process:
            continue

        try:
            name=PnrConfig.get(SectionName,'name')
            logger.debug('%s :: PNR config Section name : %s', GetCurFunc(), name)
        except:
            pass

        try:
            alias=PnrConfig.get(SectionName,'alias')
        except:
            pass

        pathhead, pathtail = os.path.split(name)
        if pathhead:
            ProcessName = alias
        else:
            ProcessName = name
        logger.debug('%s :: pathhead, pathtail : %s, %s', GetCurFunc(), pathhead, pathtail)
        logger.debug('%s :: process name : %s', GetCurFunc(), ProcessName)

        # SPS는 PNR이 DELLOG를 Fork하여 중복표시됨.. skip..
#       if ProcessName == 'DELLOG':
#           continue

        # argv 가 있으면 프로세스이름에 추가
        argv=PnrConfig.get(SectionName,'argv')
        if argv and pathtail[-3:]!=".sh":
            ProcessName = ProcessName + ' ' + argv

        try:
            ha_enable=PnrConfig.get(SectionName,'ha_enable')
            ha_enable=CommentRemove(ha_enable)
            startflag=PnrConfig.get(SectionName,'startflag')
            startflag=CommentRemove(startflag)
        except:
            pass

        if HaStatus == 'ACTIVE':
            if startflag == '1':
                AppendProcessNameList.append(ProcessName)
        else:
            if ha_enable == '1':
                continue
            elif ha_enable == '0' and startflag == '1':
                AppendProcessNameList.append(ProcessName)

        if ProcessName == 'MPSIF_P':
            MpsifProcessName = ['MPSIF_C 1','MPSIF_C 2','MPSIF_C 3','MPSIF_C 4','MPSIF_C 5','MPSIF_C 6']
            AppendProcessNameList = AppendProcessNameList + MpsifProcessName

        if ProcessName == 'CDSIF':
            CdsConfigPath = '/home/tmr/config/TSPS/CDSIF.cfg'
            CdsConfig = ConfigParser.RawConfigParser()
            CdsConfig.read(CdsConfigPath)
            CdsSectionNameList = CdsConfig.sections()
            # CDSIF fork process list
            for SectionName in CdsSectionNameList:
                if SectionName == 'COMMON':
                    continue
                RunningMode=CdsConfig.get(SectionName,'RUNNING_MODE')
                RunningMode=CommentRemove(RunningMode)
                if RunningMode == '1':
                    AppendProcessNameList.append(CdsConfig.get(SectionName,'PROCESS_NAME'))

    logger.info('%s :: Process List : %s', GetCurFunc(), AppendProcessNameList)
    return AppendProcessNameList

def omppnr_process_name(HOST_INFO, PNR_CONFIG_PATH):
#   if HOST_INFO.system_name == 'tmr01' and HOST_INFO.hostclass == 'OMP':
#       AppendProcessNameList = []
#       return AppendProcessNameList
    ConfigFileCheck(PNR_CONFIG_PATH)

    PnrConfig = ConfigParser.RawConfigParser()
    PnrConfig.read(PNR_CONFIG_PATH)
    PnrSectionNameList = PnrConfig.sections()

    HaStatus = HOST_INFO.ha_operating_mode
    logger.info('%s :: HaStatus : %s', GetCurFunc(), HaStatus)
    AppendProcessNameList = ['PNR']
    # PNR fork process list

    try:
        valid_process=PnrConfig.getint('main','processes')
    except:
        valid_process=PnrConfig.getint(' main ','processes')
    logger.info('%s :: PNR valid process : %s', GetCurFunc(), valid_process)

    for SectionName in PnrSectionNameList:
        if SectionName == 'main' or SectionName == 'logger.main' or \
            SectionName == ' main ' or SectionName == 'PATH' or \
            SectionName == 'sink.ConsoleSink' or SectionName == 'sink.RollingFileSink' :
            continue

        logger.info('%s :: PNR config Section Name : %s', GetCurFunc(), SectionName)
        valid_process_checker = re.compile("\d{1,2}")
        valid_process_counter = valid_process_checker.findall(SectionName)
        logger.info('%s :: valid_process_counter : %s', GetCurFunc(), valid_process_counter)
        if int(valid_process_counter[0]) > valid_process:
            continue

        try:
            name=PnrConfig.get(SectionName,'name')
            logger.debug('%s :: PNR config Section name : %s', GetCurFunc(), name)
        except:
            pass

        try:
            alias=PnrConfig.get(SectionName,'alias')
        except:
            pass

        pathhead, pathtail = os.path.split(name)
        if pathhead:
            ProcessName = alias
        else:
            ProcessName = name

        logger.info('%s :: process name : %s', GetCurFunc(), ProcessName)

        # SPS는 PNR이 DELLOG를 Fork하여 중복표시됨.. skip..
#       if ProcessName == 'DELLOG':
#           continue

        # argv 가 있으면 프로세스이름에 추가
        argv=PnrConfig.get(SectionName,'argv')
        argv=CommentRemove(argv)
        if argv:
            ProcessName = ProcessName + ' ' + argv

        try:
            active_standby=PnrConfig.get(SectionName,'active_standby')
            active_standby=CommentRemove(active_standby)
        except:
            pass

        if HaStatus == 'ACTIVE':
            if active_standby == '0' or active_standby == '1':
                AppendProcessNameList.append(ProcessName)
        else:
            if active_standby == '0' or active_standby == '2':
                AppendProcessNameList.append(ProcessName)

    logger.info('%s :: Process List : %s', GetCurFunc(), AppendProcessNameList)
    return AppendProcessNameList

def mpspnr_process_name(HOST_INFO, PNR_CONFIG_PATH):
#   if HOST_INFO.system_name == 'tmr01' and HOST_INFO.hostclass == 'OMP':
#       AppendProcessNameList = []
#       return AppendProcessNameList
    ConfigFileCheck(PNR_CONFIG_PATH)

    PnrConfig = ConfigParser.RawConfigParser()
    PnrConfig.read(PNR_CONFIG_PATH)
    PnrSectionNameList = PnrConfig.sections()

    HaStatus = HOST_INFO.ha_operating_mode
    logger.info('%s :: HaStatus : %s', GetCurFunc(), HaStatus)
    AppendProcessNameList = ['PNR']
    # PNR fork process list

    try:
        valid_process=PnrConfig.getint('main','processes')
    except:
        valid_process=PnrConfig.getint(' main ','processes')
    logger.info('%s :: PNR valid process : %s', GetCurFunc(), valid_process)

    for SectionName in PnrSectionNameList:
        if SectionName == 'main' or SectionName == 'logger.main' or \
            SectionName == ' main ' or SectionName == 'PATH' or \
            SectionName == 'sink.ConsoleSink' or SectionName == 'sink.RollingFileSink' :
            continue

        logger.info('%s :: PNR config Section Name : %s', GetCurFunc(), SectionName)
        valid_process_checker = re.compile("\d{1,2}")
        valid_process_counter = valid_process_checker.findall(SectionName)
        logger.info('%s :: valid_process_counter : %s', GetCurFunc(), valid_process_counter)
        if int(valid_process_counter[0]) > valid_process:
            continue

        try:
            name=PnrConfig.get(SectionName,'name')
            logger.debug('%s :: PNR config Section name : %s', GetCurFunc(), name)
        except:
            pass

        try:
            alias=PnrConfig.get(SectionName,'alias')
        except:
            pass

        pathhead, pathtail = os.path.split(name)
        if pathhead:
            ProcessName = alias
        else:
            ProcessName = name

        logger.info('%s :: process name : %s', GetCurFunc(), ProcessName)

        # SPS는 PNR이 DELLOG를 Fork하여 중복표시됨.. skip..
#       if ProcessName == 'DELLOG':
#           continue

        # argv 가 있으면 프로세스이름에 추가
        argv=PnrConfig.get(SectionName,'argv')
        argv=CommentRemove(argv)

        if argv:
            ProcessName = ProcessName + ' ' + argv

        enable=PnrConfig.get(SectionName,'enable')

        if enable == '1':
            AppendProcessNameList.append(ProcessName)

        if ProcessName == 'MPSIF_P':
            MpsifProcessName = ['MPSIF_C 1','MPSIF_C 2','MPSIF_C 3','MPSIF_C 4','MPSIF_C 5','MPSIF_C 6']
            AppendProcessNameList = AppendProcessNameList + MpsifProcessName

    logger.info('%s :: Process List : %s', GetCurFunc(), AppendProcessNameList)
    return AppendProcessNameList

def dbsvrpm_process_name(HOST_INFO, PNR_CONFIG_PATH):
#   if HOST_INFO.system_name == 'tmr01' and HOST_INFO.hostclass == 'OMP':
#       AppendProcessNameList = []
#       return AppendProcessNameList
    ConfigFileCheck(PNR_CONFIG_PATH)

    PnrConfig = ConfigParser.RawConfigParser()
    PnrConfig.read(PNR_CONFIG_PATH)
    PnrSectionNameList = PnrConfig.sections()

    HaStatus = HOST_INFO.ha_operating_mode
    logger.info('%s :: HaStatus : %s', GetCurFunc(), HaStatus)
    AppendProcessNameList = ['DBSVRPM']
    # PNR fork process list

    for SectionName in PnrSectionNameList:
        if SectionName == 'main' or SectionName == 'logger.main' or \
            SectionName == 'sink.ConsoleSink' or SectionName == 'sink.RollingFileSink' :
            continue

        logger.info('%s :: PNR config Section Name : %s', GetCurFunc(), SectionName)
        valid_process_checker = re.compile("\d{1,2}")
        valid_process_counter = valid_process_checker.findall(SectionName)

        try:
            path=PnrConfig.get(SectionName,'PATH')
        except:
            continue
        pathhead, pathtail = os.path.split(path)
#       if pathhead:
#           ProcessName = alias
#       else:
#           ProcessName = name
        ProcessName = pathtail

        logger.info('%s :: process name : %s', GetCurFunc(), ProcessName)

        # SPS는 PNR이 DELLOG를 Fork하여 중복표시됨.. skip..
#       if ProcessName == 'DELLOG':
#           continue

        # argv 가 있으면 프로세스이름에 추가
#       argv=PnrConfig.get(SectionName,'argv')
#       if argv:
#           ProcessName = ProcessName + ' ' + argv

#       ha_enable=PnrConfig.get(SectionName,'ha_enable')
#       ha_enable=CommentRemove(ha_enable)
        respawn_condition=PnrConfig.get(SectionName,'RESPAWN_CONDITION')
        respawn_condition=CommentRemove(respawn_condition)

        if HaStatus == 'ACTIVE':
            if respawn_condition == '1' or respawn_condition == '2':
                AppendProcessNameList.append(ProcessName)
        else:
            if respawn_condition == '1' or respawn_condition == '3':
                AppendProcessNameList.append(ProcessName)

        if ProcessName == 'vMPSIF_P':
            MpsifProcessName = ['vMPSIF_C 1 0','vMPSIF_C 2 0']
            AppendProcessNameList = AppendProcessNameList + MpsifProcessName

        if ProcessName == 'CDSIF' and HaStatus == 'ACTIVE':
            CdsConfigPath = '/home/vms/config/CDSIF.cfg'
            CdsConfig = ConfigParser.RawConfigParser()
            CdsConfig.read(CdsConfigPath)
            CdsSectionNameList = CdsConfig.sections()
            # CDSIF fork process list
            for SectionName in CdsSectionNameList:
                if SectionName == 'COMMON':
                    continue
                RunningMode=CdsConfig.get(SectionName,'RUNNING_MODE')
                RunningMode=CommentRemove(RunningMode)
                if RunningMode == '1':
                    AppendProcessNameList.append(CdsConfig.get(SectionName,'PROCESS_NAME'))

    logger.info('%s :: Process List : %s', GetCurFunc(), AppendProcessNameList)
    return AppendProcessNameList
