'''
nodeInfo stored by NM in format : 
{allNodes : nodeID : {nodeCpus : ___,              -> Number of cpus the node has
                      podsCpus : ___,              -> Number of cpus being used by pods on the node,
                      podsInfo : [],
                      availableCpu : ___,          -> Number of cpus available on the node
                      nodePort : ___,              -> Port on which node is listening for pod addition requests
                      lastAliveAt : ___,           -> Last heartbeat sent at (in seconds)
                      activePods : ___,            -> Number of active pods in node (len of pods)
                     }
}
'''
import uvicorn, time
from fastapi import FastAPI, Request # HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from nodeManager.nodeUtils import createNode, registerNode
from utils.redisUtils import getNodePort
from healthMonitor.healthUtils import updateHeartbeat, monitorHeartbeat, getDeadNodes
from random import randint
from typing import Dict
from threading import Thread
from datetime import datetime
from podManager.podScheduler import schedule_pod
import requests
import json
import subprocess
from contextlib import asynccontextmanager
import redis
import os
import random
import string

running_nodes=[]

async def startup_event():
    Thread(target=monitorHeartbeat, daemon=True).start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await startup_event()
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

class HeartBeat(BaseModel) :
    nodeID : str
    podsCpus : int
    activePods : int
    lastAliveAt : int

class NodeInfo(BaseModel) :
    nodeCpus : int
    podsCpus : int
    podsInfo : list
    nodePort : int
    lastAliveAt : int
    activePods : int


@app.get("/")
async def landingPage(request : Request) :
    return templates.TemplateResponse("landing.html", {"request" : request})

# Form for sending the podCpuCount param (cpu required for the pod)
@app.get("/nodeScheduleForm", response_class=HTMLResponse)
async def showScheduleForm(request: Request):
    return templates.TemplateResponse("addNode.html", {"request": request})


# GET endpoint coz I'm passing cpuCount as a queryParam - easy af
@app.get("/addNode")
async def addNode(request : Request, cpuCount:str) :
    global running_nodes
    # Spawn new node with cpuCount
    cpuCount = int(cpuCount)
    nodePort = randint(8001, 9000)
    newNodeID = createNode(cpuCount, nodePort)

    running_nodes.append({"nodeID": newNodeID, "nodePort": nodePort})

    # If node creation was successful...
    if newNodeID :
        # ...add to cluster resource pool + register
        nodeInfo = {"nodeID" : newNodeID, 
                    "nodeCpus" : cpuCount,
                    "podsInfo" : [],
                    "availableCpu" : cpuCount,
                    "podsCpus" : 0,
                    "nodePort" : nodePort,
                   }
        msg = registerNode(nodeInfo)
        return templates.TemplateResponse("displayNode.html", {
            "request": request,
            "msg" : msg,
            "nodeID": newNodeID,
            "nodePort": nodePort,
            "cpuCount": cpuCount
        })
    else :
        return templates.TemplateResponse("displayNode.html", {
            "request": request,
            "msg" : "Node couldn't be created",
            "nodeID": "NA",
            "nodePort": "NA",
            "cpuCount": "NA"
        })
    
@app.get("/viewNodes")
async def viewNodes(request: Request):
    return templates.TemplateResponse("allNodes.html", {
        "request": request,
        "nodes": running_nodes
    })

@app.post("/heartbeats")
async def heartbeats(hb : HeartBeat) :
    hbDict = {"nodeID" : hb.nodeID,
              "podsCpus" : hb.podsCpus,
              "lastAliveAt" : hb.lastAliveAt,
              "activePods" : hb.activePods}

    resp = updateHeartbeat(hbDict)
    return {'response' : resp}

@app.get("/deadNodes")
async def deadNodes(request:Request) :
    dead = getDeadNodes()
    return templates.TemplateResponse("displayDeadNode.html", {
        "request": request,
        "dead": dead,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })


# GET endpoint coz you can pass podCpus as a queryParam - easy af
# User sends add-pod request here (port=8000, /addPod)
# Function should interpret response from node on pod creation
# response format : {"message": "Success"/"Failure", "podID":str/NA, "podCpus":int/0}
# If success -> Deduct from totalCpuCount in redis, show success in /showMsg
# If failure -> display error message in /showMsg
@app.get("/addPod")
async def addPod(podCpus:int) :
    pass


@app.get("/showMsg", response_class=HTMLResponse)
async def showMsg(request: Request, msg: str):
    parts = msg.split("|", maxsplit=1)
    msg1 = parts[0]

    # Default values
    pod_id = ""
    node_id = ""
    msg2 = parts[1] if len(parts) > 1 else ""

    # Handle Pod scheduling message
    if "Pod ID:" in msg2 and "Scheduled on Node:" in msg2:
        try:
            pod_part, node_part = msg2.split(" | ")
            pod_id = pod_part.replace("Pod ID:", "").strip()
            node_id = node_part.replace("Scheduled on Node:", "").strip()
        except:
            msg2 = parts[1] if len(parts) > 1 else ""

    # Handle Node registration message
    elif "The node ID is :" in msg2:
        node_id = msg2.replace("The node ID is :", "").strip()

    return templates.TemplateResponse("message.html", {
        "request": request,
        "msg1": msg1,
        "msg2": msg2,
        "podID": pod_id,
        "nodeID": node_id
    })

