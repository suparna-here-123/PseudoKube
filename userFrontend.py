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
from podManager.podScheduler import schedule_pod


app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def landingPage(request : Request) :
    return templates.TemplateResponse("schedulePod.html", {"request" : request})
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
        msgList = registerNode(nodeInfo)
        msgStr = "|".join(msgList)
        return RedirectResponse(f"/showMsg?msg={msgStr}")
    else :
        return RedirectResponse(f"/showMsg?msg={'Node Creation Failed'}")

@app.get("/showMsg", response_class=HTMLResponse)
async def showMsg(request: Request, msg: str):
    parts = msg.split("|")
    return templates.TemplateResponse("message.html", {
        "request": request,
        "msg1": parts[0],
        "msg2": parts[1] if len(parts) > 1 else ""
    })

@app.get("/scheduleForm", response_class=HTMLResponse)
async def showScheduleForm(request: Request):
    return templates.TemplateResponse("schedulePod.html", {"request": request})

@app.get("/schedulePod")
async def schedulePod(request: Request, podCpuCount: int):
    result = schedule_pod(podCpuCount)
    if "podID" in result:
        msgList = [
            f"Pod scheduled successfully! 🎉",
            f"Pod ID: {result['podID']} | Scheduled on Node: {result['nodeID']}"
        ]
    else:
        msgList = ["Pod scheduling failed. 😞", result["msg"]]
    
    msgStr = "|".join(msgList)
    return RedirectResponse(f"/showMsg?msg={msgStr}")

if __name__ == "__main__" :
    uvicorn.run(app, host="localhost")