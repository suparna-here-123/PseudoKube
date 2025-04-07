import docker, shortuuid, json
import redis, os, time, requests
from dotenv import load_dotenv

load_dotenv()
r = redis.Redis(host='localhost', port=int(os.getenv("REDIS_PORT")), decode_responses=True)

def createNode(cpuCount:int, nodePort:int) :
    try :
        client = docker.from_env()
        nodeID = shortuuid.uuid()
        newNode = client.containers.run(
        image="python",
        command=["sh", "-c", f"pip install -r /app/nodeManager/nodeRequirements.txt && python3 /app/nodeManager/nodeScript.py {nodeID} {nodePort} {cpuCount}"],
        volumes={"/home/suyog/Cloud Computing/Project/PseudoKube": {"bind": "/app", "mode": "ro"},},
        ports={f"{nodePort}/tcp": nodePort}, # container_port: host_port
        extra_hosts={"host.docker.internal": "host-gateway"},
        detach=True,
        name="cont_" + nodeID
        )
        return nodeID
    
    except Exception as e:
        return 'createNode ' + str(e)

# def registerNode(nodeInfo : dict) :
#     try :
#         r = redis.Redis(host='localhost', port=os.getenv("REDIS_PORT"), decode_responses=True)
#         # Storing node-specific details
#         r.hset(nodeInfo["nodeID"], "cpuCount", nodeInfo["cpuCount"])
        
#         # Incrementing across-node cpuCount
#         r.incrby("totalCpuCount", nodeInfo["cpuCount"])
#         return ["Registered node successfully :D", "The node ID is : " + nodeInfo["nodeID"]]
    
#     except Exception as e:
#         # return "Error registering node :("
#         return e

def registerNode(nodeInfo : dict) :
    try :
        r = redis.Redis(host='localhost', port=os.getenv("REDIS_PORT"), decode_responses=True)
        
        nodeID = nodeInfo["nodeID"]
        cpuCount = nodeInfo["cpuCount"]

        # Store node total CPU
        r.hset(nodeID, mapping={
            "cpuCount": cpuCount,
            "availableCpu": cpuCount
        })

        # Update global total CPU count
        r.incrby("totalCpuCount", cpuCount)
        # Update available CPU count
        r.incrby("availableCpu", cpuCount)

        return ["Registered node successfully :D", "The node ID is : " + nodeID]
    except Exception as e:
        #return "Error registering node :("
        return 'registerNode ' + str(e)
    
def updateHeartbeat(hb:dict) :
    try :
        nodeInfo = json.loads(r.hget("allNodes", hb["nodeID"]))

        # Updating heartbeat-related fields
        nodeInfo['podsCpus'] = hb["podsCpus"]
        nodeInfo['lastAliveAt'] = hb["lastAliveAt"]
        nodeInfo['activePods'] = hb["activePods"]
        nodeInfo['status'] = 'ALIVE'

        # Saving to redis
        r.hset("allNodes", hb["nodeID"], json.dumps(nodeInfo))

        return "HB Updated"
    
    except Exception as e:
        return str(e)

# Checks if nodes are alive every 10 seconds
def monitorHeartbeat() :
    while True :
        time.sleep(5)
        print('Checking...')
        rn = time.time()
        allNodes = r.hgetall('allNodes')
        for nodeID, nodeInfo in allNodes.items() :
            nodeInfo = json.loads(nodeInfo)
            if rn - nodeInfo.get('lastAliveAt', 0) > 10 :
                nodeInfo['status'] = 'DEAD'
                r.hset("allNodes", nodeID, json.dumps(nodeInfo))
                print(nodeID)

# Returns dead nodes in format {nodeID : {nodeInfo}}
def getDeadNodes() :
    deadNodes = {}
    allNodes = r.hgetall("allNodes")
    for nodeID, nodeInfo in allNodes.items() :
        nodeInfo = json.loads(nodeInfo)
        if nodeInfo['status'] == 'DEAD' :
            nodeInfo['aliveMinsAgo'] = (time.time() - nodeInfo['lastAliveAt']) // 60
            deadNodes[nodeID] = nodeInfo
    return deadNodes

    
if __name__ == "__main__" :
    monitorHeartbeat()