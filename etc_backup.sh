#!/bin/bash
#Purpose = Backup of /etc Data
#Version 1.1
#START


DATE=`date +%Y%m%d`
HOSTNAME=`hostname`
FILENAME1=etc_bkup_${HOSTNAME}_${DATE}.tar.gz #define Backup file name format.
FILENAME2=secure_bkup_${HOSTNAME}_${DATE}.tar.gz #define Backup file name format.

SRCDIR1=/etc # Source Directory 1.
SRCDIR2="/var/log/secure /var/log/dmesg /var/log/messages /var/log/wtmp \
/var/log/lastlog /var/log/cron /var/log/xferlog /var/log/sulog \
/var/log/btmp"
SRCDIR3=/root/.bash_history

DESDIR1=/nas/HC/ETC_BK # Destination of backup file.
DESDIR2=/nas/HC/Secure # Destination of backup file.

# For gnu/tar
tar -cpzf $DESDIR1/$FILENAME1 $SRCDIR1
tar -cpzf ${DESDIR2}/${FILENAME2} $SRCDIR2 $SRCDIR3

# For non gnu/tar
#tar -cpf - $DESDIR/$FILENAME $SRCDIR1 | gzip > $DESDIR/$FILENAME

#END

/nas/HC/dellog.py