# Form for sending the podCpuCount param (cpu required for the pod)
@app.get("/scheduleForm", response_class=HTMLResponse)
async def showScheduleForm(request: Request):
    # Generate a unique pod ID
    podID = ''.join(random.choices(string.ascii_letters + string.digits, k=24))
    return templates.TemplateResponse("schedulePod.html", {
        "request": request,
        "podID": podID
    })

# Taking the podCpuCount param as an int and not a str as it is easier for computation during the best fit scheduling part
@app.get("/schedulePodWithAlgorithm")
async def schedulePodWithAlgorithm(request: Request, podID: str, podCpuCount: int, algorithm: str = None):
    if algorithm is None:
        # If no algorithm specified, show the scheduling options page
        return templates.TemplateResponse("schedulingOptions.html", {
            "request": request,
            "podID": podID,
            "podCpuCount": podCpuCount
        })
    
    # Simulate the scheduling without actually scheduling
    result = simulate_scheduling(podCpuCount, algorithm)
    
    if result:
        return {
            "success": True,
            "podID": podID,
            "nodeID": result["nodeID"],
            "nodePort": result["nodePort"],
            "availableCpu": result["availableCpu"],
            "nodeCpus": result["nodeCpus"],
            "message": f"Simulated scheduling using {algorithm} algorithm"
        }
    
    return {
        "success": False,
        "message": "No suitable node found for scheduling"
    }

@app.get("/schedulePod")
async def schedulePod(request: Request, podCpuCount: int):
    # This is the actual scheduling endpoint that uses best-fit
    result = schedule_pod(podCpuCount)
    flag = 0

    if result["msg"] == "SUCCESS":
        nodePort = getNodePort(result["nodeID"])
        nodeResponse = requests.get(f"http://localhost:{nodePort}/addPod?podCpus={result['podCpuCount']}&podID={result['podID']}&availableCpu={result['availableCpu']}") 
        if nodeResponse.status_code == 200 and nodeResponse.json().get("msg") == "SUCCESS":
            flag = 1
            # Get node information from Redis
            r = redis.Redis(host='localhost', port=int(os.getenv("REDIS_PORT", "55000")), decode_responses=True)
            nodeInfo = json.loads(r.hget("allNodes", result["nodeID"]))
            
            return templates.TemplateResponse("message.html", {
                "request": request,
                "msg1": "Pod scheduled successfully! 🎉",
                "msg2": f"Pod ID: {result['podID']} | Scheduled on Node: {result['nodeID']} | Node Port: {nodePort} | Available CPU: {nodeInfo['availableCpu']}"
            })
    
    return templates.TemplateResponse("message.html", {
        "request": request,
        "msg1": "Pod scheduling failed. 😞",
        "msg2": result["msg"]
    })

def simulate_scheduling(podCpuCount: int, algorithm: str):
    r = redis.Redis(host='localhost', port=int(os.getenv("REDIS_PORT", "55000")), decode_responses=True)
    allNodes = r.hgetall("allNodes")
    
    # Convert nodes to list for consistent ordering
    nodes_list = [(nodeID, json.loads(nodeInfo)) for nodeID, nodeInfo in allNodes.items()]
    
    if algorithm == "first-fit":
        # First Fit: Allocate to first node that has enough resources
        for nodeID, nodeInfo in nodes_list:
            if nodeInfo['availableCpu'] >= podCpuCount:
                # Get the next available container port
                container_port = 8001 + len(nodeInfo['podsInfo'])
                return {
                    "nodeID": nodeID,
                    "nodePort": nodeInfo['nodePort'],  # Node's listening port
                    "containerPort": container_port,   # Container's port
                    "availableCpu": nodeInfo['availableCpu'] - podCpuCount,
                    "nodeCpus": nodeInfo['availableCpu']
                }
    
    elif algorithm == "best-fit":
        # Best Fit: Allocate to node with smallest available CPU that can fit the pod
        best_node = None
        min_leftover = float('inf')
        
        for nodeID, nodeInfo in nodes_list:
            if nodeInfo['availableCpu'] >= podCpuCount:
                leftover = nodeInfo['availableCpu'] - podCpuCount
                if leftover < min_leftover:
                    min_leftover = leftover
                    container_port = 8001 + len(nodeInfo['podsInfo'])
                    best_node = {
                        "nodeID": nodeID,
                        "nodePort": nodeInfo['nodePort'],
                        "containerPort": container_port,
                        "availableCpu": nodeInfo['availableCpu'] - podCpuCount,
                        "nodeCpus": nodeInfo['availableCpu']
                    }
        return best_node
    
    elif algorithm == "worst-fit":
        # Worst Fit: Allocate to node with largest available CPU
        worst_node = None
        max_available = -1
        
        for nodeID, nodeInfo in nodes_list:
            if nodeInfo['availableCpu'] >= podCpuCount and nodeInfo['availableCpu'] > max_available:
                max_available = nodeInfo['availableCpu']
                container_port = 8001 + len(nodeInfo['podsInfo'])
                worst_node = {
                    "nodeID": nodeID,
                    "nodePort": nodeInfo['nodePort'],
                    "containerPort": container_port,
                    "availableCpu": nodeInfo['availableCpu'] - podCpuCount,
                    "nodeCpus": nodeInfo['availableCpu']
                }
        return worst_node
    
    return None

if __name__ == "__main__" :
    uvicorn.run(app, host="0.0.0.0", port=8000)