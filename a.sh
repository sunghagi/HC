#!/bin/bash

USERID=$(cat /etc/passwd | awk -F: '{print $3}')

for uid in $USERID; do
	if [ $uid -ge 500 ] ; then
		username=$(grep ".:.:$uid" /etc/passwd | awk -F: '{print $1}')
		echo $username
   fi
done
