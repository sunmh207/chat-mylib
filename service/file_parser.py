import os
import PyPDF2
import docx
from service.exception import BaseException,ExceededMaxPagesError,ExceededMaxWordsError,UnsupportError
import openpyxl


class FileParser(object):
    SUPPORT_DOC_MAX_WORDS = 20000
    SUPPORT_DOC_MAX_PAGES = 10
    SUPPORT_EXTS = ['.txt', '.csv','md','.pdf', '.doc', '.docx','.xlsx','xls']

    def __get_parser_by_ext(self, ext):
        if ext.lower() in ['.txt','.md','.csv']:
            return TXTParser();
        elif ext.lower() in ['.pdf']:
            return PDFParser();
        elif ext.lower() in ['.doc','.docx']:
            return WordParser();
        elif ext.lower() in ['.xls','.xlsx']:
            return ExcelParser();

    #将文件内容解析为文本
    def parse(self, file_path):
        #根据扩展名生成策略类
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.SUPPORT_EXTS:
            raise UnsupportError('不支持的文件格式！ 目前支持的文件格式有:' + ','.join(self.SUPPORT_EXTS))

        paraser = self.__get_parser_by_ext(ext);
        return paraser.parse(file_path)

class TXTParser(FileParser):
    def parse(self, file_pat):
        with open(file_pat, 'r') as file:
            file_content = file.read()
            if(len(file_content) > self.SUPPORT_DOC_MAX_WORDS):
                #抛出异常
                raise ExceededMaxWordsError('超出最大字数:'+str(self.SUPPORT_DOC_MAX_WORDS))
            return file_content

class PDFParser(FileParser):
    def parse(self,file_path):
        # 打开PDF文件
        with open(file_path, 'rb') as file:
            # 创建PdfFileReader对象
            pdf = PyPDF2.PdfReader(file_path)
            # 获取PDF文件的页面数量
            num_pages = len(pdf.pages)
            if num_pages > self.SUPPORT_DOC_MAX_PAGES:
                raise ExceededMaxPagesError('超出最大页数:' + str(self.SUPPORT_DOC_MAX_PAGES))

            text = ''
            # 读取每一页的内容
            for page in range(num_pages):
                page_text = pdf.pages[page].extract_text()
                text += page_text

            if (len(text) > self.SUPPORT_DOC_MAX_WORDS):
                raise ExceededMaxPagesError('超出最大字数:' + str(self.SUPPORT_DOC_MAX_WORDS))
            # 返回解析后的文本内容
            return text

class WordParser(FileParser):
    def parse(self, file_path):
        # 打开Word文件
        doc = docx.Document(file_path)
        # 读取每一段的内容
        text = ''
        for para in doc.paragraphs:
            text += para.text
        if (len(text) > self.SUPPORT_DOC_MAX_WORDS):
            raise ExceededMaxWordsError('超出最大字数:' + str(self.SUPPORT_DOC_MAX_WORDS))
        # 返回解析后的文本内容
        return text

class ExcelParser(FileParser):
    def parse(self, file_path):
        # 打开Excel文件
        wb = openpyxl.load_workbook(file_path)
        # 选择第一个工作表
        sheet = wb.active
        # 读取每一个单元格的内容
        text = ''
        for row in sheet.rows:
            row_str = '|'
            for cell in row:
                row_str += str(cell.value) + '|'
            text += row_str + '\n'
        # 返回解析后的文本内容
        return text