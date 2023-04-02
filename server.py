# -*- coding: utf-8 -*-
import hashlib
from openai import OpenAIError
from flask import Flask, render_template, request, jsonify,redirect, url_for,send_from_directory
from mylib.service.exception import BaseException
from mylib.service.ai_service import AIService
from mylib.service.resource_service import ResourceService

import os
from configparser import ConfigParser

def splitext(value):
    return os.path.splitext(value)[1]

app = Flask(__name__)
app.add_template_filter(splitext)
app.debug = True  # 开启debug模式

config = ConfigParser()
config.read('.env')

UPLOAD_DIR = config.get('storage', 'upload_dir')
FLASK_HOST = config.get('flask', 'host')
FLASK_PORT = config.getint('flask', 'port')


#生成报错信息格式
def upload_error_response(msg):
    json_response = {"status": "error", "data": {"message": msg,"summary":""}}
    return jsonify(json_response)
#生成成功信息格式
def upload_success_response(msg, summary):
    json_response = {"status": "success", "data": {"message": msg,"summary":summary}}
    return jsonify(json_response)


@app.route("/")
def homepage():
    return render_template('index.html')

@app.route("/mobile")
def mobile():
    return render_template('mobile.html')

@app.route("/upload", methods=['GET','POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            content = file.read()
            id = hashlib.md5(content).hexdigest()
            basename, ext = os.path.splitext(file.filename)
            uuid_filename = id + ext
            # 保存文件到指定目录
            file_path = os.path.join(os.getcwd(), UPLOAD_DIR, uuid_filename)
            file.seek(0)
            file.save(file_path)
            print('收到上传文件:origon name=', file.filename, ', 保存后名称=', uuid_filename)

            try:
                resource = ResourceService().upsert(file_path=file_path, resource_id=id,resource_name = file.filename)
            except BaseException as e:
                return upload_error_response(msg = e.message)
            except OpenAIError as openaie:
                return upload_error_response(msg=openaie.user_message)

            return upload_success_response(msg = '上传成功', summary = resource.summary)
        else:
            upload_error_response(msg = '未收到上传文件')

@app.route('/completions', methods=['POST'])
def completions():
    prompts = request.get_json()
    result = AIService().make_completion(prompts)
    return {"status":"success","data":{"message":"返回成功","result":result}}

@app.route("/admin")
def admin():
    # 获取当前页数，默认为第一页
    page = int(request.args.get('page', 1))
    page_size = 30
    # 计算起始索引和结束索引
    start = (page - 1) * page_size
    #总记录数
    total = ResourceService().count()
    #总页数
    total_pages = (total + page_size -1) // page_size

    resources = ResourceService().list(start, page_size)
    return render_template('admin/index.html',resources=resources,page=page, total_pages=total_pages)

@app.route("/delfile", methods=['GET','POST'])
def delfiel():
    id = request.args.get('id')
    ResourceService().delete(id)
    return redirect(url_for('admin'))

#预览
@app.route('/preview/<string:resource_id>')
def show(resource_id):
    resource = ResourceService().get(resource_id)
    basename, ext = os.path.splitext(resource.name)
    filename = resource.id + ext
    return send_from_directory(os.path.join(app.root_path, 'upload'), filename)


#completions对外接口,与completions相同,仅路由不同
@app.route("/api/completions", methods=['POST'])
def api_completions():
    return completions()

#upload对外接口,与upload相同,仅路由不同
@app.route("/api/upload", methods=['POST'])
def api_upload():
    return upload()

#设置icon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), './imgs/favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)