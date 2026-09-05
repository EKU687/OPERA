from fpdf import FPDF
import datetime
import os
from utils.pdf_utils import nettoyer_texte_pdf

class GenerateurSopPro(FPDF):
    def __init__(self, site_nom, code_doc, titre, version, date_ver, redacteur):
        super().__init__()
        self.site_nom = site_nom
        self.code_doc = code_doc
        self.titre = titre
        self.version = version
        self.date_ver = date_ver
        self.redacteur = redacteur
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        if os.path.exists("logo_gouv.png"):
            self.image("logo_gouv.png", x=10, y=8, w=25)

        self.set_font("helvetica", "B", 10)
        self.set_text_color(20, 35, 60)
        self.cell(0, 4, "GOUVERNEMENT DE LA NOUVELLE-CALEDONIE", ln=True, align="R")
        self.set_font("helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, "DIRECTION DES SECURITES - PROJET OPERA", ln=True, align="R")
        self.ln(4)

        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.6)
        self.line(10, 22, 200, 22)
        self.ln(4)

        self.set_fill_color(230, 238, 248)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(0, 51, 102)
        self.cell(130, 8, f" PROCEDURE : {nettoyer_texte_pdf(self.titre).upper()}", fill=True, ln=False)
        self.cell(60, 8, f" REF : {self.code_doc} ", fill=True, ln=True, align="R")
        self.ln(3)

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
    
    # Cadre & Domaine
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 6, " 1. CADRE & DOMAINE D'APPLICATION", fill=True, ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 9)
    pdf.multi_cell(0, 5, f"Objectif : {nettoyer_texte_pdf(proc['objectif'])}\nDomaine : {nettoyer_texte_pdf(proc['domaine_application'])}\nMateriel/Docs : {nettoyer_texte_pdf(proc.get('materiel_requis', 'N/A'))}")
    pdf.ln(4)
    
    # Déroulement
    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, " 2. DEROULEMENT DE LA PROCEDURE", fill=True, ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 9)
    deroulement = proc.get('deroulement', [])
    if isinstance(deroulement, list):
        for idx, etape in enumerate(deroulement, start=1):
            txt = etape if isinstance(etape, str) else etape.get('action', '')
            pdf.multi_cell(0, 5, f"{idx}. {nettoyer_texte_pdf(txt)}")
    else:
        pdf.multi_cell(0, 5, nettoyer_texte_pdf(str(deroulement)))
    pdf.ln(4)

    # Vigilance
    if proc.get('points_vigilance'):
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(254, 237, 232)
        pdf.set_draw_color(220, 53, 69)
        pdf.cell(0, 6, " 3. POINTS DE VIGILANCE & SECURITE", fill=True, border=1, ln=True)
        pdf.set_font("helvetica", "I", 9)
        pdf.multi_cell(0, 5, nettoyer_texte_pdf(proc['points_vigilance']), border='LRB')
        pdf.ln(6)

    # Historique & Gouvernance
    pdf.set_font("helvetica", "B", 9)
    pdf.cell(0, 5, " HISTORIQUE DES MODIFICATIONS & GOUVERNANCE", ln=True)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(40, 5, f" Date : {proc['date_version']}", border=1)
    pdf.cell(30, 5, f" Version : {proc['version']}", border=1)
    pdf.cell(60, 5, f" Redacteur : {nettoyer_texte_pdf(proc['redacteur'])}", border=1)
    pdf.cell(60, 5, f" Validation : Direction des Securites", border=1, ln=True)

    return bytes(pdf.output())