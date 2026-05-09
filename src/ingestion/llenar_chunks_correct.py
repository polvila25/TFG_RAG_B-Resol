# src/ingestion/llenar_chunks_correct.py
from __future__ import annotations

import argparse
import copy
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


# ============================================================
# CONFIGURACIÓN
# ============================================================

DEFAULT_CHUNKS_DIR = Path("data/procesed/chunks")
DEFAULT_REPORTS_DIR = Path("data/procesed/reports")
DEFAULT_BACKUP_DIR = Path("data/procesed/backups")


IGNORED_FILENAMES = {
    "validation_report.json",
    "all_chunks.json",
    "all_chunks_embedded.json",
}


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


CIRCUIT_DOCUMENT_TYPES = {
    "circuit_actuacio",
    "protocol_circuit",
}


RELATED_PROTOCOLS_BY_FILENAME = {
    "circuit_actuacio_drogues_secundaria.json": [
        "protocol_drogues_secundaria"
    ],
    "circuit_ciberassetjament.json": [
        "protocol_ciberassetjament"
    ],
    "circuit_actuacio_violencia_chunks.json": [
        "protocol_violencia_ambit_educatiu"
    ],
    "circuit_transgenere_chunks.json": [
        "protocol_acompanyament_alumnat_transgenere"
    ],
    "faltes_greus_chunks.json": [
        "protocol_faltes_greus_convivencia"
    ],
    "protocol_maltractament_infantil_chunks.json": [
        "protocol_maltractament_infantil_adolescent"
    ],
    "protocol_menors_14_chunks.json": [
        "protocol_menors_14_infraccio_penal"
    ],
}


REPRESENTATION_TYPE_BY_DOCUMENT_TYPE = {
    "protocol": "redacted_protocol",
    "framework_protocol": "redacted_protocol",
    "guidance": "educational_guide",
    "circuit_actuacio": "visual_circuit",
    "protocol_circuit": "visual_circuit",
    "law": "legal_text",
    "law_decree": "legal_text",
    "organic_law": "legal_text",
}


# ============================================================
# NUEVO: RISK CATEGORY
# ============================================================

RISK_CATEGORIES = {
    "assetjament_escolar",
    "ciberassetjament",
    "conductes_odi_discriminacio",
    "violencies_masclistes",
    "violencia_sexual",
    "maltractament_infantil",
    "violencia_familiar",
    "falta_greument_perjudicial",
    "menor_14_infraccio_penal",
    "presumpte_delicte",
    "extremisme_violent",
    "conducta_suicida",
    "autolesions",
    "tca",
    "consum_substancies",
    "conflicte_convivencia",
    "acompanyament_alumnat_transgenere",
    "general",
}


# Archivos claros: se clasifican directamente por filename.
RISK_CATEGORY_BY_FILENAME = {
    "circuit_actuacio_drogues_secundaria.json": "consum_substancies",
    "170505-PROTOCOL-SECUNDARIA-DROGUES-DEFINITIU.json": "consum_substancies",

    "circuit_ciberassetjament.json": "ciberassetjament",
    "protocol-ciberassetjament-arxiu-unificat.json": "ciberassetjament",

    "circuit_transgenere_chunks.json": "acompanyament_alumnat_transgenere",
    "protocol-transgenere.json": "acompanyament_alumnat_transgenere",

    "Detecció-i-prevenció-a-laula-tca.json": "tca",

    "faltes_greus_chunks.json": "falta_greument_perjudicial",
    "protocol-intervencio-faltes-greus-convivencia.json": "falta_greument_perjudicial",

    "protocol_maltractament_infantil_chunks.json": "maltractament_infantil",
    "protocol_menors_14_chunks.json": "menor_14_infraccio_penal",

    # Estos dos son transversales. Se usan como fallback.
    "protocol_violencia_chunks.json": "general",
    "circuit_actuacio_violencia_chunks.json": "general",
}


# Archivos donde SÍ queremos afinar por contenido.
CONTENT_BASED_RISK_FILES = {
    "protocol_violencia_chunks.json",
    "circuit_actuacio_violencia_chunks.json",
}


