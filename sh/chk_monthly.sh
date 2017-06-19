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

echo "1. Uptime 시간을 확인한다."
echo ""
CntUptimeDays=`uptime | awk '{print $3}'`
if [ $CntUptimeDays -lt 365 ] ; then
   Result="정상"
else
   Result="점검"
fi
printf "---------------------------------------------------------\n"
printf "      Server 가동시간    |    %4s days\n" $CntUptimeDays
printf "---------------------------------------------------------\n"
printf "          점검결과       |       %4s\n" $Result
printf "---------------------------------------------------------\n\n\n"

echo "2. 파일시스템 inode 샤용량 점검 "
echo ""
#FS_list="/ /home/vms"

printf "---------------------------------------------------------\n"
printf "    Mounted On   |  capacity  |  Status         \n"
printf "---------------------------------------------------------\n"

for fs in $FS_list
do
   Usage=`df -i $fs | tail -1 | awk '{print $5}' | tr -d "%"`
   if [ $Usage -gt 70 ] ; then
      Result="점검"
   else
      Result="정상"
   fi
   printf "  %-14s |    %3s %%   |   %4s\n" $fs $Usage $Result
done
printf "---------------------------------------------------------\n\n"

echo "3. 파일시스템 샤용량 점검 "
echo ""
#FS_list="/ /export/home /MBOX"

printf "---------------------------------------------------------\n"
printf "    Mounted On   |  capacity  |  Status         \n"
printf "---------------------------------------------------------\n"

for fs in $FS_list
do
   Usage=`df -k $fs | tail -1 | awk '{print $5}' | tr -d "%"`
   if [ $Usage -gt 70 ] ; then
      Result="점검"
   else
      Result="정상"
   fi
   printf "  %-14s |    %3s %%   |   %4s\n" $fs $Usage $Result
done
printf "---------------------------------------------------------\n\n"

echo "4. Core 파일 생성 여부 확인 "
echo ""

find /home/vms -name core.[1-9][0-9]* > corelist.log
grep core corelist.log > /dev/null

retcode=$?
if [ $retcode = 0 ] ; then
Result="점검"
else
Result="정상"
fi

printf "---------------------------------------------------------\n"
printf "    Core 파일 생성 확인 결과   |   %4s\n"  $Result
printf "    Core 파일 목록 \n"
/bin/more corelist.log
printf "---------------------------------------------------------\n\n\n"
/bin/rm corelist.log
