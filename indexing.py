import os
import re
import json
from collections import defaultdict

def tokenize(text):
    return re.findall(r'\w+', text.lower())

def extract_document_id(filename):
    match = re.search(r'\d+', filename)
    if match:
        return match.group()
    else:
        return None

def create_inverse_index(folder_path):
    inverse_index = defaultdict(set)
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            with open(os.path.join(folder_path, filename), 'r', encoding='utf-8') as file:
                document_id = extract_document_id(filename)
                if document_id is not None:
                    text = file.read()
                    words = tokenize(text)
                    for word in words:
                        inverse_index[word].add(document_id)
    return inverse_index

def save_inverse_index(inverse_index, output_folder, engine_name):
    inverse_index_serializable = {
        word: sorted(list(doc_ids), key=lambda x: int(x))
        for word, doc_ids in inverse_index.items()
    }
    inverse_index_serializable = {k: inverse_index_serializable[k] for k in sorted(inverse_index_serializable)}
    output_file = os.path.join(output_folder, f"{engine_name}_inverse_index.json")
    with open(output_file, 'w') as file:
        json.dump(inverse_index_serializable, file)
    return output_file

if __name__ == "__main__":
    search_engines_path = "M:/Master 1 semester/Information Modeling/Lab2/Serach_engines_M"
    output_folder = "M:/Master 1 semester/Information Modeling/Lab2/Inverse Indices"
    os.makedirs(output_folder, exist_ok=True)
    for engine_folder in os.listdir(search_engines_path):
        engine_folder_path = os.path.join(search_engines_path, engine_folder)
        if os.path.isdir(engine_folder_path):
            inverse_index = create_inverse_index(engine_folder_path)
            output_file = save_inverse_index(inverse_index, output_folder, engine_folder)
            print("Inverse index for", engine_folder, "saved to", output_file)
