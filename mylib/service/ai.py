import os
from configparser import ConfigParser

import openai

from mylib.service.log import logger
from mylib.service.qdrant import QdrantService


class AIService:
    def __init__(self):
        self.config = ConfigParser()
        self.config.read('.env')
        self.QDRANT_IP = self.config.get('qdrant', 'ip')
        self.QDRANT_PORT = self.config.getint('qdrant', 'port')
        self.COLLECTION_NAME = self.config.get('qdrant', 'collection_name')
        self.OPENAI_EMBEDDING_MODEL = "text-embedding-ada-002"
        self.VECTOR_SIZE = 1536
        self.OPENAI_CHAT_COMPLETION_MODEL = "gpt-3.5-turbo"

    def __make_summary_prompt(self, text):
        q = "请对以下内容写一段简短对摘要. \n" + text
        return [
            {'role': 'user', 'content': q},
        ]

    def make_summary(self, text):
        """
        给text生成摘要
        :param text:
        :return: 摘要文字
        """

        # completion接口输入不能超过4097个token
        if len(text) > 2000:
            text = text[:2000]
        completion = openai.ChatCompletion.create(
            temperature=0.7,
            model=self.OPENAI_CHAT_COMPLETION_MODEL,
            messages=self.__make_summary_prompt(text),
        )
        return completion.choices[0].message.content

    def __make_completion_prompt(self, prompts, ref_pages):
        user_prompt1 = '我给你提供以下几份资料\n'
        user_prompt2 = ""
        # 带有索引的格式
        for index, ref_page in enumerate(ref_pages):
            user_prompt2 += '第' + str(index + 1) + '份资料\n' \
                            + '资料名称:《' + ref_page['resource_name'] + '》\n' \
                            + '所在页码:第' + str(ref_page['page_no'] + 1) + '页\n' \
                            + '资料内容:' + str(ref_page['text']) + '\n'
        user_prompt3 = "请根据上述资料，回答下面的问题,不超过300字，如果必要，请给出相关资料的名称、页码和章节信息。\n"
        post_prompts = [
            {'role': 'user', 'content': user_prompt1},
            {'role': 'user', 'content': user_prompt2},
            {'role': 'user', 'content': user_prompt3},
        ]
        post_prompts.extend(prompts)
        logger.debug("组装后的prompt:{0}".format(post_prompts))
        return post_prompts

    def make_completion(self, prompts: list):
        """
        执行逻辑：
        首先使用openai的Embedding API将输入的文本转换为向量
        然后使用Qdrant的search API进行搜索，搜索结果中包含了向量和payload
        payload中包含了resource_name、page_no和text，resource_name是文件名,page_no是页码,text是内容
        最后使用openai的ChatCompletion API进行对话生成

        返回值:
        {
            "message":"....",
            "refs":[
                {"resource_id":"","resource_name":""},
                {...}
            ]
        }
        """

        prompt4embedding = ''
        for prompt in prompts:
            if prompt["role"] == "user":
                prompt4embedding += prompt['content']

        openai.api_key = os.getenv("OPENAI_API_KEY")
        openai_embeddings = openai.Embedding.create(model=self.OPENAI_EMBEDDING_MODEL, input=prompt4embedding)
        logger.debug("embedding({0})=".format(openai_embeddings["data"][0]["embedding"]))

        search_result = QdrantService().search(query_vector=openai_embeddings["data"][0]["embedding"], limit=3)
        ref_pages = []
        ref_resources = []

        """
        因为提示词的长度有限，每个匹配的相关摘要我在这里只取了前500个字符
        """
        for result in search_result:
            if len(result.payload["text"]) > 500:
                summary = result.payload["text"][:500]
            else:
                summary = result.payload["text"]
            ref_pages.append({"resource_name": result.payload["resource_name"], "page_no": result.payload["page_no"],
                              "text": summary})
            # 去重(不包含资源，则加进去)
            if not any(item["resource_id"] == result.payload["resource_id"] for item in ref_resources):
                ref_resources.append(
                    {"resource_id": result.payload["resource_id"], "resource_name": result.payload["resource_name"]})

        completion = openai.ChatCompletion.create(
            temperature=0.7,
            model="gpt-3.5-turbo",
            messages=self.__make_completion_prompt(prompts, ref_pages),
        )
        message = completion.choices[0].message.content
        logger.debug("系统给的答案:{0}".format(message))
        result = {
            "message": message,
            "refs": ref_resources
        }
        return result
