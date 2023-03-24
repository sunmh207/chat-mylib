from configparser import ConfigParser
import openai
from mylib.service.qdrant_service import QdrantService
import os
from mylib.service.log import logger

class AIService:
    config = ConfigParser()
    config.read('.env')

    QDRANT_IP = config.get('qdrant', 'ip')
    QDRANT_PORT = config.getint('qdrant', 'port')
    COLLECTION_NAME = config.get('qdrant', 'collection_name')

    OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
    VECTOR_SIZE = 1536

    OPENAI_CHAT_COMPLETION_MODEL = "gpt-3.5-turbo"
    def __make_summary_prompt(self, text):
        q = "请对以下内容写一段简短对摘要. \n" + text
        return [
            {'role': 'user', 'content': q},
        ]

    def make_summary(self, text):
        """
        给text生成摘要
        :param text:
        :return:
        """

        #completion接口输入不能超过4097个token
        if (len(text) > 2000):
            text = text[:2000]
        completion = openai.ChatCompletion.create(
            temperature=0.7,
            model=self.OPENAI_CHAT_COMPLETION_MODEL,
            messages=self.__make_summary_prompt(text),
        )
        return completion.choices[0].message.content


    def __make_completion_prompt(self, question, answers):
        system = '你是一个问答机器人'
        q = "我们提供了以下背景信息. \n"
        # 带有索引的格式
        for index, answer in enumerate(answers):
            q += str(index + 1) +  '. '+ answer['resource_name'] +':' + str(answer['text']) + '\n'
        q += "请根据这些背景信息而不是你已有的先验知识回答下面的问题：\n"
        q += question

        return [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': q},
        ]

    def make_completion(self, prompt):
        """
        执行逻辑：
        首先使用openai的Embedding API将输入的文本转换为向量
        然后使用Qdrant的search API进行搜索，搜索结果中包含了向量和payload
        payload中包含了title和text，title是疾病的标题，text是摘要
        最后使用openai的ChatCompletion API进行对话生成
        """

        openai.api_key = os.getenv("OPENAI_API_KEY")
        openai_embeddings = openai.Embedding.create(model=self.OPENAI_EMBEDDING_MODEL, input=prompt)
        logger.debug("embedding({0})=".format(openai_embeddings["data"][0]["embedding"]))

        search_result = QdrantService().search(query_vector=openai_embeddings["data"][0]["embedding"],limit=3 )
        answers = []

        """
        因为提示词的长度有限，每个匹配的相关摘要我在这里只取了前1000个字符
        """
        for result in search_result:
            if len(result.payload["text"]) > 1000:
                summary = result.payload["text"][:1000]
            else:
                summary = result.payload["text"]
            answers.append({"resource_name": result.payload["resource_name"], "text": summary})

        completion = openai.ChatCompletion.create(
            temperature=0.7,
            model="gpt-3.5-turbo",
            messages=self.__make_completion_prompt(prompt, answers),
        )
        return completion.choices[0].message.content
