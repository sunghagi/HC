#!/bin/bash
#Purpose = Backup of /etc Data
#Version 1.1
#START

DATE=`date +%Y%m%d`
HOSTNAME=`hostname`

SRCDIR1="/var/log/secure* /var/log/messages* \
/var/log/cron* /var/log/xferlog* \
/var/log/wtmp* /var/log/btmp* \
/var/log/dmesg* /var/log/lastlog* /var/log/sulog* "

SRCDIR2=/root/.bash_history

#DESDIR=/nas/HC/Secure # Destination of backup file.
DESDIR=/nas/HC/Secure # Destination of backup file.
DIRNAME=${HOSTNAME}_${DATE} #define Backup file name format.

if [ -d $DESDIR/$DIRNAME ] ; then
	DIRNAME=${HOSTNAME}_2_${DATE} #define Backup file name format.
fi

if [ ! -d $DESDIR/$DIRNAME ] ; then
	mkdir -p $DESDIR/$DIRNAME
fi

cp -p $SRCDIR1 $SRCDIR2 $DESDIR/$DIRNAME

#END
