# services/delta_service.py
"""
Service de calcul automatique de Delta (Diff) entre deux versions de procédures.
Génère la synthèse visuelle et textuelle pour la notification ORBIS.

Auteur : Éric KUTER
Date : 28/09/2026
"""

from typing import Any, Dict, List


def comparer_deroulements_json(
    ancien_deroulement: List[Dict[str, Any]],
    nouveau_deroulement: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compare deux listes d'étapes (JSON) et identifie les ajouts, modifications et suppressions.

    Chaque étape est identifiée par son 'code' (ex: 'STEP-01') ou à défaut par
    sa position.
    """
    # Indexation par code d'étape pour comparaison rapide
    anciennes_etapes = {
        step.get("code", f"STEP-{i:02d}"): step
        for i, step in enumerate(ancien_deroulement, start=1)
    }
    nouvelles_etapes = {
        step.get("code", f"STEP-{i:02d}"): step
        for i, step in enumerate(nouveau_deroulement, start=1)
    }

    ajouts = []
    modifications = []
    suppressions = []

    # 1. Détection des ajouts et des modifications
    for code, nouveau_step in nouvelles_etapes.items():
        if code not in anciennes_etapes:
            ajouts.append(nouveau_step)
        else:
            ancien_step = anciennes_etapes[code]
            if ancien_step.get("action") != nouveau_step.get(
                "action"
            ) or ancien_step.get("zone") != nouveau_step.get("zone"):
                modifications.append(
                    {
                        "code": code,
                        "avant": ancien_step,
                        "apres": nouveau_step,
                    }
                )

    # 2. Détection des suppressions
    for code, ancien_step in anciennes_etapes.items():
        if code not in nouvelles_etapes:
            suppressions.append(ancien_step)

    # 3. Génération de la synthèse textuelle pour la modale ORBIS
    lignes_delta = []

    if ajouts:
        for item in ajouts:
            zone = item.get("zone", "GÉNÉRALE")
            action = item.get("action") or item.get("consigne", "Action ajoutée")
            lignes_delta.append(
                f"➕ [NOUVEAU - {item.get('code', 'STEP')}] Zone {zone} :" f" {action}"
            )

    if modifications:
        for mod in modifications:
            code = mod["code"]
            action_av = mod["avant"].get("action", "")
            action_ap = mod["apres"].get("action", "")
            lignes_delta.append(
                f"✏️ [MODIFIÉ - {code}] Ancienne consigne : '{action_av}' ➔"
                f" Nouvelle consigne : '{action_ap}'"
            )

    if suppressions:
        for item in suppressions:
            lignes_delta.append(
                f"➖ [SUPPRIMÉ - {item.get('code', 'STEP')}]"
                f" {item.get('action', 'Étape retirée')}"
            )

    resume_texte = (
        "\n".join(lignes_delta)
        if lignes_delta
        else "Aucun changement structurel détecté."
    )

    return {
        "est_modifie": bool(ajouts or modifications or suppressions),
        "ajouts": ajouts,
        "modifications": modifications,
        "suppressions": suppressions,
        "resume_texte_orbis": resume_texte,
    }
