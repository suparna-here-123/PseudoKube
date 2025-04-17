import redis, os, json
from dotenv import load_dotenv

load_dotenv()
REDIS_PORT = os.getenv("REDIS_PORT", "55000")  # Default to 55000 if not set
r = redis.Redis(host='localhost', port=int(REDIS_PORT), decode_responses=True)

def getNodePort(nodeID:str) :
    try :
        nodeInfo = json.loads(r.hget("allNodes", nodeID))
        return nodeInfo["nodePort"]
    
    except Exception as e:
        return str(e) 