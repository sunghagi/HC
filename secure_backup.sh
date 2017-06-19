#!/bin/bash
#Purpose = Backup of /etc Data
#Version 1.1
#START

DATE=`date +%Y%m%d`
FIRSTDAY_OF_MONTH=`date +%Y%m01`
HOSTNAME=`hostname`
FILENAME=secure_bkup_${HOSTNAME}_${DATE}.tar.gz #define Backup file name format.

RHEL_VER=`cat /etc/redhat-release  | awk '{print $7}'`
if [ $RHEL_VER = 5.6 ] ; then
	SRCDIR1="/var/log/secure.1 /var/log/messages.1 \
	/var/log/cron.1 /var/log/xferlog.1 \
	/var/log/wtmp.1 /var/log/btmp \
	/var/log/dmesg /var/log/dmesg.old /var/log/lastlog /var/log/sulog "
else
	SRCDIR1="/var/log/secure-${DATE} /var/log/messages-${DATE}\
	/var/log/cron-${DATE} /var/log/xferlog${DATE} \
	/var/log/wtmp-${FIRSTDAY_OF_MONTH} /var/log/btmp-${FIRSTDAY_OF_MONTH} \
	/var/log/dmesg /var/log/dmesg.old /var/log/lastlog /var/log/sulog "
fi

SRCDIR2=/root/.bash_history

DESDIR=/nas/HC/Secure # Destination of backup file.

# For gnu/tar
tar -cpzf $DESDIR/$FILENAME $SRCDIR1 $SRCDIR2

# For non gnu/tar
#tar -cpf - $DESDIR/$FILENAME $SRCDIR1 | gzip > $DESDIR/$FILENAME

#END

/nas/HC/dellog.py
