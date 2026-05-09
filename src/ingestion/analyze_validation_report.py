import json
import csv
from pathlib import Path
from collections import Counter, defaultdict


REPORT_PATH = Path("data/procesed/chunks/validation_report.json")
CSV_OUTPUT = Path("data/procesed/chunks/validation_errors.csv")
SUMMARY_OUTPUT = Path("data/procesed/chunks/validation_summary.txt")


def load_report(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"No existe el reporte: {path.resolve()}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def infer_error_type(message: str) -> str:
    """
    Clasifica errores aunque tu reporte actual no tenga error_code.
    """
    msg = message.lower()

    if "falta campo obligatorio" in msg:
        return "MISSING_REQUIRED_FIELD"

    if "sin payload" in msg or "payload no es un objeto" in msg:
        return "INVALID_PAYLOAD"

    if "sin id" in msg:
        return "MISSING_ID"

    if "vector" in msg:
        return "VECTOR_ERROR"

    if "embedding_text" in msg:
        return "EMBEDDING_TEXT_ERROR"

    if "text está vacío" in msg or "payload.text" in msg:
        return "TEXT_ERROR"

    if "retrieval_layer" in msg:
        return "RETRIEVAL_LAYER_ERROR"

    if "application_layer" in msg:
        return "APPLICATION_LAYER_ERROR"

    if "document_type desconocido" in msg:
        return "UNKNOWN_DOCUMENT_TYPE"

    if "related_protocols" in msg:
        return "RELATED_PROTOCOLS_ERROR"

    if "previous_step_id" in msg:
        return "PREVIOUS_STEP_LINK_ERROR"

    if "next_step_ids" in msg:
        return "NEXT_STEP_LINK_ERROR"

    if "law_abbreviation" in msg or "article" in msg or "legal_function" in msg:
        return "LEGAL_METADATA_ERROR"

    return "OTHER"


def extract_missing_field(message: str) -> str:
    """
    Intenta extraer el campo faltante de mensajes tipo:
    'Falta campo obligatorio payload.risk_category.'
    """
    marker = "payload."

    if marker not in message:
        return ""

    field = message.split(marker, 1)[1]
    field = field.replace(".", "")
    field = field.strip()

    return field


def analyze_report(report: dict) -> None:
    issues = report.get("issues", [])

    if not issues:
        print("No hay issues en el reporte.")
        return

    severity_counter = Counter()
    type_counter = Counter()
    file_counter = Counter()
    missing_field_counter = Counter()
    chunk_error_counter = Counter()

    examples_by_type = defaultdict(list)

    rows = []

    for issue in issues:
        severity = issue.get("severity", "unknown")
        file = issue.get("file", "unknown")
        chunk_id = issue.get("chunk_id", "")
        message = issue.get("message", "")

        error_type = issue.get("error_code") or infer_error_type(message)

        severity_counter[severity] += 1
        type_counter[error_type] += 1
        file_counter[file] += 1

        if chunk_id:
            chunk_error_counter[chunk_id] += 1

        if error_type == "MISSING_REQUIRED_FIELD":
            missing_field = issue.get("field") or extract_missing_field(message)
            if missing_field:
                missing_field_counter[missing_field] += 1

        if len(examples_by_type[error_type]) < 5:
            examples_by_type[error_type].append({
                "file": file,
                "chunk_id": chunk_id,
                "message": message,
            })

        rows.append({
            "severity": severity,
            "error_type": error_type,
            "file": file,
            "chunk_id": chunk_id,
            "message": message,
        })

    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with CSV_OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "severity",
                "error_type",
                "file",
                "chunk_id",
                "message",
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    lines = []

    lines.append("RESUMEN DE VALIDACIÓN")
    lines.append("====================")
    lines.append("")

    lines.append("Por severidad:")
    for key, value in severity_counter.most_common():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("Por tipo de error:")
    for key, value in type_counter.most_common():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("Campos faltantes más repetidos:")
    for key, value in missing_field_counter.most_common(30):
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("Archivos con más errores:")
    for key, value in file_counter.most_common(30):
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("Chunks con más errores:")
    for key, value in chunk_error_counter.most_common(30):
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("Ejemplos por tipo de error:")
    lines.append("==========================")

    for error_type, examples in examples_by_type.items():
        lines.append("")
        lines.append(f"{error_type}")
        lines.append("-" * len(error_type))

        for ex in examples:
            lines.append(f"Archivo: {ex['file']}")
            lines.append(f"Chunk:   {ex['chunk_id']}")
            lines.append(f"Error:   {ex['message']}")
            lines.append("")

    SUMMARY_OUTPUT.write_text("\n".join(lines), encoding="utf-8")

    print("\nANÁLISIS DEL REPORTE COMPLETADO")
    print("==============================")
    print(f"Total issues: {len(issues)}")
    print(f"CSV generado: {CSV_OUTPUT}")
    print(f"Resumen generado: {SUMMARY_OUTPUT}")
    print("")
    print("Top tipos de error:")
    for key, value in type_counter.most_common(10):
        print(f"- {key}: {value}")


if __name__ == "__main__":
    report = load_report(REPORT_PATH)
    analyze_report(report)