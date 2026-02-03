#!/usr/bin/env python3
"""
Test Korean Tokenization Strategies
"""

import re

def tokenize_v1(text):
    """Current method"""
    return re.findall(r'[\w가-힣]+', text.lower())

def tokenize_v2(text):
    """Korean particle stripping"""
    text = text.lower()
    # Strip common Korean particles
    text = re.sub(r'(의|이|가|을|를|에|에서|으로|로|와|과|도)(?=\s|$)', '', text)
    return re.findall(r'[\w가-힣]+', text)

def tokenize_v3_ngrams(text):
    """Include character n-grams for Korean"""
    text = text.lower()
    tokens = []
    
    # Word-level tokens
    words = re.findall(r'[\w가-힣]+', text)
    tokens.extend(words)
    
    # For Korean words, add character bigrams and trigrams
    for word in words:
        if any('\uac00' <= c <= '\ud7a3' for c in word):  # Contains Korean
            # Remove particles
            word_clean = re.sub(r'(의|이|가|을|를|에|에서|으로|로|와|과|도)$', '', word)
            if word_clean and word_clean != word:
                tokens.append(word_clean)
            
            # Bigrams
            if len(word_clean) >= 2:
                for i in range(len(word_clean) - 1):
                    tokens.append(word_clean[i:i+2])
    
    return list(set(tokens))  # Unique tokens

# Test
query = "배경자아의 역할"
doc1 = "배경자아의 역할 설명"
doc2 = "배경자아는 무의식의 관찰자"

print(f"Query: {query}\n")
print(f"v1 (current): {tokenize_v1(query)}")
print(f"v2 (particle strip): {tokenize_v2(query)}")
print(f"v3 (ngrams): {tokenize_v3_ngrams(query)}")
print()
print(f"Doc1: {doc1}")
print(f"  v1: {tokenize_v1(doc1)}")
print(f"  v2: {tokenize_v2(doc1)}")
print(f"  v3: {tokenize_v3_ngrams(doc1)}")
print()
print(f"Doc2: {doc2}")
print(f"  v3: {tokenize_v3_ngrams(doc2)}")

# Check overlap
query_tokens_v3 = set(tokenize_v3_ngrams(query))
doc1_tokens_v3 = set(tokenize_v3_ngrams(doc1))
doc2_tokens_v3 = set(tokenize_v3_ngrams(doc2))

print(f"\nQuery vs Doc1 overlap (v3): {query_tokens_v3 & doc1_tokens_v3}")
print(f"Query vs Doc2 overlap (v3): {query_tokens_v3 & doc2_tokens_v3}")
