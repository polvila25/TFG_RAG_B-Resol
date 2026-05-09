import json
from pathlib import Path
from typing import Any, Dict, List


CHUNKS_ROOT = Path("data/procesed/chunks")
OUTPUT_FILE = Path("data/procesed/chunks/all_chunks.json")


EXCLUDED_FILES = {
    "validation_report.json",
    "all_chunks.json",
    "all_chunks_embedded.json",
}


def load_chunks(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"{path} no contiene una lista JSON.")

    return data


def merge_chunks(
    chunks_root: Path = CHUNKS_ROOT,
    output_file: Path = OUTPUT_FILE,
) -> List[Dict[str, Any]]:

    all_chunks = []
    seen_ids = set()

    files = [
        path
        for path in chunks_root.rglob("*.json")
        if path.name not in EXCLUDED_FILES
    ]

    for file_path in sorted(files):
        chunks = load_chunks(file_path)

        for chunk in chunks:
            chunk_id = chunk.get("id")

            if chunk_id in seen_ids:
                raise ValueError(f"ID duplicado detectado: {chunk_id}")

            seen_ids.add(chunk_id)
            all_chunks.append(chunk)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"Chunks unificados: {len(all_chunks)}")
    print(f"Archivo generado: {output_file}")

    return all_chunks


if __name__ == "__main__":
    merge_chunks()