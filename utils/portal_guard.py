# utils/portail_guard.py
"""
Module de contrôle d'accès et d'authentification SSO pour le Portail Central GNC.
Intègre un mécanisme de contournement (Bypass) sécurisé pour le développement local.

Auteur : Éric KUTER
Date : 28/09/2026
"""

import streamlit as st
from supabase import Client


def verifier_acces_depuis_portail(supabase: Client) -> dict:
    """Vérifie que l'accès provient obligatoirement du Portail GNC.

    En environnement local (IS_DEV = True), contourne la vérification SSO et
    injecte un profil de test.
    """
    # =========================================================================
    # 0. BYPASS MODE DÉVELOPPEMENT LOCAL (Seulement si IS_DEV = True dans secrets.toml)
    # =========================================================================
    is_dev_mode = False
    try:
        is_dev_mode = st.secrets.get("IS_DEV", False)
    except Exception:
        is_dev_mode = False

    if is_dev_mode:
        st.warning(
            "⚠️ **MODE DÉVELOPPEMENT LOCAL ACTIF** — Vérification du Portail"
            " GNC contournée."
        )
        mock_user = {
            "id": "dev-user-001",
            "login": "eric.kuter",
            "nom": "Kuter Eric (Dev)",
            "role": "manager",
            "service": "SURETE_TEST",
            "site_defaut": "SITE OUEMO",
        }
        st.session_state["authenticated_from_portal"] = True
        st.session_state["user_info"] = mock_user
        return mock_user

    # =========================================================================
    # 1. VÉRIFICATION DU CACHE DE SESSION LOCAL
    # =========================================================================
    if st.session_state.get("authenticated_from_portal") and st.session_state.get(
        "user_info"
    ):
        return st.session_state["user_info"]

    # =========================================================================
    # 2. RÉCUPÉRATION DU JETON DANS L'URL (?session_token=...)
    # =========================================================================
    query_params = st.query_params
    token_url = query_params.get("session_token")

    if not token_url:
        afficher_ecran_blocage(
            "Aucun jeton de session détecté. L'application OPERA doit être"
            " lancée depuis le Portail Central GNC."
        )

    # =========================================================================
    # 3. CONTRÔLE DE SÉCURITÉ DANS LA BASE DE DONNÉES SUPABASE
    # =========================================================================
    try:
        res_session = (
            supabase.table("Sessions_Portail")
            .select("*, Utilisateur(id, login, nom, role, service, site_defaut)")
            .eq("token", token_url)
            .eq("actif", True)
            .execute()
        )
        sessions_list = res_session.data or []

        if not sessions_list:
            afficher_ecran_blocage(
                "Jeton de session invalide ou expiré. Veuillez relancer"
                " l'application depuis le Portail Central GNC."
            )

        session_data = sessions_list[0]
        user_info = session_data.get("Utilisateur", {})

        if not user_info:
            afficher_ecran_blocage("Compte utilisateur introuvable ou désactivé.")

        # =========================================================================
        # 4. VALIDATION ET MISE EN CACHE DU PROFIL
        # =========================================================================
        st.session_state["authenticated_from_portal"] = True
        st.session_state["user_info"] = user_info
        st.session_state["session_token_actuel"] = token_url

        return user_info

    except Exception as err:
        afficher_ecran_blocage(f"Erreur de contrôle de sécurité Portail : {err}")


def afficher_ecran_blocage(message_erreur: str):
    """Écran de verrouillage stylisé en cas d'accès direct non autorisé."""
    st.error("⛔ **ACCÈS NON AUTORISÉ — PORTAIL CENTRAL GNC REQUIS**")

    st.markdown(
        f"""
        <div style="background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; border-radius: 6px; margin: 10px 0 20px 0; color: #856404;">
            <b>🔒 Règle de Sécurité Institutionnelle :</b><br>{message_erreur}
        </div>
        """,
        unsafe_allow_html=True,
    )

    url_portail = "https://portail-gnc.streamlit.app"
    st.markdown(
        f"""
        <a href="{url_portail}" target="_self">
            <button style="background-color: #0d6efd; color: white; border: none; padding: 12px 24px; font-weight: bold; border-radius: 6px; cursor: pointer; width: 100%;">
                👉 Se connecter sur le Portail Central GNC
            </button>
        </a>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


def deconnecter_et_retourner_portail(supabase: Client):
    """Invalide la session en base de données et redirige vers le Portail Central GNC."""
    token_actuel = st.session_state.get("session_token_actuel")

    if token_actuel:
        try:
            supabase.table("Sessions_Portail").update({"actif": False}).eq(
                "token", token_actuel
            ).execute()
        except Exception as e:
            print(f"⚠️ Erreur d'invalidation de session : {e}")

    st.session_state.clear()
    url_portail = "https://portail-gnc.streamlit.app"

    st.markdown(
        f"""
        <script type="text/javascript">
            window.close();
            setTimeout(function() {{ window.location.href = "{url_portail}"; }}, 300);
        </script>
        <div style="padding: 20px; text-align: center;">
            <h3>🔒 Session fermée avec succès.</h3>
            <p><a href="{url_portail}">Cliquer ici pour revenir au Portail GNC</a>.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()
