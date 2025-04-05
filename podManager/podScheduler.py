import redis, os, shortuuid
from dotenv import load_dotenv
load_dotenv()

# using best fit algorithm to schedule pods as of now, can be changed to first fit or worst fit if required

def schedule_pod(podCpuCount: int):
    r = redis.Redis(host='localhost', port=os.getenv("REDIS_PORT"), decode_responses=True)
    all_keys = r.keys()

    best_fit_node = None
    min_leftover = float('inf')

    # for every node in the cluster, check if the available CPU is greater than or equal to the podCpuCount. From those that are, find the one with the least leftover CPU and allocate the pod to that node.

    for node_id in all_keys:
        if node_id in ['totalCpuCount'] or "_pods" in node_id:
            continue

        try:
            cpu_available = int(r.hget(node_id, 'availableCpu'))

            if cpu_available >= podCpuCount:
                leftover = cpu_available - podCpuCount
                if leftover < min_leftover:
                    best_fit_node = node_id
                    min_leftover = leftover
        except Exception:
            continue

    if best_fit_node:
        podID = shortuuid.uuid()

        # Decrement availableCpu
        r.hincrby(best_fit_node, "availableCpu", -podCpuCount)

        # Store pod inside the node’s podsInfo hash
        r.hset(f"{best_fit_node}_pods", podID, podCpuCount)

        # Update global total available CPU count
        r.decrby("totalCpuCount", podCpuCount)

        return {
            "msg": "Pod scheduled successfully",
            "podID": podID,
            "nodeID": best_fit_node
        }
    else:
        return {"msg": "No suitable node found. Pod scheduling failed."}
