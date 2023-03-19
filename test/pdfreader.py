from PyPDF2 import PdfReader

def printPdf(pdffile):
    reader = PdfReader(pdffile)
    number_of_pages = len(reader.pages)
    print('page #:', number_of_pages)

    for i in range(number_of_pages):
        page = reader.pages[i]
        text = page.extract_text()
        print(text)



if __name__ == '__main__':
    import sys
    pdffile = sys.argv[1]
    printPdf(pdffile)