# Reglas ordenadas de más específico a más general.
RISK_CATEGORY_CONTENT_RULES = [
    {
        "risk_category": "conducta_suicida",
        "keywords": [
            "conducta suïcida",
            "conducta suicida",
            "ideació suïcida",
            "ideacio suicida",
            "suïcidi",
            "suicidi",
            "risc autolític",
            "risc autolitic",
        ],
    },
    {
        "risk_category": "autolesions",
        "keywords": [
            "autolesió",
            "autolesio",
            "autolesions",
            "autoagressió",
            "autoagressio",
            "autolesiva",
            "autolesiu",
        ],
    },
    {
        "risk_category": "violencia_sexual",
        "keywords": [
            "violència sexual",
            "violencia sexual",
            "abús sexual",
            "abus sexual",
            "agressió sexual",
            "agressio sexual",
            "assetjament sexual",
        ],
    },
    {
        "risk_category": "violencies_masclistes",
        "keywords": [
            "violències masclistes",
            "violencies masclistes",
            "violència masclista",
            "violencia masclista",
            "violència de gènere",
            "violencia de genero",
            "violència de gènere",
        ],
    },
    {
        "risk_category": "extremisme_violent",
        "keywords": [
            "extremisme violent",
            "radicalització",
            "radicalitzacio",
            "radicalisme",
            "terrorisme",
        ],
    },
    {
        "risk_category": "maltractament_infantil",
        "keywords": [
            "maltractament infantil",
            "maltractament",
            "negligència",
            "negligencia",
            "desemparament",
            "infància en risc",
            "infancia en risc",
        ],
    },
    {
        "risk_category": "violencia_familiar",
        "keywords": [
            "violència familiar",
            "violencia familiar",
            "àmbit familiar",
            "ambit familiar",
            "violència domèstica",
            "violencia domestica",
        ],
    },
    {
        "risk_category": "conductes_odi_discriminacio",
        "keywords": [
            "conductes d'odi",
            "conductes d’odi",
            "delictes d'odi",
            "delictes d’odi",
            "odi i discriminació",
            "odi i discriminacio",
            "discriminació",
            "discriminacio",
            "racisme",
            "xenofòbia",
            "xenofobia",
            "lgtbifòbia",
            "lgtbifobia",
            "homofòbia",
            "homofobia",
            "transfòbia",
            "transfobia",
        ],
    },
    {
        "risk_category": "ciberassetjament",
        "keywords": [
            "ciberassetjament",
            "ciberacoso",
            "xarxes socials",
            "instagram",
            "whatsapp",
            "internet",
            "entorn digital",
            "mitjans digitals",
        ],
    },
    {
        "risk_category": "assetjament_escolar",
        "keywords": [
            "assetjament escolar",
            "bullying",
            "assetjament entre iguals",
        ],
    },
    {
        "risk_category": "falta_greument_perjudicial",
        "keywords": [
            "faltes greument perjudicials",
            "falta greument perjudicial",
            "faltes greus",
            "falta greu",
            "expedient disciplinari",
            "incoació d'expedient",
            "incoacio expedient",
            "mesures correctores",
            "mesures sancionadores",
        ],
    },
    {
        "risk_category": "presumpte_delicte",
        "keywords": [
            "presumpte delicte",
            "delicte",
            "derivació penal",
            "derivacio penal",
            "fiscalia",
            "ministeri fiscal",
            "mossos d'esquadra",
            "mossos d’esquadra",
            "policia",
        ],
    },
    {
        "risk_category": "conflicte_convivencia",
        "keywords": [
            "conflicte de convivència",
            "conflicte de convivencia",
            "conflicte convivència",
            "conflicte convivencia",
            "conductes contràries",
            "conductes contraries",
            "convivència",
            "convivencia",
        ],
    },
]


# ============================================================
# UTILIDADES JSON
# ============================================================

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def is_valid_chunk_file(path: Path) -> bool:
    if path.name in IGNORED_FILENAMES:
        return False

    if path.suffix.lower() != ".json":
        return False

    return True


