#!/bin/bash

echo redis address $SYMPH_REDIS_ADDR
ray start --redis-address=$SYMPH_REDIS_ADDR