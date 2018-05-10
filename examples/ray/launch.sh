#!/bin/bash

make push
python symph_launcher.py $@
sleep 2
kurreal process
