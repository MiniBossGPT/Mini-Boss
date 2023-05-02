from miniboss.logs import logger
from miniboss.memory.local import LocalCache


# List of supported memory backends
# Add a backend to this list if the import attempt is successful
supported_memory = ["local"]

# try:
#     from miniboss.memory.redismem import RedisMemory
#
#     supported_memory.append("redis")
# except ImportError:
#     RedisMemory = None
#
# try:
#     from miniboss.memory.pinecone import PineconeMemory
#
#     supported_memory.append("pinecone")
# except ImportError:
#     PineconeMemory = None
#
# try:
#     from miniboss.memory.weaviate import WeaviateMemory
#
#     supported_memory.append("weaviate")
# except ImportError:
#     WeaviateMemory = None
#
# try:
#     from miniboss.memory.milvus import MilvusMemory
#
#     supported_memory.append("milvus")
# except ImportError:
#     MilvusMemory = None


def get_memory(cfg, init=False):
    memory = None
    # if cfg.memory_backend == "pinecone":
    #     if not PineconeMemory:
    #         logger.warn(
    #             "Error: Pinecone is not installed. Please install pinecone"
    #             " to use Pinecone as a memory backend."
    #         )
    #     else:
    #         memory = PineconeMemory(cfg)
    #         if init:
    #             memory.clear()
    # elif cfg.memory_backend == "redis":
    #     if not RedisMemory:
    #         logger.warn(
    #             "Error: Redis is not installed. Please install redis-py to"
    #             " use Redis as a memory backend."
    #         )
    #     else:
    #         memory = RedisMemory(cfg)
    # elif cfg.memory_backend == "weaviate":
    #     if not WeaviateMemory:
    #         logger.warn(
    #             "Error: Weaviate is not installed. Please install weaviate-client to"
    #             " use Weaviate as a memory backend."
    #         )
    #     else:
    #         memory = WeaviateMemory(cfg)
    # elif cfg.memory_backend == "milvus":
    #     if not MilvusMemory:
    #         logger.warn(
    #             "Error: pymilvus sdk is not installed."
    #             "Please install pymilvus to use Milvus or Zilliz Cloud as memory backend."
    #         )
    #     else:
    #         memory = MilvusMemory(cfg)

    if memory is None:
        memory = LocalCache(cfg)
        if init:
            memory.clear()
    return memory


def get_supported_memory_backends():
    return supported_memory


__all__ = [
    "get_memory",
    "LocalCache"
]
