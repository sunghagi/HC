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

echo "1. Uptime �ð��� Ȯ���Ѵ�."
echo ""
CntUptimeDays=`uptime | awk '{print $3}'`
if [ $CntUptimeDays -lt 365 ] ; then
   Result="����"
else
   Result="����"
fi
printf "---------------------------------------------------------\n"
printf "      Server �����ð�    |    %4s days\n" $CntUptimeDays
printf "---------------------------------------------------------\n"
printf "          ���˰��       |       %4s\n" $Result
printf "---------------------------------------------------------\n\n\n"

echo "2. ���Ͻý��� inode ���뷮 ���� "
echo ""
#FS_list="/ /home/vms"

printf "---------------------------------------------------------\n"
printf "    Mounted On   |  capacity  |  Status         \n"
printf "---------------------------------------------------------\n"

for fs in $FS_list
do
   Usage=`df -i $fs | tail -1 | awk '{print $5}' | tr -d "%"`
   if [ $Usage -gt 70 ] ; then
      Result="����"
   else
      Result="����"
   fi
   printf "  %-14s |    %3s %%   |   %4s\n" $fs $Usage $Result
done
printf "---------------------------------------------------------\n\n"

echo "3. ���Ͻý��� ���뷮 ���� "
echo ""
#FS_list="/ /export/home /MBOX"

printf "---------------------------------------------------------\n"
printf "    Mounted On   |  capacity  |  Status         \n"
printf "---------------------------------------------------------\n"

for fs in $FS_list
do
   Usage=`df -k $fs | tail -1 | awk '{print $5}' | tr -d "%"`
   if [ $Usage -gt 70 ] ; then
      Result="����"
   else
      Result="����"
   fi
   printf "  %-14s |    %3s %%   |   %4s\n" $fs $Usage $Result
done
printf "---------------------------------------------------------\n\n"

echo "4. Core ���� ���� ���� Ȯ�� "
echo ""

find /home/vms -name core.[1-9][0-9]* > corelist.log
grep core corelist.log > /dev/null

retcode=$?
if [ $retcode = 0 ] ; then
Result="����"
else
Result="����"
fi

printf "---------------------------------------------------------\n"
printf "    Core ���� ���� Ȯ�� ���   |   %4s\n"  $Result
printf "    Core ���� ��� \n"
/bin/more corelist.log
printf "---------------------------------------------------------\n\n\n"
/bin/rm corelist.log
