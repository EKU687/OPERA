# 🛡️ OPERA — Outil de Procédures, Exigences et Registres d'Astreinte (V1)

[![Version](https://img.shields.io/badge/Version-v1.0.0-blue.svg)](https://github.com/)
[![Environnement](https://img.shields.io/badge/Environnement-PRODUCTION-brightgreen.svg)](https://portail-gnc.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/Supabase-PostgreSQL-green.svg)](https://supabase.com/)

> **OPERA** est l'application métier dédiée à la modélisation, à l'archivage sécurisé, au versioning strict et à la diffusion contrôlée des procédures d'exploitation, des protocoles de sûreté et des fiches réflexes d'urgence.

---

## 📌 Fonctionnalités Principales

* 📑 **Gestion & Structuration des Procédures :** Cycle de vie complet des fiches réflexes (Brouillon, Relecture, Validation, Publication, Archivage) avec numérotation stricte et traçabilité.
* 🔒 **Matrice des Droits & Habilitations (RBAC/ABAC) :** Contrôle d'accès granulaire garantissant la confidentialité des protocoles sensibles selon le rôle et le niveau d'habilitation de l'agent.
* ✒️ **Workflow de Validation & Émargement :** Relecture croisée obligatoire, signature électronique des révisions et suivi de la prise de connaissance des consignes d'urgence.
* 📜 **Traçabilité & Immutabilité (Audit Trail) :** Journalisation infalsifiable de chaque consultation, export ou modification avec chaînage de hachage SHA-256.
* 📄 **Génération & Diffusion PDF/A :** Moteur d'export haute fidélité pour impression ou consultation hors-ligne sécurisée en cas de perte de réseau.
* 🔑 **Authentification Sécurisée & Secours :** Intégration au SSO d'entreprise (OAuth2/OIDC) et accès d'urgence sécurisé par clé matérielle **YubiKey**.

---

## 🛠️ Stack Technique & Outils

* **Langage & Framework :** Python 3.14 / FastAPI (Backend REST) & Streamlit (Console d'administration)
* **Backend & Storage :** Supabase (PostgreSQL 15+, RLS, Realtime) & Stockage chiffré S3/MinIO (AES-256)
* **Fuseau Horaire Applicatif :** `Pacific/Noumea` (UTC+11)
* **Qualité de code :** PEP 8 strict (Black Formatter & Linter Ruff)
* **CI/CD & Déploiement :** Streamlit Cloud / Docker Container (Déploiement automatique sur merge `main`)

---

## 🚀 Installation & Lancement en Local

### 1. Prérequis
* Python 3.14+
* Git
* Clé d'API Supabase / Environnement virtuel configuré

### 2. Cloner le dépôt
```bash
git clone https://github.com/votre-orga/opera-procedures.git
cd opera-procedures
```

### 3. Environnement virtuel & Dépendances
```bash
python3.14 -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configuration des variables d'environnement
Créez un fichier `.env` à la racine du projet :
```env
ENVIRONMENT=development
TIMEZONE=Pacific/Noumea
SUPABASE_URL=https://votre-instance.supabase.co
SUPABASE_KEY=votre_cle_anon_ou_service_role
JWT_SECRET_KEY=votre_cle_secrete_jwt
```

### 5. Lancement de l'application
```bash
streamlit run app.py
```

---

## 🛠️ Commandes Utiles (CLI Maintenance)

OPERA embarque un module CLI Python pour la gestion de la sûreté et l'exploitation :

```bash
# Vérifier la santé des connexions et services
python -m opera.cli check-health

# Débloquer un compte utilisateur verrouillé par sécurité
python -m opera.cli unlock-user --username <identifiant>

# Vérifier l'intégrité de la chaîne d'audit (Audit Trail SHA-256)
python -m opera.cli verify-audit-chain
```

---

## 🛡️ Exigences Sûreté & Confidentialité

* **Classification :** Documents restreints — Diffusion soumise à habilitation.
* **Maintien en Condition de Sécurité (MCS) :** Les dépendances Python sont auditées à chaque build via `pip-audit` et `safety`.
* **Signalement de Vulnérabilité :** Ne pas ouvrir de ticket GitHub public. Contactez directement le RSSI / Responsable Sûreté de l'entité.