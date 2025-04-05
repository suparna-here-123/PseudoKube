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
    parts = msg.split("|", maxsplit=1)
    msg1 = parts[0]

    # Split Pod ID and Node ID separately if possible
    pod_node_info = parts[1] if len(parts) > 1 else ""
    pod_id = ""
    node_id = ""

    if "Pod ID:" in pod_node_info and "Scheduled on Node:" in pod_node_info:
        try:
            pod_part, node_part = pod_node_info.split(" | ")
            pod_id = pod_part.replace("Pod ID:", "").strip()
            node_id = node_part.replace("Scheduled on Node:", "").strip()
        except:
            pass

    return templates.TemplateResponse("message.html", {
        "request": request,
        "msg1": msg1,
        "podID": pod_id,
        "nodeID": node_id
    })

@app.get("/scheduleForm", response_class=HTMLResponse)
async def showScheduleForm(request: Request):
    return templates.TemplateResponse("schedulePod.html", {"request": request})

@app.get("/schedulePod")
async def schedulePod(request: Request, podCpuCount: int):
    result = schedule_pod(podCpuCount)

    if "podID" in result:
        msg1 = "Pod scheduled successfully! 🎉"
        msg2 = f"Pod ID: {result['podID']} | Scheduled on Node: {result['nodeID']}"
    else:
        msg1 = "Pod scheduling failed. 😞"
        msg2 = result["msg"]

    msgStr = f"{msg1}|{msg2}"
    print(">>> Message string going to /showMsg:", msgStr)  # 🪵 Debug log
    return RedirectResponse(f"/showMsg?msg={msgStr}", status_code=302)

    
    msgStr = "|".join(msgList)
    return RedirectResponse(f"/showMsg?msg={msgStr}")

if __name__ == "__main__" :
    uvicorn.run(app, host="localhost")