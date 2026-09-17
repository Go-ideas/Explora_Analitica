from __future__ import annotations

from dataclasses import dataclass

from src.analytics_core.result_identity import stable_json


@dataclass(frozen=True)
class LegacyIdentityBridge:
    question_id: str
    structure_ref: str
    structure_type: str
    # canonical identity -> physical variable and raw code (None for column-per-option RM)
    rows: tuple[tuple[str, str, str | None], ...]
    banner_members: tuple[tuple[str, str, str, str], ...] = ()
    provenance_refs: tuple[str, ...] = ()

    @property
    def identity(self) -> str:
        return stable_json(self)

    def validate(self) -> None:
        if not self.question_id or not self.structure_ref or not self.provenance_refs:
            raise ValueError("Missing stable identity/provenance in Legacy bridge")
        if self.structure_type not in {"RU", "RM"}:
            raise ValueError("Unsupported Legacy bridge scope")
        ids = [row[0] for row in self.rows]
        physical = [(row[1], row[2]) for row in self.rows]
        if not ids or any(not row[0] or not row[1] for row in self.rows):
            raise ValueError("Missing stable row identity")
        if len(set(ids)) != len(ids) or len(set(physical)) != len(physical):
            raise ValueError("Duplicate/conflicting Legacy identity mapping")
        if self.structure_type == "RU" and any(row[2] is None for row in self.rows):
            raise ValueError("RU bridge requires raw category identity")
        if self.structure_type == "RM" and any(row[2] is not None for row in self.rows):
            raise ValueError("RM bridge supports column-per-option identity only")
        members = [(row[0], row[1]) for row in self.banner_members]
        sources = [(row[2], row[3]) for row in self.banner_members]
        if any(not all(row) for row in self.banner_members) or len(set(members)) != len(members) or len(set(sources)) != len(sources):
            raise ValueError("Duplicate/conflicting banner identity mapping")
