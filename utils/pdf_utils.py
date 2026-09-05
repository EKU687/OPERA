def nettoyer_texte_pdf(texte: str) -> str:
    """Transforme les caractères Unicode complexes en équivalents Latin-1 compatibles Helvetica."""
    if not texte:
        return ""
    
    replacements = {
        "…": "...",
        "—": "-",
        "–": "-",
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "«": '"',
        "»": '"',
        "•": "-",
        "°": " deg.",
        "œ": "oe",
        "Œ": "OE",
        "æ": "ae",
        "Æ": "AE",
    }
    
    for char_invalide, remplacement in replacements.items():
        texte = texte.replace(char_invalide, remplacement)
        
    return texte