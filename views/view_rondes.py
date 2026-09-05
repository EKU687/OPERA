import streamlit as st
import datetime
from pdf_engines.pdf_rondes import creer_pdf_ronde

def afficher_vue_rondes(supabase, user_info, est_manager):
    st.subheader("🧭 Module Rondes & Patrouilles Séquentielles")
    
    if est_manager:
        tab_terrain, tab_creation, tab_mco = st.tabs([
            "📄 Vue Terrain & PDF", 
            "➕ Création & Arborescence", 
            "🛠️ Modification / Suppression"
        ])
    else:
        tab_terrain = st.container()

    # ==========================================
    # ONGLET 1 : VUE TERRAIN
    # ==========================================
    with tab_terrain:
        reponse_sites = supabase.table("opera_sites").select("*").execute()
        sites = reponse_sites.data
        
        if sites:
            options_sites = {site["nom_site"]: site["id"] for site in sites}
            site_choisi = st.selectbox("📍 Sélectionner un site opérationnel :", options_sites.keys(), key="select_terrain_rondes")
            site_id = options_sites[site_choisi]
            
            arborescence = supabase.table("opera_missions") \
                .select("*, opera_secteurs(*, opera_consignes(*))") \
                .eq("site_id", site_id) \
                .execute()
                
            missions = arborescence.data
            
            if missions:
                for mission in missions:
                    st.markdown(f"### 🕒 {mission['titre_mission']} ({mission['horaire_cible']})")
                    secteurs_tries = sorted(mission.get('opera_secteurs', []), key=lambda x: x['ordre_passage'])
                    
                    for secteur in secteurs_tries:
                        with st.expander(f"🏢 Secteur : {secteur['nom_secteur']}", expanded=True):
                            consignes_triees = sorted(secteur.get('opera_consignes', []), key=lambda x: x['ordre_execution'])
                            for consigne in consignes_triees:
                                icone = "👁️" if consigne['type_action'] == 'Vérification' else "🔒"
                                st.write(f"{icone} **{consigne['type_action']}** : {consigne['description']}")
                    
                    st.markdown("---")
                    fichier_pdf = creer_pdf_ronde(site_choisi, mission, secteurs_tries)
                    nom_fichier = f"Protocole_{site_choisi}_{mission['titre_mission'].replace(' ', '_')}.pdf"
                    
                    st.download_button(
                        label="📄 Télécharger la fiche d'intervention PDF",
                        data=fichier_pdf,
                        file_name=nom_fichier,
                        mime="application/pdf",
                        key=f"dl_pdf_{mission['id']}"
                    )
            else:
                st.info("Aucune ronde active enregistrée pour ce site.")
        else:
            st.warning("Aucun site enregistré dans la base de données.")

    # ==========================================
    # ONGLETS MANAGER
    # ==========================================
    if est_manager:
        with tab_creation:
            st.write("**Espace d'extension du référentiel des rondes**")
            
            # Bloc 1 : Site
            with st.expander("📍 1. Ajouter un nouveau Site", expanded=False):
                with st.form("form_site_rondes", clear_on_submit=True):
                    nom_nouveau_site = st.text_input("Nom du Site (ex: Magenta)")
                    adresse_site = st.text_input("Adresse / Localisation")
                    if st.form_submit_button("Enregistrer le site"):
                        if nom_nouveau_site.strip():
                            supabase.table("opera_sites").insert({"nom_site": nom_nouveau_site, "adresse": adresse_site}).execute()
                            st.success(f"Site '{nom_nouveau_site}' opérationnel.")
                            st.rerun()
                        else:
                            st.error("Le nom du site est obligatoire.")

            # Bloc 2 : Mission
            with st.expander("🕒 2. Ajouter une Mission (Ronde)", expanded=False):
                if sites:
                    site_rattache = st.selectbox("Lier au site :", options_sites.keys(), key="select_admin_mission_rondes")
                    with st.form("form_mission_rondes", clear_on_submit=True):
                        titre_mission = st.text_input("Type de mission (ex: Ronde de fermeture, Ronde Intérieure)")
                        
                        mode_horaire = st.radio(
                            "Désignation de la fréquence / horaire :",
                            ["Horaire fixe (ex: 20:00)", "Fréquence récurrente (ex: Toutes les heures)"],
                            horizontal=True
                        )
                        
                        col_h1, col_h2 = st.columns(2)
                        with col_h1:
                            horaire_fixe = st.time_input("Horaire fixe", datetime.time(20, 00))
                        with col_h2:
                            frequence_texte = st.selectbox(
                                "Fréquence récurrente", 
                                ["Toutes les heures", "Toutes les 2 heures", "Toutes les 3 heures", "Continu / Permanence"]
                            )
                        
                        if st.form_submit_button("Enregistrer la mission"):
                            if titre_mission.strip():
                                horaire_final = horaire_fixe.strftime("%H:%M") if "fixe" in mode_horaire else frequence_texte
                                supabase.table("opera_missions").insert({
                                    "site_id": options_sites[site_rattache],
                                    "titre_mission": titre_mission,
                                    "horaire_cible": horaire_final
                                }).execute()
                                st.success(f"Mission '{titre_mission}' ({horaire_final}) enregistrée.")
                                st.rerun()
                            else:
                                st.error("Le titre de la mission est obligatoire.")

            toutes_missions = supabase.table("opera_missions").select("id, titre_mission, site_id").execute().data
            tous_secteurs = supabase.table("opera_secteurs").select("id, nom_secteur, mission_id").execute().data

            # Bloc 3 : Secteur
            with st.expander("🏢 3. Ajouter un Secteur (Zone)", expanded=False):
                if toutes_missions:
                    options_missions = {f"{next((s['nom_site'] for s in sites if s['id'] == m['site_id']), 'Site Inconnu')} - {m['titre_mission']}": m['id'] for m in toutes_missions}
                    mission_choisie = st.selectbox("Lier à la mission :", options_missions.keys(), key="select_admin_secteur_rondes")
                    mission_id_cible = options_missions[mission_choisie]
                    
                    secteurs_existants = supabase.table("opera_secteurs").select("ordre_passage, nom_secteur").eq("mission_id", mission_id_cible).order("ordre_passage").execute().data
                    if secteurs_existants:
                        st.caption("🏢 Secteurs configurés dans ce parcours :")
                        st.dataframe(secteurs_existants, use_container_width=True)
                        prochain_ordre_sec = max([s['ordre_passage'] for s in secteurs_existants]) + 1
                    else:
                        prochain_ordre_sec = 1

                    with st.form("form_secteur_rondes", clear_on_submit=True):
                        nom_secteur = st.text_input("Nom du Secteur (ex: Zone ZA01)")
                        ordre_passage = st.number_input("Ordre de passage", min_value=1, value=prochain_ordre_sec, step=1)
                        if st.form_submit_button("Enregistrer le secteur"):
                            if nom_secteur.strip():
                                sec_a_decaler = supabase.table("opera_secteurs").select("id, ordre_passage").eq("mission_id", mission_id_cible).gte("ordre_passage", ordre_passage).execute().data
                                for s in sec_a_decaler:
                                    supabase.table("opera_secteurs").update({"ordre_passage": s["ordre_passage"] + 1}).eq("id", s["id"]).execute()

                                supabase.table("opera_secteurs").insert({
                                    "mission_id": mission_id_cible,
                                    "nom_secteur": nom_secteur,
                                    "ordre_passage": ordre_passage
                                }).execute()
                                st.success(f"Secteur '{nom_secteur}' inséré.")
                                st.rerun()
                            else:
                                st.error("Le nom du secteur est obligatoire.")

            # Bloc 4 : Consigne
            with st.expander("📋 4. Ajouter une Consigne", expanded=False):
                if tous_secteurs and toutes_missions:
                    options_secteurs = {}
                    for sec in tous_secteurs:
                        m_parent = next((m for m in toutes_missions if m['id'] == sec['mission_id']), None)
                        if m_parent:
                            s_parent = next((s['nom_site'] for s in sites if s['id'] == m_parent['site_id']), "Site Inconnu")
                            options_secteurs[f"{s_parent} - {m_parent['titre_mission']} > {sec['nom_secteur']}"] = sec['id']

                    secteur_choisi = st.selectbox("Lier au secteur :", options_secteurs.keys(), key="select_admin_consigne_rondes")
                    secteur_id_cible = options_secteurs[secteur_choisi]
                    
                    consignes_existantes = supabase.table("opera_consignes").select("ordre_execution, type_action, description").eq("secteur_id", secteur_id_cible).order("ordre_execution").execute().data
                    if consignes_existantes:
                        st.caption("📋 Consignes configurées dans cette zone :")
                        st.dataframe(consignes_existantes, use_container_width=True)
                        prochain_ordre_con = max([c['ordre_execution'] for c in consignes_existantes]) + 1
                    else:
                        prochain_ordre_con = 1

                    with st.form("form_consigne_rondes", clear_on_submit=True):
                        type_action = st.selectbox("Nature de l'action", ["Vérification", "Condamnation", "Pointage", "Alerte"])
                        description = st.text_input("Action précise")
                        ordre_execution = st.number_input("Ordre d'exécution", min_value=1, value=prochain_ordre_con, step=1)
                        
                        if st.form_submit_button("Enregistrer la consigne"):
                            if description.strip():
                                consignes_a_decaler = supabase.table("opera_consignes").select("id, ordre_execution").eq("secteur_id", secteur_id_cible).gte("ordre_execution", ordre_execution).execute().data
                                for c in consignes_a_decaler:
                                    supabase.table("opera_consignes").update({"ordre_execution": c["ordre_execution"] + 1}).eq("id", c["id"]).execute()

                                supabase.table("opera_consignes").insert({
                                    "secteur_id": secteur_id_cible,
                                    "type_action": type_action,
                                    "description": description,
                                    "ordre_execution": ordre_execution
                                }).execute()
                                st.success("Action terrain ajoutée.")
                                st.rerun()
                            else:
                                st.error("La description est obligatoire.")

        # ONGLET 3 : MCO
        with tab_mco:
            st.write("**Maintien en Condition Opérationnelle (Rondes)**")
            toutes_consignes = supabase.table("opera_consignes").select("*").execute().data
            
            if toutes_consignes and tous_secteurs and toutes_missions and sites:
                options_mco_consigne = {}
                for con in toutes_consignes:
                    sec_p = next((s for s in tous_secteurs if s['id'] == con['secteur_id']), None)
                    if sec_p:
                        mis_p = next((m for m in toutes_missions if m['id'] == sec_p['mission_id']), None)
                        if mis_p:
                            site_p = next((s for s in sites if s['id'] == mis_p['site_id']), None)
                            nom_site = site_p['nom_site'] if site_p else "Site Inconnu"
                            libelle = f"[{nom_site.upper()}] > {mis_p['titre_mission']} > {sec_p['nom_secteur']} | Pos {con['ordre_execution']} : [{con['type_action']}] {con['description']}"
                            options_mco_consigne[libelle] = con

                if options_mco_consigne:
                    consigne_selectionnee = st.selectbox("Sélectionner l'action à modifier ou supprimer :", options_mco_consigne.keys())
                    obj_con = options_mco_consigne[consigne_selectionnee]
                    
                    st.markdown("---")
                    col_m, col_s = st.columns([3, 1])
                    
                    with col_m:
                        with st.form("form_edit_con_rondes"):
                            st.write("**Édition de l'action**")
                            nouveau_type = st.selectbox("Type", ["Vérification", "Condamnation", "Pointage", "Alerte"], index=["Vérification", "Condamnation", "Pointage", "Alerte"].index(obj_con['type_action']))
                            nouvelle_desc = st.text_input("Description", value=obj_con['description'])
                            nouvel_ordre = st.number_input("Ordre d'exécution", value=obj_con['ordre_execution'], min_value=1)
                            
                            if st.form_submit_button("💾 Mettre à jour"):
                                if nouvelle_desc.strip():
                                    supabase.table("opera_consignes").update({
                                        "type_action": nouveau_type,
                                        "description": nouvelle_desc,
                                        "ordre_execution": nouvel_ordre
                                    }).eq("id", obj_con['id']).execute()
                                    st.success("Consigne mise à jour.")
                                    st.rerun()
                                else:
                                    st.error("La description ne peut pas être vide.")
                    
                    with col_s:
                        st.write("**Zone critique**")
                        if st.button("🗑️ Supprimer", type="primary", key="btn_suppr_consigne_ronde"):
                            sec_id = obj_con['secteur_id']
                            ordre_suppr = obj_con['ordre_execution']
                            
                            supabase.table("opera_consignes").delete().eq("id", obj_con['id']).execute()
                            
                            realignement = supabase.table("opera_consignes").select("id, ordre_execution").eq("secteur_id", sec_id).gt("ordre_execution", ordre_suppr).execute().data
                            for c in realignement:
                                supabase.table("opera_consignes").update({"ordre_execution": c["ordre_execution"] - 1}).eq("id", c["id"]).execute()

                            st.warning("Consigne supprimée.")
                            st.rerun()