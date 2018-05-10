#!/bin/bash

ray start --redis-address=$SYMPH_REDIS_SERVER_ADDR
echo =========================== WORKER STARTED: $1 ===========================
tail -f /dev/null  # sleep indefinitely