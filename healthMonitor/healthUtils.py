import redis, os, time, json
from dotenv import load_dotenv

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

def getDeadNodes() :
    deadNodes = {}
    allNodes = r.hgetall("allNodes")
    for nodeID, nodeInfo in allNodes.items() :
        nodeInfo = json.loads(nodeInfo)
        if nodeInfo['status'] == 'DEAD' :
            nodeInfo['aliveMinsAgo'] = (time.time() - nodeInfo['lastAliveAt']) // 60
            deadNodes[nodeID] = nodeInfo
    return deadNodes 