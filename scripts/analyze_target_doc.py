#!/usr/bin/env python3
"""
Direct Analysis: Find "배경자아의 역할 설명" document and analyze its scores
"""

import json
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
import re

LEDGER_FILE = Path("/home/bino/agi/fdo_agi_repo/memory/resonance_ledger.jsonl")

def tokenize_korean(text):
    """Korean-aware tokenization"""
    text = text.lower()
    tokens = []
    words = re.findall(r'[\w가-힣]+', text)
    tokens.extend(words)
    
    for word in words:
        if any('\uac00' <= c <= '\ud7a3' for c in word):
            word_clean = re.sub(r'(의|이|가|을|를|에|에서|은|는|으로|로|와|과|도|만|부터|까지|한테)$', '', word)
            if word_clean and word_clean != word:
                tokens.append(word_clean)
    
    return list(set(tokens))

query = "배경자아의 역할"
target_title = "배경자아의 역할 설명"

print(f"Query: {query}")
print(f"Target: {target_title}")
print(f"Query tokens: {tokenize_korean(query)}")
print(f"Target tokens: {tokenize_korean(target_title)}")
print()

# Create query embedding
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
query_vec = model.encode(query, convert_to_numpy=True)
query_norm = np.linalg.norm(query_vec)

# Find the document
with open(LEDGER_FILE, 'r') as f:
    for i, line in enumerate(f, 1):
        try:
            doc = json.loads(line)
            if '배경자아의 역할 설명' in doc.get('summary', ''):
                doc_vec = np.array(doc['vector'])
                doc_norm = np.linalg.norm(doc_vec)
                
                semantic_score = np.dot(query_vec, doc_vec) / (query_norm * doc_norm)
                
                print(f"✅ FOUND at line {i}")
                print(f"   Summary: {doc['summary']}")
                print(f"   Semantic Score: {semantic_score:.4f}")
                print(f"   Narrative preview: {doc['narrative'][:200]}...")
                print()
                
                # Check keyword overlap
                doc_tokens = tokenize_korean(doc['summary'] + ' ' + doc['narrative'][:500])
                query_tokens = set(tokenize_korean(query))
                overlap = query_tokens & set(doc_tokens)
                
                print(f"   Keyword Overlap: {overlap}")
                print(f"   Document keywords (first 20): {list(doc_tokens)[:20]}")
                break
        except:
            continue
