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

@app.post("/analyze")
async def analyze_text(request: AnalysisRequestBody):
    doc = nlp(request.text)
    print(doc, 'hello')
    print(doc.text)
    for token in doc:
        print(token.text, token.pos_, token.dep_)
    words = [token.text for token in doc if token.is_punct != True]
    res = doc.to_json()
    res['words'] = words
    return res
