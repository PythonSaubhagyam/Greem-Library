import pymupdf as fitz
import re

# print(fitz.__doc__)
doc = fitz.open("iesc106.pdf")
raw_text = ""
for page in doc:
    raw_text += page.get_text()
# print(raw_text[:500])
raw_text = raw_text  

clean_text = re.sub(r'\s+', ' ', raw_text).strip()


# print(clean_text[:1000])

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks

chunks = chunk_text(clean_text)


paper_config = {
    "total_marks": 40,
    "difficulty_distribution": {
        "easy": 30,
        "medium": 50,
        "hard": 20
    },
    "question_types": {
        "mcq": 10,
        "short": 10,
        "long": 20
    },
    "chapter_scope": "entire_pdf"
}

import streamlit as st
import subprocess

st.set_page_config(page_title="Question Paper Generator", layout="wide")

st.title("📄 Local AI Question Paper Generator")

prompt = st.text_area("Enter Instructions / Content", height=300)

if st.button("Generate  "):
    result = subprocess.run(
        ["ollama", "run", "phi"],
        input=prompt,
        text=True,
        capture_output=True
    )
    st.text_area("Generated Question Paper", result.stdout, height=400)

# import spacy
# nlp = spacy.load("en_core_web_sm")

# doc = nlp(clean_text)
# sentences = [sent.text for sent in doc.sents]

# print(sentences)

# IMPORTANT_PHRASES = [
#     "is the process",
#     "takes place",
#     "produces"
# ]

# def is_definition(sentence):
#     doc = nlp(sentence)
#     for token in doc:
#         if token.lemma_ == "be":
#             return True
#     return False

# def score_sentence(sentence):
#     score = 0
#     doc = nlp(sentence)

#     # Definition pattern
#     if is_definition(sentence):
#         score += 3

#     # Length matters (too short = bad)
#     score += min(len(sentence.split()), 30) * 0.1

#     # Nouns = concepts
#     noun_count = len([t for t in doc if t.pos_ == "NOUN"])
#     score += noun_count * 0.2

#     return score


# for sentence in sentences:
#     sentence_score = score_sentence(sentence)
#     if sentence_score >= 2.0:
#         print(f"Score: {sentence_score:.2f} | Sentence: {sentence}")
        

# QUESTION_WORDS = (
#     "what", "how", "why", "differentiate",
#     "identify", "name", "define", "explain"
# )

# def is_question(sentence):
#     s = sentence.strip().lower()
#     return s.startswith(QUESTION_WORDS) or s.endswith("?")

# fact_sentences = [
#     s for s in sentences
#     if score_sentence(s) >= 3.0 and not is_question(s)
# ]

# # print("\n\nExtracted Facts:\n",fact_sentences)

# SKIP_PHRASES = [
#     "for example",
#     "we recall",
#     "from the last chapter",
#     "let us",
#     "consider",
#     "such as"
# ]

# def is_examinable(sentence):
#     s = sentence.lower()
#     return not any(p in s for p in SKIP_PHRASES)

# valid_sentences = [
#     s for s in sentences
#     if score_sentence(s) >= 3.0
#     and not is_question(s)
#     and is_examinable(s)
# ]

# print("\n\Valid Facts:\n",valid_sentences)


# def classify_sentence(sentence):
#     doc = nlp(sentence.lower())

#     if "type" in sentence or "types" in sentence:
#         return "TYPES"

#     for token in doc:
#         if token.lemma_ == "be":
#             return "DEFINITION"

#     if any(word in sentence for word in ["function", "role", "helps"]):
#         return "FUNCTION"

#     if any(word in sentence for word in ["found", "present", "located"]):
#         return "LOCATION"

#     return "GENERAL"

# def extract_real_subject(sentence):
#     doc = nlp(sentence)

#     for token in doc:
#         # Nominal subject of main verb
#         if token.dep_ == "nsubj":
#             return token.text

#     # fallback: longest noun phrase
#     noun_chunks = list(doc.noun_chunks)
#     if noun_chunks:
#         return max(noun_chunks, key=lambda x: len(x.text)).text

#     return None

# BAD_SUBJECTS = {
#     "example", "chapter", "figure", "table", "this", "that"
# }

# def valid_subject(subject):
#     if subject is None:
#         return False
#     return subject.lower() not in BAD_SUBJECTS
    
# def generate_question(sentence):
#     category = classify_sentence(sentence)
#     subject = extract_real_subject(sentence)
#     print(f"Category: {category}, Subject: {subject}")
    
#     if not valid_subject(subject):
#         return None

#     templates = {
#         "DEFINITION": f"Define {subject}.",
#         "TYPES": f"What are the types of {subject}?",
#         "FUNCTION": f"What is the function of {subject}?",
#         "LOCATION": f"Where is {subject} found?",
#         "GENERAL": None
#     }

#     return templates.get(category)
# # print(valid_sentences[154])
# # print(generate_question(valid_sentences[153]))

# RELATION_PATTERNS = {
#     "CLASSIFICATION": [
#         "types of",
#         "classified into",
#         "are of",
#         "kinds of",
#         "grouped into"
#     ],
#     "DEFINITION": [
#         "is defined as",
#         "refers to",
#         "is called",
#         "is known as"
#     ],
#     "FUNCTION": [
#         "function of",
#         "helps in",
#         "is responsible for",
#         "plays a role in"
#     ],
#     "COMPOSITION": [
#         "is made of",
#         "consists of",
#         "composed of"
#     ]
# }

# def detect_relation(sentence):
#     s = sentence.lower()
#     for relation, patterns in RELATION_PATTERNS.items():
#         for p in patterns:
#             if p in s:
#                 return relation
#     return None


# def extract_knowledge_unit(sentence):
#     doc = nlp(sentence)
#     relation = detect_relation(sentence)
#     if not relation:
#         return None

#     concept = None
#     answers = []

#     # Find noun chunks
#     noun_chunks = [chunk.text for chunk in doc.noun_chunks]

#     if relation == "CLASSIFICATION":
#         # heuristic:
#         # last noun chunk = concept
#         # earlier nouns = answers
#         if len(noun_chunks) >= 2:
#             concept = noun_chunks[-1]
#             answers = noun_chunks[:-1]

#     elif relation == "FUNCTION":
#         # subject = concept, object = function
#         for token in doc:
#             if token.dep_ == "nsubj":
#                 concept = token.text
#             if token.dep_ == "dobj":
#                 answers.append(token.text)

#     if concept and answers:
#         return {
#             "concept": concept,
#             "relation": relation,
#             "answers": answers,
#             "source_sentence": sentence
#         }

#     return None


# INVALID_CONCEPT_WORDS = {
#     "which", "we", "they", "fig", "figure",
#     "body", "section", "types", "type",
#     "number", "one", "two", "three"
# }

# def clean_text_chunk(text):
#     text = re.sub(r"\(.*?\)", "", text)   # remove brackets
#     text = re.sub(r"\d+", "", text)       # remove numbers
#     return text.strip()

# def extract_classification(sentence):
#     doc = nlp(sentence)
#     noun_chunks = [clean_text_chunk(c.text) for c in doc.noun_chunks]

#     # Remove junk chunks
#     noun_chunks = [
#         c for c in noun_chunks
#         if len(c.split()) <= 3
#         and c.lower() not in INVALID_CONCEPT_WORDS
#     ]

#     if len(noun_chunks) < 2:
#         return None

#     # Heuristic:
#     # concept = noun after "types of" OR last meaningful noun
#     concept = None
#     answers = []

#     for i, token in enumerate(doc):
#         if token.text.lower() == "types" and token.nbor(1).text.lower() == "of":
#             concept = clean_text_chunk(" ".join(
#                 t.text for t in token.rights
#             ))

#     if not concept:
#         concept = noun_chunks[-1]

#     answers = noun_chunks[:-1]

#     # Final validation
#     if concept.lower() in INVALID_CONCEPT_WORDS:
#         return None

#     answers = [
#         a for a in answers
#         if a.lower() not in INVALID_CONCEPT_WORDS
#         and len(a) > 2
#     ]

#     if len(answers) < 2:
#         return None

#     return {
#         "concept": concept,
#         "relation": "CLASSIFICATION",
#         "answers": answers,
#         "source_sentence": sentence
#     }


# def extract_knowledge_unit(sentence):
#     relation = detect_relation(sentence)
#     print(sentence,'-',relation)
#     if relation == "CLASSIFICATION":
#         return extract_classification(sentence)
#     return ''


# knowledge_units = []
# print("Knowledge Units:\n\n")
# for s in valid_sentences:
#     ku = extract_knowledge_unit(s)
#     if ku:
#         knowledge_units.append(ku)

# for ku in knowledge_units:
#     print(ku)