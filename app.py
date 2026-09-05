import streamlit as st
from supabase import create_client, Client
from utils.portal_guard import verifier_acces_depuis_portail, deconnecter_et_retourner_portail
from views.view_rondes import afficher_vue_rondes
from views.view_sop import afficher_vue_sop

# ==========================================
# CONFIGURATION DE L'INTERFACE
# ==========================================
st.set_page_config(
    page_title="OPERA — Protocoles Sûreté", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialisation de la connexion Supabase
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
    
    # 🔒 VERROUILLAGE PORTAIL GNC (SPOE - Single Point of Entry)
    user_info = verifier_acces_depuis_portail(supabase)

    # Bandeau Supérieur & Profil Utilisateur
    col_titre, col_user = st.columns([4, 1])
    with col_titre:
        st.title("🛡️ Projet OPERA")
        st.caption("Référentiel des Protocoles de Sûreté & Fiches d'Intervention")
    with col_user:
        st.write(f"👤 **{user_info.get('nom', 'Agent')}**")
        st.caption(f"Rôle : {user_info.get('role', 'Agent')}")
        if st.button("🚪 Déconnexion", type="secondary"):
            deconnecter_et_retourner_portail(supabase)

    st.markdown("---")

    # Contrôle d'Accès Basé sur les Rôles (RBAC)
    est_manager = user_info.get("role", "").upper() in ["MANAGER", "ADMIN", "CHEF_DE_SITE"]

    # Navigation Principale - Choix du Domaine
    module_choisi = st.radio(
        "Sélectionner le domaine opérationnel :",
        ["🧭 Rondes & Patrouilles Séquentielles", "📜 Procédures Permanentes & SOP"],
        horizontal=True
    )
    st.markdown("---")

    # Aiguillage vers les modules métiers isolés
    if "Rondes" in module_choisi:
        afficher_vue_rondes(supabase, user_info, est_manager)
    else:
        afficher_vue_sop(supabase, user_info, est_manager)

# ==========================================
# FILET DE SÉCURITÉ GLOBAL
# ==========================================
except Exception as e:
    st.error("❌ Échec de la communication avec le système central OPERA.")
    st.exception(e)