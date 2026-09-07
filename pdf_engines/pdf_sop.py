import os
import datetime
from fpdf import FPDF
from utils.pdf_utils import nettoyer_texte_pdf

def formater_date_fr(date_val):
    if not date_val:
        return ""
    if isinstance(date_val, str):
        try:
            dt = datetime.datetime.strptime(date_val.split("T")[0], "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            return date_val
    elif isinstance(date_val, (datetime.date, datetime.datetime)):
        return date_val.strftime("%d/%m/%Y")
    return str(date_val)

class GenerateurSopPro(FPDF):
    def __init__(self, site_nom, code_doc, titre, version, date_ver, redacteur):
        super().__init__()
        self.site_nom = site_nom
        self.code_doc = code_doc
        self.titre = titre
        self.version = version
        self.date_ver = date_ver
        self.redacteur = redacteur
        
        # Marge supérieure stricte à 35 mm
        self.set_margins(10, 35, 10)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Ne JAMAIS modifier les marges à l'intérieur de header() !
        dossier_pdf_engines = os.path.dirname(os.path.abspath(__file__))
        racine_projet = os.path.dirname(dossier_pdf_engines)
        dossier_assets = os.path.join(racine_projet, "assets")

        logo_path = None
        if os.path.exists(dossier_assets):
            for fichier in os.listdir(dossier_assets):
                if fichier.lower().startswith("logo_gouv"):
                    logo_path = os.path.join(dossier_assets, fichier)
                    break

        # Logo de Y=3 à Y=23
        if logo_path and os.path.exists(logo_path):
            self.image(logo_path, x=10, y=3, w=15)

        # En-tête administratif à droite
        self.set_font("helvetica", "B", 10)
        self.set_text_color(20, 35, 60)
        self.set_xy(10, 6)
        self.cell(0, 4, "GOUVERNEMENT DE LA NOUVELLE-CALEDONIE", ln=True, align="R")
        self.set_font("helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, "PROJET OPERA", ln=True, align="R")

        # Ligne bleue à Y=28
        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.6)
        self.line(10, 28, 200, 28)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"{self.code_doc} - {self.version} - Page {self.page_no()}/{{nb}}", align="C")

def creer_pdf_sop(proc, site_nom):
    pdf = GenerateurSopPro(
        site_nom,
        nettoyer_texte_pdf(proc['code_doc']),
        nettoyer_texte_pdf(proc['titre']),
        nettoyer_texte_pdf(proc['version']),
        str(proc['date_version']),
        nettoyer_texte_pdf(proc['redacteur'])
    )
    pdf.add_page()
    w_effective = pdf.epw 

    # Positionnement explicite du cartouche sous la ligne bleue (Y=33)
    pdf.set_y(33)

    # Cartouche Titre + Référence
    pdf.set_fill_color(230, 238, 248)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(0, 51, 102)
    
    titre_clean = nettoyer_texte_pdf(proc['titre']).upper()
    if len(titre_clean) > 42:
        titre_clean = titre_clean[:39] + "..."

    pdf.cell(130, 8, f" PROCEDURE : {titre_clean}", fill=True, ln=False)
    pdf.cell(60, 8, f" REF : {proc['code_doc']} ", fill=True, ln=True, align="R")
    pdf.ln(4)

    # 1. Cadre & Domaine
    pdf.set_x(10)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(w_effective, 6, " 1. CADRE & DOMAINE D'APPLICATION", fill=True, ln=True)
    pdf.ln(2)
    
    pdf.set_x(10)
    pdf.set_font("helvetica", "", 9)
    txt_cadre = f"Objectif : {nettoyer_texte_pdf(proc['objectif'])}\nDomaine : {nettoyer_texte_pdf(proc['domaine_application'])}\nMateriel/Docs : {nettoyer_texte_pdf(proc.get('materiel_requis', 'N/A'))}"
    pdf.multi_cell(w_effective, 5, txt_cadre)
    pdf.ln(4)
    
    # 2. Déroulement
    pdf.set_x(10)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(w_effective, 6, " 2. DEROULEMENT DE LA PROCEDURE", fill=True, ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 9)
    deroulement = proc.get('deroulement', [])
    if isinstance(deroulement, list):
        for idx, etape in enumerate(deroulement, start=1):
            pdf.set_x(10)
            txt = etape if isinstance(etape, str) else etape.get('action', '')
            pdf.multi_cell(w_effective, 5, f"{idx}. {nettoyer_texte_pdf(txt)}")
    else:
        pdf.set_x(10)
        pdf.multi_cell(w_effective, 5, nettoyer_texte_pdf(str(deroulement)))
    pdf.ln(4)

    # 3. Vigilance
    if proc.get('points_vigilance'):
        pdf.set_x(10)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(254, 237, 232)
        pdf.set_draw_color(220, 53, 69)
        pdf.cell(w_effective, 6, " 3. POINTS DE VIGILANCE & SECURITE", fill=True, border=1, ln=True)
        
        pdf.set_x(10)
        pdf.set_font("helvetica", "I", 9)
        pdf.multi_cell(w_effective, 5, nettoyer_texte_pdf(proc['points_vigilance']), border='LRB')
        pdf.ln(6)

    # 4. Historique & Gouvernance
    pdf.set_x(10)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_draw_color(180, 180, 180)
    pdf.cell(w_effective, 5, " HISTORIQUE DES MODIFICATIONS & GOUVERNANCE", ln=True)
    
    date_fr = formater_date_fr(proc['date_version'])
    
    pdf.set_x(10)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(40, 5, f" Date : {date_fr}", border=1)
    pdf.cell(30, 5, f" Version : {proc['version']}", border=1)
    pdf.cell(60, 5, f" Redacteur : {nettoyer_texte_pdf(proc['redacteur'])}", border=1)
    pdf.cell(60, 5, " Validation : Direction des Securites", border=1, ln=True)

    return bytes(pdf.output())