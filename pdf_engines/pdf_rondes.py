from fpdf import FPDF
import datetime
import os
from utils.pdf_utils import nettoyer_texte_pdf

class GenerateurProtocolePro(FPDF):
    def __init__(self, site_nom, mission_titre, horaire):
        super().__init__()
        self.site_nom = site_nom
        self.mission_titre = mission_titre
        self.horaire = horaire
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        if os.path.exists("logo_gouv.png"):
            self.image("logo_gouv.png", x=10, y=8, w=28)

        self.set_font("helvetica", "B", 11)
        self.set_text_color(20, 35, 60)
        self.cell(0, 5, "GOUVERNEMENT DE LA NOUVELLE-CALEDONIE", ln=True, align="R")
        self.set_font("helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "DIRECTION DES SECURITES - PROJET OPERA", ln=True, align="R")
        self.ln(6)

        self.set_draw_color(0, 51, 102)
        self.set_line_width(0.8)
        self.line(10, 25, 200, 25)
        self.ln(6)

        titre_clean = nettoyer_texte_pdf(self.mission_titre).upper()
        site_clean = nettoyer_texte_pdf(self.site_nom).upper()
        horaire_clean = nettoyer_texte_pdf(str(self.horaire))
        
        self.set_fill_color(240, 243, 246)
        self.set_font("helvetica", "B", 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f" PROTOCOLE : {site_clean} - {titre_clean} ({horaire_clean})", fill=True, ln=True)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        date_edition = datetime.datetime.now().strftime("%d/%m/%Y a %H:%M")
        self.cell(0, 10, f"Document Officiel OPERA - Genere le {date_edition} - Page {self.page_no()}/{{nb}}", align="C")

def creer_pdf_ronde(nom_site, mission, secteurs):
    pdf = GenerateurProtocolePro(nom_site, mission['titre_mission'], mission['horaire_cible'])
    pdf.add_page()
    
    for secteur in secteurs:
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(215, 228, 242)
        
        nom_sec_clean = nettoyer_texte_pdf(secteur['nom_secteur']).upper()
        pdf.cell(0, 7, f" SECTEUR : {nom_sec_clean}", fill=True, ln=True)
        pdf.ln(2)
        
        consignes = sorted(secteur.get('opera_consignes', []), key=lambda x: x['ordre_execution'])
        pdf.set_font("helvetica", "", 10)
        
        for consigne in consignes:
            action = nettoyer_texte_pdf(consigne['type_action']).upper()
            desc = nettoyer_texte_pdf(consigne['description'])
            
            pdf.cell(5, 6, "") 
            pdf.cell(0, 6, f"[  ] {action} : {desc}", ln=True)
        pdf.ln(4)
        
    return bytes(pdf.output())