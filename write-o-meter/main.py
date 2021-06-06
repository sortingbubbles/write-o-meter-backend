from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import spacy
import re

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
    res['words'] = len(words)
    res['texts'] = texts
    return res

@app.post("/analyze-custom")
async def analyze_text_custom(request: AnalysisRequestBody):
    res = {
        'words': '-',
        'sents': '-',
        'paragraphs': '-'
    }
    text = re.sub(' +', ' ', request.text)
    res['sents'] = re.split('\\. |\\.\\.\\. |; | ! ', text)
    res['tokens'] = tokenize_sentences(text.strip().split(' '))
    res['texts'] = split_texts(res['tokens'])
    res['words'] = find_num_of_words(res['tokens'])
    return res

def split_texts(tokens):
    texts = []
    for token in tokens:
        texts.append(token['lemma'])
    return texts

def find_num_of_words(tokens):
    counter = 0
    for token in tokens:
        if token['pos'] == 'ABBR':
            counter = counter + token['numOfWords']
        if token['pos'] != 'PUNCT' and token['pos'] != 'ABBR':
            counter = counter + 1
    return counter


def tokenize_sentences(words):
    simeia_stiksis_telika_mona = [';', '!', ',', '-', ':', ')', '»', '·', '.']
    simeia_stiksis_arxi_leksis = ['(', '«']
    tokens = []
    for word in words:
        tok = False
        symbol = False
        if word.endswith(('...')):
            symbol = punct(word[-3:], True)
            tok = preliminary_check(word[0:-3])
        elif word.endswith(('..')):
            symbol = punct(word[-1], True)
            tok = abbreviation(word[:-1], findOccurrences(word[:-1], '.'))
        elif findOccurrences(word, '.') > 1:
            tok = abbreviation(word, findOccurrences(word, '.'))
        elif word.endswith(tuple(simeia_stiksis_telika_mona)):
            tok = preliminary_check(word[0:-1])
            symbol = punct(word[-1], True)
        if word.startswith(('--')):
            symbol = punct(word[0:2], False)
            tok = preliminary_check(word[2:])
        elif word.startswith(tuple(simeia_stiksis_arxi_leksis)):
            symbol = punct(word[0], False)
            tok = preliminary_check(word[1:])

        if symbol and symbol['isAtEnd'] == False:
            tokens.append(symbol)
        
        if tok == False:
            tokens.append(preliminary_check(word))
        else:
            tokens.append(tok)
            
        if symbol and symbol['isAtEnd'] == True:
            tokens.append(symbol)
    for (index, token) in enumerate(tokens):
        if token['pos'] == False:
            previousToken = False
            nextToken = False
            if (index > 0):
                previousToken = tokens[index-1]
            if (index < len(tokens) - 1):
                nextToken = tokens[index + 1]
            tokens[index] = secondary_check(token['word'], previousToken, nextToken)
    for (index, token) in enumerate(tokens):
        if token['pos'] == False:
            previousToken = False
            nextToken = False
            if (index > 0):
                previousToken = tokens[index-1]
            if (index < len(tokens) - 1):
                nextToken = tokens[index + 1]
            tokens[index] = last_check(token['word'], previousToken, nextToken)
    return tokens


def punct(symbol, einai_teliko):
    punct = {
        'tag': 'PUNCT',
        'pos': 'PUNCT',
        'lemma': symbol,
        'dep': 'punct',
        'isAtEnd': einai_teliko
    }
    return punct

def last_check(word, previousToken, nextToken):
    print('ast', word)
    res = secondary_check(word, previousToken, nextToken)
    if res['pos'] == False:
        return {
            'tag': 'OTHER',
            'pos': 'OTHER',
            'lemma': word,
            'dep': 'other'
        }
    else:
        return res
        

def secondary_check(word, previousToken, nextToken):
    if previousToken and previousToken['pos'] == 'ADV':
        return {
            'tag': 'ADJ',
            'pos': 'ADJ',
            'lemma': word,
            'dep': 'adj'
        }
    if word[0].isupper():
        if previousToken and (previousToken['pos'] != 'PUNCT' or previousToken['pos'] == 'DET'):
            return {
                'tag': 'PROPN',
                'pos': 'PROPN',
                'lemma': word,
                'dep': 'propn'
            }
    if previousToken and previousToken['pos'] == 'DET':
        if nextToken and (nextToken['pos'] == False or nextToken['pos'] == 'NOUN'):
            return {
                'tag': 'ADJ',
                'pos': 'ADJ',
                'lemma': word,
                'dep': 'adj'
            }
        if nextToken and (nextToken['pos'] != False or nextToken['pos'] != 'ADJ'):
            return {
                'tag': 'NOUN',
                'pos': 'NOUN',
                'lemma': word,
                'dep': 'noun'
            }
    if previousToken and previousToken['pos'] == 'ADP':
        if nextToken and (nextToken['pos'] == False):
            return {
                'tag': 'ADJ',
                'pos': 'ADJ',
                'lemma': word,
                'dep': 'adj'
            }
        return {
            'tag': 'NOUN',
            'pos': 'NOUN',
            'lemma': word,
            'dep': 'noun'
        }
    if previousToken and previousToken['pos'] == 'VERB':
        if nextToken and (nextToken['pos'] == False):
            return {
                'tag': 'ADJ',
                'pos': 'ADJ',
                'lemma': word,
                'dep': 'adj'
            }
        return {
            'tag': 'NOUN',
            'pos': 'NOUN',
            'lemma': word,
            'dep': 'noun'
        }
    if previousToken and previousToken['pos'] == 'NUM':
        return {
            'tag': 'NOUN',
            'pos': 'NOUN',
            'lemma': word,
            'dep': 'noun'
        }
    if previousToken and previousToken['pos'] == 'ADJ':
        return {
            'tag': 'NOUN',
            'pos': 'NOUN',
            'lemma': word,
            'dep': 'noun'
        }
    return {
        'tag': 'OTHER',
        'pos': 'OTHER',
        'lemma': word,
        'dep': 'other'
    }

