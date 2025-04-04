'''Script that runs in every node spawned by Node Manager'''
import sys, time
import datetime

# Extracting unique node ID from command line argument
nodeID = sys.argv[1]
cpuCount = sys.argv[2]

# Start time of node
startTime = datetime.datetime()

# print(f"I am {nodeID} and I started at {startTime}")