def get_chunks(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return data

    if isinstance(data, dict) and isinstance(data.get("chunks"), list):
        return data["chunks"]

    raise ValueError("Formato JSON no válido. Se esperaba una lista o un objeto con clave 'chunks'.")


def set_chunks(data: Any, chunks: List[Dict[str, Any]]) -> Any:
    if isinstance(data, list):
        return chunks

    if isinstance(data, dict) and isinstance(data.get("chunks"), list):
        new_data = copy.deepcopy(data)
        new_data["chunks"] = chunks
        return new_data

    raise ValueError("Formato JSON no válido. No se pueden guardar los chunks.")


# ============================================================
# LÓGICA DE NORMALIZACIÓN
# ============================================================

def expected_layers_from_document_type(document_type: str) -> Tuple[str | None, bool | None]:
    if document_type in APPLICATION_DOCUMENT_TYPES:
        return "application", True

    if document_type in LEGAL_DOCUMENT_TYPES:
        return "legal_support", False

    return None, None


def is_valid_related_protocols(value: Any) -> bool:
    if not isinstance(value, list):
        return False

    if len(value) == 0:
        return False

    for item in value:
        if not isinstance(item, str):
            return False

        if item.strip() == "":
            return False

    return True


def infer_related_protocols_from_filename(file_path: Path) -> List[str] | None:
    return RELATED_PROTOCOLS_BY_FILENAME.get(file_path.name)


def normalize_related_protocols(
    payload: Dict[str, Any],
    file_path: Path,
    changes: List[Dict[str, Any]],
) -> None:
    document_type = payload.get("document_type")

    if document_type not in CIRCUIT_DOCUMENT_TYPES:
        return

    current_related_protocols = payload.get("related_protocols")

    if is_valid_related_protocols(current_related_protocols):
        return

    inferred_related_protocols = infer_related_protocols_from_filename(file_path)

    if inferred_related_protocols is None:
        changes.append(
            {
                "field": "payload.related_protocols",
                "old_value": current_related_protocols,
                "new_value": None,
                "reason": (
                    "El chunk es un circuito, pero no existe una regla para inferir "
                    "related_protocols desde el nombre del archivo."
                ),
                "action": "manual_review_required",
            }
        )
        return

    payload["related_protocols"] = inferred_related_protocols

    changes.append(
        {
            "field": "payload.related_protocols",
            "old_value": current_related_protocols,
            "new_value": inferred_related_protocols,
            "reason": (
                "El chunk es un circuito y related_protocols estaba ausente, "
                "vacío o inválido. Se ha inferido desde el nombre del archivo."
            ),
            "action": "updated",
        }
    )


def normalize_representation_type(
    payload: Dict[str, Any],
    changes: List[Dict[str, Any]],
) -> None:
    document_type = payload.get("document_type")

    if not isinstance(document_type, str):
        return

    expected_representation_type = REPRESENTATION_TYPE_BY_DOCUMENT_TYPE.get(document_type)

    if expected_representation_type is None:
        return

    current_representation_type = payload.get("representation_type")

    if current_representation_type == expected_representation_type:
        return

    payload["representation_type"] = expected_representation_type

    changes.append(
        {
            "field": "payload.representation_type",
            "old_value": current_representation_type,
            "new_value": expected_representation_type,
            "reason": (
                f"document_type='{document_type}' requiere "
                f"representation_type='{expected_representation_type}'."
            ),
            "action": "updated",
        }
    )


# ============================================================
# NUEVO: NORMALIZACIÓN RISK_CATEGORY
# ============================================================

def is_valid_risk_category(value: Any) -> bool:
    return isinstance(value, str) and value.strip() in RISK_CATEGORIES


def build_risk_context_text(
    chunk: Dict[str, Any],
    payload: Dict[str, Any],
    file_path: Path,
) -> str:
    parts = [
        file_path.name,
        chunk.get("id", ""),
        payload.get("step_id", ""),
        payload.get("chunk_title", ""),
        payload.get("chunk_type", ""),
        payload.get("procedure", ""),
        payload.get("phase", ""),
        payload.get("source_document", ""),
        payload.get("keywords", ""),
        payload.get("text", ""),
        payload.get("embedding_text", ""),
    ]

    return " ".join(str(part).lower() for part in parts if part)


def infer_risk_category_from_content(
    chunk: Dict[str, Any],
    payload: Dict[str, Any],
    file_path: Path,
) -> str | None:
    context = build_risk_context_text(chunk, payload, file_path)

    for rule in RISK_CATEGORY_CONTENT_RULES:
        for keyword in rule["keywords"]:
            if keyword.lower() in context:
                return rule["risk_category"]

    return None


def infer_risk_category(
    chunk: Dict[str, Any],
    payload: Dict[str, Any],
    file_path: Path,
) -> Tuple[str | None, str]:
    file_name = file_path.name

    # 1. En documentos transversales de violencia, primero afinamos por contenido.
    if file_name in CONTENT_BASED_RISK_FILES:
        inferred_by_content = infer_risk_category_from_content(
            chunk=chunk,
            payload=payload,
            file_path=file_path,
        )

        if inferred_by_content is not None:
            return inferred_by_content, "content_rule"

        fallback = RISK_CATEGORY_BY_FILENAME.get(file_name)
        return fallback, "filename_fallback"

    # 2. En documentos claros, usamos directamente el filename.
    inferred_by_filename = RISK_CATEGORY_BY_FILENAME.get(file_name)

    if inferred_by_filename is not None:
        return inferred_by_filename, "filename"

    # 3. Si no hay regla de filename, intentamos contenido como último recurso.
    inferred_by_content = infer_risk_category_from_content(
        chunk=chunk,
        payload=payload,
        file_path=file_path,
    )

    if inferred_by_content is not None:
        return inferred_by_content, "content_rule_fallback"

    return None, "manual_review_required"


def normalize_risk_category(
    chunk: Dict[str, Any],
    payload: Dict[str, Any],
    file_path: Path,
    changes: List[Dict[str, Any]],
) -> None:
    current_risk_category = payload.get("risk_category")

    if is_valid_risk_category(current_risk_category):
        return

    inferred_risk_category, method = infer_risk_category(
        chunk=chunk,
        payload=payload,
        file_path=file_path,
    )

    if inferred_risk_category is None:
        changes.append(
            {
                "field": "payload.risk_category",
                "old_value": current_risk_category,
                "new_value": None,
                "reason": (
                    "No se ha podido inferir risk_category con reglas de filename "
                    "ni con reglas de contenido."
                ),
                "action": "manual_review_required",
            }
        )
        return

    if inferred_risk_category not in RISK_CATEGORIES:
        changes.append(
            {
                "field": "payload.risk_category",
                "old_value": current_risk_category,
                "new_value": inferred_risk_category,
                "reason": "La categoría inferida no pertenece a la taxonomía permitida.",
                "action": "manual_review_required",
            }
        )
        return

    payload["risk_category"] = inferred_risk_category

    changes.append(
        {
            "field": "payload.risk_category",
            "old_value": current_risk_category,
            "new_value": inferred_risk_category,
            "reason": f"risk_category inferido mediante método: {method}.",
            "action": "updated",
        }
    )


def normalize_chunk_layers(
    chunk: Dict[str, Any],
    file_path: Path,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    normalized_chunk = copy.deepcopy(chunk)
    changes = []

    payload = normalized_chunk.get("payload")

    if not isinstance(payload, dict):
        changes.append(
            {
                "field": "payload",
                "old_value": payload,
                "new_value": {},
                "reason": "El chunk no tenía payload válido. Se crea payload vacío.",
            }
        )
        payload = {}
        normalized_chunk["payload"] = payload

    document_type = payload.get("document_type")

    if not isinstance(document_type, str):
        return normalized_chunk, changes

    expected_retrieval_layer, expected_application_layer = expected_layers_from_document_type(
        document_type=document_type
    )

    if expected_retrieval_layer is not None:
        current_retrieval_layer = payload.get("retrieval_layer")

        if current_retrieval_layer != expected_retrieval_layer:
            changes.append(
                {
                    "field": "payload.retrieval_layer",
                    "old_value": current_retrieval_layer,
                    "new_value": expected_retrieval_layer,
                    "reason": (
                        f"document_type='{document_type}' requiere "
                        f"retrieval_layer='{expected_retrieval_layer}'"
                    ),
                }
            )

            payload["retrieval_layer"] = expected_retrieval_layer

    if expected_application_layer is not None:
        current_application_layer = payload.get("application_layer")

        if current_application_layer != expected_application_layer:
            changes.append(
                {
                    "field": "payload.application_layer",
                    "old_value": current_application_layer,
                    "new_value": expected_application_layer,
                    "reason": (
                        f"document_type='{document_type}' requiere "
                        f"application_layer={expected_application_layer}"
                    ),
                }
            )

            payload["application_layer"] = expected_application_layer

    normalize_related_protocols(
        payload=payload,
        file_path=file_path,
        changes=changes,
    )

    normalize_representation_type(
        payload=payload,
        changes=changes,
    )

    normalize_risk_category(
        chunk=normalized_chunk,
        payload=payload,
        file_path=file_path,
        changes=changes,
    )

    return normalized_chunk, changes


# ============================================================
# BACKUP
# ============================================================

def create_backup(chunks_dir: Path, backup_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"chunks_backup_layers_{timestamp}"

    backup_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(chunks_dir, backup_path)

    return backup_path


# ============================================================
# PROCESAMIENTO
# ============================================================

def process_file(file_path: Path, apply_changes: bool) -> Dict[str, Any]:
    original_data = load_json(file_path)
    chunks = get_chunks(original_data)

    normalized_chunks = []
    file_changes = []

    for index, chunk in enumerate(chunks):
        chunk_id = chunk.get("id", f"unknown_index_{index}")

        normalized_chunk, changes = normalize_chunk_layers(
            chunk=chunk,
            file_path=file_path,
        )

        normalized_chunks.append(normalized_chunk)

        if changes:
            file_changes.append(
                {
                    "chunk_index": index,
                    "chunk_id": chunk_id,
                    "changes": changes,
                }
            )

    if apply_changes and file_changes:
        output_data = set_chunks(original_data, normalized_chunks)
        save_json(file_path, output_data)

    return {
        "file": str(file_path),
        "chunks_checked": len(chunks),
        "chunks_modified": len(file_changes),
        "changes": file_changes,
    }


def normalize_directory(
    chunks_dir: Path,
    reports_dir: Path,
    backup_dir: Path,
    apply_changes: bool,
) -> Dict[str, Any]:

    if not chunks_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta de chunks: {chunks_dir}")

    json_files = sorted(
        path for path in chunks_dir.rglob("*.json")
        if is_valid_chunk_file(path)
    )

    backup_path = None

    if apply_changes:
        backup_path = create_backup(chunks_dir, backup_dir)

    files_report = []
    total_chunks_checked = 0
    total_chunks_modified = 0
    total_field_changes = 0

    for file_path in json_files:
        file_report = process_file(
            file_path=file_path,
            apply_changes=apply_changes,
        )

        files_report.append(file_report)

        total_chunks_checked += file_report["chunks_checked"]
        total_chunks_modified += file_report["chunks_modified"]

        for chunk_change in file_report["changes"]:
            total_field_changes += len(chunk_change["changes"])

    report = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "apply" if apply_changes else "dry_run",
        "chunks_dir": str(chunks_dir),
        "backup_path": str(backup_path) if backup_path else None,
        "files_checked": len(json_files),
        "chunks_checked": total_chunks_checked,
        "chunks_modified": total_chunks_modified,
        "field_changes": total_field_changes,
        "files": files_report,
    }

    reports_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = reports_dir / f"fill_layers_related_protocols_risk_report_{timestamp}.json"

    save_json(report_path, report)

    report["report_path"] = str(report_path)

    return report


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rellena retrieval_layer, application_layer, related_protocols, "
            "representation_type y risk_category en chunks JSON."
        )
    )

    parser.add_argument(
        "--chunks-dir",
        type=Path,
        default=DEFAULT_CHUNKS_DIR,
        help="Carpeta donde están los JSON de chunks.",
    )

    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=DEFAULT_REPORTS_DIR,
        help="Carpeta donde se guardará el informe.",
    )

    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=DEFAULT_BACKUP_DIR,
        help="Carpeta donde se guardará el backup.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica los cambios. Si no se usa, solo hace dry-run.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    report = normalize_directory(
        chunks_dir=args.chunks_dir,
        reports_dir=args.reports_dir,
        backup_dir=args.backup_dir,
        apply_changes=args.apply,
    )

    print("\n================ FILL CHUNK METADATA ================")
    print(f"Modo: {report['mode']}")
    print(f"Archivos revisados: {report['files_checked']}")
    print(f"Chunks revisados: {report['chunks_checked']}")
    print(f"Chunks modificados: {report['chunks_modified']}")
    print(f"Cambios de campos: {report['field_changes']}")
    print(f"Informe generado en: {report['report_path']}")

    if report["backup_path"]:
        print(f"Backup creado en: {report['backup_path']}")

    if report["mode"] == "dry_run":
        print("\nNo se ha modificado ningún archivo.")
        print("Para aplicar los cambios ejecuta:")
        print("python src/ingestion/llenar_chunks_correct.py --apply")

    print("=====================================================\n")


if __name__ == "__main__":
    main()