import os
import json

def load_inverse_indices(directory):
    inverse_indices = {}
    for filename in os.listdir(directory):
        if filename.endswith("_inverse_index.json"):
            with open(os.path.join(directory, filename), 'r') as file:
                inverse_indices[filename] = json.load(file)
    return inverse_indices

def search_documents_with_word(index, word):
    word = word.lower()
    if word in index:
        return set(index[word])
    return set()

if __name__ == "__main__":
    search_engines_path = "M:/Master 1 semester/Information Modeling/Lab2/Inverse Indices"
    inverse_indices = load_inverse_indices(search_engines_path)
    query = input("Enter the words you want to check, separated by commas: ")
    words_to_check = [word.strip() for word in query.split(',')]

    if len(words_to_check) == 1:
        print(f"Searching for documents containing the word '{words_to_check[0]}' in any index file:")
        word_to_check = words_to_check[0]
        for index_name, index in inverse_indices.items():
            print("Index:", os.path.splitext(index_name)[0].replace("_inverse_index", ""))
            documents_with_word = search_documents_with_word(index, word_to_check)
            if documents_with_word:
                sorted_documents = sorted(documents_with_word, key=lambda x: int(x))
                print("Documents:", sorted_documents)
            else:
                print("No documents found.")
    elif len(words_to_check) >= 2:
        print(f"Searching for documents containing all of the following words: {', '.join(words_to_check)}")
        for index_name, index in inverse_indices.items():
            print("Index:", os.path.splitext(index_name)[0].replace("_inverse_index", ""))
            documents_containing_all = None
            for word in words_to_check:
                documents_with_word = search_documents_with_word(index, word)
                if documents_containing_all is None:
                    documents_containing_all = documents_with_word
                else:
                    documents_containing_all = documents_containing_all.intersection(documents_with_word)
            if documents_containing_all:
                sorted_documents = sorted(documents_containing_all, key=lambda x: int(x))
                print("Documents:", sorted_documents)
            else:
                print("No documents found.")
    else:
        print("Please provide at least one word.")