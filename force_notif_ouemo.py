# force_notif_ouemo.py (Dans le projet OPERA)
"""
Script d'injection de test : Génère une notification active
pour le site 'SITE OUEMO' afin d'effectuer le test visuel dans ORBIS.

Auteur : Éric KUTER
Date : 28/09/2026
"""

import sys
import toml
from supabase import create_client, Client
from services.procedure_service import publier_nouvelle_version_procedure


def init_supabase_local() -> Client:
    """Instancie le client Supabase à partir du secrets.toml local."""
    try:
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets["SUPABASE_URL"]
        key = secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as err:
        print(f"❌ Impossible de charger les secrets : {err}")
        sys.exit(1)


def injecter_notification_ouemo():
    print("🚀 --- INJECTION TEST NOTIFICATION OPERA (SITE OUEMO) ---")
    supabase = init_supabase_local()

    # 1. Recherche du site 'SITE OUEMO' ou 'OUEMO'
    res_site = (
        supabase.table("opera_sites")
        .select("id, nom_site")
        .ilike("nom_site", "%OUEMO%")
        .execute()
    )

    if res_site.data:
        site_id = res_site.data[0]["id"]
        nom_site = res_site.data[0]["nom_site"]
        print(f"📍 Site trouvé en BDD : {nom_site} (UUID: {site_id})")
    else:
        # Création explicite si le site n'existe pas encore dans opera_sites
        res_site = (
            supabase.table("opera_sites").insert({"nom_site": "SITE OUEMO"}).execute()
        )
        site_id = res_site.data[0]["id"]
        print(f"📍 Site créé avec succès : SITE OUEMO (UUID: {site_id})")

    # 2. Récupération ou création de la procédure modèle
    res_proc = (
        supabase.table("opera_procedures").select("id").eq("site_id", site_id).execute()
    )

    if res_proc.data:
        proc_id = res_proc.data[0]["id"]
    else:
        proc_payload = {
            "site_id": site_id,
            "code_doc": "RND-OUEMO-01",
            "titre": "Ronde de Fermeture Ouémo",
            "objectif": "Sécurisation périmètre et points sensibles",
            "domaine_application": "Sûreté Bâtiment",
            "deroulement": [{"step": 1, "action": "Fermeture Grille Principale"}],
            "version": "1.0",
            "redacteur": "Éric KUTER",
            "est_actif": True,
        }
        proc_res = supabase.table("opera_procedures").insert(proc_payload).execute()
        proc_id = proc_res.data[0]["id"]

    # 3. Publication de la Version 1.3 avec le Delta (Ajout Porte D07)
    deroulement_v1_3 = [
        {"step": 1, "action": "Fermeture Grille Principale", "zone": "ACCES"},
        {
            "step": 2,
            "action": "Verrouillage Porte D07 zone ZC01",
            "zone": "ZC01",
        },  # ⬅️ NOVEAU STEP !
        {"step": 3, "action": "Armement Alarme Intrusion", "zone": "PC"},
    ]

    changelog_txt = "Ajout de la vérification Porte D07 suite aux consignes de sûreté."
    delta_orbis_txt = (
        "[NOUVEAU - STEP 02] Verrouillage obligatoire de la Porte D07 en zone ZC01."
    )

    res = publier_nouvelle_version_procedure(
        supabase_client=supabase,
        procedure_id=proc_id,
        nouvelle_version="1.3",
        changelog=changelog_txt,
        nouveau_deroulement_json=deroulement_v1_3,
        redacteur="Éric KUTER",
        resume_delta_orbis=delta_orbis_txt,
    )

    print(f"\n✨ {res['message']}")
    print(f"🔑 ID Notification ORBIS : {res['notification_id']}")
    print(
        "🎉 Injection réussie ! Vous pouvez maintenant vérifier l'affichage dans ORBIS."
    )


if __name__ == "__main__":
    injecter_notification_ouemo()
