"""
Straatclassificatie Antwerpen — A tot E categorie.
Bepaalt correctiefactor op de wijkgemiddelde prijs per m².
"""
from __future__ import annotations

# Standaard correctiefactoren per straatcategorie
STREET_CORRECTION_FACTORS = {
    "A": 1.20,  # Premiumstraat
    "B": 1.10,  # Sterke straat
    "C": 1.00,  # Gemiddelde straat (= wijkgemiddelde)
    "D": 0.85,  # Zwakkere straat
    "E": 0.75,  # Probleemstraat
}

STREET_CATEGORY_LABELS = {
    "A": "Premiumstraat",
    "B": "Sterke straat",
    "C": "Gemiddelde straat",
    "D": "Zwakkere straat",
    "E": "Probleemstraat",
}

# Bekende straatclassificaties in Antwerpen
# Per postcode, per categorie, lijst van straatnamen (of delen ervan)
KNOWN_STREETS: dict[str, dict[str, list[str]]] = {
    "2018": {
        "A": [
            "Cogels-Osylei",
            "Quinten Matsijslei",
            "Belgiëlei",  # parkzijde
            "Generaal Van Merlenstraat",
            "Graaf van Hoornestraat",
            "Ter Rivierenlaan",
            "Transvaalstraat",  # Zurenborg
            "Waterloostraat",  # Zurenborg
        ],
        "B": [
            "Draakplaats",
            "Marnixplaats",
            "Leopold de Waelplaats",
            "Volkstraat",
            "Verschansingstraat",
            "Generaal Lemanstraat",
            "Nerviërsstraat",
        ],
        "D": [
            "Plantin en Moretuslei",  # verkeerszijde
            "Singel",
        ],
    },
    "2000": {
        "A": [
            "Napoleonkaai",
            "Londenbrug",
            "Kattendijkdok",
            "Montevideostraat",  # Eilandje premium
        ],
        "B": [
            "Grote Markt",
            "Groenplaats",
            "Meir",
            "Suikerrui",
            "Schuttershofstraat",
        ],
        "D": [
            "Carnotstraat",
            "De Keyserlei",  # commercieel
            "Pelikaanstraat",
        ],
    },
    "2600": {
        "A": [
            "Fruithoflaan",
            "Mechelsesteenweg",  # villagedeelte
            "Generaal Lemanstraat",  # Berchem rustig deel
        ],
        "B": [
            "Statiestraat",
            "Driehoekstraat",
            "Diksmuidelaan",
        ],
        "D": [
            "Grote Steenweg",  # commercieel, druk
            "Ringfietspad",
        ],
    },
    "2060": {
        "B": [
            "Kroonstraat",
            "Turnhoutsebaan",  # gerenoveerd deel
        ],
        "D": [
            "Turnhoutsebaan",  # druk commercieel deel
            "Plantin en Moretuslei",
        ],
        "E": [
            "Luitenant Lippenslaan",  # zwakker deel
        ],
    },
}


def classify_street(postal_code: str, street_name: str) -> dict:
    """
    Classificeert een straat op basis van bekende straatdata.

    Returns:
        dict met: category (A-E), factor, label, matched_street, explanation
    """
    if not street_name:
        return {
            "category": "C",
            "factor": 1.00,
            "label": "Gemiddelde straat",
            "matched_street": None,
            "explanation": "Geen straatnaam beschikbaar — wijkgemiddelde toegepast.",
        }

    street_lower = street_name.lower().strip()
    pc = str(postal_code).strip()

    # Zoek in bekende straten voor deze postcode
    pc_streets = KNOWN_STREETS.get(pc, {})
    for category, streets in pc_streets.items():
        for known_street in streets:
            if known_street.lower() in street_lower or street_lower in known_street.lower():
                return {
                    "category": category,
                    "factor": STREET_CORRECTION_FACTORS[category],
                    "label": STREET_CATEGORY_LABELS[category],
                    "matched_street": known_street,
                    "explanation": f"{known_street} is geclassificeerd als categorie {category} ({STREET_CATEGORY_LABELS[category]}).",
                }

    # Niet gevonden → standaard C
    return {
        "category": "C",
        "factor": 1.00,
        "label": "Gemiddelde straat",
        "matched_street": None,
        "explanation": f"Straat '{street_name}' niet in database — wijkgemiddelde toegepast.",
    }
