#!/bin/bash

docker build -t docker_client -f examples/docker/client/Dockerfile  .  
docker build -t docker_server -f examples/docker/server/Dockerfile  .  
