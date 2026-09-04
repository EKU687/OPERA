import streamlit as st
from supabase import create_client, Client
from fpdf import FPDF
import datetime
import os
from utils.portal_guard import verifier_acces_depuis_portail, deconnecter_et_retourner_portail

# ==========================================
# 1. MOTEUR PDF INSTITUTIONNEL (Nettoyé Unicode)
# ==========================================
class GenerateurProtocolePro(FPDF):
    def __init__(self, site_nom, mission_titre, horaire):
        super().__init__()
        self.site_nom = site_nom
        self.mission_titre = mission_titre
        self.horaire = horaire
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Logo institutionnel
        if os.path.exists("logo_gouv.png"):
            self.image("logo_gouv.png", x=10, y=8, w=28)

        # En-tête administratif (Utilisation stricte du jeu de caractères Latin-1)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(20, 35, 60)
        self.cell(0, 5, "GOUVERNEMENT DE LA NOUVELLE-CALEDONIE", ln=True, align="R")
        self.set_font("helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "DIRECTION DES SECURITES - PROJET OPERA", ln=True, align="R")
        self.ln(6)

        # Ligne de séparation aux couleurs officielles
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.8)
        self.line(10, 25, 200, 25)
        self.ln(6)

        # Cartouche de la mission (Sanitisation des caractères typographiques)
        titre_clean = self.mission_titre.upper().replace("—", "-").replace("–", "-").replace("’", "'")
        site_clean = self.site_nom.upper().replace("—", "-").replace("–", "-").replace("’", "'")
        
        self.set_fill_color(240, 243, 246)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f" PROTOCOLE : {site_clean} - {titre_clean} ({self.horaire})", fill=True, ln=True)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        date_edition = datetime.datetime.now().strftime("%d/%m/%Y a %H:%M")
        self.cell(0, 10, f"Document Officiel OPERA - Genere le {date_edition} - Page {self.page_no()}/{{nb}}", align="C")

def creer_pdf(nom_site, mission, secteurs):
    pdf = GenerateurProtocolePro(nom_site, mission['titre_mission'], mission['horaire_cible'])
    pdf.add_page()
    
    for secteur in secteurs:
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(215, 228, 242)
        
        nom_sec_clean = secteur['nom_secteur'].upper().replace("—", "-").replace("–", "-").replace("’", "'")
        pdf.cell(0, 7, f" SECTEUR : {nom_sec_clean}", fill=True, ln=True)
        pdf.ln(2)
        
        consignes = sorted(secteur.get('opera_consignes', []), key=lambda x: x['ordre_execution'])
        pdf.set_font("helvetica", "", 10)
        
        for consigne in consignes:
            action = consigne['type_action'].upper().replace("—", "-").replace("–", "-").replace("’", "'")
            desc = consigne['description'].replace("—", "-").replace("–", "-").replace("’", "'")
            
            pdf.cell(5, 6, "") 
            pdf.cell(0, 6, f"[  ] {action} : {desc}", ln=True)
        pdf.ln(4)
        
    return bytes(pdf.output())

