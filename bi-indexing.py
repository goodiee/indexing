import json
import re
from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, Iterable, Optional, Set

TOKEN_RE = re.compile(r"\w+", re.UNICODE)
FIRST_NUMBER_RE = re.compile(r"\d+")


def generate_2grams(text: str) -> Iterable[str]:
    tokens = TOKEN_RE.findall(text.lower())
    for a, b in zip(tokens, tokens[1:]):
        yield f"{a} {b}"


def extract_document_id(filename: str) -> Optional[str]:
    m = FIRST_NUMBER_RE.search(filename)
    return m.group(0) if m else None


def create_2grams_index(folder_path: str) -> Dict[str, Set[str]]:
    base = Path(folder_path)
    bigrams_index: DefaultDict[str, Set[str]] = defaultdict(set)

    for path in base.iterdir():
        if not path.is_file() or path.suffix.lower() != ".txt":
            continue

        document_id = extract_document_id(path.name)
        if document_id is None:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(errors="ignore")

        for bg in generate_2grams(text):
            bigrams_index[bg].add(document_id)

    return bigrams_index


def save_2grams_index(bigrams_index: Dict[str, Set[str]],
                      output_folder: str,
                      engine_name: str) -> str:
    out_dir = Path(output_folder)
    out_dir.mkdir(parents=True, exist_ok=True)

    def sort_key(x: str):
        try:
            return (0, int(x))
        except ValueError:
            return (1, x)

    serializable = {
        bigram: sorted(list(doc_ids), key=sort_key)
        for bigram, doc_ids in bigrams_index.items()
    }

    ordered = {k: serializable[k] for k in sorted(serializable)}

    output_file = out_dir / f"{engine_name}_bi_grams.json"
    output_file.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(output_file)


if __name__ == "__main__":
    SEARCH_ENGINES_PATH = Path(r"M:/Master 1st semester/IM/LAB3/indexing/Serach_engines_M")
    OUTPUT_FOLDER = Path(r"M:/Master 1st semester/IM/LAB3/indexing/Bi-grams")

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    for engine_folder in sorted(p for p in SEARCH_ENGINES_PATH.iterdir() if p.is_dir()):
        bi_grams_index = create_2grams_index(str(engine_folder))
        output_file = save_2grams_index(bi_grams_index, str(OUTPUT_FOLDER), engine_folder.name)
        print(f"Bi-grams index for {engine_folder.name} saved to {output_file}")
