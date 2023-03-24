from configparser import ConfigParser
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, models
import openai
import os
from typing import List
from qdrant_client.conversions import common_types as types
from mylib.service.log import logger

class QdrantService:
    config = ConfigParser()
    config.read('.env')

    QDRANT_IP = config.get('qdrant', 'ip')
    QDRANT_PORT = config.getint('qdrant', 'port')
    COLLECTION_NAME = config.get('qdrant', 'collection_name')

    OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
    VECTOR_SIZE = 1536

    # 保存到Qdrant(update or insert)
    def upsert(self, point: PointStruct):
        print('FileStruct(' + point.id + ')即将写入qdrant...')
        qdclient = QdrantClient(self.QDRANT_IP, port=self.QDRANT_PORT)
        # openai.api_key = os.getenv("OPENAI_API_KEY")

        # collection不存在，则创建
        collections = qdclient.get_collections()
        if any(collection.name == self.COLLECTION_NAME for collection in collections.collections):
            logger.info("找到qdrant collection:{0}".format(self.COLLECTION_NAME))
        else:
            logger.info("qdrant collection:{0}不存在".format(self.COLLECTION_NAME))
            qdclient.create_collection(collection_name=self.COLLECTION_NAME,
                                       vectors_config=VectorParams(size=self.VECTOR_SIZE, distance=Distance.COSINE))

        # 调用openai做embedding
        # openai_embeddings = openai.Embedding.create(model=self.OPENAI_EMBEDDING_MODEL, input=point.payload['text'])
        # embedding = openai_embeddings["data"][0]["embedding"]

        # 创建索引
        qdclient.upsert(collection_name=self.COLLECTION_NAME, wait=True, points=[point])
        logger.info("resouce{0}的第{1}页写入qdrant成功".format(point.payload['resource_name'],point.payload['page_no']))

    def search(self, query_vector, limit=3, search_params={"exact": False, "hnsw_ef": 128}) -> List[types.ScoredPoint]:
        qdclient = QdrantClient(self.QDRANT_IP, port=self.QDRANT_PORT)
        search_result = qdclient.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_vector,
            limit=limit,
            search_params=search_params
        )
        return search_result
