from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct, models
from service.file import FileStruct
import os
import openai
from configparser import ConfigParser



class LibTookit:
    # QDRANT_IP = '127.0.0.1'
    # QDRANT_PORT = 6333
    # COLLECTION_NAME = 'data_collection'

    config = ConfigParser()
    config.read('.env')

    QDRANT_IP = config.get('qdrant', 'ip')
    QDRANT_PORT = config.getint('qdrant', 'port')
    COLLECTION_NAME = config.get('qdrant', 'collection_name')

    OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
    VECTOR_SIZE = 1536

    #保存到Qdrant
    def save_to_qdrant(self,file_struct:FileStruct):
        print('FileStruct('+file_struct.id+')即将写入qdrant...')
        qdclient = QdrantClient(self.QDRANT_IP, port=self.QDRANT_PORT)
        openai.api_key = os.getenv("OPENAI_API_KEY")

        # collection不存在，则创建
        collections = qdclient.get_collections()
        if any(collection.name == self.COLLECTION_NAME for collection in collections.collections):
            print('找到connection:',self.COLLECTION_NAME)
        else:
            print('connection:', self.COLLECTION_NAME,'不存在')
            qdclient.create_collection(collection_name=self.COLLECTION_NAME, vectors_config=VectorParams(size=self.VECTOR_SIZE, distance=Distance.COSINE))

        # 调用openai做embedding
        openai_embeddings = openai.Embedding.create(model=self.OPENAI_EMBEDDING_MODEL, input=file_struct.text)
        embedding = openai_embeddings["data"][0]["embedding"]

        point = PointStruct(id=file_struct.id, vector=embedding, payload={"filename":file_struct.filename,"text": file_struct.text})
        # 创建索引
        qdclient.upsert(collection_name=self.COLLECTION_NAME,wait=True,points=[point])
        print('FileStruct(' + file_struct.id + ')写入qdrant成功')

    def __make_query_prompt(self, question, answers):
        system = '你是一个问答机器人'
        q = "我们提供了以下背景信息. \n"
        # 带有索引的格式
        for index, answer in enumerate(answers):
            q += str(index + 1) +  ': ' + str(answer['text']) + '\n'
        q += "请根据这些背景信息而不是你已有的先验知识回答下面的问题：\n"
        q += question

        return [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': q},
        ]

    #问答
    def query(self, query_str):
        """
        执行逻辑：
        首先使用openai的Embedding API将输入的文本转换为向量
        然后使用Qdrant的search API进行搜索，搜索结果中包含了向量和payload
        payload中包含了title和text，title是疾病的标题，text是摘要
        最后使用openai的ChatCompletion API进行对话生成
        """
        qdclient = QdrantClient(self.QDRANT_IP, port=self.QDRANT_PORT)
        openai.api_key = os.getenv("OPENAI_API_KEY")
        openai_embeddings = openai.Embedding.create(model=self.OPENAI_EMBEDDING_MODEL,input=query_str)
        print('embedding(',query_str,')=',openai_embeddings["data"][0]["embedding"])
        """
        因为提示词的长度有限，所以我只取了搜索结果的前3个，如果想要更多的搜索结果，可以把limit设置为更大的值
        """
        search_result = qdclient.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=openai_embeddings["data"][0]["embedding"],
            limit=5,
            search_params={"exact": False, "hnsw_ef": 128}
        )
        answers = []

        """
        因为提示词的长度有限，每个匹配的相关摘要我在这里只取了前300个字符，如果想要更多的相关摘要，可以把这里的300改为更大的值
        """
        for result in search_result:
            if len(result.payload["text"]) > 1000:
                summary = result.payload["text"][:1000]
            else:
                summary = result.payload["text"]
            answers.append({"filename": result.payload["filename"], "text": summary})

        completion = openai.ChatCompletion.create(
            temperature=0.7,
            model="gpt-3.5-turbo",
            messages=self.__make_query_prompt(query_str, answers),
        )

        # return {
        #     "answer": completion.choices[0].message.content,
        # }
        return completion.choices[0].message.content

    def __make_summary_prompt(self, text):
        q = "请对以下内容写一段简短对摘要. \n" + text
        return [
            {'role': 'user', 'content': q},
        ]

    def summary(self, text):
        #completion接口输入不能超过4097个token
        if(len(text)>2000):
            text = text[:2000]
        completion = openai.ChatCompletion.create(
            temperature=0.7,
            model="gpt-3.5-turbo",
            messages=self.__make_summary_prompt(text),
        )
        return completion.choices[0].message.content

    #资源列表
    def point_list(self,next_page_offset, limit):
        qdclient = QdrantClient(self.QDRANT_IP, port=self.QDRANT_PORT)
        return qdclient.scroll(
            collection_name=self.COLLECTION_NAME,
            offset=next_page_offset,
            limit=limit,
            with_payload=True,
        )

    # 删除资源
    def del_point(self, id):
        qdclient = QdrantClient(self.QDRANT_IP, port=self.QDRANT_PORT)
        return qdclient.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=models.PointIdsList(
                points=[id],
            ),
        )