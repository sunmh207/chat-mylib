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
        count = len(answers)
        # system = '你是一个问答机器人'
        user_prompt1='我给你提供以下{0}份资料\n'.format(count)

        user_prompt2 = ""
        # 带有索引的格式
        for index, answer in enumerate(answers):
            user_prompt2 += '第' + str(index+1) +'份资料\n'\
                + '资料名称:《'+ answer['resource_name'] +'》\n' \
                + '所在页码:第' + str(answer['page_no'] + 1)+'页\n' \
                + '资料内容:' + str(answer['text']) + '\n'
        user_prompt3 = "请根据刚才的资料，回答下面的问题,如果内容超过多，则不必完整回答，显示对应资料的名称、页码和章节信息。\n"

        prompt = [
            # {'role': 'system', 'content': system},
            {'role': 'user', 'content': user_prompt1},
            {'role': 'user', 'content': user_prompt2},
            {'role': 'user', 'content': user_prompt3},
            {'role': 'user', 'content': '问题:' + question},
        ]
        logger.debug("组装后的prompt:{0}".format(prompt))
        return prompt

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
            answers.append({"resource_name": result.payload["resource_name"], "page_no": result.payload["page_no"],"text": summary})

        completion = openai.ChatCompletion.create(
            temperature=0.7,
            model="gpt-3.5-turbo",
            messages=self.__make_completion_prompt(prompt, answers),
        )
        return completion.choices[0].message.content
