'''
---------------------------------------------------------
| Script that runs in every node spawned by Node Manager |
---------------------------------------------------------

'''
import sys, time, requests
import time, json
import uvicorn, shortuuid
from threading import Thread
from fastapi import FastAPI, Request # HTTPException

# Extracting unique node ID from command line argument
nodeID = sys.argv[1]
nodePort = sys.argv[2]
cpuCount = sys.argv[3]

# In-memory storage of on-node pods info -> podsInfo = {podId<str> : podCpus<int>}
pods = {}

# Starting fastAPI server to listen for pod assignment
app = FastAPI()

# Node should send confirmation of pod creation
@app.get("/addPod")
async def addPod(request:Request, podCpus:int) :
    pass

# ------------------------------------------------------------------------
def sendHeartbeat() :
    # Sends heartbeat every 5 seconds
    while True :
        podsCpuCount = sum(pods.values()) if pods else 0
        hb = {"nodeID" : nodeID, 
              "podsCpus" : podsCpuCount,
              "lastAliveAt" : time.time(),
              "activePods" : len(pods),
             }
        
        requests.post(url="localhost:8000/heartbeats",
                      json=json.dumps(hb))        
        time.sleep(5)

if __name__ == "__main__" :
    hbt = Thread(target=sendHeartbeat, daemon=True)
    uvicorn.run(app, host='localhost', port=nodePort)