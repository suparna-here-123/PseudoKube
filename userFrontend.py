'''
nodeInfo format : 
{nodeID : {cpuCount : ___,
           podsInfo : {
                podID : ___,
                podCpuCount : ____
                }
            }
}
'''
import uvicorn
from fastapi import FastAPI, Request # HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from nodeManager.nodeUtils import createNode, registerNode


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def landingPage(request : Request) :
    return templates.TemplateResponse("addNode.html", {"request" : request})
    # return {"message" : "Landing page"}

# GET endpoint coz I'm passing cpuCount as a queryParam - easy af
@app.get("/addNode")
async def addNode(request : Request, cpuCount:str) :
    # Spawn new node with cpuCount
    newNodeID = createNode(cpuCount)
    # print(newNodeID)
    # If node creation was successful...
    if newNodeID :
        # ...add to cluster resource pool
        nodeInfo = {"nodeID" : newNodeID, "cpuCount" : int(cpuCount), "podsInfo" : {}}
        msg = registerNode(nodeInfo)
        return RedirectResponse(f"/showMsg?msg={msg}")
    else :
        return RedirectResponse(f"/showMsg?msg={'Node Creation Failed'}")

@app.get("/showMsg", response_class=HTMLResponse)
async def showMsg(request : Request, msg : str) :
    return templates.TemplateResponse("message.html", {"request" : request, "msg" : msg})

if __name__ == "__main__" :
    uvicorn.run(app, host="localhost")