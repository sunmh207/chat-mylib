# -*- coding: utf-8 -*-
import hashlib
import os
import json
from configparser import ConfigParser

from flask import (Flask, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)
from openai import OpenAIError
import openai

from mylib.service.log import logger
from mylib.service.qdrant import QdrantService
from mylib.service.ai import AIService
from mylib.service.exception import BaseException
from mylib.service.resource import ResourceService
from mylib.service.dingtalk import DingtalkService
from mylib.service.log import logger


def splitext(value):
    return os.path.splitext(value)[1]


app = Flask(__name__)
app.add_template_filter(splitext)
app.debug = True  # 开启debug模式

config = ConfigParser()
config.read('.env')

UPLOAD_DIR = config.get('storage', 'upload_dir', fallback='upload')
FLASK_HOST = config.get('flask', 'host', fallback='127.0.0.1')
FLASK_PORT = config.getint('flask', 'port', fallback=3000)

#支持设置openai代理
os.environ["OPENAI_API_BASE"] = config.get('openai', 'openai_api_base', fallback='https://api.openai.com/v1')

DINGTALK_WEBHOOK_URL = config.get('dingtalk', 'webhook_url')
DINGTALK_SECRET = config.get('dingtalk', 'secret')



# 生成报错信息格式
def upload_error_response(msg):
    json_response = {"status": "error", "data": {"message": msg, "summary": ""}}
    return jsonify(json_response)


# 生成成功信息格式
def upload_success_response(msg, summary):
    json_response = {"status": "success", "data": {"message": msg, "summary": summary}}
    return jsonify(json_response)


@app.route("/")
def homepage():
    return render_template('index.html')

@app.route('/setkey', methods=['POST'])
def receive_key():
    os.environ["OPENAI_API_KEY"] = request.form['key']
    print('OPENAI_API_KEY 被设置为：',os.getenv("OPENAI_API_KEY"))
    return "OpenAI API Key设置成功！"

@app.route("/mobile")
def mobile():
    return render_template('mobile.html')


@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            content = file.read()
            resource_id = hashlib.md5(content).hexdigest()
            basename, ext = os.path.splitext(file.filename)
            uuid_filename = resource_id + ext
            # 保存文件到指定目录
            file_path = os.path.join(os.getcwd(), UPLOAD_DIR, uuid_filename)
            file.seek(0)
            file.save(file_path)
            print('收到上传文件:origin name=', file.filename, ', 保存后名称=', uuid_filename)

            try:
                resource = ResourceService().upsert(file_path=file_path, resource_id=resource_id, resource_name=file.filename)
            except BaseException as e:
                return upload_error_response(msg=e.message)
            except OpenAIError as openai_e:
                return upload_error_response(msg=openai_e.user_message)

            return upload_success_response(msg='上传成功', summary=resource.summary)
        else:
            upload_error_response(msg='未收到上传文件')


@app.route('/completions', methods=['POST'])
def completions():
    if not os.getenv("OPENAI_API_KEY"):
        return {"status": "error", "data": {"message": "没有OpenAI API Key，请点击右上角[key]按钮填写。"}}
    prompts = request.get_json()
    result = AIService().make_completion(prompts)
    return {"status": "success", "data": {"message": "返回成功", "result": result}}


@app.route("/admin")
def admin():
    # 获取当前页数，默认为第一页
    page = int(request.args.get('page', 1))
    page_size = 30
    # 计算起始索引和结束索引
    start = (page - 1) * page_size
    # 总记录数
    total = ResourceService().count()
    # 总页数
    total_pages = (total + page_size - 1) // page_size

    resources = ResourceService().list(start, page_size)
    return render_template('admin/index.html', resources=resources, page=page, total_pages=total_pages)


@app.route("/del_file", methods=['GET', 'POST'])
def del_file():
    res_id = request.args.get('id')
    ResourceService().delete(res_id)
    return redirect(url_for('admin'))


# 预览
@app.route('/preview/<string:resource_id>')
def show(resource_id):
    resource = ResourceService().get(resource_id)
    basename, ext = os.path.splitext(resource.name)
    filename = resource.id + ext
    return send_from_directory(os.path.join(app.root_path, 'upload'), filename)


# completions对外接口,与completions相同,仅路由不同
@app.route("/api/completions", methods=['POST'])
def api_completions():
    return completions()


# upload对外接口,与upload相同,仅路由不同
@app.route("/api/upload", methods=['POST'])
def api_upload():
    return upload()


# 设置icon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), './imgs/favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route("/dingtalkbot", methods=["POST"])
def dingtalkbot():
    message = json.loads(request.get_data())
    timestamp = request.headers.get('timestamp')
    sign = request.headers.get('sign')
    logger.debug(message)
    dingtalk_service = DingtalkService(DINGTALK_WEBHOOK_URL,DINGTALK_SECRET)
    if dingtalk_service.verify(sign, timestamp):
        # 签名验证通过，处理消息
        sender_nick = message['senderNick']
        msg_type = message['msgtype']
        if msg_type == 'text':
            msg_content = message['text']['content']
        elif msg_type == 'markdown':
            msg_content = message['markdown']['title'] + '\n' + message['markdown']['text']
        else:
            msg_content = 'unknown message type'

        #回答问题
        prompts=[{"role":"user","content":msg_content}]
        answer = AIService().make_completion(prompts)
        dingtalk_service.send(answer['message'])
        return jsonify({'msg': 'success'})
    else:
        # 签名验证失败，不处理消息
        return jsonify({'msg': 'signature error'}, status=401)

#测试qdrant
@app.route("/test/qdrant/search", methods=['POST'])
def test_qdrant_search():
    data = json.loads(request.get_data())
    message = data['message']
    openai.api_key = os.getenv("OPENAI_API_KEY")
    openai_embeddings = openai.Embedding.create(model="text-embedding-ada-002", input=message)
    logger.debug("embedding({0})=".format(openai_embeddings["data"][0]["embedding"]))

    search_result = QdrantService().search(query_vector=openai_embeddings["data"][0]["embedding"], limit=3)

    res_arr = []
    for result in search_result:
        res = {}
        res['score'] = result.score
        res['resource_name'] =  result.payload['resource_name']
        res['text'] =  result.payload['text']
        res_arr.append(res)
    return res_arr

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)

