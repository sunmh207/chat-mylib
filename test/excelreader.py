import openpyxl

class ExcelParser:
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
            text += row_str +'\n'
        # 返回解析后的文本内容
        return text

if __name__ == '__main__':
    reader = ExcelParser()
    text = reader.parse('/Users/sunminghui/Downloads/特种作业项目组成员.xlsx')
    print(text)