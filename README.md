# PseudoK8s

## Prerequisites to run container using python API for docker
2) Add the project directory under `Docker Settings` -> `Resources` -> `File Sharing`
3) Run `sh startK8s.sh` from `PseudoKube` directory only.

## userFrontend.py
Frontend of app, accepts user inputs to create and monitor nodes

## requirements.txt
Python dependencies to be installed

## .env
* In case there's an issue connecting to docker daemon from python script, run `docker context inspect $(docker context show) | awk -F '"' '/"Host"/ {print $4}'` and save that to the `DOCKER_HOST` variable

## nodeManager
Contains all files required by the node manager

## nodeScript.py
Script that runs in every node once spawned.
Sends heartbeats to node manager, maintains pod array

## nodeUtils
Helper functions required by `/userFrontend.py`
Add the PROJECT_PATH variable (absolute path) to the .env file to allow access to your project folder

## nodeInfo format : 

## Things to do
1) Loading page before server is up on the node?
2) Script to start redis container -> frontend (HEARTBEAT MONITORING THREAD)

## Information about node stored in format
{allNodes : nodeID : {nodeCpus : ___,              -> Number of cpus the node has
                      podsCpus : ___,              -> Number of cpus being used by pods on the node,
                      podsInfo : [],               -> [{podID -> str : podCpuCount -> int}, {}, .....]
                      availableCpu : ___,          -> Number of cpus available on the node
                      nodePort : ___,              -> Port on which node is listening for pod addition requests
                      lastAliveAt : ___,           -> Last heartbeat sent at (in seconds)
                      activePods : ___,            -> Number of active pods in node (len of pods)
                     }
}
