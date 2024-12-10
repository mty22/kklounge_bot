#!/bin/bash
# This probably won't work on your system. Oh well.
echo "=> Launching to screen.."
screen -S kklbot -d -m /root/py311/bin/python /storage/nfs/matt/git/kklounge_bot/bot/bot.py
sleep 3
screen -ls
