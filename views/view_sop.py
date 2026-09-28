# view_sop.py
"""
Module OPERA : Gestion, Versioning et Publication des Procédures Opérationnelles Normalisées (SOP).
Incorpore le moteur de calcul de Delta et la diffusion vers la Main Courante ORBIS.

Auteur : Éric KUTER
Date : 28/09/2026
"""

import datetime
import os
import streamlit as st
from pdf_engines.pdf_sop import creer_pdf_sop
from services.delta_service import comparer_deroulements_json
from services.procedure_service import publier_nouvelle_version_procedure


def afficher_vue_sop(supabase, user_info, est_manager):
    st.subheader("📜 Module Procédures Opérationnelles Normalisées (SOP)")

    if est_manager:
        tab_consult, tab_saisie = st.tabs(
            [
                "📄 Consultation & PDF",
                "🛠️ Saisie & Édition / Publication ORBIS",
            ]
        )
    else:
        tab_consult = st.container()

    # ==========================================
    # 1. CONSULTATION & TÉLÉCHARGEMENT PDF
    # ==========================================
    with tab_consult:
        reponse_sites = supabase.table("opera_sites").select("*").execute()
        sites = reponse_sites.data

        if sites:
            options_sites = {site["nom_site"]: site["id"] for site in sites}
            site_choisi = st.selectbox(
                "📍 Sélectionner le site :",
                options_sites.keys(),
                key="select_site_sop",
            )
            site_id = options_sites[site_choisi]

            procs = (
                supabase.table("opera_procedures")
                .select("*")
                .eq("site_id", site_id)
                .eq("est_actif", True)
                .order("code_doc")
                .execute()
                .data
            )

            if procs:
                for proc in procs:
                    with st.expander(
                        f"📋 [{proc['code_doc']}] {proc['titre']} (v{proc.get('version', '1.0')})",
                        expanded=False,
                    ):
                        st.write(f"**Objectif :** {proc['objectif']}")
                        st.write(
                            "**Domaine d'application :**"
                            f" {proc['domaine_application']}"
                        )
                        st.write(
                            "**Matériel requis :**"
                            f" {proc.get('materiel_requis', 'Aucun')}"
                        )

                        st.markdown("---")
                        st.write("**Déroulement de la procédure :**")
                        deroulement = proc.get("deroulement", [])
                        if isinstance(deroulement, list):
                            for idx, etape in enumerate(deroulement, start=1):
                                txt = (
                                    etape
                                    if isinstance(etape, str)
                                    else etape.get("action", "")
                                )
                                st.write(f"{idx}. {txt}")
                        else:
                            st.write(str(deroulement))

                        if proc.get("points_vigilance"):
                            st.warning(
                                "⚠️ **Points de Vigilance :**"
                                f" {proc['points_vigilance']}"
                            )

                        st.caption(
                            f"Dernière révision : {proc['date_version']} par"
                            f" {proc['redacteur']}"
                        )

                        # Génération PDF
                        pdf_bytes = creer_pdf_sop(proc, site_choisi)
                        st.download_button(
                            label=(f"📄 Télécharger la fiche {proc['code_doc']} (PDF)"),
                            data=pdf_bytes,
                            file_name=f"{proc['code_doc']}_{site_choisi}.pdf",
                            mime="application/pdf",
                            key=f"dl_sop_{proc['id']}",
                        )
            else:
                st.info("Aucune procédure permanente configurée pour ce site.")
        else:
            st.warning("Aucun site enregistré dans la base de données.")

    # ==========================================
    # 2. SAISIE / ÉDITION MANAGER & PUBLICATION DELTA
    # ==========================================
    if est_manager:
        with tab_saisie:
            if sites:
                st.write(
                    "**Espace d'édition, de versioning et de MCO des Procédures (SOP)**"
                )

                mode_action = st.radio(
                    "Action à effectuer :",
                    [
                        "➕ Créer une nouvelle procédure",
                        "✏️ Modifier / Réviser une procédure existante",
                    ],
                    horizontal=True,
                )

                site_rattache = st.selectbox(
                    "Site concerné :",
                    options_sites.keys(),
                    key="select_site_saisie_sop",
                )
                site_id_selectionne = options_sites[site_rattache]

                proc_a_modifier = None
                default_code = ""
                default_titre = ""
                default_version = "1.0"
                default_redacteur = user_info.get(
                    "full_name", user_info.get("nom", "Éric KUTER")
                )
                default_objectif = ""
                default_domaine = ""
                default_materiel = ""
                default_deroulement = ""
                default_vigilance = ""

                if "Modifier" in mode_action:
                    procs_du_site = (
                        supabase.table("opera_procedures")
                        .select("*")
                        .eq("site_id", site_id_selectionne)
                        .order("code_doc")
                        .execute()
                        .data
                    )
                    if procs_du_site:
                        dict_procs = {
                            f"[{p['code_doc']}] {p['titre']} (v{p.get('version', '1.0')})": p
                            for p in procs_du_site
                        }
                        choix_proc = st.selectbox(
                            "Procédure à modifier :", dict_procs.keys()
                        )
                        proc_a_modifier = dict_procs[choix_proc]

                        default_code = proc_a_modifier.get("code_doc", "")
                        default_titre = proc_a_modifier.get("titre", "")

                        # Incrément automatique de version (ex: 1.0 -> 1.1)
                        v_actuelle = proc_a_modifier.get("version", "1.0")
                        try:
                            v_clean = v_actuelle.replace("v", "").strip()
                            maj, min_v = map(int, v_clean.split("."))
                            default_version = f"{maj}.{min_v + 1}"
                        except Exception:
                            default_version = "1.1"

                        default_redacteur = proc_a_modifier.get(
                            "redacteur",
                            user_info.get(
                                "full_name", user_info.get("nom", "Éric KUTER")
                            ),
                        )
                        default_objectif = proc_a_modifier.get("objectif", "")
                        default_domaine = proc_a_modifier.get("domaine_application", "")
                        default_materiel = proc_a_modifier.get("materiel_requis", "")

                        deroul_list = proc_a_modifier.get("deroulement", [])
                        if isinstance(deroul_list, list):
                            lines = [
                                (
                                    item
                                    if isinstance(item, str)
                                    else item.get("action", "")
                                )
                                for item in deroul_list
                            ]
                            default_deroulement = "\n".join(lines)
                        else:
                            default_deroulement = str(deroul_list)

                        default_vigilance = proc_a_modifier.get("points_vigilance", "")
                    else:
                        st.info(
                            "Aucune procédure à modifier pour ce site."
                            " Passez en mode 'Créer'."
                        )

                st.markdown("---")

                with st.form("form_sop_mco", clear_on_submit=False):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        code_doc = st.text_input(
                            "Référence Document (ex: SOP-ACC-001)",
                            value=default_code,
                        )
                        version = st.text_input(
                            "Numéro de la Version à publier",
                            value=default_version,
                        )
                    with col2:
                        titre = st.text_input(
                            "Titre de la procédure", value=default_titre
                        )
                        redacteur = st.text_input(
                            "Rédacteur / Responsable",
                            value=default_redacteur,
                        )

                    objectif = st.text_area(
                        "Objectif de la procédure", value=default_objectif
                    )
                    domaine = st.text_area(
                        "Domaine d'application (Qui ? Où ?)",
                        value=default_domaine,
                    )
                    materiel = st.text_input(
                        "Matériel & Documents nécessaires",
                        value=default_materiel,
                    )

                    st.markdown("---")
                    st.write(
                        "📝 **Déroulement étape par étape** (Saisir une étape par ligne) :"
                    )
                    deroulement_raw = st.text_area(
                        "Étapes (Saut de ligne entre chaque étape)",
                        value=default_deroulement,
                        height=180,
                    )

                    vigilance = st.text_area(
                        "⚠️ Points de vigilance / Sécurité critiques",
                        value=default_vigilance,
                    )

                    st.markdown("---")
                    st.caption("🚨 **Option de Synchronisation ORBIS**")
                    publier_orbis = st.checkbox(
                        "Pousser cette mise à jour dans ORBIS et imposer l'émargement aux agents",
                        value=True,
                    )
                    delta_custom = st.text_input(
                        "Remarque / Delta personnalisé pour la modale ORBIS (Facultatif) :",
                        placeholder="ex: [NOUVEAU] Ajout de la consigne d'évacuation en étape 3",
                    )

                    col_btn1, _ = st.columns([2, 1])
                    with col_btn1:
                        libelle_bouton = (
                            "💾 Valider & Publier la Révision"
                            if proc_a_modifier
                            else "💾 Enregistrer la Procédure SOP"
                        )
                        submitted = st.form_submit_button(libelle_bouton)

                    if submitted:
                        if code_doc.strip() and titre.strip():
                            # Transformation des lignes texte en liste d'étapes
                            liste_etapes_text = [
                                ligne.strip()
                                for ligne in deroulement_raw.split("\n")
                                if ligne.strip()
                            ]

                            # Formatage sous forme de structure JSON pour l'engine de Delta
                            nouveau_json_deroulement = [
                                {
                                    "code": f"STEP-{idx:02d}",
                                    "action": txt,
                                    "zone": "GÉNÉRALE",
                                }
                                for idx, txt in enumerate(liste_etapes_text, start=1)
                            ]

                            # 1. Traitement BDD initial dans opera_procedures
                            payload_base = {
                                "site_id": site_id_selectionne,
                                "code_doc": code_doc,
                                "titre": titre,
                                "objectif": objectif,
                                "domaine_application": domaine,
                                "materiel_requis": materiel,
                                "deroulement": nouveau_json_deroulement,
                                "points_vigilance": vigilance,
                                "version": version,
                                "date_version": datetime.date.today().isoformat(),
                                "redacteur": redacteur,
                                "est_actif": True,
                            }

                            if proc_a_modifier:
                                proc_id = proc_a_modifier["id"]
                                supabase.table("opera_procedures").update(
                                    payload_base
                                ).eq("id", proc_id).execute()

                                # Calcul du Delta par rapport à l'ancienne version
                                ancien_deroulement_raw = proc_a_modifier.get(
                                    "deroulement", []
                                )
                                ancien_json = [
                                    {
                                        "code": f"STEP-{idx:02d}",
                                        "action": (
                                            item
                                            if isinstance(item, str)
                                            else item.get("action", "")
                                        ),
                                        "zone": "GÉNÉRALE",
                                    }
                                    for idx, item in enumerate(
                                        ancien_deroulement_raw, start=1
                                    )
                                ]
                                delta_result = comparer_deroulements_json(
                                    ancien_json, nouveau_json_deroulement
                                )
                                texte_delta_final = (
                                    delta_custom.strip()
                                    if delta_custom.strip()
                                    else delta_result["resume_texte_orbis"]
                                )
                                changelog_txt = (
                                    f"Révision v{version} : {texte_delta_final}"
                                )
                            else:
                                # Création initiale : insertion et récupération de l'UUID
                                res_ins = (
                                    supabase.table("opera_procedures")
                                    .insert(payload_base)
                                    .execute()
                                )
                                proc_id = res_ins.data[0]["id"]
                                texte_delta_final = (
                                    f"➕ [NOUVELLE PROCÉDURE v{version}] {titre}"
                                )
                                changelog_txt = f"Création initiale v{version}"

                            # 2. Publication unifiée via le service OPERA -> ORBIS
                            if publier_orbis:
                                res_pub = publier_nouvelle_version_procedure(
                                    supabase_client=supabase,
                                    procedure_id=proc_id,
                                    nouvelle_version=version,
                                    changelog=changelog_txt,
                                    nouveau_deroulement_json=nouveau_json_deroulement,
                                    redacteur=redacteur,
                                    resume_delta_orbis=(
                                        f"🚨 [{code_doc}] {titre} (v{version}) :\n{texte_delta_final}"
                                    ),
                                )
                                st.info(
                                    f"🔔 Alerte d'émargement transmise à ORBIS ! (SHA-256 : `{res_pub['sha256'][:12]}...`)"
                                )

                            st.success(
                                f"🎉 Procédure '{code_doc} - {titre}' enregistrée en v{version} !"
                            )
                            st.rerun()
                        else:
                            st.error("La référence et le titre sont obligatoires.")

                if proc_a_modifier:
                    st.markdown("---")
                    with st.expander("🗑️ Zone de Suppression (Zone Sensible)"):
                        st.caption(
                            "Cette action supprimera définitivement cette procédure du référentiel."
                        )
                        if st.button(
                            "🗑️ Supprimer cette procédure",
                            type="primary",
                            key="btn_del_sop",
                        ):
                            supabase.table("opera_procedures").delete().eq(
                                "id", proc_a_modifier["id"]
                            ).execute()
                            st.warning(
                                f"Procédure '{proc_a_modifier['code_doc']}' supprimée."
                            )
                            st.rerun()
