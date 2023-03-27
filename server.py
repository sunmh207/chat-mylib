# -*- coding: utf-8 -*-
import hashlib
from openai import OpenAIError
from flask import Flask, render_template, request, jsonify,redirect, url_for
from mylib.service.file_parser import FileParser
from mylib.service.exception import BaseException
from mylib.service.ai_service import AIService
from mylib.service.resource_service import ResourceService
# from service.utils import LibTookit
# from service.file import FileStruct
import os
from configparser import ConfigParser

app = Flask(__name__)
app.debug = True  # 开启debug模式

config = ConfigParser()
config.read('.env')

UPLOAD_DIR = config.get('storage', 'upload_dir')
FLASK_HOST = config.get('flask', 'host')
FLASK_PORT = config.getint('flask', 'port')


#生成报错信息格式
def upload_error_response(msg):
    json_response = {
        'success':  0,
        'message': msg,
        'summary': ''
    }
    return jsonify(json_response)
#生成成功信息格式
def upload_success_response(msg, summary):
    json_response = {
        'success': 1,
        'message': msg,
        'summary': summary
    }
    return jsonify(json_response)


@app.route("/")
def homepage():
    return render_template('index.html')

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
                resource = ResourceService().upsert(file_path,file.filename)
            except BaseException as e:
                return upload_error_response(msg = e.message)
            except OpenAIError as openaie:
                return upload_error_response(msg=openaie.user_message)

            return upload_success_response(msg = '上传成功', summary = resource.summary)
        else:
            upload_error_response(msg = '未收到上传文件')

@app.route('/completions', methods=['POST'])
def search():
    # question = request.form['question']
    #获取json格式的数据
    prompts = request.get_json()
    print(type(prompts))
    answer = AIService().make_completion(prompts)
    return answer

@app.route("/admin")
def admin():
    return render_template('admin/index.html')

@app.route("/files")
def files():
    offset = 0
    limit =300
    resources =  ResourceService().list(offset,limit)
    return {
        "items":resources,
    }

@app.route("/delfile", methods=['GET','POST'])
def delfiel():
    id = request.args.get('id')
    ResourceService().delete(id)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT)