"""Deterministic questionnaire order evidence; never analytical or human authority."""
from copy import deepcopy
import re
from typing import Any, Mapping

# Require letters followed by digits; bare narrative numbers are not identities.
_TOKEN = r"[A-Za-z]{1,12}[._-]?\d{1,6}[A-Za-z]?"
_HEADER = re.compile(rf"^\s*({_TOKEN})(?=$|[\s.):?\-])", re.IGNORECASE)
_LABEL = re.compile(rf"(?<![A-Za-z0-9_])({_TOKEN})(?![A-Za-z0-9_])", re.IGNORECASE)


def normalized_question_ref(token: str) -> str | None:
    if not re.fullmatch(_TOKEN, token):
        return None
    return re.sub(r"[._-]", "", token).upper()


def questionnaire_sequence(paragraphs: list[str]) -> list[dict[str, Any]]:
    sequence = []
    for index, text in enumerate(paragraphs):
        match = _HEADER.match(text)
        if match:
            sequence.append({"question_ref": normalized_question_ref(match[1]), "paragraph_index": index, "source_text": text[:240]})
    return sequence


def exact_questionnaire_positions(variable: str, paragraphs: list[str]) -> list[dict[str, Any]]:
    pattern = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(variable)}(?![A-Za-z0-9_])", re.IGNORECASE)
    positions = []
    for index, text in enumerate(paragraphs):
        if pattern.search(text):
            header = _HEADER.match(text)
            positions.append({"question_ref": normalized_question_ref(header[1]) if header else normalized_question_ref(variable) or variable.casefold(), "paragraph_index": index})
    return positions


def _unique_position(candidates):
    refs = {ref for ref, _ in candidates}
    if len(refs) != 1:
        return None
    return next(iter(refs)), min(index for _, index in candidates)


def review_editor_items(review: Mapping[str, Any], analysis: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return ordered copies with presentation evidence; preserve the stored review."""
    questionnaire = analysis.get("questionnaire", {}) or {}
    sequence = questionnaire.get("question_sequence", [])
    if questionnaire.get("format_supported_for_text_evidence") is False:
        sequence = []
    by_ref: dict[str, list[int]] = {}
    for entry in sequence:
        by_ref.setdefault(entry["question_ref"], []).append(entry["paragraph_index"])
    variables = {row["variable"]: row for row in analysis.get("variables", [])}
    ordered = []
    for detection_index, original in enumerate(review.get("items", [])):
        item = deepcopy(original)
        family, _, name = item["item_id"].partition("::")
        candidates = []
        if by_ref:
            if family in {"LOOP", "RM", "GRID"}:
                parent = normalized_question_ref(name)
                candidates = [(parent, index) for index in by_ref.get(parent, [])]
            else:
                row = variables.get(name, {})
                exact = row.get("questionnaire_exact_positions", [])
                if exact:
                    candidates = [(entry["question_ref"], entry["paragraph_index"]) for entry in exact]
                else:
                    # Compatibility with older Source Analysis containing bounded text only.
                    refs = {normalized_question_ref(name)} if row.get("questionnaire_exact_matches", 0) else set()
                    if not any(ref in by_ref for ref in refs):
                        refs = {normalized_question_ref(match[1]) for match in _LABEL.finditer(row.get("label", ""))}
                    candidates = [(ref, index) for ref in refs for index in by_ref.get(ref, [])]
        position = _unique_position(candidates)
        item["questionnaire_order_key"] = position[1] if position else None
        item["questionnaire_question_ref"] = position[0] if position else None
        item["questionnaire_order_status"] = "MAPPED" if position else "UNRESOLVED" if candidates else "UNMAPPED"
        # A group wins a shared position; otherwise preserve original detection order.
        key = (position is None, position[1] if position else 0, (0 if family in {"LOOP", "RM", "GRID"} else 1) if position else 0, detection_index, item["item_id"])
        ordered.append((key, item))
    return [item for _, item in sorted(ordered, key=lambda pair: pair[0])]
