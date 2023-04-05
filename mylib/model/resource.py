
"""
一个资源是一份独立的完整的内容，如一个pdf文件等。
"""
class Resource:
    def __init__(self, id: str, name: str, summary: str, type: str, created_time: int, updated_time: int):
        self.id = id    # uuid
        self.name = name    # 文件名或标题
        self.summary = summary  # 摘要
        self.type = type    # 类型，如pdf、excel、txt等
        self.created_time = created_time # 创建时间,时间戳
        self.updated_time = updated_time # 更新时间,时间戳