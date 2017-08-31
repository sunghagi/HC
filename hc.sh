#!/bin/bash
source /home/vic/.bash_profile

DATE=`date +%Y%m%d`
sudo chmod 666 /nas/HC/${DATE}*.csv
sudo chmod 666 /nas/HC/log/hc.log

/nas/HC/HC.py

#/nas/HC/dellog.py
