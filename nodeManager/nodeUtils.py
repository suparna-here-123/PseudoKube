import docker, shortuuid, json
import redis, os, time, requests
from dotenv import load_dotenv

load_dotenv()
r = redis.Redis(host='localhost', port=os.getenv("REDIS_PORT"), decode_responses=True)

def createNode(cpuCount:int, nodePort:int) :
    try :
        client = docker.from_env()
        nodeID = shortuuid.uuid()
        newNode = client.containers.run(
        image="python",
        command=f"python3 /app/nodeScript.py {nodeID} {nodePort} {cpuCount}",
        volumes={
                "/home/suppra/Desktop/CloudComputing/PseudoKube/nodeManager": {
                "bind": "/app",
                "mode": "ro"
            }
        },
            detach=True,
            name="cont_" + nodeID
        )
        return nodeID
    
    except Exception as e:
        return 'createNode ' + str(e)

def registerNode(nodeInfo : dict) :
    try :
        # Storing node-specific details
        r.hset("allNodes", nodeInfo["nodeID"], json.dumps(nodeInfo))

        # Adding to resource count (shouldn't include cpus occupied by pods)
        r.incrby("availableCpus", nodeInfo["nodeCpus"])
        return "Registered node successfully :D"
    
    except Exception as e:
        #return "Error registering node :("
        return 'registerNode ' + str(e)
    
def updateHeartbeat(hb:dict) :
    try :
        r.hset("allNodes", hb["nodeID"], "podsCpus", hb["podsCpus"])
        r.hset("allNodes", hb["nodeID"], "lastAliveAt", hb["lastAliveAt"])
        r.hset("allNodes", hb["nodeID"], "activePods", hb["activePods"])
        return 1
    except :
        return 0

# Checks if nodes are alive every 10 seconds
def monitorHeartbeat() :
    while True :
        rn = time.time()
        allNodes = r.hgetall('allNodes')
        for nodeID, nodeInfo in allNodes.items() :
            nodeInfo = json.loads(nodeInfo)
            if rn - nodeInfo['lastAliveAt'] > 15 :
                r.hset("deadNodes", nodeID, nodeInfo)
        time.sleep(10)

def getDeadNodes() :
    deadNodes = r.hgetall("deadNodes")
    return deadNodes
    
# if __name__ == "__main__" :
#     #print(registerNode({'nodeID': 'LzCFsHhep7zhasWHXtMrzG', 'cpuCount': 1}))
#     print(createNode(cpuCount=3, nodePort=8001))