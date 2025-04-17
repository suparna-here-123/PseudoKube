import docker, shortuuid, json
import redis, os, time, requests
from dotenv import load_dotenv
from healthMonitor.healthUtils import updateHeartbeat, monitorHeartbeat, getDeadNodes

load_dotenv()
REDIS_PORT = os.getenv("REDIS_PORT", "55000")  # Default to 55000 if not set
r = redis.Redis(host='localhost', port=int(REDIS_PORT), decode_responses=True)

def createNode(cpuCount:int, nodePort:int) :
    try :
        client = docker.from_env()
        nodeID = shortuuid.uuid()
        newNode = client.containers.run(
        image="python",
        command=["sh", "-c", f"pip install -r /app/nodeManager/nodeRequirements.txt && python3 /app/nodeManager/nodeScript.py {nodeID} {nodePort} {cpuCount}"],
        volumes={os.getenv("PROJECT_PATH"): {"bind": "/app", "mode": "ro"},},
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
        # Add status field
        nodeInfo['status'] = 'ALIVE'
        r.hset("allNodes", nodeID, json.dumps(nodeInfo))

        # Adding to resource count (shouldn't include cpus occupied by pods)
        r.incrby("clusterCpuCount", nodeInfo["nodeCpus"])
        return "Registered node successfully :D"
    
    except Exception as e:
        return "Error registering node :("

if __name__ == "__main__" :
    monitorHeartbeat()