from configparser import ConfigParser
from typing import (
    List,
    Optional,
)

from qdrant_client import QdrantClient
from qdrant_client.conversions import common_types as types
from qdrant_client.http.models import (Distance, PointStruct, VectorParams,
                                       models)

from mylib.service.log import logger


class QdrantService:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read('.env')
        self.QDRANT_IP = self.config.get('qdrant', 'ip', fallback='0.0.0.0')
        self.QDRANT_PORT = self.config.getint('qdrant', 'port', fallback=6333)
        self.COLLECTION_NAME = self.config.get('qdrant', 'collection_name', fallback='data_collection')
        self.SCORE_THRESHOLD = self.config.get('qdrant', 'score_threshold', fallback=0.0)
        self.OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
        self.VECTOR_SIZE = 1536
        self.qdclient = QdrantClient(self.QDRANT_IP, port=self.QDRANT_PORT)

        collections = self.qdclient.get_collections()
        if any(collection.name == self.COLLECTION_NAME for collection in collections.collections):
            logger.info("找到qdrant collection:{0}".format(self.COLLECTION_NAME))
        else:
            logger.info("qdrant collection:{0}不存在".format(self.COLLECTION_NAME))
            self.qdclient.create_collection(collection_name=self.COLLECTION_NAME,
                                            vectors_config=VectorParams(size=self.VECTOR_SIZE,
                                                                        distance=Distance.COSINE))

    # 保存到Qdrant(update or insert)
    def upsert(self, point: PointStruct):
        logger.info('FileStruct{0}即将写入qdrant...'.format(point.id))
        # 创建索引
        self.qdclient.upsert(collection_name=self.COLLECTION_NAME, wait=True, points=[point])
        logger.info(
            "resource{0}的第{1}页写入qdrant成功".format(point.payload['resource_name'], point.payload['page_no']))

    def search(self, query_vector, search_params={"exact": False, "hnsw_ef": 128},
               limit=3) -> List[types.ScoredPoint]:
        """
        搜索与query_vector最相似的limit个向量
        :param query_vector:
        :param limit:
        :param search_params:
        :return:
        """
        try:
            search_result = self.qdclient.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=query_vector,
                search_params=search_params,
                limit=limit,
                score_threshold=self.SCORE_THRESHOLD,
            )
            return search_result
        except Exception as e:
            logger.error("Qdrant搜索失败: {0}".format(str(e)))
            return []

    def delete(self, selector):
        """
        按照指定条件删除数据
        :param selector: 删除条件
        :return:
        """
        try:
            self.qdclient.delete(collection_name=self.COLLECTION_NAME, points_selector=selector)
        except Exception as e:
            logger.error("Qdrant删除失败: {0}".format(str(e)))

    def delete_by_point_id(self, point_id):
        """
        按照point_id删除数据
        :param point_id: point_id
        :return:
        """
        self.delete(models.PointIdsList(points=[point_id]))

    def delete_by_resource_id(self, resource_id):
        """
        按照resource_id删除数据
        :param resource_id: resource_id
        :return:
        """
        self.delete(models.FilterSelector(filter=models.Filter(
            must=[models.FieldCondition(key="resource_id", match=models.MatchValue(value=resource_id))]
        )))
