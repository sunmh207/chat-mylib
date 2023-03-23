import docx

def parse(file_path):
    # 打开Word文件
    doc = docx.Document(file_path)
    # 读取每一段的内容
    text = ''
    for para in doc.paragraphs:
        print(para.text)
        print('=========')
        text += para.text

    # 返回解析后的文本内容
    return text

if __name__ == '__main__':
    import sys
    file_path = sys.argv[1]
    print(file_path)
    parse(file_path)