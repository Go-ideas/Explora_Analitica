from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

from src.operator_console import (
    OPERATOR_CONSOLE_VERSION,
    OperatorConsoleError,
    analyze_source_inputs,
    author_execution_release_draft,
    author_project_spec_draft,
    build_structure_review,
    approve_execution_release,
    archive_directory,
    build_package,
    cleanup_workspace,
    create_workspace,
    decision_rows,
    execution_targets,
    finalize_structure_review,
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

    upload_tab, review_tab, spec_tab, decision_tab, package_tab, execute_tab, trace_tab = st.tabs(
        ["1. Proyecto", "2. Revisión", "3. Project Spec", "4. Decisiones", "5. Package", "6. Ejecutar", "7. Trazabilidad"]
    )

    with upload_tab:
        st.subheader("Archivos del proyecto")
        st.info(
            "Carga lo que tengas. EXPLORA puede analizar determinísticamente la metadata del SAV y usar el cuestionario DOCX como evidencia. "
            "Las clasificaciones detectadas son candidatos y no se convierten en Project Spec sin revisión."
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
            project_upload = st.file_uploader(
                "Importar Project Spec existente (opción avanzada, .json)",
                type=["json"],
                key="operator_project",
            )
            project_spec = _activate_json("project_spec", project_upload, role="project_spec")
            _artifact_line("Project Spec", st.session_state.get("project_spec_artifact"))

            release_upload = st.file_uploader(
                "Importar Execution Release existente (opción avanzada, .json)",
                type=["json"],
                key="operator_release",
            )
            execution_release = _activate_json("execution_release", release_upload, role="execution_release")
            _artifact_line("Execution Release", st.session_state.get("execution_release_artifact"))

        st.divider()
        st.subheader("Analizar fuentes")
        can_analyze = dataset is not None
        if st.button(
            "Analizar archivos cargados",
            type="primary",
            disabled=not can_analyze,
            help="Lee metadata SPSS y evidencia textual del cuestionario. No calcula resultados analíticos.",
        ):
            try:
                analysis = analyze_source_inputs(
                    dataset.stored_path,
                    questionnaire_path=None if questionnaire is None else questionnaire.stored_path,
                    datamap_path=None if datamap is None else datamap.stored_path,
                )
                st.session_state.source_analysis = analysis
                st.session_state.pop("structure_review", None)
                st.success("Análisis de fuentes completado. Revisa candidatos antes de generar configuración.")
            except OperatorConsoleError as exc:
                st.error(str(exc))

        analysis = st.session_state.get("source_analysis")
        if analysis:
            metrics = st.columns(6)
            metrics[0].metric("Casos", f"{analysis['dataset']['n_cases']:,}")
            metrics[1].metric("Variables", f"{analysis['dataset']['n_variables']:,}")
            metrics[2].metric("RM candidatos", len(analysis["rm_group_candidates"]))
            metrics[3].metric("Loop candidatos", len(analysis.get("loop_group_candidates", [])))
            metrics[4].metric("Grid candidatos", len(analysis.get("grid_group_candidates", [])))
            metrics[5].metric("Pesos candidatos", len(analysis["weight_candidates"]))

            if analysis["id_candidates"]:
                st.caption("ID únicos candidatos: " + ", ".join(analysis["id_candidates"]))
            if analysis.get("id_signal_candidates"):
                st.caption(
                    "Señales de identidad para revisión: "
                    + ", ".join(
                        f"{item['variable']} ({item['uniqueness_ratio']:.1%} únicos)"
                        for item in analysis["id_signal_candidates"]
                    )
                )
            if analysis["weight_candidates"]:
                st.caption("Candidatos a ponderador: " + ", ".join(analysis["weight_candidates"]))

            group_sections = [
                ("Grupos RM candidatos — requieren revisión", analysis["rm_group_candidates"]),
                ("Repeticiones LOOP candidatas — no tratar como RM", analysis.get("loop_group_candidates", [])),
                ("Filas GRID candidatas — fuera del perfil cualificado actual", analysis.get("grid_group_candidates", [])),
            ]
            for title, items in group_sections:
                if items:
                    st.markdown(f"**{title}**")
                    rows = [
                        {
                            "grupo": item["group"],
                            "n_variables": len(item["variables"]),
                            "variables": ", ".join(item["variables"]),
                            "autoridad": item["authority"],
                        }
                        for item in items
                    ]
                    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

            st.markdown("**Inventario de variables y evidencia**")
            variable_rows = [
                {
                    "variable": item["variable"],
                    "label": item["label"],
                    "tipo": item["data_type"],
                    "value_labels": item["value_label_count"],
                    "match_cuestionario": item["questionnaire_exact_matches"],
                    "candidato": item["candidate_role"],
                    "autoridad": item["authority"],
                }
                for item in analysis["variables"]
            ]
            st.dataframe(pd.DataFrame(variable_rows), width="stretch", hide_index=True, height=420)

            questionnaire_info = analysis["questionnaire"]
            if questionnaire_info["filename"]:
                st.caption(
                    f"Cuestionario: {questionnaire_info['paragraphs_extracted']} párrafos extraídos · "
                    f"{questionnaire_info['variables_with_exact_questionnaire_match']} variables con match exacto."
                )
            st.download_button(
                "Descargar análisis de fuentes",
                data=json.dumps(analysis, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
                file_name="explora_source_analysis.json",
                mime="application/json",
            )
            st.warning(
                "Este análisis todavía NO es Project Spec. El siguiente módulo convertirá los candidatos revisados "
                "en decisiones estructuradas y dejará cualquier ambigüedad como HUMAN_DECISION_REQUIRED."
            )

        if analysis:
            st.markdown("**Siguiente paso: revisión humana de estructuras**")
            if st.button("Preparar revisión de estructuras", key="prepare_structure_review"):
                st.session_state.structure_review = build_structure_review(analysis)
                st.success("Revisión preparada. Abre la pestaña 2. Revisión.")
                st.rerun()

        if project_spec:
            summary = intake_summary(project_spec)
            st.divider()
            cols = st.columns(4)
            cols[0].metric("Project", summary.get("project_id") or "—")
            cols[1].metric("Project Spec", summary["status"])
            cols[2].metric("Targets", " + ".join(execution_targets(project_spec)) or "NONE")
            cols[3].metric("Fingerprint", summary["fingerprint"][:12] + "…")

    with review_tab:
        analysis = st.session_state.get("source_analysis")
        if not analysis:
            st.warning("Primero ejecuta Analizar archivos cargados en la pestaña Proyecto.")
        else:
            review = st.session_state.get("structure_review")
            if review is None:
                st.info(
                    "El análisis de fuentes ya existe. Prepara la revisión para convertir candidatos "
                    "en decisiones humanas explícitas."
                )
                if st.button("Preparar revisión", type="primary", key="prepare_review_tab"):
                    st.session_state.structure_review = build_structure_review(analysis)
                    st.rerun()
            else:
                st.subheader("Revisión de estructuras y roles")
                st.caption(
                    "Nada se convierte en Project Spec desde esta tabla hasta que exista una decisión humana. "
                    "RU, RM, LOOP_RU y LOOP_NUMERICO están cualificados. LOOP_RM, GRID y NUMERIC "
                    "independiente permanecen fuera del perfil; significancia LOOP continúa fail-closed."
                )
                summary = review.get("summary", {})
                m = st.columns(5)
                m[0].metric("Items", summary.get("total_items", 0))
                m[1].metric("Pendientes", summary.get("pending_items", 0))
                m[2].metric("Aprobados", summary.get("approved_items", 0))
                m[3].metric("Excluidos", summary.get("excluded_items", 0))
                m[4].metric("Estado", review.get("status", "—"))

                rows = []
                for item in review["items"]:
                    rows.append(
                        {
                            "item_id": item["item_id"],
                            "variables": ", ".join(item["variables"]),
                            "propuesta": item["proposed_type"],
                            "confianza": item["proposal_confidence"],
                            "capacidad": item["capability_status"],
                            "estado": item["review_state"],
                            "tipo_final": item["final_type"],
                            "nota_humana": item.get("human_note", ""),
                            "evidencia": " | ".join(item.get("evidence", [])),
                        }
                    )
                edited = st.data_editor(
                    pd.DataFrame(rows),
                    width="stretch",
                    hide_index=True,
                    disabled=[
                        "item_id", "variables", "propuesta", "confianza",
                        "capacidad", "evidencia",
                    ],
                    column_config={
                        "estado": st.column_config.SelectboxColumn(
                            "estado",
                            options=["PENDING", "APPROVED", "EXCLUDED"],
                            required=True,
                        ),
                        "tipo_final": st.column_config.SelectboxColumn(
                            "tipo_final",
                            options=[
                                "RU", "RM", "NUMERIC", "SCALE", "GRID_ESCALA", "GRID_RM",
                                "LOOP_RU", "LOOP_RM", "LOOP_NUMERICO",
                                "RESPONDENT_ID", "WEIGHT", "META_CONTROL", "UNCLASSIFIED",
                            ],
                            required=True,
                        ),
                    },
                    key="structure_review_editor",
                    height=520,
                )
                if st.button("Guardar revisión humana", type="primary"):
                    decisions = [
                        {
                            "item_id": row["item_id"],
                            "review_state": row["estado"],
                            "final_type": row["tipo_final"],
                            "human_note": row["nota_humana"],
                        }
                        for row in edited.to_dict("records")
                    ]
                    try:
                        st.session_state.structure_review = finalize_structure_review(
                            review, decisions
                        )
                        st.success("Revisión guardada.")
                        st.rerun()
                    except OperatorConsoleError as exc:
                        st.error(str(exc))

                review = st.session_state.get("structure_review", review)
                gaps = review.get("summary", {}).get("capability_gaps", [])
                if review.get("status") == "NEEDS_HUMAN_DECISION":
                    st.warning("Aún existen decisiones pendientes.")
                elif review.get("status") == "CAPABILITY_GAP":
                    st.error(
                        "La revisión está completa, pero incluye estructuras no cualificadas por el perfil vigente. "
                        "Puedes excluirlas para un alcance parcial o abrir un milestone de capacidad."
                    )
                    if gaps:
                        st.dataframe(pd.DataFrame(gaps), width="stretch", hide_index=True)
                elif review.get("status") == "READY_FOR_PROJECT_SPEC_DRAFT":
                    st.success(
                        "Revisión completa y compatible con el perfil actual. "
                        "Continúa en la pestaña Project Spec para generar el Project Spec Draft."
                    )

                st.download_button(
                    "Descargar revisión de estructuras",
                    data=json.dumps(review, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
                    file_name="explora_structure_review.json",
                    mime="application/json",
                )

    with spec_tab:
        analysis = st.session_state.get("source_analysis")
        review = st.session_state.get("structure_review")
        if analysis and review and review.get("status") == "READY_FOR_PROJECT_SPEC_DRAFT":
            st.subheader("Generar Project Spec Draft")
            with st.form("project_spec_draft_form"):
                left, right = st.columns(2)
                project_id = left.text_input("Project ID")
                display_name = right.text_input("Display name")
                project_version = left.text_input("Project version", value="1.0.0")
                spec_version = right.text_input("Spec version", value="1.0.0")
                generate_draft = st.form_submit_button(
                    "Generar Project Spec Draft",
                    type="primary",
                )
            if generate_draft:
                result = author_project_spec_draft(
                    analysis,
                    review,
                    {
                        "project_id": project_id,
                        "display_name": display_name,
                        "project_version": project_version,
                        "spec_version": spec_version,
                    },
                )
                st.session_state.project_spec_draft_result = result
                if result.status == "DRAFT_VALID" and result.project_spec is not None:
                    st.session_state.project_spec = result.project_spec

        draft_result = st.session_state.get("project_spec_draft_result")
        if draft_result is not None:
            metrics = st.columns(4)
            metrics[0].metric("Draft", draft_result.status)
            metrics[1].metric("Errores", len(draft_result.errors))
            metrics[2].metric("Warnings", len(draft_result.warnings))
            metrics[3].metric(
                "Fingerprint",
                (draft_result.project_spec_fingerprint or "—")[:12],
            )
            if draft_result.errors:
                st.dataframe(pd.DataFrame(draft_result.errors), width="stretch", hide_index=True)
            if draft_result.ambiguities:
                st.dataframe(pd.DataFrame(draft_result.ambiguities), width="stretch", hide_index=True)
            if draft_result.project_spec is not None:
                st.download_button(
                    "Descargar Project Spec Draft",
                    data=json.dumps(
                        draft_result.project_spec,
                        ensure_ascii=False,
                        indent=2,
                    ).encode("utf-8"),
                    file_name="explora_project_spec_draft.json",
                    mime="application/json",
                )

        project_spec = st.session_state.get("project_spec")
        if not project_spec:
            st.warning("Completa la revisión para generar un draft o importa un Project Spec existente.")
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
            intake = intake_summary(project_spec)
            dataset = st.session_state.get("dataset_artifact")
            questionnaire = st.session_state.get("questionnaire_artifact")
            datamap = st.session_state.get("datamap_artifact")
            if intake["ready"]:
                st.subheader("Generar Execution Release Draft")
                if dataset is None or questionnaire is None:
                    st.warning("Dataset y cuestionario con fingerprint son necesarios para autorizar el draft.")
                else:
                    with st.form("execution_release_draft_form"):
                        left, right = st.columns(2)
                        release_spec_id = left.text_input("Release Spec ID")
                        release_spec_version = right.text_input("Release Spec version", value="1.0.0")
                        package_id = left.text_input("Package ID")
                        package_version = right.text_input("Package version", value="1.0.0")
                        dataset_version = left.text_input("Dataset version", value="1.0.0")
                        internal_project_name = right.text_input("Internal project name")
                        generate_release = st.form_submit_button("Generar Execution Release Draft", type="primary")
                    if generate_release:
                        result = author_execution_release_draft(
                            project_spec,
                            {
                                "dataset_filename": dataset.original_name,
                                "dataset_sha256": dataset.sha256,
                                "questionnaire_filename": questionnaire.original_name,
                                "questionnaire_sha256": questionnaire.sha256,
                                "datamap_ref": "NONE" if datamap is None else f"sha256:{datamap.sha256}",
                            },
                            {
                                "release_spec_id": release_spec_id,
                                "release_spec_version": release_spec_version,
                                "package_id": package_id,
                                "package_version": package_version,
                                "dataset_version": dataset_version,
                                "internal_project_name": internal_project_name,
                            },
                        )
                        st.session_state.execution_release_draft_result = result
                        if result.status == "ER_DRAFT_VALID":
                            st.session_state.execution_release = result.execution_release
                            st.session_state.pop("approved_execution_release", None)
                            st.rerun()
            release_result = st.session_state.get("execution_release_draft_result")
            if release_result is not None:
                cols = st.columns(4)
                cols[0].metric("ER Draft", release_result.status)
                cols[1].metric("Errores", len(release_result.errors))
                cols[2].metric("B3", release_result.b3_status)
                cols[3].metric("Fingerprint", (release_result.execution_release_fingerprint or "—")[:12])
                if release_result.errors:
                    st.dataframe(pd.DataFrame(release_result.errors), width="stretch", hide_index=True)
                if release_result.execution_release is not None:
                    st.download_button(
                        "Descargar Execution Release Draft",
                        data=json.dumps(release_result.execution_release, ensure_ascii=False, indent=2).encode("utf-8"),
                        file_name="execution_release_draft.json",
                        mime="application/json",
                    )
            execution_release = st.session_state.get("approved_execution_release") or st.session_state.get("execution_release")
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
