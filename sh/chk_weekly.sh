#!/bin/ksh

export PATH=$PATH:/home/vms/bin
ID=`/usr/bin/id`

CntNorm=2
CntNormMemory=2048
CntNormVsmssConn=1
CntNormCdsConn=4
FS_list="/ /home/vms"

echo "============================================================================"
echo ""

echo "1. NTP 동작상태를 확인한다."
echo ""
CntNtpConf=`cat /etc/ntp/ntpservers | grep -v ^# | wc -l`
CntNtpPeers=`ntpq -p | grep "^*" | wc -l`
#if [ $CntNtpPeers -eq $CntNtpConf ] ; then
if [ $CntNtpPeers -ge 1 ] ; then
   Result="정상"
else
  Result="점검"
fi
printf "---------------------------------------------------------\n"
printf "       NTP 점검결과         |       %4s\n" $Result
printf "---------------------------------------------------------\n"
ntpq -p
printf "---------------------------------------------------------\n\n\n"


echo "2. 좀비 프로세스 상태 점검 "
echo ""

ps -ef > pslist.log
grep defunct pslist.log > /dev/null

retcode=$?
if [ $retcode = 0 ] ; then
	Result="점검"
else
	Result="정상"
fi

printf "---------------------------------------------------------\n"
printf "    좀비프로세스 상태       |       %4s\n"  $Result
printf "---------------------------------------------------------\n\n\n"
/bin/rm pslist.log



echo "3. 디스크 이중화 상태 점검"
echo ""

ChkMPS=`hostname | grep -i mps`
if [ X$ChkMPS == "X" ] ; then
	printf "---------------------------------------------------------\n"
	sudo hpacucli ctrl slot=0 show config | /bin/grep physicaldrive
	printf "---------------------------------------------------------\n\n\n"
else
	# For MPS
	printf "---------------------------------------------------------\n"
	sudo mpt-status -i 1 | /bin/grep phy
	printf "---------------------------------------------------------\n\n\n"
fi