# ==========================================
# 2. CONFIGURATION DE L'INTERFACE & REQUÊTES
# ==========================================
st.set_page_config(
    page_title="OPERA — Protocoles Sûreté", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
    
    # 🔒 VERROUILLAGE PORTAIL GNC (SPOE)
    user_info = verifier_acces_depuis_portail(supabase)

    # Bandeau Supérieur & Profil
    col_titre, col_user = st.columns([4, 1])
    with col_titre:
        st.title("🛡️ Projet OPERA")
        st.caption("Standardisation et Pilotage des Protocoles de Sûreté")
    with col_user:
        st.write(f"👤 **{user_info.get('nom', 'Agent')}**")
        st.caption(f"Rôle : {user_info.get('role', 'Agent')}")
        if st.button("🚪 Déconnexion", type="secondary"):
            deconnecter_et_retourner_portail(supabase)

    st.markdown("---")

    # Contrôle RBAC
    est_manager = user_info.get("role", "").upper() in ["MANAGER", "ADMIN", "CHEF_DE_SITE"]

    if est_manager:
        tab_terrain, tab_creation, tab_mco = st.tabs([
            "📄 Vue Terrain & PDF", 
            "➕ Création & Arborescence", 
            "🛠️ Modification / Suppression"
        ])
    else:
        tab_terrain = st.container()
        st.info("🔒 **Mode Consultation Agent** : Téléchargement des fiches d'intervention uniquement.")

    # ==========================================
    # ONGLET 1 : VUE TERRAIN (Lecture Seule)
    # ==========================================
    with tab_terrain:
        reponse_sites = supabase.table("opera_sites").select("*").execute()
        sites = reponse_sites.data
        
        if sites:
            options_sites = {site["nom_site"]: site["id"] for site in sites}
            site_choisi = st.selectbox("📍 Sélectionner un site opérationnel :", options_sites.keys(), key="select_terrain")
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
                    fichier_pdf = creer_pdf(site_choisi, mission, secteurs_tries)
                    nom_fichier = f"Protocole_{site_choisi}_{mission['titre_mission'].replace(' ', '_')}.pdf"
                    
                    st.download_button(
                        label="📄 Télécharger la fiche d'intervention PDF",
                        data=fichier_pdf,
                        file_name=nom_fichier,
                        mime="application/pdf"
                    )
            else:
                st.info("Aucune procédure active pour ce site.")
        else:
            st.warning("Aucun site enregistré dans la base de données.")

    # ==========================================
    # ONGLETS MANAGER (Si habilité)
    # ==========================================
    if est_manager:
        # ONGLET 2 : CRÉATION & ARBORESCENCE
        with tab_creation:
            st.write("**Espace d'extension du référentiel sûreté**")
            
            # Bloc 1 : Site
            with st.expander("📍 1. Ajouter un nouveau Site", expanded=False):
                with st.form("form_site", clear_on_submit=True):
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
            with st.expander("🕒 2. Ajouter une Mission", expanded=False):
                if sites:
                    site_rattache = st.selectbox("Lier au site :", options_sites.keys(), key="select_admin_mission")
                    with st.form("form_mission", clear_on_submit=True):
                        titre_mission = st.text_input("Type de mission (ex: Ronde de fermeture)")
                        horaire = st.time_input("Horaire cible", datetime.time(20, 00))
                        if st.form_submit_button("Enregistrer la mission"):
                            if titre_mission.strip():
                                supabase.table("opera_missions").insert({
                                    "site_id": options_sites[site_rattache],
                                    "titre_mission": titre_mission,
                                    "horaire_cible": horaire.strftime("%H:%M")
                                }).execute()
                                st.success("Mission enregistrée.")
                                st.rerun()
                            else:
                                st.error("Le titre de la mission est obligatoire.")

            toutes_missions = supabase.table("opera_missions").select("id, titre_mission, site_id").execute().data
            tous_secteurs = supabase.table("opera_secteurs").select("id, nom_secteur, mission_id").execute().data

            # Bloc 3 : Secteur
            with st.expander("🏢 3. Ajouter un Secteur (Zone)", expanded=False):
                if toutes_missions:
                    options_missions = {f"{next((s['nom_site'] for s in sites if s['id'] == m['site_id']), 'Site Inconnu')} - {m['titre_mission']}": m['id'] for m in toutes_missions}
                    mission_choisie = st.selectbox("Lier à la mission :", options_missions.keys(), key="select_admin_secteur")
                    mission_id_cible = options_missions[mission_choisie]
                    
                    secteurs_existants = supabase.table("opera_secteurs").select("ordre_passage, nom_secteur").eq("mission_id", mission_id_cible).order("ordre_passage").execute().data
                    if secteurs_existants:
                        st.caption("🏢 Secteurs configurés dans ce parcours :")
                        st.dataframe(secteurs_existants, use_container_width=True)
                        prochain_ordre_sec = max([s['ordre_passage'] for s in secteurs_existants]) + 1
                    else:
                        prochain_ordre_sec = 1

                    with st.form("form_secteur", clear_on_submit=True):
                        nom_secteur = st.text_input("Nom du Secteur (ex: Zone ZA01)")
                        ordre_passage = st.number_input("Ordre de passage", min_value=1, value=prochain_ordre_sec, step=1)
                        if st.form_submit_button("Enregistrer le secteur"):
                            if nom_secteur.strip():
                                # Décalage automatique des secteurs
                                sec_a_decaler = supabase.table("opera_secteurs").select("id, ordre_passage").eq("mission_id", mission_id_cible).gte("ordre_passage", ordre_passage).execute().data
                                for s in sec_a_decaler:
                                    supabase.table("opera_secteurs").update({"ordre_passage": s["ordre_passage"] + 1}).eq("id", s["id"]).execute()

                                supabase.table("opera_secteurs").insert({
                                    "mission_id": mission_id_cible,
                                    "nom_secteur": nom_secteur,
                                    "ordre_passage": ordre_passage
                                }).execute()
                                st.success(f"Secteur '{nom_secteur}' inséré à la position {ordre_passage}.")
                                st.rerun()
                            else:
                                st.error("Le nom du secteur est obligatoire.")

            # Bloc 4 : Consigne (Insertion avec décalage automatique)
            with st.expander("📋 4. Ajouter une Consigne", expanded=False):
                if tous_secteurs and toutes_missions:
                    options_secteurs = {}
                    for sec in tous_secteurs:
                        m_parent = next((m for m in toutes_missions if m['id'] == sec['mission_id']), None)
                        if m_parent:
                            s_parent = next((s['nom_site'] for s in sites if s['id'] == m_parent['site_id']), "Site Inconnu")
                            options_secteurs[f"{s_parent} - {m_parent['titre_mission']} > {sec['nom_secteur']}"] = sec['id']

                    secteur_choisi = st.selectbox("Lier au secteur :", options_secteurs.keys(), key="select_admin_consigne")
                    secteur_id_cible = options_secteurs[secteur_choisi]
                    
                    consignes_existantes = supabase.table("opera_consignes").select("ordre_execution, type_action, description").eq("secteur_id", secteur_id_cible).order("ordre_execution").execute().data
                    if consignes_existantes:
                        st.caption("📋 Consignes configurées dans cette zone :")
                        st.dataframe(consignes_existantes, use_container_width=True)
                        prochain_ordre_con = max([c['ordre_execution'] for c in consignes_existantes]) + 1
                    else:
                        prochain_ordre_con = 1

                    with st.form("form_consigne", clear_on_submit=True):
                        type_action = st.selectbox("Nature de l'action", ["Vérification", "Condamnation", "Pointage", "Alerte"])
                        description = st.text_input("Action précise (ex: Fermer la porte A03 à clé)")
                        ordre_execution = st.number_input("Ordre d'exécution", min_value=1, value=prochain_ordre_con, step=1)
                        
                        if st.form_submit_button("Enregistrer la consigne"):
                            if description.strip():
                                # DÉCALAGE AUTOMATIQUE (+1 aux consignes existantes >= ordre_execution)
                                consignes_a_decaler = supabase.table("opera_consignes").select("id, ordre_execution").eq("secteur_id", secteur_id_cible).gte("ordre_execution", ordre_execution).execute().data
                                for c in consignes_a_decaler:
                                    supabase.table("opera_consignes").update({"ordre_execution": c["ordre_execution"] + 1}).eq("id", c["id"]).execute()

                                supabase.table("opera_consignes").insert({
                                    "secteur_id": secteur_id_cible,
                                    "type_action": type_action,
                                    "description": description,
                                    "ordre_execution": ordre_execution
                                }).execute()
                                st.success("Action terrain ajoutée (numérotation réalignée).")
                                st.rerun()
                            else:
                                st.error("La description est obligatoire.")

        # ONGLET 3 : MCO (Fil d'Ariane & Suppression avec Réalignement)
        with tab_mco:
            st.write("**Maintien en Condition Opérationnelle (Ajustement du référentiel)**")
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
                        with st.form("form_edit_con"):
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
                        if st.button("🗑️ Supprimer", type="primary"):
                            sec_id = obj_con['secteur_id']
                            ordre_suppr = obj_con['ordre_execution']
                            
                            # 1. Suppression
                            supabase.table("opera_consignes").delete().eq("id", obj_con['id']).execute()
                            
                            # 2. Réalignement (-1 aux suivants)
                            realignement = supabase.table("opera_consignes").select("id, ordre_execution").eq("secteur_id", sec_id).gt("ordre_execution", ordre_suppr).execute().data
                            for c in realignement:
                                supabase.table("opera_consignes").update({"ordre_execution": c["ordre_execution"] - 1}).eq("id", c["id"]).execute()

                            st.warning("Consigne supprimée et séquence réalignée.")
                            st.rerun()
            else:
                st.info("Aucune consigne enregistrée.")

# ==========================================
# FILET DE SÉCURITÉ GLOBAL
# ==========================================
except Exception as e:
    st.error("❌ Échec de la communication avec la base de données.")
    st.exception(e)