def preliminary_check(word):
    arthra = ['ο', 'η', 'το', 'του', 'της', 'του', 'το', 'τον', 'τη', 'την', 'το', 'οι', 'τα', 'των', 'τους', 'τις', 'ένας', 'μια', 'ένα', 'ενός', 'μιας', 'έναν']
    antonimies = ['εγώ', 'εσύ', 'εμένα', 'μου', 'εσένα', 'σ21ου', 'εσύ', 'εμείς', 'εσείς', 'εμάς', 'μας', 'εσάς', 'σας', 'αυτός', 'αυτή', 'αυτό', 'αυτού', 'αυτής', 'αυτόν', 'αυτήν', 'αυτών', 'αυτούς', 'αυτές', 'αυτά', 'τούτος', 'τούτη', 'τούτο', 'ίδιος', 'ίδια', 'ίδιο', 'εκείνος', 'εκείνη', 'εκείνο', 'εκείνα', 'εκείνων', 'τέτοιος', 'τέτοια', 'τέτοιο']
    epirimata = ['πού', 'γύρω', 'πιο', 'πότε', 'ήδη', 'κάπου', 'σήμερα', 'αύριο', 'χθες', 'πουθενά', 'κάποτε', 'πόσο', 'άλλοτε', 'τότε', 'παντού', 'εδώ', 'εκεί', 'οπουδήποτε', 'όπου', 'πώς', 'πόσο', 'ναι', 'μάλιστα', 'βέβαια', 'βεβαιότατα', 'όσο', 'πάνω', 'κάτω', 'δεξιά', 'αριστερά', 'μέσα', 'έξω', 'εμπρός', 'μπρος', 'πίσω', 'δίπλα', 'πλάι', 'απέναντι', 'κοντά', 'μακρυά', 'χαμηλά', 'ψηλά', 'συχνά', 'καλά', 'κακά', 'μόνο', 'πολύ', 'καθόλου', 'διόλου', 'εξίσου', 'μόλις', 'όχι', 'δεν', 'δε', 'μη', 'μην', 'ίσως', 'τάχα', 'δήθεν', 'πιθανόν', 'τελείως', 'διαρκώς', 'επίσης', 'κυρίως']
    protheseis = ['από', 'εξαιτίας', 'προς', 'ως', 'για', 'με', 'σε', 'κατά', 'μετά', 'από', 'αντί', 'δίχως', 'χωρίς', 'παρά', 'ίσαμε', 'επί', 'δια', 'πλην', 'μείον', 'συν', 'στο', 'στα', 'στον', 'στη', 'στην']
    syndesmoi = ['και', 'ή', 'μα', 'ώστε', 'δηλαδή', 'ότι', 'όταν', 'αν', 'γιατί', 'παρά', 'είτε', 'ούτε', 'μήτε', 'ουδέ', 'άμα', 'ενώ', 'καθώς', 'αφού', 'αφότου', 'ωσότου', 'επειδή', 'μήπως', 'σαν', 'μόλις', 'αλλά', 'μολονότι', 'λοιπόν']
    if word.lower() in arthra:
        return {
            'tag': 'DET',
            'pos': 'DET',
            'lemma': word,
            'dep': 'det'
        }
    if word.lower() in syndesmoi:
        return {
        'tag': 'CONJ',
        'pos': 'CONJ',
        'lemma': word,
        'dep': 'conj'
    }
    if word.lower() in protheseis:
        return {
            'tag': 'ADP',
            'pos': 'ADP',
            'lemma': word,
            'dep': 'adp'
    }
    if word.lower() in antonimies:
        return {
            'tag': 'PRON',
            'pos': 'PRON',
            'lemma': word,
            'dep': 'pron'
        }
    if word.endswith(('ίως', 'ώς', 'όν', 'ως', 'όλου')) or word in epirimata:
        return {
            'tag': 'ADV',
            'pos': 'ADV',
            'lemma': word,
            'dep': 'adv'
        }
    if word.endswith(('ικός', 'ικό', 'ική')):
        return {
            'tag': 'ADJ',
            'pos': 'ADJ',
            'lemma': word,
            'dep': 'adj'
        }
    if word.startswith(('0', '1', '2', '3', '4', '5', '6','7','8', '9')):
        return {
            'tag': 'NUM',
            'pos': 'NUM',
            'lemma': word,
            'dep': 'num'
        }
    if word.endswith(('ώνω', 'εί', 'ξε', 'ουμε', 'ήκει', 'είτε', 'ώνει', 'αίνει', 'αι', 'ηκε', 'άνει', 'ίζει', 'ίζω', 'άζει', 'ούν', 'ουν', 'άζω', 'ψτε', 'φτε', 'έχει', 'έχεις', 'έχω', 'έχουμε', 'έχετε', 'έχουν')):
        return {
            'tag': 'VERB',
            'pos': 'VERB',
            'lemma': word,
            'dep': 'verb'
        }
    if word.endswith(('ένος', 'ένη', 'ένο', 'ώντας', 'όντας')):
        return {
            'tag': 'PARTCP',
            'pos': 'PARTCP',
            'lemma': word,
            'dep': 'prtcp'
        }
    return {
        'pos': False,
        'word': word
    }


def findOccurrences(s, ch):
    return len([i for i, letter in enumerate(s) if letter == ch])


def abbreviation(word, numOfAbbreviatedWords):
    return {
        'tag': 'ABBR',
        'numOfWords': numOfAbbreviatedWords,
        'pos': 'ABBR',
        'lemma': word,
        'dep': 'abbr'
    }
