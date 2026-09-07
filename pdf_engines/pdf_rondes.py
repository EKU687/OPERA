import os
import datetime
from fpdf import FPDF
from utils.pdf_utils import nettoyer_texte_pdf

def formater_date_fr(date_val):
    if not date_val:
        return datetime.datetime.now().strftime("%d/%m/%Y")
    if isinstance(date_val, str):
        try:
            dt = datetime.datetime.strptime(date_val.split("T")[0], "%Y-%m-%d")
            return dt.strftime("%d/%m/%Y")
        except ValueError:
            return date_val
    elif isinstance(date_val, (datetime.date, datetime.datetime)):
        return date_val.strftime("%d/%m/%Y")
    return str(date_val)

class GenerateurProtocolePro(FPDF):
    def __init__(self, site_nom, mission_titre, horaire):
        super().__init__()
        self.site_nom = site_nom
        self.mission_titre = mission_titre
        self.horaire = horaire
        
        self.set_margins(10, 41, 10)
        self.set_auto_page_break(auto=True, margin=15)

    def add_page(self, orientation="", format="", same=False):
        super().add_page(orientation=orientation, format=format, same=same)
        self.set_y(41)

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
            self.image(logo_path, x=10, y=3, w=15)

        self.set_font("helvetica", "B", 10)
        self.set_text_color(20, 35, 60)
        self.set_xy(10, 6)
        self.cell(0, 4, "GOUVERNEMENT DE LA NOUVELLE-CALEDONIE", ln=True, align="R")
        self.set_font("helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, "PROJET OPERA", ln=True, align="R")

        # Ligne bleue descendue à Y=28 mm pour laisser respirer "CALÉDONIE"
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

    # Cartouche de Mission (Page 1) à Y=32
    pdf.set_y(32)
    pdf.set_fill_color(230, 238, 248)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(0, 51, 102)
    
    titre_clean = nettoyer_texte_pdf(mission['titre_mission']).upper()
    site_clean = nettoyer_texte_pdf(nom_site).upper()
    horaire_clean = nettoyer_texte_pdf(str(mission['horaire_cible']))
    
    pdf.cell(130, 8, f" PROTOCOLE DE RONDE : {titre_clean}", fill=True, ln=False)
    pdf.cell(60, 8, f" SITE : {site_clean} ({horaire_clean}) ", fill=True, ln=True, align="R")
    pdf.ln(4)
    
    for secteur in secteurs:
        consignes = sorted(secteur.get('opera_consignes', []), key=lambda x: x['ordre_execution'])
        hauteur_bloc = 8 + (len(consignes) * 6)
        
        if pdf.get_y() + hauteur_bloc > 270:
            pdf.add_page()

        pdf.set_x(10)
        pdf.set_font("helvetica", "B", 10)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(0, 0, 0)
        
        nom_sec_clean = nettoyer_texte_pdf(secteur['nom_secteur']).upper()
        pdf.cell(w_effective, 6, f" SECTEUR : {nom_sec_clean}", fill=True, ln=True)
        pdf.ln(2)
        
        pdf.set_font("helvetica", "", 9)
        for consigne in consignes:
            action = nettoyer_texte_pdf(consigne['type_action']).upper()
            desc = nettoyer_texte_pdf(consigne['description'])
            
            pdf.set_x(10)
            pdf.cell(5, 5, "") 
            pdf.multi_cell(w_effective - 5, 5, f"[  ] {action} : {desc}")
        pdf.ln(3)
        
    if pdf.get_y() + 20 > 270:
        pdf.add_page()

    pdf.ln(2)
    pdf.set_x(10)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_draw_color(180, 180, 180)
    pdf.cell(w_effective, 5, " HISTORIQUE DES MODIFICATIONS & GOUVERNANCE", ln=True)
    
    date_fr = formater_date_fr(mission.get('date_creation'))
    horaire_txt = horaire_clean
    if len(horaire_txt) > 22:
        horaire_txt = horaire_txt[:19] + "..."

    pdf.set_x(10)
    pdf.set_font("helvetica", "", 8)
    pdf.cell(35, 5, f" Date : {date_fr}", border=1)
    pdf.cell(45, 5, f" Horaire : {horaire_txt}", border=1)
    pdf.cell(55, 5, f" Editeur : Eric Kuter", border=1)
    pdf.cell(55, 5, " Validation : PC Surete GNC", border=1, ln=True)

    return bytes(pdf.output())