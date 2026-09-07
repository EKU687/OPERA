import streamlit as st
import datetime
from pdf_engines.pdf_sop import creer_pdf_sop

def afficher_vue_sop(supabase, user_info, est_manager):
    st.subheader("📜 Module Procédures Opérationnelles Normalisées (SOP)")
    
    if est_manager:
        tab_consult, tab_saisie = st.tabs(["📄 Consultation & PDF", "🛠️ Saisie & Édition / MCO"])
    else:
        tab_consult = st.container()

    # ==========================================
    # CONSULTATION & TÉLÉCHARGEMENT PDF
    # ==========================================
    with tab_consult:
        reponse_sites = supabase.table("opera_sites").select("*").execute()
        sites = reponse_sites.data
        
        if sites:
            options_sites = {site["nom_site"]: site["id"] for site in sites}
            site_choisi = st.selectbox("📍 Sélectionner le site :", options_sites.keys(), key="select_site_sop")
            site_id = options_sites[site_choisi]
            
            procs = supabase.table("opera_procedures").select("*").eq("site_id", site_id).eq("est_actif", True).execute().data
            
            if procs:
                for proc in procs:
                    with st.expander(f"📋 [{proc['code_doc']}] {proc['titre']} ({proc['version']})", expanded=False):
                        st.write(f"**Objectif :** {proc['objectif']}")
                        st.write(f"**Domaine d'application :** {proc['domaine_application']}")
                        st.write(f"**Matériel requis :** {proc.get('materiel_requis', 'Aucun')}")
                        
                        st.markdown("---")
                        st.write("**Déroulement de la procédure :**")
                        deroulement = proc.get('deroulement', [])
                        if isinstance(deroulement, list):
                            for idx, etape in enumerate(deroulement, start=1):
                                txt = etape if isinstance(etape, str) else etape.get('action', '')
                                st.write(f"{idx}. {txt}")
                        else:
                            st.write(str(deroulement))
                            
                        if proc.get('points_vigilance'):
                            st.warning(f"⚠️ **Points de Vigilance :** {proc['points_vigilance']}")
                            
                        st.caption(f"Dernière révision : {proc['date_version']} par {proc['redacteur']}")
                        
                        # Génération PDF
                        pdf_bytes = creer_pdf_sop(proc, site_choisi)
                        st.download_button(
                            label=f"📄 Télécharger la fiche {proc['code_doc']} (PDF)",
                            data=pdf_bytes,
                            file_name=f"{proc['code_doc']}_{site_choisi}.pdf",
                            mime="application/pdf",
                            key=f"dl_sop_{proc['id']}"
                        )
            else:
                st.info("Aucune procédure permanente configurée pour ce site.")
        else:
            st.warning("Aucun site enregistré.")

    # ==========================================
    # SAISIE / ÉDITION MANAGER (MCO)
    # ==========================================
    if est_manager:
        with tab_saisie:
            if sites:
                st.write("**Espace d'édition et de MCO des Procédures Opérationnelles (SOP)**")
                
                # Selection du Mode (Création ou Édition)
                mode_action = st.radio(
                    "Action à effectuer :",
                    ["➕ Créer une nouvelle procédure", "✏️ Modifier / Réviser une procédure existante"],
                    horizontal=True
                )
                
                site_rattache = st.selectbox("Site concerné :", options_sites.keys(), key="select_site_saisie_sop")
                site_id_selectionne = options_sites[site_rattache]
                
                # Initialisation des variables par défaut
                proc_a_modifier = None
                default_code = ""
                default_titre = ""
                default_version = "v1.0"
                default_redacteur = user_info.get('nom', 'Kuter Eric')
                default_objectif = ""
                default_domaine = ""
                default_materiel = ""
                default_deroulement = ""
                default_vigilance = ""
                
                # Si Mode Édition : Sélection et Pré-remplissage
                if "Modifier" in mode_action:
                    procs_du_site = supabase.table("opera_procedures").select("*").eq("site_id", site_id_selectionne).execute().data
                    if procs_du_site:
                        dict_procs = {f"[{p['code_doc']}] {p['titre']} ({p['version']})" : p for p in procs_du_site}
                        choix_proc = st.selectbox("Procédure à modifier :", dict_procs.keys())
                        proc_a_modifier = dict_procs[choix_proc]
                        
                        # Pré-remplissage des champs avec la donnée BDD
                        default_code = proc_a_modifier.get('code_doc', '')
                        default_titre = proc_a_modifier.get('titre', '')
                        default_version = proc_a_modifier.get('version', 'v1.1')
                        default_redacteur = proc_a_modifier.get('redacteur', user_info.get('nom', ''))
                        default_objectif = proc_a_modifier.get('objectif', '')
                        default_domaine = proc_a_modifier.get('domaine_application', '')
                        default_materiel = proc_a_modifier.get('materiel_requis', '')
                        
                        # Reconstitution du texte déroulement
                        deroul_list = proc_a_modifier.get('deroulement', [])
                        if isinstance(deroul_list, list):
                            lines = []
                            for item in deroul_list:
                                lines.append(item if isinstance(item, str) else item.get('action', ''))
                            default_deroulement = "\n".join(lines)
                        else:
                            default_deroulement = str(deroul_list)
                            
                        default_vigilance = proc_a_modifier.get('points_vigilance', '')
                    else:
                        st.info("Aucune procédure à modifier pour ce site. Passez en mode 'Créer'.")

                st.markdown("---")
                
                # Formulaire Dynamique
                with st.form("form_sop_mco", clear_on_submit=False):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        code_doc = st.text_input("Référence Document (ex: SOP-ACC-001)", value=default_code)
                        version = st.text_input("Version du document", value=default_version)
                    with col2:
                        titre = st.text_input("Titre de la procédure", value=default_titre)
                        redacteur = st.text_input("Rédacteur / Responsable", value=default_redacteur)

                    objectif = st.text_area("Objectif de la procédure", value=default_objectif)
                    domaine = st.text_area("Domaine d'application (Qui ? Où ?)", value=default_domaine)
                    materiel = st.text_input("Matériel & Documents nécessaires", value=default_materiel)

                    st.markdown("---")
                    st.write("  **Déroulement étape par étape** (Saisir une étape par ligne) :")
                    deroulement_raw = st.text_area("Étapes (Saut de ligne entre chaque étape)", value=default_deroulement, height=180)

                    vigilance = st.text_area("⚠️ Points de vigilance / Sécurité critiques", value=default_vigilance)

                    col_btn1, col_btn2 = st.columns([2, 1])
                    
                    with col_btn1:
                        libelle_bouton = "💾 Mettre à jour la Procédure" if proc_a_modifier else "💾 Enregistrer la Procédure SOP"
                        submitted = st.form_submit_button(libelle_bouton)
                    
                    if submitted:
                        if code_doc.strip() and titre.strip():
                            liste_etapes = [ligne.strip() for ligne in deroulement_raw.split("\n") if ligne.strip()]
                            payload = {
                                "site_id": site_id_selectionne,
                                "code_doc": code_doc,
                                "titre": titre,
                                "objectif": objectif,
                                "domaine_application": domaine,
                                "materiel_requis": materiel,
                                "deroulement": liste_etapes,
                                "points_vigilance": vigilance,
                                "version": version,
                                "date_version": datetime.date.today().isoformat(),
                                "redacteur": redacteur
                            }
                            
                            if proc_a_modifier:
                                # UPDATE BDD
                                supabase.table("opera_procedures").update(payload).eq("id", proc_a_modifier['id']).execute()
                                st.success(f"Procédure '{code_doc}' révisée et mise à jour avec succès.")
                            else:
                                # INSERT BDD
                                supabase.table("opera_procedures").insert(payload).execute()
                                st.success(f"Procédure '{code_doc} - {titre}' enregistrée.")
                                
                            st.rerun()
                        else:
                            st.error("La référence et le titre sont obligatoires.")

                # Option de Suppression (MCO Critique)
                if proc_a_modifier:
                    st.markdown("---")
                    with st.expander("🗑️ Zone de Suppression (Zone Sensible)"):
                        st.caption("Cette action supprimera définitivement cette procédure du référentiel.")
                        if st.button("🗑️ Supprimer cette procédure", type="primary", key="btn_del_sop"):
                            supabase.table("opera_procedures").delete().eq("id", proc_a_modifier['id']).execute()
                            st.warning(f"Procédure '{proc_a_modifier['code_doc']}' supprimée.")
                            st.rerun()