# src/ingestion/validate_chunks.py
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# CONFIGURACIÓN
# ============================================================

CHUNKS_ROOT = Path("data/procesed/chunks")
REPORT_OUTPUT = Path("data/procesed/chunks/validation_report.json")


APPLICATION_DOCUMENT_TYPES = {
    "protocol",
    "framework_protocol",
    "guidance",
    "circuit_actuacio",
    "protocol_circuit",
}

LEGAL_DOCUMENT_TYPES = {
    "law",
    "law_decree",
    "organic_law",
}

COMMON_REQUIRED_PAYLOAD_FIELDS = [
    "text",
    "embedding_text",
    "chunk_title",
    "chunk_type",
    "document_type",
    "source_document",
    "language",
    "domain",
    "jurisdiction",
    "risk_category",
    "requires_human_review",
]

CIRCUIT_REQUIRED_FIELDS = [
    "step_id",
    "representation_type",
    "retrieval_layer",
    "application_layer",
    "phase",
    "procedure",
    "previous_step_id",
    "next_step_ids",
    "related_protocols",
]

LEGAL_REQUIRED_FIELDS = [
    "retrieval_layer",
    "application_layer",
    "law_abbreviation",
    "article",
    "legal_function",
]


# ============================================================
# FUNCIONES BÁSICAS
# ============================================================

def load_json_file(path: Path) -> List[Dict[str, Any]]:
    """
    Carga un archivo JSON de chunks.

    Se espera una lista:
    [
      {"id": "...", "vector": null, "payload": {...}},
      ...
    ]
    """
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido en {path}: {e}") from e

    if not isinstance(data, list):
        raise ValueError(f"El archivo {path} debe contener una lista de chunks.")

    return data


def find_chunk_files(root: Path) -> List[Path]:
    """
    Busca todos los JSON dentro de data/processed/chunks.
    Excluye reportes y archivos unificados si existen.
    """
    files = []

    for path in root.rglob("*.json"):
        if path.name in {
            "validation_report.json",
            "all_chunks.json",
            "all_chunks_embedded.json",
        }:
            continue

        files.append(path)

    return sorted(files)


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_list(value: Any) -> bool:
    return isinstance(value, list)


def add_issue(
    issues: List[Dict[str, Any]],
    severity: str,
    file_path: Path,
    chunk_id: Optional[str],
    message: str,
    error_code: str = "GENERAL_ERROR",
    field: Optional[str] = None,
    current_value: Any = None,
    expected_value: Any = None,
) -> None:
    issues.append({
        "severity": severity,
        "error_code": error_code,
        "file": str(file_path),
        "chunk_id": chunk_id,
        "field": field,
        "current_value": current_value,
        "expected_value": expected_value,
        "message": message,
    })


# ============================================================
# VALIDACIONES POR CHUNK
# ============================================================

