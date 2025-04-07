#!/usr/bin/bash

docker pull redis:latest

docker run -d \
  --name redisContainer \
  -p 55000:6379 \
  redis:latest

python3 ./userFrontend.py