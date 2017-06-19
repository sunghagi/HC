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

echo "1. NTP ���ۻ��¸� Ȯ���Ѵ�."
echo ""
CntNtpConf=`cat /etc/ntp/ntpservers | grep -v ^# | wc -l`
CntNtpPeers=`ntpq -p | grep "^*" | wc -l`
#if [ $CntNtpPeers -eq $CntNtpConf ] ; then
if [ $CntNtpPeers -ge 1 ] ; then
   Result="����"
else
  Result="����"
fi
printf "---------------------------------------------------------\n"
printf "       NTP ���˰��         |       %4s\n" $Result
printf "---------------------------------------------------------\n"
ntpq -p
printf "---------------------------------------------------------\n\n\n"


echo "2. ���� ���μ��� ���� ���� "
echo ""

ps -ef > pslist.log
grep defunct pslist.log > /dev/null

retcode=$?
if [ $retcode = 0 ] ; then
	Result="����"
else
	Result="����"
fi

printf "---------------------------------------------------------\n"
printf "    �������μ��� ����       |       %4s\n"  $Result
printf "---------------------------------------------------------\n\n\n"
/bin/rm pslist.log



echo "3. ��ũ ����ȭ ���� ����"
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
