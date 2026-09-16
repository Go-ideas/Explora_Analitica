from __future__ import annotations

from dataclasses import replace

from src.web_canonical.models import CanonicalWebProjection


class CanonicalExportReleaseError(PermissionError):
    pass


def official_released_export_bytes(
    projection: CanonicalWebProjection,
) -> bytes:
    if not bool(projection.release.get("releasable")):
        raise CanonicalExportReleaseError(
            "Official released export requires releasable=true."
        )
    return _projection_csv_bytes(
        projection,
        export_path="OFFICIAL_RELEASED_EXPORT",
    )


def internal_qa_export_bytes(
    projection: CanonicalWebProjection,
) -> bytes:
    return _projection_csv_bytes(
        projection,
        export_path="INTERNAL_QA_EXPORT",
    )


def _projection_csv_bytes(
    projection: CanonicalWebProjection,
    *,
    export_path: str,
) -> bytes:
    table = projection.table.copy()
    table.insert(0, "export_path", export_path)
    table.insert(1, "release_releasable", projection.release.get("releasable"))
    table.insert(
        2,
        "qa_release_status",
        projection.release.get("qa_release_status"),
    )
    return table.to_csv(index=False).encode("utf-8")
