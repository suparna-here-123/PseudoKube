'''
nodeInfo stored by NM in format : 
{allNodes : nodeID : {nodeCpus : ___,              -> Number of cpus the node has
                      podsCpus : ___,              -> Number of cpus being used by pods on the node
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
from nodeManager.nodeUtils import createNode, registerNode, updateHeartbeat, monitorHeartbeat, getDeadNodes
from random import randint
from typing import Dict
from threading import Thread
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Defining templates to extract info from post requests
class HeartBeat(BaseModel) :
    nodeID : str
    podsCpus : int
    activePods : int
    lastAliveAt : int

class NodeInfo(BaseModel) :
    nodeCpus : int
    podsCpus : int
    nodePort : int
    lastAliveAt : int
    activePods : int


@app.get("/")
async def landingPage(request : Request) :
    return templates.TemplateResponse("addNode.html", {"request" : request})


# GET endpoint coz I'm passing cpuCount as a queryParam - easy af
@app.get("/addNode")
async def addNode(request : Request, cpuCount:str) :
    # Spawn new node with cpuCount
    cpuCount = int(cpuCount)
    nodePort = randint(8001, 9000)
    newNodeID = createNode(cpuCount, nodePort)
    # If node creation was successful...
    if newNodeID :
        # ...add to cluster resource pool + register
        nodeInfo = {"nodeID" : newNodeID, 
                    "nodeCpus" : cpuCount,
                    "podsCpus" : 0,
                    "nodePort" : nodePort,
                   }
        msg = registerNode(nodeInfo)
        return templates.TemplateResponse("displayNode.html", {
            "request": request,
            "msg" : "Node Creation Succeeded!",
            "nodeID": newNodeID,
            "nodePort": nodePort,
            "cpuCount": cpuCount
        })
    else :
        return templates.TemplateResponse("displayNode.html", {
            "request": request,
            "msg" : "Node Creation Failed",
            "nodeID": "NA",
            "nodePort": "NA",
            "cpuCount": "NA"
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
async def showMsg(request : Request, msg : str) :
    return templates.TemplateResponse("message.html", {"request" : request, "msg" : msg})

if __name__ == "__main__" :
    hbt = Thread(target=monitorHeartbeat, daemon=True)
    hbt.start()
    uvicorn.run(app, host="0.0.0.0", port=8000)