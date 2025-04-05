import redis, os, shortuuid
from dotenv import load_dotenv
load_dotenv()

def schedule_pod(podCpuCount: int):
    r = redis.Redis(host='localhost', port=os.getenv("REDIS_PORT"), decode_responses=True)
    all_keys = r.keys()

    best_fit_node = None
    min_leftover = float('inf')

    for node_id in all_keys:
        if node_id in ['totalCpuCount']:
            continue

        try:
            cpu_available = int(r.hget(node_id, 'cpuCount'))

            if cpu_available >= podCpuCount:
                leftover = cpu_available - podCpuCount
                if leftover < min_leftover:
                    best_fit_node = node_id
                    min_leftover = leftover
        except Exception:
            continue

    if best_fit_node:
        podID = shortuuid.uuid()
        
        # Decrement availableCpu NOT cpuCount
        r.hincrby(best_fit_node, "availableCpu", -podCpuCount)
        
        # Store pod info (you can keep this structure or modify it)
        r.hset(f"{best_fit_node}_pod_{podID}", "podCpuCount", podCpuCount)

        # Update global total available CPU count
        r.decrby("totalCpuCount", podCpuCount)

        return {
            "msg": "Pod scheduled successfully",
            "podID": podID,
            "nodeID": best_fit_node
        }
    else:
        return {"msg": "No suitable node found. Pod scheduling failed."}
