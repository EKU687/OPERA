import os
import datetime
from fpdf import FPDF
from utils.pdf_utils import nettoyer_texte_pdf

class GenerateurProtocolePro(FPDF):
    def __init__(self, site_nom, mission_titre, horaire):
        super().__init__()
        self.site_nom = site_nom
        self.mission_titre = mission_titre
        self.horaire = horaire
        self.set_margins(10, 45, 10)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        dossier_pdf_engines = os.path.dirname(os.path.abspath(__file__))
        racine_projet = os.path.dirname(dossier_pdf_engines)
        dossier_assets = os.path.join(racine_projet, "assets")

        logo_path = None
        if os.path.exists(dossier_assets):
            for fichier in os.listdir(dossier_assets):
                if fichier.lower().startswith("logo_gouv"):
                    logo_path = os.path.join(dossier_assets, fichier)
                    break

        if logo_path and os.path.exists(logo_path):
            self.image(logo_path, x=10, y=5, w=16)

        self.set_font("helvetica", "B", 10)
        self.set_text_color(20, 35, 60)
        self.set_xy(10, 6)
        self.cell(0, 4, "GOUVERNEMENT DE LA NOUVELLE-CALEDONIE", ln=True, align="R")
        self.set_font("helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, "PROJET OPERA", ln=True, align="R")

        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.6)
        self.line(10, 28, 200, 28)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        date_edition = datetime.datetime.now().strftime("%d/%m/%Y a %H:%M")
        self.cell(0, 10, f"Document Officiel OPERA - Genere le {date_edition} - Page {self.page_no()}/{{nb}}", align="C")

def creer_pdf_ronde(nom_site, mission, secteurs):
    pdf = GenerateurProtocolePro(nom_site, mission['titre_mission'], mission['horaire_cible'])
    pdf.add_page()
    w_effective = pdf.epw
    
    pdf.set_y(32)

    titre_clean = nettoyer_texte_pdf(mission['titre_mission']).upper()
    site_clean = nettoyer_texte_pdf(nom_site).upper()
    horaire_clean = nettoyer_texte_pdf(str(mission['horaire_cible']))
    
    pdf.set_fill_color(240, 243, 246)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, f" PROTOCOLE : {site_clean} - {titre_clean} ({horaire_clean})", fill=True, ln=True)
    pdf.ln(5)
    
    for secteur in secteurs:
        pdf.set_x(10)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(215, 228, 242)
        
        nom_sec_clean = nettoyer_texte_pdf(secteur['nom_secteur']).upper()
        pdf.cell(w_effective, 7, f" SECTEUR : {nom_sec_clean}", fill=True, ln=True)
        pdf.ln(2)
        
        consignes = sorted(secteur.get('opera_consignes', []), key=lambda x: x['ordre_execution'])
        pdf.set_font("helvetica", "", 10)
        
        for consigne in consignes:
            action = nettoyer_texte_pdf(consigne['type_action']).upper()
            desc = nettoyer_texte_pdf(consigne['description'])
            
            pdf.set_x(10)
            pdf.cell(5, 6, "") 
            pdf.multi_cell(w_effective - 5, 6, f"[  ] {action} : {desc}")
        pdf.ln(4)
        
    return bytes(pdf.output())