'''
---------------------------------------------------------
| Script that runs in every node spawned by Node Manager |
---------------------------------------------------------

'''
import sys, time, requests
import time, json
import uvicorn, shortuuid
from fastapi.templating import Jinja2Templates
from threading import Thread
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Extracting unique node ID from command line argument
nodeID = str(sys.argv[1])
nodePort = int(sys.argv[2])
cpuCount = int(sys.argv[3])
lastHB = 0

# In-memory storage of on-node pods info -> podsInfo = {podId<str> : podCpus<int>}
pods = {}

# Starting fastAPI server to listen for pod assignment
app = FastAPI()
templates = Jinja2Templates(directory="/app/templates")

@app.get("/")
async def nodeLanding(request:Request) :
    return templates.TemplateResponse("displayNode.html", {
        "request": request,
        "msg" : "You've reached a node - Here's my info!",
        "nodeID": nodeID,
        "nodePort": nodePort,
        "cpuCount": cpuCount
    })

# using GET endpoint coz I'm passing cpuCount as a queryParam - easy af
# Node should send confirmation of pod creation
@app.get("/addPod")
async def addPod(request:Request, podCpus:int, podID:str, availableCpu:int) :
    global cpuCount
    try:
        pods[podID] = podCpus
        cpuCount = availableCpu
        return JSONResponse(status_code=200, content={"msg": "SUCCESS"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"msg": "FAILED", "error": str(e)})
    
@app.get("/viewPods")
async def viewPods(request:Request) :
    return templates.TemplateResponse("podsInfo.html", {
        "request": request,
        "pods": pods
    })

@app.get("/lastHB")
async def lastHBAt(request : Request) :
    return {"Last Heartbeat At" : lastHB}

# ------------------------------------------------------------------------
def sendHeartbeat() :
    global lastHB
    # Sends heartbeat every 5 seconds
    while True :
        podsCpuCount = sum(pods.values()) if pods else 0
        hb = {"nodeID" : nodeID, 
              "podsCpus" : podsCpuCount,
              "lastAliveAt" : int(time.time()),
              "activePods" : len(pods)
             }
        
        response = requests.post(url="http://host.docker.internal:8000/heartbeats", 
                                 headers={'Content-Type': 'application/json'},
                                 json=hb)
        # response = requests.post(url="http://127.0.0.1:8000/heartbeats", 
        #                     headers={'Content-Type': 'application/json'},
        #                     json=hb)
        lastHB = hb["lastAliveAt"]
        time.sleep(5)

if __name__ == "__main__" :
    hbt = Thread(target=sendHeartbeat, daemon=True)
    hbt.start()
    uvicorn.run(app, host='0.0.0.0', port=nodePort)