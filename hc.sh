#!/bin/bash
source /home/vic/.bash_profile

DATE=`date +%Y%m%d`
sudo chmod 666 /nas/HC/${DATE}*.csv

/nas/HC/HC.py

/nas/HC/dellog.py
