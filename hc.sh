#!/bin/bash
source /home/vms/.bash_profile

DATE=`date +%Y%m%d`
sudo chmod 666 /nas/HC/${DATE}*.csv

/nas/HC/HC.py
