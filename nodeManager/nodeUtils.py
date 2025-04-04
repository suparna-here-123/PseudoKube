import docker, shortuuid, redis, os
from dotenv import load_dotenv

load_dotenv()

def createNode(cpuCount : str) :
    try :
        client = docker.from_env()
        nodeID = shortuuid.uuid()
        newNode = client.containers.run(
            image = "python",
            command = ["python3", "nodeScript.py", nodeID, cpuCount],
            detach = True,
            name = "cont_" + nodeID
        )
        return nodeID
    except Exception as e:
        return e

def registerNode(nodeInfo : dict) :
    try :
        r = redis.Redis(host='localhost', port=os.getenv("REDIS_PORT"), decode_responses=True)
        # Storing node-specific details
        r.hset(nodeInfo["nodeID"], "cpuCount", nodeInfo["cpuCount"])
        
        # Incrementing across-node cpuCount
        r.incrby("totalCpuCount", nodeInfo["cpuCount"])
        return "Registered node successfully :D"
    
    except Exception as e:
        # return "Error registering node :("
        return e
    
# if __name__ == "__main__" :
#     print(registerNode({'nodeID': 'LzCFsHhep7zhasWHXtMrzG', 'cpuCount': 1}))