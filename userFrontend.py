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

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Defining templates to extract info from post requests
class HeartBeat(BaseModel) :
    nodeID : int
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
        return RedirectResponse(f"/showMsg?msg={msg}")
    else :
        return RedirectResponse(f"/showMsg?msg={'Node Creation Failed'}")

@app.post("/heartbeats")
async def heartbeats(hb : HeartBeat) :
    hbDict = {"nodeID" : hb.nodeID,
              "podsCpus" : hb.podsCpus,
              "lastAliveAt" : hb.lastAliveAt,
              "activePods" : hb.activePods}

    if not updateHeartbeat(hbDict) :
        print(f"Error updating heartbeat of node {hb.nodeID}")


@app.get("/deadNodes")
async def deadNodes(request:Request) :
    return {"message" : getDeadNodes()}



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
    uvicorn.run(app, host="localhost", port=8000)