def validate_base_structure(
    chunk: Dict[str, Any],
    file_path: Path,
    issues: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Valida estructura mínima:
    {
      "id": "...",
      "vector": null,
      "payload": {...}
    }
    """
    chunk_id = chunk.get("id")

    if not is_non_empty_string(chunk_id):
        add_issue(
            issues,
            "error",
            file_path,
            None,
            "Chunk sin id válido.",
        )
        return None

    if "vector" not in chunk:
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "Falta el campo vector.",
        )

    if chunk.get("vector") is not None and not isinstance(chunk.get("vector"), list):
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "El campo vector debe ser null antes de generar embeddings, o una lista después.",
        )

    payload = chunk.get("payload")

    if not isinstance(payload, dict):
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "Falta payload o payload no es un objeto.",
        )
        return None

    return payload


def validate_common_payload_fields(
    payload: Dict[str, Any],
    file_path: Path,
    chunk_id: str,
    issues: List[Dict[str, Any]],
) -> None:
    for field in COMMON_REQUIRED_PAYLOAD_FIELDS:
        if field not in payload:
            add_issue(
                issues,
                "error",
                file_path,
                chunk_id,
                f"Falta campo obligatorio payload.{field}.",
            )

    text = payload.get("text")
    embedding_text = payload.get("embedding_text")

    if not is_non_empty_string(text):
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "payload.text está vacío o no es string.",
        )

    if not is_non_empty_string(embedding_text):
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "payload.embedding_text está vacío o no es string.",
        )

    if is_non_empty_string(text) and len(text.strip()) < 20:
        add_issue(
            issues,
            "warning",
            file_path,
            chunk_id,
            "payload.text es muy corto. Revisa si el chunk aporta suficiente información.",
        )

    if is_non_empty_string(embedding_text) and len(embedding_text.strip()) < 30:
        add_issue(
            issues,
            "warning",
            file_path,
            chunk_id,
            "payload.embedding_text es muy corto. Puede recuperar peor.",
        )

    if payload.get("risk_category") == "general":
        add_issue(
            issues,
            "warning",
            file_path,
            chunk_id,
            "risk_category = general. Revisa si podría ser una categoría más específica.",
        )


def validate_application_layer(
    payload: Dict[str, Any],
    file_path: Path,
    chunk_id: str,
    issues: List[Dict[str, Any]],
) -> None:
    """
    Protocolos, circuitos y guías deben estar en capa application.
    """
    retrieval_layer = payload.get("retrieval_layer")
    application_layer = payload.get("application_layer")

    if retrieval_layer != "application":
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "Documento de aplicación con retrieval_layer distinto de 'application'.",
        )

    if application_layer is not True:
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "Documento de aplicación con application_layer distinto de true.",
        )


def validate_legal_layer(
    payload: Dict[str, Any],
    file_path: Path,
    chunk_id: str,
    issues: List[Dict[str, Any]],
) -> None:
    """
    Leyes y decretos deben estar en legal_support.
    """
    retrieval_layer = payload.get("retrieval_layer")
    application_layer = payload.get("application_layer")

    if retrieval_layer != "legal_support":
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "Documento legal con retrieval_layer distinto de 'legal_support'.",
        )

    if application_layer is not False:
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "Documento legal con application_layer distinto de false.",
        )

    for field in LEGAL_REQUIRED_FIELDS:
        if field not in payload:
            add_issue(
                issues,
                "error",
                file_path,
                chunk_id,
                f"Chunk legal sin payload.{field}.",
            )


def validate_circuit_payload(
    payload: Dict[str, Any],
    file_path: Path,
    chunk_id: str,
    issues: List[Dict[str, Any]],
) -> None:
    """
    Validación específica para circuitos visuales.
    """
    for field in CIRCUIT_REQUIRED_FIELDS:
        if field not in payload:
            add_issue(
                issues,
                "error",
                file_path,
                chunk_id,
                f"Chunk de circuito sin payload.{field}.",
                error_code="MISSING_CIRCUIT_FIELD",
                field=f"payload.{field}",
                current_value=None,
                expected_value="required",
            )

    if payload.get("representation_type") != "visual_circuit":
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "Circuito con representation_type distinto de 'visual_circuit'.",
            error_code="INVALID_CIRCUIT_REPRESENTATION_TYPE",
            field="payload.representation_type",
            current_value=payload.get("representation_type"),
            expected_value="visual_circuit",
        )

    if not is_list(payload.get("next_step_ids")):
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "payload.next_step_ids debe ser una lista.",
            error_code="INVALID_NEXT_STEP_IDS",
            field="payload.next_step_ids",
            current_value=payload.get("next_step_ids"),
            expected_value="list",
        )

    related_protocols = payload.get("related_protocols")

    if not isinstance(related_protocols, list) or not related_protocols:
        add_issue(
            issues,
            "error",
            file_path,
            chunk_id,
            "payload.related_protocols debe ser una lista no vacía en circuitos.",
            error_code="INVALID_RELATED_PROTOCOLS",
            field="payload.related_protocols",
            current_value=related_protocols,
            expected_value="non_empty_list",
        )
        
def validate_chunk(
    chunk: Dict[str, Any],
    file_path: Path,
    issues: List[Dict[str, Any]],
) -> None:
    payload = validate_base_structure(chunk, file_path, issues)

    if payload is None:
        return

    chunk_id = chunk["id"]

    validate_common_payload_fields(payload, file_path, chunk_id, issues)

    document_type = payload.get("document_type")

    if document_type in APPLICATION_DOCUMENT_TYPES:
        validate_application_layer(payload, file_path, chunk_id, issues)

    elif document_type in LEGAL_DOCUMENT_TYPES:
        validate_legal_layer(payload, file_path, chunk_id, issues)

    else:
        add_issue(
            issues,
            "warning",
            file_path,
            chunk_id,
            f"document_type desconocido o no clasificado: {document_type}",
        )

    if document_type in {"circuit_actuacio", "protocol_circuit"}:
        validate_circuit_payload(payload, file_path, chunk_id, issues)


# ============================================================
# VALIDACIONES GLOBALES
# ============================================================

def validate_duplicate_ids(
    all_chunks: List[Tuple[Path, Dict[str, Any]]],
    issues: List[Dict[str, Any]],
) -> None:
    seen = {}

    for file_path, chunk in all_chunks:
        chunk_id = chunk.get("id")

        if not chunk_id:
            continue

        if chunk_id in seen:
            add_issue(
                issues,
                "error",
                file_path,
                chunk_id,
                f"ID duplicado. También aparece en {seen[chunk_id]}.",
            )
        else:
            seen[chunk_id] = str(file_path)


def validate_circuit_links(
    all_chunks: List[Tuple[Path, Dict[str, Any]]],
    issues: List[Dict[str, Any]],
) -> None:
    """
    Comprueba que previous_step_id y next_step_ids apunten a chunks existentes.
    """
    ids = {
        chunk.get("id")
        for _, chunk in all_chunks
        if chunk.get("id")
    }

    for file_path, chunk in all_chunks:
        chunk_id = chunk.get("id")
        payload = chunk.get("payload", {})

        if not isinstance(payload, dict):
            continue

        document_type = payload.get("document_type")

        if document_type not in {"circuit_actuacio", "protocol_circuit"}:
            continue

        previous_step_id = payload.get("previous_step_id")
        next_step_ids = payload.get("next_step_ids", [])

        if previous_step_id is not None and previous_step_id not in ids:
            add_issue(
                issues,
                "warning",
                file_path,
                chunk_id,
                f"previous_step_id apunta a un id no encontrado: {previous_step_id}",
            )

        if isinstance(next_step_ids, list):
            for next_id in next_step_ids:
                if next_id not in ids:
                    add_issue(
                        issues,
                        "warning",
                        file_path,
                        chunk_id,
                        f"next_step_ids contiene un id no encontrado: {next_id}",
                    )


def build_summary(
    files: List[Path],
    all_chunks: List[Tuple[Path, Dict[str, Any]]],
    issues: List[Dict[str, Any]],
) -> Dict[str, Any]:
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    by_document_type = {}

    for _, chunk in all_chunks:
        payload = chunk.get("payload", {})

        if not isinstance(payload, dict):
            continue

        document_type = payload.get("document_type", "unknown")
        by_document_type[document_type] = by_document_type.get(document_type, 0) + 1

    return {
        "files_checked": len(files),
        "chunks_checked": len(all_chunks),
        "errors": len(errors),
        "warnings": len(warnings),
        "chunks_by_document_type": by_document_type,
    }


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def validate_all_chunks(
    chunks_root: Path = CHUNKS_ROOT,
    report_output: Path = REPORT_OUTPUT,
) -> Dict[str, Any]:
    files = find_chunk_files(chunks_root)

    if not files:
        raise FileNotFoundError(f"No se han encontrado archivos JSON en {chunks_root}")

    issues: List[Dict[str, Any]] = []
    all_chunks: List[Tuple[Path, Dict[str, Any]]] = []

    for file_path in files:
        try:
            chunks = load_json_file(file_path)
        except Exception as e:
            add_issue(
                issues,
                "error",
                file_path,
                None,
                str(e),
            )
            continue

        for chunk in chunks:
            all_chunks.append((file_path, chunk))
            validate_chunk(chunk, file_path, issues)

    validate_duplicate_ids(all_chunks, issues)
    validate_circuit_links(all_chunks, issues)

    summary = build_summary(files, all_chunks, issues)

    report = {
        "summary": summary,
        "issues": issues,
    }

    report_output.parent.mkdir(parents=True, exist_ok=True)

    with report_output.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\nVALIDACIÓN COMPLETADA")
    print("====================")
    print(f"Archivos revisados: {summary['files_checked']}")
    print(f"Chunks revisados:   {summary['chunks_checked']}")
    print(f"Errores:            {summary['errors']}")
    print(f"Warnings:           {summary['warnings']}")
    print(f"Reporte guardado:   {report_output}")

    if summary["errors"] > 0:
        print("\nHay errores. No recomiendo indexar en Qdrant todavía.")
    else:
        print("\nSin errores críticos. Puedes pasar a embeddings e indexación.")

    return report


if __name__ == "__main__":
    validate_all_chunks()