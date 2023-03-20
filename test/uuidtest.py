# import uuid
# print(uuid.uuid4())


import os
filename = '中文 文件名.txt'
basename, ext = os.path.splitext(filename)
print(basename)
print(ext)