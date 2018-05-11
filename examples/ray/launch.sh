#!/bin/bash

make push
python kube_launcher.py $@
sleep 15
kurreal list-processes
