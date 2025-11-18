import os
import json
import math
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple



def tokenize_text(text: str) -> List[str]:
    return re.findall(r'\w+', text.lower())


def compute_idf(corpus_tokens: List[List[str]]) -> Dict[str, float]:
    N = len(corpus_tokens)
    doc_freq = defaultdict(int)

    for doc in corpus_tokens:
        for term in set(doc):
            doc_freq[term] += 1

    idf = {}
    for term, df in doc_freq.items():
        idf[term] = math.log2(N / df)

    return idf


def build_document_vectors(docs_tokens: Dict[str, List[str]], idf: Dict[str, float]):
    doc_vecs = {}
    for doc_id, tokens in docs_tokens.items():
        tf = Counter(tokens)
        vec = {}
        for term, count in tf.items():
            if term in idf:
                vec[term] = count * idf[term]
        doc_vecs[doc_id] = vec
    return doc_vecs


def build_query_vector(query_terms: List[str], idf: Dict[str, float]):
    if not query_terms:
        return {}

    tf = Counter(query_terms)
    max_tf = max(tf.values())

    q_vec = {}
    for term, freq in tf.items():
        if term in idf:
            normalized_tf = freq / max_tf
            q_vec[term] = normalized_tf * idf[term]

    return q_vec


def cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    if not v1 or not v2:
        return 0.0

    # dot product
    dot = sum(v1[t] * v2.get(t, 0) for t in v1)

    norm1 = math.sqrt(sum(w * w for w in v1.values()))
    norm2 = math.sqrt(sum(w * w for w in v2.values()))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot / (norm1 * norm2)



def save_tf_idf_index(index: Dict[str, Dict[str, float]], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)


def load_tf_idf_index(path: str) -> Dict[str, Dict[str, float]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# SEARCH
def search(doc_vectors: Dict[str, Dict[str, float]], query_vector: Dict[str, float]):
    results = []
    for doc_id, d_vec in doc_vectors.items():
        sim = cosine_similarity(d_vec, query_vector)
        if sim > 0:
            results.append((doc_id, sim))
    return sorted(results, key=lambda x: -x[1])




base_path = r"M:/Master 1st semester/IM/LAB3/indexing/Serach_engines_M"
output_folder = r"M:/Master 1st semester/IM/LAB3/indexing/tf_idf_indices"

os.makedirs(output_folder, exist_ok=True)



print("Indexing all engines...")

for engine_folder in os.listdir(base_path):
    engine_folder_path = os.path.join(base_path, engine_folder)
    if not os.path.isdir(engine_folder_path):
        continue

    docs_tokens = {}

    # Read all txt files inside engine folder
    for filename in os.listdir(engine_folder_path):
        if filename.endswith(".txt"):
            full_path = os.path.join(engine_folder_path, filename)
            with open(full_path, "r", encoding="utf-8") as f:
                text = f.read()
            tokens = tokenize_text(text)
            doc_id = os.path.splitext(filename)[0]
            docs_tokens[doc_id] = tokens

    if not docs_tokens:
        continue

    # Compute IDF for this engine
    corpus_tokens = list(docs_tokens.values())
    idf = compute_idf(corpus_tokens)

    # Build document tf-idf vectors
    doc_vectors = build_document_vectors(docs_tokens, idf)

    # Save index
    out_path = os.path.join(output_folder, f"{engine_folder}_tf_idf.json")
    save_tf_idf_index(doc_vectors, out_path)

print("Indexing complete.\n")


keywords_input = input("Enter keywords separated by commas: ")
keywords = [w.strip().lower() for w in keywords_input.split(",") if w.strip()]


for json_file in os.listdir(output_folder):
    if not json_file.endswith(".json"):
        continue

    engine_name = json_file.replace("_tf_idf.json", "")
    index_path = os.path.join(output_folder, json_file)

    # Load document vectors
    doc_vectors = load_tf_idf_index(index_path)

    # Extract IDF terms from doc vectors (reverse-engineer since stored)
    # Recompute df properly like before
    all_tokens = []
    for vec in doc_vectors.values():
        tokens = []
        for term, weight in vec.items():

            tokens.append(term)
        all_tokens.append(tokens)

    idf = compute_idf(all_tokens)

    # Build query vector
    q_vec = build_query_vector(keywords, idf)

    # Search
    results = search(doc_vectors, q_vec)

    print(f"\nResults for engine '{engine_name}':")
    if results:
        for doc_id, score in results:
            print(f"  {doc_id}: {score:.4f}")
    else:
        print("  No matching documents.")
