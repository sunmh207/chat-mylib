# 基础镜像
FROM python:3.10

# 将文件拷贝到容器中
WORKDIR /app
COPY . /app
COPY ./.env.dist /app/.env

# 安装依赖
RUN pip install -r /app/requirements.txt

EXPOSE 3000

# 运行服务
CMD ["python", "server.py"]