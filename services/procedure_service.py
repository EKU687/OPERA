# services/procedure_service.py
"""
Service Métier OPERA : Gestion du versioning des procédures,
calcul de l'empreinte d'intégrité SHA-256, archivage des deltas
et publication des notifications de mise à jour vers ORBIS.

Auteur : Éric KUTER
Date : 28/09/2026
"""

import datetime
import hashlib
import json
from typing import Any, Dict, List, Optional


def calculer_hash_json(data: Any) -> str:
    """
    Génère une empreinte SHA-256 déterministe à partir d'une structure JSON.
    Garantit l'intégrité et la non-altération du déroulement de la ronde.
    """
    json_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def publier_nouvelle_version_procedure(
    supabase_client,
    procedure_id: str,
    nouvelle_version: str,
    changelog: str,
    nouveau_deroulement_json: List[Dict[str, Any]],
    redacteur: str,
    resume_delta_orbis: str,
) -> Dict[str, Any]:
    """
    Publie une nouvelle version de procédure/ronde dans OPERA :
    1. Calcule l'empreinte SHA-256 de la nouvelle version.
    2. Met à jour la table principale 'opera_procedures'.
    3. Archive le snapshot dans 'opera_procedure_versions'.
    4. Pousse une alerte d'émargement active dans 'opera_orbis_notifications'.

    :param supabase_client: Client API Supabase initialisé.
    :param procedure_id: UUID de la procédure ciblée.
    :param nouvelle_version: Numéro de version (ex: "1.3").
    :param changelog: Explication de la modification (ex: "Ajout Porte D07 zone ZC01").
    :param nouveau_deroulement_json: Liste des étapes ordonnées au format JSON.
    :param redacteur: Identifiant ou nom du responsable sûreté rédacteur.
    :param resume_delta_orbis: Texte synthétique destiné à la modale ORBIS.
    :return: Dictionnaire contenant le statut et l'ID de la notification générée.
    """
    date_jour = datetime.date.today().isoformat()

    # 1. Vérification de l'existence de la procédure dans OPERA
    proc_actuelle_res = (
        supabase_client.table("opera_procedures")
        .select("*")
        .eq("id", procedure_id)
        .execute()
    )

    if not proc_actuelle_res.data:
        raise ValueError(f"Procédure introuvable pour l'ID : {procedure_id}")

    proc_actuelle = proc_actuelle_res.data[0]
    site_id = proc_actuelle["site_id"]
    titre_proc = proc_actuelle["titre"]
    code_doc = proc_actuelle["code_doc"]

    # Empreinte numérique d'intégrité SHA-256
    hash_sha256 = calculer_hash_json(nouveau_deroulement_json)

    # 2. Mise à jour de la table principale 'opera_procedures' (Version Active)
    supabase_client.table("opera_procedures").update(
        {
            "version": nouvelle_version,
            "date_version": date_jour,
            "deroulement": nouveau_deroulement_json,
            "redacteur": redacteur,
        }
    ).eq("id", procedure_id).execute()

    # 3. Historisation dans 'opera_procedure_versions' (Snapshot & Audit Trail)
    supabase_client.table("opera_procedure_versions").insert(
        {
            "procedure_id": procedure_id,
            "version": nouvelle_version,
            "changelog": f"[{hash_sha256[:8]}] {changelog}",
            "deroulement_json": nouveau_deroulement_json,
            "redacteur": redacteur,
            "valide_par": redacteur,
        }
    ).execute()

    # 4. Désactivation des anciennes notifications d'émargement non traitées pour cette procédure
    supabase_client.table("opera_orbis_notifications").update({"est_active": False}).eq(
        "procedure_id", procedure_id
    ).execute()

    # 5. Publication de la nouvelle notification d'émargement à destination d'ORBIS
    notif_payload = {
        "site_id": site_id,
        "procedure_id": procedure_id,
        "version_cible": nouvelle_version,
        "titre_notification": f"🚨 MAJ Procédure : {code_doc} - {titre_proc} (v{nouvelle_version})",
        "resume_delta": resume_delta_orbis,
        "est_active": True,
    }

    res_notif = (
        supabase_client.table("opera_orbis_notifications")
        .insert(notif_payload)
        .execute()
    )

    notif_id = res_notif.data[0]["id"] if res_notif.data else None

    return {
        "status": "success",
        "message": f"Procédure {code_doc} (v{nouvelle_version}) enregistrée. Empreinte SHA-256 : {hash_sha256[:12]}...",
        "notification_id": notif_id,
        "sha256": hash_sha256,
    }
