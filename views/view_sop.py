import streamlit as st
import datetime
from pdf_engines.pdf_sop import creer_pdf_sop

def afficher_vue_sop(supabase, user_info, est_manager):
    st.subheader("📜 Module Procédures Opérationnelles Normalisées (SOP)")
    
    if est_manager:
        tab_consult, tab_saisie = st.tabs(["📄 Consultation & PDF", "➕ Nouvelle Procédure / Édition"])
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
    # SAISIE / CRÉATION MANAGER
    # ==========================================
    if est_manager:
        with tab_saisie:
            st.write("**Création d'une nouvelle consigne permanente / SOP**")
            if sites:
                site_rattache = st.selectbox("Rattacher au site :", options_sites.keys(), key="select_site_saisie_sop")
                
                with st.form("form_nouvelle_sop", clear_on_submit=True):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        code_doc = st.text_input("Référence Document (ex: SOP-ACC-001)")
                        version = st.text_input("Version", value="v1.0")
                    with col2:
                        titre = st.text_input("Titre de la procédure (ex: Procédure d'accueil visiteurs)")
                        redacteur = st.text_input("Rédacteur / Responsable", value=user_info.get('nom', 'Direction des Sécurités'))

                    objectif = st.text_area("Objectif de la procédure")
                    domaine = st.text_area("Domaine d'application (Qui ? Où ?)")
                    materiel = st.text_input("Matériel & Documents nécessaires (ex: Registre, Badges, Pièce d'identité)")

                    st.markdown("---")
                    st.write("  **Déroulement étape par étape** (Saisir une étape par ligne) :")
                    deroulement_raw = st.text_area("Étapes (Saut de ligne entre chaque étape)", height=150, placeholder="Accueillir le visiteur et demander la pièce d'identité\nVérifier le motif de la visite\n...")

                    vigilance = st.text_area("⚠️ Points de vigilance / Sécurité critiques")

                    if st.form_submit_button("💾 Enregistrer la Procédure SOP"):
                        if code_doc.strip() and titre.strip():
                            liste_etapes = [ligne.strip() for ligne in deroulement_raw.split("\n") if ligne.strip()]
                            
                            supabase.table("opera_procedures").insert({
                                "site_id": options_sites[site_rattache],
                                "code_doc": code_doc,
                                "titre": titre,
                                "objectif": objectif,
                                "domaine_application": domaine,
                                "materiel_requis": materiel,
                                "deroulement": liste_etapes,
                                "points_vigilance": vigilance,
                                "version": version,
                                "redacteur": redacteur
                            }).execute()
                            
                            st.success(f"Procédure '{code_doc} - {titre}' enregistrée dans le référentiel.")
                            st.rerun()
                        else:
                            st.error("La référence et le titre sont obligatoires.")