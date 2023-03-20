# -*- coding: utf-8 -*-
import hashlib
from openai import OpenAIError
from flask import Flask, render_template, request, jsonify
from service.file_parser import FileParser
from service.exception import BaseException
from service.utils import LibTookit
from service.file import FileStruct
import os

app = Flask(__name__)
app.debug = True  # 开启debug模式

UPLOAD_DIR = 'upload'

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
def root():
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

            #文件转化为文本内容
            parser = FileParser()
            try:
                text = parser.parse(file_path)
            except BaseException as e:
                return upload_error_response(msg = e.message)
            except OpenAIError as openaie:
                return upload_error_response(msg=openaie.message)

            summary = LibTookit().summary(text)

            file_struct = FileStruct(id=id, filename=file.filename, text=text)
            #保存到qdrant库
            tookit = LibTookit()
            tookit.save_to_qdrant(file_struct)

            return upload_success_response(msg = '上传成功', summary = summary)
        else:
            upload_error_response(msg = '未收到上传文件')

@app.route('/completions', methods=['POST'])
def search():
    question = request.form['question']
    answer = LibTookit().query(question)
    return answer

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3001)