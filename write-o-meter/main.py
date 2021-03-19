from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
import spacy

nlp = spacy.load("el_core_news_sm")
class AnalysisRequestBody(BaseModel):
    text: str

app = FastAPI()

origins = [
    "https://sortingbubbles.github.io",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analyze-spacy")
async def analyze_text(request: AnalysisRequestBody):
    doc = nlp(request.text)
    print(doc)
    for token in doc:
        print(token.text, token.pos_, token.dep_)
    words = [token.text for token in doc if token.is_punct != True]
    texts = [token.text for token in doc]
    res = doc.to_json()
    res['words'] = words
    res['texts'] = texts
    return res

@app.post("/analyze-custom")
async def analyze_text_custom(request: AnalysisRequestBody):
    res = {
        'words': '-',
        'sents': '-',
        'paragraphs': '-'
    }
    xorismos_protaseon = ['...', ';', '!']
    text = request.text
    for simeio_stiksis in xorismos_protaseon:
        text = text.replace(simeio_stiksis, '.')
    res['words'] = text.split(' ')
    res['texts'] = text.split(' ')
    res['sents'] = text.split('. ')
    return res
