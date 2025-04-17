import redis, os, time, json, requests
from dotenv import load_dotenv
from podManager.podScheduler import schedule_pod
from utils.redisUtils import getNodePort

load_dotenv()
REDIS_PORT = os.getenv("REDIS_PORT", "55000")  # Default to 55000 if not set
r = redis.Redis(host='localhost', port=int(REDIS_PORT), decode_responses=True)

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

def reschedule_pods_from_dead_node(nodeID: str):
    try:
        print(f"\nAttempting to reschedule pods from dead node {nodeID}")
        
        # Get all pods from the dead node
        nodeInfo = json.loads(r.hget("allNodes", nodeID))
        pods_to_reschedule = nodeInfo['podsInfo']
        
        if not pods_to_reschedule:
            print(f"No pods to reschedule on node {nodeID}")
            return []
            
        print(f"Found {len(pods_to_reschedule)} pods to reschedule")
        
        # Clear pods from dead node
        nodeInfo['podsInfo'] = []
        nodeInfo['podsCpus'] = 0
        nodeInfo['availableCpu'] = nodeInfo['nodeCpus']
        r.hset("allNodes", nodeID, json.dumps(nodeInfo))
        
        # Attempt to reschedule each pod
        failed_pods = []
        for pod in pods_to_reschedule:
            print(f"\nAttempting to reschedule pod {pod['podID']} with {pod['podCpuCount']} CPUs")
            
            # Try to schedule the pod using best-fit algorithm
            result = schedule_pod(pod['podCpuCount'])
            
            if result["msg"] == "SUCCESS":
                print(f"Found suitable node {result['nodeID']} for pod {pod['podID']}")
                
                # Update the pod's node assignment
                nodePort = getNodePort(result["nodeID"])
                if not nodePort:
                    print(f"Failed to get port for node {result['nodeID']}")
                    failed_pods.append(pod['podID'])
                    continue
                    
                print(f"Contacting node {result['nodeID']} at port {nodePort}")
                nodeResponse = requests.get(
                    f"http://localhost:{nodePort}/addPod?podCpus={result['podCpuCount']}&podID={result['podID']}&availableCpu={result['availableCpu']}"
                )
                
                if nodeResponse.status_code == 200 and nodeResponse.json().get("msg") == "SUCCESS":
                    print(f"Successfully rescheduled pod {pod['podID']} to node {result['nodeID']}")
                else:
                    print(f"Failed to add pod {pod['podID']} to node {result['nodeID']}")
                    failed_pods.append(pod['podID'])
            else:
                print(f"Failed to find suitable node for pod {pod['podID']}")
                failed_pods.append(pod['podID'])
        
        if failed_pods:
            print(f"\nFailed to reschedule pods: {failed_pods}")
        else:
            print("\nSuccessfully rescheduled all pods!")
            
        return failed_pods
    except Exception as e:
        print(f"Error rescheduling pods from dead node {nodeID}: {str(e)}")
        return []

def monitorHeartbeat() :
    while True :
        rn = time.time()
        allNodes = r.hgetall('allNodes')
        print("\nChecking node heartbeats...")
        for nodeID, nodeInfo in allNodes.items() :
            nodeInfo = json.loads(nodeInfo)
            lastAlive = nodeInfo.get('lastAliveAt', 0)
            timeSinceLastHB = rn - lastAlive
            print(f"Node {nodeID}: Last heartbeat {timeSinceLastHB:.2f} seconds ago")
            
            if timeSinceLastHB > 10 :
                # Initialize status if it doesn't exist
                if 'status' not in nodeInfo:
                    nodeInfo['status'] = 'ALIVE'
                
                if nodeInfo['status'] != 'DEAD':  # Only process if node wasn't already dead
                    print(f"\nNode {nodeID} has died! Last heartbeat was {timeSinceLastHB:.2f} seconds ago")
                    nodeInfo['status'] = 'DEAD'
                    r.hset("allNodes", nodeID, json.dumps(nodeInfo))
                    # Trigger pod rescheduling for newly dead node
                    print(f"Attempting to reschedule pods from dead node {nodeID}")
                    failed_pods = reschedule_pods_from_dead_node(nodeID)
                    if failed_pods:
                        print(f"Failed to reschedule pods: {failed_pods}")
        time.sleep(5)

def getDeadNodes() :
    deadNodes = {}
    rn = time.time()
    allNodes = r.hgetall("allNodes")
    for nodeID, nodeInfo in allNodes.items() :
        nodeInfo = json.loads(nodeInfo)
        # Consider a node dead if either:
        # 1. Its status is explicitly marked as 'DEAD'
        # 2. It hasn't sent a heartbeat in more than 10 seconds
        if nodeInfo['status'] == 'DEAD' or (rn - nodeInfo.get('lastAliveAt', 0) > 10):
            nodeInfo['aliveMinsAgo'] = (time.time() - nodeInfo['lastAliveAt']) // 60
            deadNodes[nodeID] = nodeInfo
    return deadNodes 