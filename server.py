# -*- coding: utf-8 -*-
import uuid
from werkzeug.utils import secure_filename
import openai
from flask import Flask, render_template, request, jsonify
import os
import PyPDF2
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

app = Flask(__name__)

SUPPORT_DOC_MAX_LENGTH = 50000
SUPPORT_DOC_MAX_PAGE = 10
SUPPORT_EXTS = ['.pdf', '.txt', '.csv', '.doc','.docx']
UPLOAD_DIR = 'upload'

QDRANT_IP = '127.0.0.1'
QDRANT_PORT = 6333
COLLECTION_NAME = 'data_collection'



#生成报错信息格式
def error_response(msg):
    json_response = {
        'code':  0,
        'message': msg,
        'data': {}
    }
    return jsonify(json_response)
#生成成功信息格式
def success_response(msg, data):
    json_response = {
        'code': 1,
        'message': msg,
        'data': data
    }
    return jsonify(json_response)

"""
对文件内容做embedding
input:
    items[0]:文件名
    items[1]:文件内容
output:
    [文件名, 文件内容, embedding]
"""
def openai_embeddings(items):
    sentence_embeddings = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=items[1]
    )
    return [items[0], items[1], sentence_embeddings["data"][0]["embedding"]]

@app.route("/")
def root():
    return render_template('index.html')

@app.route("/upload", methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            # 生成唯一文件名
            extension = os.path.splitext(file.filename)[1].lower()
            if extension not in SUPPORT_EXTS:
                return "目前支持格式:" + ",".join(ext for ext in SUPPORT_EXTS)
            #TODO 需要避免同名文件覆盖
            uuid_filename = '{}{}'.format(uuid.uuid4().hex, os.path.splitext(secure_filename(file.filename))[-1])
            # 保存文件到指定目录
            filepath = os.path.join(os.getcwd(), UPLOAD_DIR, uuid_filename)
            file.save(filepath)
            print('收到上传文件:origon name=', file.filename, ', 保存后名称=', uuid_filename)

            #文件转化为文本内容
            text = ''
            #生成摘要信息
            summary = ''

            # 判断PDF文件页数
            if extension == '.pdf':
                pdf = PyPDF2.PdfReader(filepath)
                num_pages = len(pdf.pages)
                if num_pages > SUPPORT_DOC_MAX_PAGE:
                    return error_response("PDF文件不能超过{}页".format(SUPPORT_DOC_MAX_PAGE))
                for i in range(num_pages):
                    page = pdf.pages[i]
                    text += page.extract_text()
                    print(text)

            qdclient = QdrantClient(QDRANT_IP, port=QDRANT_PORT)
            collection_name = COLLECTION_NAME
            openai.api_key = os.getenv("OPENAI_API_KEY")

            # 创建collection
            qdclient.recreate_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

            #调用openai 做embedding
            item = openai_embeddings([file.filename,text])


            qdclient.upsert(
                collection_name=collection_name,
                wait=True,
                points=[
                    PointStruct(id=uuid_filename, vector=item[2], payload={"title": item[0], "text": item[1]}),
                ],
            )
            return success_response('上传成功',)

        else:
            error_response('未收到上传文件')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)