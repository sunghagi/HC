#!/bin/ksh

export PATH=$PATH:/home/vms/bin
ID=`/usr/bin/id`

CntNormSpsCpu=8
CntNormEtcCpu=4
CntNormSpsMemory=20480
CntNormEtcMemory=4096
CntNormVsmssConn=1
CntNormCdsConn=4
FS_list="/ /home/vms"

echo "============================================================================"
echo ""

echo "1. ���μ��� ���� Ȯ��"
/home/vms/bin/chk

echo ""
echo ""

echo "2. �������� Ȯ��"
ChkSPS=`hostname | grep -i sps`
if [ X$ChkSPS == "X" ] ; then
	 printf "---------------------------------------------------------\n"
	 printf "      SPS ������ �ƴմϴ�.       \n"
	 printf "---------------------------------------------------------\n\n\n"
else
	VSMSS_IP=`grep ADDRESS /home/vms/config/GIPSMS.cfg | awk '{print $3}'`
	CntVsmssConn=`netstat -an | grep ESTA | grep $VSMSS_IP | wc -l`
	 if [ $CntVsmssConn -eq $CntNormVsmssConn ] ; then
		  Result="����"
	 else
		  Result="����"
	 fi
	 printf "---------------------------------------------------------\n"
	 printf "      VSMSS �������� ���˰��       |       %4s\n" $Result
	 printf "---------------------------------------------------------\n\n\n"
	CntCdsConn=`netstat -an | grep ESTA | egrep '9011|9012' | wc -l`
	 if [ $CntVsmssConn -eq $CntNormCdsConn ] ; then
		  Result="����"
	 else
		  Result="����"
	 fi
	 printf "---------------------------------------------------------\n"
	 printf "      CDS �������� ���˰��       |       %4s\n" $Result
	 printf "---------------------------------------------------------\n\n\n"
fi


echo "3. CPU�� ���� �νĵǾ����� Ȯ���Ѵ�."
echo ""
CntCpu=`cat /proc/cpuinfo | grep processor | wc -l`
if [ X$ChkSPS == "X" ] ; then
	if [ $CntCpu -eq $CntNormEtcCpu ] ; then
		Result="����"
	else
		Result="����"
	fi
else
	# For SPS
	if [ $CntCpu -eq $CntNormSpsCpu ] ; then
		Result="����"
	else
		Result="����"
	fi
fi
printf "---------------------------------------------------------\n"
printf "      �νĵ� CPU ����   |      %2s �� \n" $CntCpu
printf "---------------------------------------------------------\n"
printf "        �� �� �� ��     |       %4s\n" $Result
printf "---------------------------------------------------------\n\n\n"


echo "4. Memory�� ���� �νĵǾ����� Ȯ���Ѵ�."
echo ""
#CntMemory=`cat /proc/meminfo | grep MemTotal | awk '{print $2}'`
CntMemory=`sudo dmidecode | egrep 'Size: .... MB' | awk 'BEGIN {sum=0;} {sum += $2} END {print sum}'`
ChkSPS=`hostname | grep -i sps`
if [ X$ChkSPS == "X" ] ; then
	if [ $CntMemory -eq $CntNormEtcMemory ] ; then
		Result="����"
	else
		Result="����"
	fi
else
	# For SPS
	if [ $CntMemory -eq $CntNormSpsMemory ] ; then
		Result="����"
	else
		Result="����"
	fi
fi
printf "---------------------------------------------------------\n"
printf "      Memory �뷮          |       %5s MB\n" $CntMemory
printf "---------------------------------------------------------\n"
printf "      �� �� �� ��          |       %4s\n" $Result
printf "---------------------------------------------------------\n\n\n"




