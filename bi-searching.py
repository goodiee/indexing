import argparse
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple, Iterable, Optional
import re


TOKEN_RE = re.compile(r"\w+", re.UNICODE)

def tokenize(text: str) -> List[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t]

def make_bigrams(tokens: Iterable[str]) -> List[str]:
    t = [x for x in tokens if x]
    return [f"{a} {b}" for a, b in zip(t, t[1:])]

def extract_doc_id(path: Path) -> str:
    m = re.search(r"\d+", path.name)
    return m.group(0) if m else path.stem

def sort_key_numeric_then_lex(x: str) -> Tuple[int, int | str]:
    try: return (0, int(x))
    except ValueError: return (1, x)


def index_folder(input_dir: Path) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    inv_uni: Dict[str, Set[str]] = defaultdict(set)
    inv_bi:  Dict[str, Set[str]] = defaultdict(set)

    for p in sorted(input_dir.glob("*.txt")):
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = p.read_text(errors="ignore")
        doc_id = extract_doc_id(p)
        toks = tokenize(text)

        # Unigrams
        for t in set(toks):                
            inv_uni[t].add(doc_id)

        # Bigrams
        for bg in set(make_bigrams(toks)): 
            inv_bi[bg].add(doc_id)

    # Convert to sorted lists for JSON
    uni_json = {t: sorted(list(ds), key=sort_key_numeric_then_lex) for t, ds in inv_uni.items()}
    bi_json  = {t: sorted(list(ds), key=sort_key_numeric_then_lex) for t, ds in inv_bi.items()}

    # Sort keys deterministically
    uni_json = {k: uni_json[k] for k in sorted(uni_json)}
    bi_json  = {k: bi_json[k]  for k in sorted(bi_json)}
    return uni_json, bi_json

def save_indices(out_dir: Path, engine: str,
                 uni_index: Dict[str, List[str]],
                 bi_index: Dict[str, List[str]]) -> Tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    uni_path = out_dir / f"{engine}_inverse_index.json"
    bi_path  = out_dir / f"{engine}_bi_grams.json"
    uni_path.write_text(json.dumps(uni_index, ensure_ascii=False, indent=2), encoding="utf-8")
    bi_path.write_text(json.dumps(bi_index,  ensure_ascii=False, indent=2), encoding="utf-8")
    return uni_path, bi_path


def load_indices_recursive(indices_dir: Path, suffix: str) -> Dict[str, Dict[str, List[str]]]:
    out: Dict[str, Dict[str, List[str]]] = {}
    if not indices_dir.exists(): return out
    for p in indices_dir.rglob(f"*{suffix}.json"):
        try:
            with p.open("r", encoding="utf-8") as f:
                engine = p.stem.replace(suffix, "")
                out[engine] = json.load(f)
        except Exception as e:
            print(f"[!] Failed to load {p}: {e}")
    return out


def rank_documents(
    words: List[str],
    uni_index: Optional[Dict[str, List[str]]],
    bi_index:  Optional[Dict[str, List[str]]],
    w_bigram: float,
    w_unigram: float
) -> List[Tuple[str, float]]:
 
    words = [w.strip().lower() for w in words if w.strip()]
    q_bigrams = make_bigrams(words)

    scores: Dict[str, float] = {}

    # Unigrams
    if uni_index:
        for w in words:
            for d in uni_index.get(w, []):
                scores[d] = scores.get(d, 0.0) + w_unigram

    # Bigrams (boosted)
    if bi_index:
        for bg in q_bigrams:
            for d in bi_index.get(bg, []):
                scores[d] = scores.get(d, 0.0) + w_bigram

    return sorted(scores.items(), key=lambda kv: (-kv[1], sort_key_numeric_then_lex(kv[0])))

def print_ranked(engine: str, ranked: List[Tuple[str, float]], top_k: int) -> None:
    print(f"\nIndex: {engine}")
    if not ranked:
        print("No documents found.")
        return
    for doc, sc in ranked[:top_k]:
        print(f"  doc={doc}  score={sc:.2f}")


def cli_index(args: argparse.Namespace) -> None:
    input_dir = Path(args.input)
    if not input_dir.exists():
        raise SystemExit(f"[!] Input folder not found: {input_dir}")

    uni, bi = index_folder(input_dir)
    uni_p, bi_p = save_indices(Path(args.out), args.engine, uni, bi)
    print(f"[i] Saved: {uni_p}")
    print(f"[i] Saved: {bi_p}")
    print("[✓] Indexing complete.")

def cli_search(args: argparse.Namespace) -> None:
    base = Path(args.indices)
    inv = load_indices_recursive(base, "_inverse_index")
    bi  = load_indices_recursive(base, "_bi_grams")

    if not inv and not bi:
        raise SystemExit("[!] No indices found. Check your --indices path and filenames.")

    query = input("Enter the words to search (comma-separated): ").strip()
    if not query:
        print("Please provide at least one word.")
        return
    words = [w for w in query.split(",") if w.strip()]

    engines = sorted(set(inv.keys()) | set(bi.keys()))
    print("\nRanked results (bigrams prioritized when present):")
    for engine in engines:
        ranked = rank_documents(
            words=words,
            uni_index=inv.get(engine),
            bi_index=bi.get(engine),
            w_bigram=args.w_bigram,
            w_unigram=args.w_unigram
        )
        print_ranked(engine, ranked, args.top_k)

def main() -> None:
    ap = argparse.ArgumentParser(description="HW3 Bigram-boosted Search Engine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_index = sub.add_parser("index", help="Build and save unigram + bigram indices")
    p_index.add_argument("--input",  required=True, help="Folder with .txt documents")
    p_index.add_argument("--out",    required=True, help="Folder to save indices")
    p_index.add_argument("--engine", required=True, help="Engine name for output filenames")
    p_index.set_defaults(func=cli_index)

    p_search = sub.add_parser("search", help="Load indices and run ranked search")
    p_search.add_argument("--indices",   required=True, help="Folder containing saved indices")
    p_search.add_argument("--w-bigram",  type=float, default=3.0, help="Weight for bigram matches")
    p_search.add_argument("--w-unigram", type=float, default=1.0, help="Weight for unigram matches")
    p_search.add_argument("--top-k",     type=int,   default=20,  help="Results per engine to display")
    p_search.set_defaults(func=cli_search)

    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
