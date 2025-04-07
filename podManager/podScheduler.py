import redis, os, shortuuid, json
from dotenv import load_dotenv
load_dotenv()

# using best fit algorithm to schedule pods as of now, can be changed to first fit or worst fit if required

def schedule_pod(podCpuCount: int):
    r = redis.Redis(host='localhost', port=os.getenv("REDIS_PORT"), decode_responses=True)
    allNodes = r.hgetall("allNodes")
    best_fit_node = None
    min_leftover = float('inf')

    # for every node in the cluster, check if the available CPU is greater than or equal to the podCpuCount. From those that are, find the one with the least leftover CPU and allocate the pod to that node.

    for node_id in allNodes.keys():
        nodeInfo = json.loads(allNodes[node_id])
        availableCpu = nodeInfo["availableCpu"]

        if availableCpu >= podCpuCount:
            leftover = availableCpu - podCpuCount
            if leftover < min_leftover:
                best_fit_node = node_id
                min_leftover = leftover

    if best_fit_node:
        podID = shortuuid.uuid()

        print("Before decrementing : ", r.hget('allNodes', best_fit_node))  # 🪵 Debug log

        # Decrement availableCpu[]
        bestNodeInfo = json.loads(allNodes[best_fit_node])
        bestNodeInfo['availableCpu'] -= podCpuCount
        r.hset("allNodes", best_fit_node, json.dumps(bestNodeInfo))

        
        print("After decrementing : ", r.hget('allNodes', best_fit_node))  # 🪵 Debug log

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
        return {"msg" : 'FAILED'}
