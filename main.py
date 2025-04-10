import re
from collections import Counter
from math import log10
from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


app = FastAPI()
templates = Jinja2Templates(directory="templates")


def calculate_tf(list_words: list[str]) -> dict[str, float]:
    """Принимает список слов. Возвращает словарь, где ключ - это слово, а значение - его tf"""
    count_words = len(list_words)  # кол-во слов
    dict_words = Counter(list_words)

    res = {}
    for word in dict_words.keys():
        res[word] = dict_words[word] / count_words
    return res


def calculate_idf(word: str, docs_texts: list[list[str]]) -> float:
    """Принимает слово, для которого вычисляется idf, и список списков слов, где list[i] - список слов i-ого документа.
    Возвращает idf для переданного слова."""
    count_docs = len(docs_texts)  # кол-во документов
    return log10(count_docs / sum([1 for doc_text in docs_texts if word in doc_text]))


@app.post("/")
async def create_docs(docs: list[UploadFile], request: Request):
    docs_texts = []
    for doc in docs:  # получение списка списков слов из документов
        text = (await doc.read()).decode('utf-8')
        clear_split_text = re.sub(r'[^\w\s]', '', text.lower()).split()
        docs_texts.append(clear_split_text)

    data = []
    # получение списка словарей формата
    # {
    #   "doc_name": <название документа>,
    #   "doc_data": <список словарей формата {'name': <слово>, 'tf': <tf>, 'idf': <idf>}
    # }
    for doc_num, doc in enumerate(docs):
        tf = calculate_tf(docs_texts[doc_num])
        doc_data = []
        for word in tf.keys():
            doc_data.append({'name': word, 'tf': tf[word], 'idf': calculate_idf(word, docs_texts)})
        doc_data = sorted(doc_data, key=lambda x: (x['idf'], x['tf'], x['name']), reverse=True)[:50]
        data.append({"doc_name": doc.filename, "doc_data": doc_data})

    return templates.TemplateResponse("table.html", {
        "request": request,
        "data": data,
        "docs_length": len(docs),
    })


@app.get("/", response_class=HTMLResponse)
def main(request: Request):
    return templates.TemplateResponse("upload_form.html", {"request": request})
