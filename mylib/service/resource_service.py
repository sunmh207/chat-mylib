from mylib.entity.resource import Resource
from mylib.service.file_parser import FileParser
from mylib.service.mysql_service import MySQLService
from mylib.service.log import logger
from mylib.service.qdrant_service import QdrantService
import hashlib
import time
import openai
from qdrant_client.http.models import PointStruct
from mylib.service.ai_service import AIService
import os


class ResourceService:
    def upsert(self, file_path, resource_id, resource_name='') -> Resource:
        """
        解析file_path文件内容,并存储起来(同时存储到MySQL 和 Qdrant). 通过文件内容到MD5得到ID值，如果ID重复则更新，确保同样的文件不会保留两份。
        :param file_path:
        :param resource_id:
        :param resource_name:
        :return:
        """

        # 解析文件内容
        file_struct = FileParser().parse(file_path)
        resource_type = file_struct.type
        resource_summary = AIService().make_summary(file_struct.full_text)

        # 存储到mysql数据库
        conn = MySQLService().get_connection()
        cursor = conn.cursor()

        # 判断resource是否存在
        query_sql = "select * from resource where id = %s"
        cursor.execute(query_sql, resource_id)
        result = cursor.fetchone()
        if result:
            update_sql = "update resource set name = %s, summary=%s, type=%s, updated_time = %s where id = %s"
            cursor.execute(update_sql, (resource_name, resource_summary, resource_type, time.time(), resource_id))
        else:
            insert_sql = "insert into resource(id, name, summary, type, created_time, updated_time)" \
                         "values (%s, %s, %s, %s, %s, %s) "
            cursor.execute(insert_sql,
                           (resource_id, resource_name, resource_summary, resource_type, time.time(), time.time()))
        try:
            conn.commit()
            logger.info("保存Resource {0} 到MySQL，成功".format(resource_id))
        except Exception as e:
            conn.rollback()
            logger.error("保存Resource {0} 到MySQL，失败".format(resource_id))

        # 存储到qdrant
        qdrant_service = QdrantService()

        # 分页存储
        for page_no in range(len(file_struct.pages)):
            page_text = file_struct.pages[page_no]
            # 调用openai做embedding
            openai_embeddings = openai.Embedding.create(model="text-embedding-ada-002", input=page_text)
            embedding = openai_embeddings["data"][0]["embedding"]

            # 将resource id和当前页码合并,再hash生成唯一id
            point_id = hashlib.md5((resource_id + str(page_no)).encode('utf-8')).hexdigest()
            point = PointStruct(id=point_id, vector=embedding,
                                payload={"resource_id": resource_id, "resource_name": resource_name, "page_no": page_no,
                                         "text": page_text, "updated_time": time.time()})
            # 创建索引
            qdrant_service.upsert(point)
        return Resource(id=resource_id, name=resource_name, summary=resource_summary, type=resource_type,
                        created_time=time.time(), updated_time=time.time())

    def count(self) -> int:
        with MySQLService().get_connection() as conn, conn.cursor() as cursor:
            query_sql = "SELECT COUNT(*) AS cnt FROM resource"
            cursor.execute(query_sql)
            # 获取查询结果
            result = cursor.fetchone()
            return result[0]

    def get(self, id):
        with MySQLService().get_connection() as conn, conn.cursor() as cursor:
            sql = "SELECT id, name, summary, type, created_time, updated_time FROM resource WHERE id=%s"
            cursor.execute(sql, (id,))
            row = cursor.fetchone()
            if row:
                return Resource(*row)
            else:
                return None

    def list(self, start, limit) -> [Resource]:
        with MySQLService().get_connection() as conn, conn.cursor() as cursor:
            sql = "SELECT id, name, summary, type, created_time, updated_time FROM resource ORDER BY updated_time DESC LIMIT %s,%s"
            cursor.execute(sql, (start, limit))
            result = cursor.fetchall()
            return [self._row_to_resource(row) for row in result]

    def _row_to_resource(self, row):
        return Resource(
            id=row[0],
            name=row[1],
            summary=row[2],
            type=row[3],
            created_time=self._timestamp_to_str(row[4]),
            updated_time=self._timestamp_to_str(row[5])
        )

    def _timestamp_to_str(self, timestamp):
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

    def delete(self, id):
        # 查询资源信息

        with MySQLService().get_connection() as conn, conn.cursor() as cursor:
            query = 'SELECT name FROM resource WHERE id=%s LIMIT 1'
            cursor.execute(query, (id,))
            result = cursor.fetchone()
            filename = result[0]
            ext = os.path.splitext(filename)[1]
            file_uuid_name = id + ext
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, '../../upload', file_uuid_name)
            # 删除文件
            if os.path.exists(file_path):
                os.remove(file_path)

            # 从mysql数据库中删除
            sql = "delete from resource where id = %s"
            try:
                cursor.execute(sql, id)
                conn.commit()
                logger.info("从MySQL中删除Resource {0}，成功".format(id))
            except Exception as e:
                conn.rollback()
                logger.error("从MySQL中删除Resource {0}，失败".format(id))

        # 从qdrant中删除
        QdrantService().delete_by_resource_id(id)
