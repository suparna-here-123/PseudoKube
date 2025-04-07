# PseudoK8s

## Prerequisites to run container using python API for docker
* Add project directory containing files `<project_dir>/nodeManager/nodeScript.py` and `<project_dir>/requirements.txt` to virtual file under `Docker Settings` -> ``

## userFrontend.py
Frontend of app, accepts user inputs to create and monitor nodes

## requirements.txt
Python dependencies to be installed

## .env
* In case there's an issue connecting to docker daemon from python script, run `docker context inspect $(docker context show) | awk -F '"' '/"Host"/ {print $4}'` and save that to the `DOCKER_HOST` variable

* Pull redis docker image and run it on port of your choice, set it in `REDIS_PORT`

## nodeManager
Contains all files required by the node manager

## nodeScript.py
Script that runs in every node once spawned.
Sends heartbeats to node manager, maintains pod array

## nodeUtils
Helper functions required by `/userFrontend.py`

## nodeInfo format : 
{nodeID : {
    cpuCount : ___,
    availableCpu : ___,
           podsInfo : {
                podID : ___,
                podCpuCount : ____
                }
            }
}

## Things to do
1) Loading page before server is up on the node?
2) Script to start redis container -> frontend (HEARTBEAT MONITORING THREAD)