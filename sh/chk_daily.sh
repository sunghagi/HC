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

echo "1. 프로세스 상태 확인"
/home/vms/bin/chk

echo ""
echo ""

echo "2. 연동상태 확인"
ChkSPS=`hostname | grep -i sps`
if [ X$ChkSPS == "X" ] ; then
	 printf "---------------------------------------------------------\n"
	 printf "      SPS 서버가 아닙니다.       \n"
	 printf "---------------------------------------------------------\n\n\n"
else
	VSMSS_IP=`grep ADDRESS /home/vms/config/GIPSMS.cfg | awk '{print $3}'`
	CntVsmssConn=`netstat -an | grep ESTA | grep $VSMSS_IP | wc -l`
	 if [ $CntVsmssConn -eq $CntNormVsmssConn ] ; then
		  Result="정상"
	 else
		  Result="점검"
	 fi
	 printf "---------------------------------------------------------\n"
	 printf "      VSMSS 연동상태 점검결과       |       %4s\n" $Result
	 printf "---------------------------------------------------------\n\n\n"
	CntCdsConn=`netstat -an | grep ESTA | egrep '9011|9012' | wc -l`
	 if [ $CntVsmssConn -eq $CntNormCdsConn ] ; then
		  Result="정상"
	 else
		  Result="점검"
	 fi
	 printf "---------------------------------------------------------\n"
	 printf "      CDS 연동상태 점검결과       |       %4s\n" $Result
	 printf "---------------------------------------------------------\n\n\n"
fi


echo "3. CPU가 정상 인식되었는지 확인한다."
echo ""
CntCpu=`cat /proc/cpuinfo | grep processor | wc -l`
if [ X$ChkSPS == "X" ] ; then
	if [ $CntCpu -eq $CntNormEtcCpu ] ; then
		Result="정상"
	else
		Result="점검"
	fi
else
	# For SPS
	if [ $CntCpu -eq $CntNormSpsCpu ] ; then
		Result="정상"
	else
		Result="점검"
	fi
fi
printf "---------------------------------------------------------\n"
printf "      인식된 CPU 개수   |      %2s 개 \n" $CntCpu
printf "---------------------------------------------------------\n"
printf "        점 검 결 과     |       %4s\n" $Result
printf "---------------------------------------------------------\n\n\n"


echo "4. Memory가 정상 인식되었는지 확인한다."
echo ""
#CntMemory=`cat /proc/meminfo | grep MemTotal | awk '{print $2}'`
CntMemory=`sudo dmidecode | egrep 'Size: .... MB' | awk 'BEGIN {sum=0;} {sum += $2} END {print sum}'`
ChkSPS=`hostname | grep -i sps`
if [ X$ChkSPS == "X" ] ; then
	if [ $CntMemory -eq $CntNormEtcMemory ] ; then
		Result="정상"
	else
		Result="점검"
	fi
else
	# For SPS
	if [ $CntMemory -eq $CntNormSpsMemory ] ; then
		Result="정상"
	else
		Result="점검"
	fi
fi
printf "---------------------------------------------------------\n"
printf "      Memory 용량          |       %5s MB\n" $CntMemory
printf "---------------------------------------------------------\n"
printf "      점 검 결 과          |       %4s\n" $Result
printf "---------------------------------------------------------\n\n\n"




