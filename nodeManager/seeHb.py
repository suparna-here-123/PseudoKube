import redis, os, json
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis(host='0.0.0.0', port=int(os.getenv("REDIS_PORT")), decode_responses=True)


# keys = r.keys()
# print("Redis keys = ", keys)

# x = r.hgetall("allNodes")
# for key, value in x.items() :
#     print(f"{key} : {value}\n")

# print("Cluster CPU count = ", r.get("clusterCpuCount"))

allNodes = r.hgetall("allNodes")
print(allNodes)