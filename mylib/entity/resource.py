
"""
一个资源是一份独立的完整的内容，如一个pdf文件等。
"""
class Resource:
    #uuid
    id = ''
    #通常是文件名或标题
    name = ''
    #摘要
    summary = ''
    #类型，如pdf、excel、txt等
    type = ''
    #创建时间，时间戳
    created_time = ''
    #更新时间，时间戳
    updated_time = ''

    def __init__(self,id,name,summary,type,created_time,updated_time):
        self.id = id
        self.name = name
        self.summary = summary
        self.type = type
        self.created_time = created_time
        self.updated_time = updated_time


