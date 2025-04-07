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
    
    except :
        return 0


def registerNode(nodeInfo : dict) :
    try :
        # Storing node-specific details
        nodeID = nodeInfo["nodeID"]
        nodeInfo.pop("nodeID")
        r.hset("allNodes", nodeID, json.dumps(nodeInfo))

        # Adding to resource count (shouldn't include cpus occupied by pods)
        r.incrby("clusterCpuCount", nodeInfo["nodeCpus"])
        return "Registered node successfully :D"
    
    except Exception as e:
        return "Error registering node :("
    
    
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
        rn = time.time()
        allNodes = r.hgetall('allNodes')
        for nodeID, nodeInfo in allNodes.items() :
            nodeInfo = json.loads(nodeInfo)
            if rn - nodeInfo.get('lastAliveAt', 0) > 10 :
                nodeInfo['status'] = 'DEAD'
                r.hset("allNodes", nodeID, json.dumps(nodeInfo))
        time.sleep(5)

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


# Retrieve best fit node's port during pod assignment
def getNodePort(nodeID:str) :
    try :
        nodeInfo = json.loads(r.hget("allNodes", nodeID))
        return nodeInfo["nodePort"]
    
    except Exception as e:
        return str(e)
    
if __name__ == "__main__" :
    monitorHeartbeat()