import redis, os, shortuuid, json
from dotenv import load_dotenv
load_dotenv()

# using best fit algorithm to schedule pods as of now, can be changed to first fit or worst fit if required

def schedule_pod(podCpuCount: int):
    r = redis.Redis(host='localhost', port=os.getenv("REDIS_PORT"), decode_responses=True)
    allNodes = r.hgetall("allNodes")
    best_fit_node = None
    min_leftover = float('inf')

    print(f"\nAttempting to schedule pod requiring {podCpuCount} CPUs")
    print("Available nodes and their capacities:")
    
    # for every node in the cluster, check if the available CPU is greater than or equal to the podCpuCount. From those that are, find the one with the least leftover CPU and allocate the pod to that node.
    for node_id in allNodes.keys():
        nodeInfo = json.loads(allNodes[node_id])
        availableCpu = nodeInfo["availableCpu"]
        status = nodeInfo.get('status', 'ALIVE')
        
        print(f"Node {node_id}: {availableCpu} CPUs available, Status: {status}")
        
        if status == 'ALIVE' and availableCpu >= podCpuCount:
            leftover = availableCpu - podCpuCount
            if leftover < min_leftover:
                best_fit_node = node_id
                min_leftover = leftover

    if best_fit_node:
        podID = shortuuid.uuid()
        print(f"\nFound best fit node: {best_fit_node} with {min_leftover} CPUs leftover")

        # Decrement availableCpu[]
        bestNodeInfo = json.loads(allNodes[best_fit_node])
        bestNodeInfo['availableCpu'] -= podCpuCount
        
        # Save new pod info under redis
        newPodInfo = {"podID" : podID, "podCpuCount" : podCpuCount}
        bestNodeInfo['podsInfo'].append(newPodInfo)

        r.hset("allNodes", best_fit_node, json.dumps(bestNodeInfo))

        # Update global total available CPU count
        r.decrby("clusterCpuCount", podCpuCount)

        return {
            "msg": "SUCCESS",
            "podID": podID,
            "nodeID": best_fit_node,
            "podCpuCount": podCpuCount,
            "availableCpu": bestNodeInfo['availableCpu']
        }
    else:
        print("\nNo suitable node found for scheduling")
        return {"msg" : 'FAILED'}
