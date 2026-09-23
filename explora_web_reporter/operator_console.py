from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

from src.operator_console import (
    OPERATOR_CONSOLE_VERSION,
    OperatorConsoleError,
    approve_execution_release,
    archive_directory,
    build_package,
    cleanup_workspace,
    create_workspace,
    decision_rows,
    execution_targets,
    intake_summary,
    parse_json_upload,
    release_summary,
    run_web_project,
    save_upload,
    web_execution_readiness,
)


st.set_page_config(
    page_title="EXPLORA Operator Console",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _workspace():
    session_id = st.session_state.setdefault("operator_session_id", uuid4().hex)
    return create_workspace(session_id)


def _activate_upload(key: str, upload, *, role: str, allowed_suffixes=None):
    if upload is None:
        return st.session_state.get(key)
    content = upload.getvalue()
    fingerprint = __import__("hashlib").sha256(content).hexdigest()
    marker = f"{key}_fingerprint"
    if st.session_state.get(marker) == fingerprint and key in st.session_state:
        return st.session_state[key]
    artifact = save_upload(
        _workspace(),
        role=role,
        filename=upload.name,
        content=content,
        allowed_suffixes=allowed_suffixes,
    )
    st.session_state[key] = artifact
    st.session_state[marker] = fingerprint
    for downstream in ("package_evidence", "release_path", "release_summary", "release_zip"):
        st.session_state.pop(downstream, None)
    return artifact


def _activate_json(key: str, upload, *, role: str):
    artifact = _activate_upload(key + "_artifact", upload, role=role, allowed_suffixes={".json"})
    if upload is None:
        return st.session_state.get(key)
    content = upload.getvalue()
    fingerprint = __import__("hashlib").sha256(content).hexdigest()
    marker = f"{key}_json_fingerprint"
    if st.session_state.get(marker) != fingerprint:
        st.session_state[key] = parse_json_upload(content, label=role)
        st.session_state[marker] = fingerprint
        if key == "execution_release":
            st.session_state.pop("approved_execution_release", None)
    return st.session_state.get(key)


def _artifact_line(label: str, artifact) -> None:
    if artifact is None:
        st.caption(f"{label}: pendiente")
        return
    st.success(f"{label}: cargado")
    st.caption(f"{artifact.original_name} · SHA-256 {artifact.sha256[:16]}… · {artifact.size_bytes:,} bytes")


def _status_metric(label: str, value: str) -> None:
    st.metric(label, value)


def _clear() -> None:
    workspace = _workspace()
    cleanup_workspace(workspace)
    st.session_state.clear()


def main() -> None:
    _styles()
    workspace = _workspace()

    with st.sidebar:
        st.markdown("## EXPLORA")
        st.caption("OPERATOR CONSOLE")
        st.caption(OPERATOR_CONSOLE_VERSION)
        st.divider()
        st.caption("Sesión temporal")
        st.code(workspace.session_id[:12], language=None)
        st.caption("Los archivos de cliente permanecen en almacenamiento temporal de la sesión; nunca se escriben en Git.")
        if st.button("Limpiar sesión", width="stretch"):
            _clear()
            st.rerun()

    st.title("EXPLORA Operator Console")
    st.caption("Project Spec → Execution Release → RELEASED Package → CANONICAL_V1 → Web")
    st.warning("Para datos reales de clientes, despliega esta consola como app PRIVADA en Streamlit Community Cloud.")

    upload_tab, spec_tab, decision_tab, package_tab, execute_tab, trace_tab = st.tabs(
        ["1. Proyecto", "2. Project Spec", "3. Decisiones", "4. Package", "5. Ejecutar", "6. Trazabilidad"]
    )

    with upload_tab:
        st.subheader("Archivos del proyecto")
        st.info(
            "La consola no interpreta automáticamente el cuestionario ni el datamap en esta versión. "
            "Se conservan como evidencia de fuente; el Project Spec sigue siendo la configuración analítica aprobada."
        )
        left, right = st.columns(2)
        with left:
            sav = st.file_uploader("Base SPSS (.sav)", type=["sav"], key="operator_sav")
            dataset = _activate_upload("dataset_artifact", sav, role="dataset", allowed_suffixes={".sav"})
            _artifact_line("Dataset", dataset)

            questionnaire_upload = st.file_uploader(
                "Cuestionario (evidencia opcional)", type=["pdf", "docx", "xlsx"], key="operator_questionnaire"
            )
            questionnaire = _activate_upload(
                "questionnaire_artifact",
                questionnaire_upload,
                role="questionnaire",
                allowed_suffixes={".pdf", ".docx", ".xlsx"},
            )
            _artifact_line("Cuestionario", questionnaire)

            datamap_upload = st.file_uploader(
                "Datamap (evidencia opcional)", type=["xlsx", "xls", "csv"], key="operator_datamap"
            )
            datamap = _activate_upload(
                "datamap_artifact",
                datamap_upload,
                role="datamap",
                allowed_suffixes={".xlsx", ".xls", ".csv"},
            )
            _artifact_line("Datamap", datamap)

        with right:
            project_upload = st.file_uploader("EXPLORA_PROJECT_SPEC_V1 (.json)", type=["json"], key="operator_project")
            project_spec = _activate_json("project_spec", project_upload, role="project_spec")
            _artifact_line("Project Spec", st.session_state.get("project_spec_artifact"))

            release_upload = st.file_uploader(
                "EXPLORA_PROJECT_EXECUTION_RELEASE_V1 (.json)",
                type=["json"],
                key="operator_release",
            )
            execution_release = _activate_json("execution_release", release_upload, role="execution_release")
            _artifact_line("Execution Release", st.session_state.get("execution_release_artifact"))

        if project_spec:
            summary = intake_summary(project_spec)
            st.divider()
            cols = st.columns(4)
            cols[0].metric("Project", summary.get("project_id") or "—")
            cols[1].metric("Project Spec", summary["status"])
            cols[2].metric("Targets", " + ".join(execution_targets(project_spec)) or "NONE")
            cols[3].metric("Fingerprint", summary["fingerprint"][:12] + "…")

    with spec_tab:
        project_spec = st.session_state.get("project_spec")
        if not project_spec:
            st.warning("Carga un Project Spec.")
        else:
            summary = intake_summary(project_spec)
            c1, c2, c3 = st.columns(3)
            c1.metric("Estado", summary["status"])
            c2.metric("Errores", len(summary["errors"]))
            c3.metric("Warnings", len(summary["warnings"]))
            if summary["ready"]:
                st.success("Project Spec READY_FOR_EXECUTION")
            else:
                st.error("Project Spec todavía no puede ejecutarse.")
            if summary["errors"]:
                st.dataframe(pd.DataFrame(summary["errors"]), width="stretch", hide_index=True)
            if summary["warnings"]:
                st.dataframe(pd.DataFrame(summary["warnings"]), width="stretch", hide_index=True)
            with st.expander("Project Spec JSON"):
                st.json(project_spec)

    with decision_tab:
        project_spec = st.session_state.get("project_spec")
        execution_release = st.session_state.get("approved_execution_release") or st.session_state.get("execution_release")
        if not project_spec:
            st.warning("Carga un Project Spec.")
        else:
            rows = decision_rows(project_spec, execution_release)
            if rows:
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
            else:
                st.success("No hay decisiones registradas.")

        draft = st.session_state.get("execution_release")
        if draft is not None:
            current = st.session_state.get("approved_execution_release") or draft
            release_state = release_summary(project_spec, current) if project_spec else {"status": "WAITING_PROJECT_SPEC", "ready": False}
            st.subheader("B3 Human Release")
            st.info(f"Estado: {release_state['status']}")
            if not release_state.get("ready"):
                with st.form("b3_release_form"):
                    decision_id = st.text_input("Human decision ID", value="HUMAN_RELEASE_001")
                    basis = st.text_area("Base de la decisión", placeholder="Revisé Project Spec, estructuras, métricas, pesos y requests.")
                    confirm = st.checkbox("Confirmo que esta aprobación es una decisión humana de release.")
                    submitted = st.form_submit_button("Aprobar Execution Release", type="primary")
                if submitted:
                    if not confirm:
                        st.error("Se requiere confirmación explícita.")
                    else:
                        try:
                            approved = approve_execution_release(
                                draft,
                                decision_id=decision_id,
                                decision_basis=basis,
                            )
                            if project_spec:
                                check = release_summary(project_spec, approved)
                                if not check["ready"]:
                                    st.error(check.get("error") or "Execution Release inválido.")
                                else:
                                    st.session_state.approved_execution_release = approved
                                    st.success("B3 aprobado para esta sesión.")
                                    st.rerun()
                        except OperatorConsoleError as exc:
                            st.error(str(exc))
            else:
                st.success("Execution Release aprobado y válido.")
                approved = st.session_state.get("approved_execution_release") or draft
                st.download_button(
                    "Descargar Execution Release aprobado",
                    data=json.dumps(approved, ensure_ascii=False, indent=2).encode("utf-8"),
                    file_name="execution_release_approved.json",
                    mime="application/json",
                )

    with package_tab:
        project_spec = st.session_state.get("project_spec")
        execution_release = st.session_state.get("approved_execution_release") or st.session_state.get("execution_release")
        dataset = st.session_state.get("dataset_artifact")
        if not (project_spec and execution_release and dataset):
            st.warning("Se requieren dataset, Project Spec y Execution Release.")
        else:
            intake = intake_summary(project_spec)
            release_state = release_summary(project_spec, execution_release)
            c1, c2 = st.columns(2)
            c1.metric("Project Spec", intake["status"])
            c2.metric("Execution Release", release_state["status"])
            can_build = intake["ready"] and release_state["ready"]
            if st.button("Construir RELEASED Package", type="primary", disabled=not can_build):
                try:
                    evidence = build_package(
                        workspace,
                        project_spec=project_spec,
                        execution_release=execution_release,
                        source_path=dataset.stored_path,
                    )
                    st.session_state.package_evidence = evidence
                    st.success("Package generado y validado por el loader canónico.")
                except Exception as exc:
                    st.error(f"Package bloqueado: {exc}")
            evidence = st.session_state.get("package_evidence")
            if evidence:
                st.json(
                    {
                        "package_sha256": evidence.package_sha256,
                        "package_spec_hash": evidence.package_spec_hash,
                        "project_spec_fingerprint": evidence.project_spec_fingerprint,
                        "file_count": evidence.file_count,
                        "loader_roundtrip": evidence.loader_roundtrip,
                        "deterministic_zip": evidence.deterministic_zip,
                    }
                )
                st.download_button(
                    "Descargar RELEASED Package",
                    data=Path(evidence.package_path).read_bytes(),
                    file_name=Path(evidence.package_path).name,
                    mime="application/zip",
                )

    with execute_tab:
        project_spec = st.session_state.get("project_spec")
        execution_release = st.session_state.get("approved_execution_release") or st.session_state.get("execution_release")
        dataset = st.session_state.get("dataset_artifact")
        package = st.session_state.get("package_evidence")
        if not (project_spec and execution_release and dataset):
            st.warning("Completa las etapas anteriores.")
        else:
            ready, reason = web_execution_readiness(
                project_spec,
                execution_release,
                package_present=bool(package),
            )
            st.info(reason)
            targets = execution_targets(project_spec)
            if "EXCEL" in targets:
                st.warning(
                    "Excel está configurado en este proyecto, pero Operator Console V1 no lo ejecuta todavía. "
                    "La integración con QualifiedMaster se hará sin crear una ruta de cálculo alternativa."
                )
            if st.button("Ejecutar CANONICAL_V1", type="primary", disabled=not ready):
                try:
                    release_path, summary = run_web_project(
                        workspace,
                        project_spec=project_spec,
                        execution_release=execution_release,
                        source_path=dataset.stored_path,
                        package_path=package.package_path,
                    )
                    st.session_state.release_path = release_path
                    st.session_state.release_summary = summary
                    st.session_state.release_zip = archive_directory(release_path)
                    st.success("Ejecución CANONICAL_V1 completada.")
                except OperatorConsoleError as exc:
                    st.error(str(exc))
            if st.session_state.get("release_summary"):
                st.json(st.session_state.release_summary)
                st.download_button(
                    "Descargar release completo",
                    data=st.session_state.release_zip,
                    file_name="explora_canonical_release.zip",
                    mime="application/zip",
                )

    with trace_tab:
        rows = []
        for key, label in (
            ("dataset_artifact", "Dataset"),
            ("questionnaire_artifact", "Questionnaire"),
            ("datamap_artifact", "Datamap"),
            ("project_spec_artifact", "Project Spec"),
            ("execution_release_artifact", "Execution Release"),
        ):
            artifact = st.session_state.get(key)
            if artifact:
                rows.append(
                    {
                        "artifact": label,
                        "filename": artifact.original_name,
                        "sha256": artifact.sha256,
                        "bytes": artifact.size_bytes,
                    }
                )
        if rows:
            st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
        else:
            st.info("Aún no hay artefactos en la sesión.")
        st.caption(
            "La consola presenta y orquesta. Los resultados oficiales siguen siendo producidos por EXPLORA Core / CANONICAL_V1."
        )


def _styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {max-width: 1500px; padding-top: 1.4rem; padding-bottom: 3rem;}
        h1, h2, h3 {color: #17324d;}
        [data-testid="stMetric"] {border: 1px solid #dfe7eb; border-top: 3px solid #176b87; border-radius: 7px; padding: .75rem; background: white;}
        [data-testid="stSidebar"] {border-right: 1px solid #dfe7eb;}
        .stButton > button[kind="primary"]:not(:disabled) {background-color: #176b87; border-color: #176b87;}
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
