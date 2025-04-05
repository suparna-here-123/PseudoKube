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
        return [f"Error: {str(e)}"]
#     # return "Error registering node :("
    
# if __name__ == "__main__" :
#     print(registerNode({'nodeID': 'LzCFsHhep7zhasWHXtMrzG', 'cpuCount': 1}))