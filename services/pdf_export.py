"""
PDF rapport generator met fpdf2.
Genereert professionele rapporten per pand en batch-exports.
"""
from __future__ import annotations


import io
from datetime import datetime
from fpdf import FPDF

from utils.helpers import format_eur, format_pct, format_m2, format_eur_per_m2
from config import get_score_label
from data.constants import CONDITION_MAP
from models.financial import calculate_sensitivity


def _sanitize(text: str) -> str:
    """Vervangt Unicode-tekens die niet ondersteund worden door Helvetica."""
    replacements = {
        "\u2014": "-",   # em dash
        "\u2013": "-",   # en dash
        "\u2018": "'",   # left single quote
        "\u2019": "'",   # right single quote
        "\u201c": '"',   # left double quote
        "\u201d": '"',   # right double quote
        "\u2026": "...", # ellipsis
        "\u2022": "-",   # bullet
        "\u20ac": "EUR", # euro sign (use EUR as fallback)
        "\u2032": "'",   # prime
        "\u2033": '"',   # double prime
        "\u2103": "C",   # degree celsius
        "\u00b2": "2",   # superscript 2
        "\u2264": "<=",  # less than or equal
        "\u2265": ">=",  # greater than or equal
        "\u2605": "*",   # black star
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Remove any remaining non-latin1 chars
    return text.encode("latin-1", errors="replace").decode("latin-1")


class FlipReportPDF(FPDF):
    """Custom PDF klasse met Rome Flip Analyzer branding."""

    def cell(self, w=None, h=None, text="", *args, **kwargs):
        return super().cell(w, h, _sanitize(str(text)) if text else text, *args, **kwargs)

    def multi_cell(self, w, h=None, text="", *args, **kwargs):
        return super().multi_cell(w, h, _sanitize(str(text)) if text else text, *args, **kwargs)

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(26, 54, 93)  # Donkerblauw
        super().cell(0, 8, "Rome Flip Analyzer - Nymos", align="L")
        self.cell(0, 8, datetime.now().strftime("%d-%m-%Y"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(201, 160, 38)  # Goud
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(26, 54, 93)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def subsection_title(self, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(26, 54, 93)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def key_value(self, key: str, value: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(60, 60, 60)
        self.cell(70, 6, key, new_x="END")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")


def generate_property_report(listing: dict, analysis: dict, score_data: dict, params: dict) -> bytes:
    """
    Genereert een volledig PDF-rapport voor een individueel pand.

    Returns:
        PDF als bytes.
    """
    pdf = FlipReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # === PAGINA 1: SAMENVATTING ===
    pdf.add_page()
    _render_summary_page(pdf, listing, analysis, score_data)

    # === PAGINA 2: VOLLEDIGE P&L ===
    pdf.add_page()
    _render_pnl_page(pdf, analysis)

    # === PAGINA 3: ANALYSE ===
    pdf.add_page()
    _render_analysis_page(pdf, listing, analysis, score_data, params)

    return bytes(pdf.output())


def generate_batch_report(analyzed_listings: list[dict], params: dict) -> bytes:
    """
    Genereert een batch PDF-rapport met ranglijst en samenvattingen.

    Returns:
        PDF als bytes.
    """
    pdf = FlipReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Titelpagina
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 15, "Rome Flip Analyzer", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(201, 160, 38)
    pdf.cell(0, 10, "Batch Analyse Rapport", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Datum: {datetime.now().strftime('%d-%m-%Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, f"Aantal panden: {len(analyzed_listings)}", align="C", new_x="LMARGIN", new_y="NEXT")

    # Sorteer op flip score
    sorted_listings = sorted(analyzed_listings, key=lambda l: l.get("flip_score", 0), reverse=True)

    # Ranglijst tabel
    pdf.add_page()
    pdf.section_title("Ranglijst")

    # Tabel header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(26, 54, 93)
    pdf.set_text_color(255, 255, 255)

    col_widths = [12, 40, 28, 20, 28, 28, 34]
    headers = ["#", "Wijk", "Prijs", "m2", "ROI Prima", "ROI Seconda", "Score"]

    for w, h in zip(col_widths, headers):
        pdf.cell(w, 7, h, border=1, align="C", fill=True)
    pdf.ln()

    # Tabel rijen
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)

    for i, listing in enumerate(sorted_listings, 1):
        analysis = listing.get("analysis", {})
        prima_roi = analysis.get("prima_casa", analysis.get("optimistic", {})).get("roi", 0)
        seconda_roi = analysis.get("seconda_casa", analysis.get("conservative", {})).get("roi", 0)
        score = listing.get("flip_score", 0)
        label, color_hex, _ = get_score_label(score)

        # Achtergrondkleur op basis van score
        if score >= 65:
            pdf.set_fill_color(220, 255, 220)
        elif score >= 50:
            pdf.set_fill_color(255, 250, 220)
        else:
            pdf.set_fill_color(255, 230, 230)

        fill = True
        zone = listing.get("zone", "Onbekend")[:20]

        pdf.cell(col_widths[0], 6, str(i), border=1, align="C", fill=fill)
        pdf.cell(col_widths[1], 6, zone, border=1, fill=fill)
        pdf.cell(col_widths[2], 6, format_eur(listing.get("price", 0)), border=1, align="R", fill=fill)
        pdf.cell(col_widths[3], 6, f"{listing.get('surface_m2', 0):.0f}", border=1, align="C", fill=fill)
        pdf.cell(col_widths[4], 6, format_pct(prima_roi), border=1, align="R", fill=fill)
        pdf.cell(col_widths[5], 6, format_pct(seconda_roi), border=1, align="R", fill=fill)
        pdf.cell(col_widths[6], 6, f"{score} - {label}", border=1, align="C", fill=fill)
        pdf.ln()

        # Pagina-break als nodig
        if pdf.get_y() > 260:
            pdf.add_page()

    # Individuele samenvattingen voor top-panden
    top_listings = [l for l in sorted_listings if l.get("flip_score", 0) >= 50]
    if top_listings:
        pdf.add_page()
        pdf.section_title(f"Top Panden (Score >= 50) — {len(top_listings)} panden")

        for listing in top_listings:
            if pdf.get_y() > 220:
                pdf.add_page()

            analysis = listing.get("analysis", {})
            score_data = listing.get("score_data", {})
            score = listing.get("flip_score", 0)
            label, _, meaning = get_score_label(score)

            pdf.subsection_title(f"{listing.get('zone', 'Onbekend')} — Score: {score} ({label})")
            pdf.key_value("Prijs:", format_eur(listing.get("price", 0)))
            pdf.key_value("Oppervlakte:", format_m2(listing.get("surface_m2", 0)))
            pdf.key_value("Prijs/m2:", format_eur_per_m2(listing.get("price_per_m2", 0)))
            prima = analysis.get("prima_casa", analysis.get("optimistic", {}))
            seconda = analysis.get("seconda_casa", analysis.get("conservative", {}))
            pdf.key_value("ROI Prima Casa:", format_pct(prima.get("roi", 0)))
            pdf.key_value("ROI Seconda Casa:", format_pct(seconda.get("roi", 0)))
            pdf.key_value("Winst Prima Casa:", format_eur(prima.get("net_profit", 0)))
            pdf.key_value("Winst Seconda Casa:", format_eur(seconda.get("net_profit", 0)))

            risk_flags = listing.get("risk_flags", [])
            if risk_flags:
                pdf.key_value("Risico's:", ", ".join(risk_flags[:3]))

            if listing.get("url"):
                pdf.key_value("URL:", listing["url"])

            pdf.ln(4)

    return bytes(pdf.output())


def _render_summary_page(pdf: FlipReportPDF, listing: dict, analysis: dict, score_data: dict):
    """Rendert pagina 1: samenvatting."""
    score = score_data["flip_score"]
    label, color_hex, meaning = get_score_label(score)

    # Titel
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(26, 54, 93)
    title = listing.get("title", "Onbekend pand")
    if len(title) > 60:
        title = title[:57] + "..."
    pdf.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Score box
    r, g, b = int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
    pdf.set_fill_color(r, g, b)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(40, 20, str(score), border=0, fill=True, align="C")
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(80, 20, f"  {label}", align="L")
    pdf.ln(25)

    pdf.set_text_color(0, 0, 0)
    pdf.body_text(meaning)

    # Kerngetallen
    pdf.section_title("Kerngetallen")
    pdf.key_value("Vraagprijs:", format_eur(listing["price"]))
    pdf.key_value("Oppervlakte:", format_m2(listing["surface_m2"]))
    pdf.key_value("Prijs per m2:", format_eur_per_m2(listing["price_per_m2"]))
    pdf.key_value("Wijk:", listing.get("zone", "Onbekend"))

    if listing.get("address"):
        pdf.key_value("Adres:", listing["address"])
    if listing.get("floor") is not None:
        floor_text = "Begane grond" if listing["floor"] == 0 else f"Verdieping {listing['floor']}"
        pdf.key_value("Verdieping:", floor_text)

    condition_label = CONDITION_MAP.get(listing.get("condition", ""), listing.get("condition", ""))
    if condition_label:
        pdf.key_value("Staat:", condition_label)
    if listing.get("energy_class"):
        pdf.key_value("Energieklasse:", listing["energy_class"])

    pdf.ln(4)

    # ROI
    pdf.section_title("Rendement")
    prima = analysis["prima_casa"]
    seconda = analysis["seconda_casa"]
    pdf.key_value("ROI Prima Casa (2%):", format_pct(prima["roi"]))
    pdf.key_value("ROI Seconda Casa (9%):", format_pct(seconda["roi"]))
    pdf.key_value("Midpoint ROI:", format_pct(analysis["midpoint_roi"]))
    pdf.key_value("Winst Prima Casa:", format_eur(prima["net_profit"]))
    pdf.key_value("Winst Seconda Casa:", format_eur(seconda["net_profit"]))

    # Risicovlaggen
    risk_flags = score_data.get("risk_flags", [])
    if risk_flags:
        pdf.ln(4)
        pdf.section_title("Risicovlaggen")
        for flag in risk_flags:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(192, 57, 43)
            pdf.cell(5, 6, "!", new_x="END")
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 6, f"  {flag}", new_x="LMARGIN", new_y="NEXT")


def _render_pnl_page(pdf: FlipReportPDF, analysis: dict):
    """Rendert pagina 2: volledige P&L tabel."""
    pdf.section_title("Volledige Winst & Verliesrekening")

    prima = analysis["prima_casa"]
    seconda = analysis["seconda_casa"]

    # Tabel header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(26, 54, 93)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(70, 7, "Kostenpost", border=1, fill=True)
    pdf.cell(55, 7, "Prima Casa (2%)", border=1, align="C", fill=True)
    pdf.cell(55, 7, "Seconda Casa (9%)", border=1, align="C", fill=True)
    pdf.ln()

    # Rijen
    pnl_rows = [
        ("AANKOOPZIJDE", "", "", True),
        ("Aankoopprijs", format_eur(prima["purchase_price"]), format_eur(seconda["purchase_price"]), False),
        ("Registratiebelasting", format_eur(prima["registration_tax"]), format_eur(seconda["registration_tax"]), False),
        ("Notaris + kadaster", format_eur(prima["notary"]), format_eur(seconda["notary"]), False),
        ("Makelaar aankoop", format_eur(prima["broker_buy"]), format_eur(seconda["broker_buy"]), False),
        ("Renovatiekosten", format_eur(prima["renovation"]), format_eur(seconda["renovation"]), False),
        ("Architect + vergunningen", format_eur(prima["architect"]), format_eur(seconda["architect"]), False),
        ("Onvoorzien", format_eur(prima["contingency"]), format_eur(seconda["contingency"]), False),
        ("Holding costs", format_eur(prima["holding_costs"]), format_eur(seconda["holding_costs"]), False),
        ("TOTALE INVESTERING", format_eur(prima["total_investment"]), format_eur(seconda["total_investment"]), True),
        ("", "", "", False),
        ("VERKOOPZIJDE", "", "", True),
        ("Geschatte verkoopprijs", format_eur(prima["sale_price"]), format_eur(seconda["sale_price"]), False),
        ("Makelaar verkoop", format_eur(prima["broker_sell"]), format_eur(seconda["broker_sell"]), False),
        ("Plusvalenza (26%)", format_eur(prima["plusvalenza_tax"]), format_eur(seconda["plusvalenza_tax"]), False),
        ("NETTO OPBRENGST", format_eur(prima["net_revenue"]), format_eur(seconda["net_revenue"]), True),
        ("", "", "", False),
        ("NETTO WINST", format_eur(prima["net_profit"]), format_eur(seconda["net_profit"]), True),
        ("ROI", format_pct(prima["roi"]), format_pct(seconda["roi"]), True),
    ]

    for label, prima_val, seconda_val, is_bold in pnl_rows:
        if not label:
            pdf.ln(2)
            continue

        if is_bold:
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_fill_color(240, 240, 240)
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_fill_color(255, 255, 255)

        pdf.set_text_color(0, 0, 0)
        pdf.cell(70, 6, label, border=1, fill=is_bold)
        pdf.cell(55, 6, prima_val, border=1, align="R", fill=is_bold)
        pdf.cell(55, 6, seconda_val, border=1, align="R", fill=is_bold)
        pdf.ln()


def _render_analysis_page(pdf: FlipReportPDF, listing: dict, analysis: dict, score_data: dict, params: dict):
    """Rendert pagina 3: score breakdown, gevoeligheid, wijkcontext."""

    # Score breakdown
    pdf.section_title("Flip Score Breakdown")
    scores = score_data.get("component_scores", {})
    weights = score_data.get("weights", {})

    component_names = {
        "roi": "ROI",
        "margin": "Marge",
        "neighborhood": "Wijk",
        "risk": "Risico",
        "liquidity": "Liquiditeit",
        "surface": "Oppervlakte",
    }

    for key, name in component_names.items():
        val = scores.get(key, 0)
        weight = weights.get(key, 0) * 100
        weighted = val * weights.get(key, 0)
        pdf.key_value(f"{name} ({weight:.0f}%):", f"{val}/100 (gewogen: {weighted:.1f})")

    pdf.ln(4)

    # Gevoeligheidsanalyse
    pdf.section_title("Gevoeligheidsanalyse")
    scenarios = calculate_sensitivity(listing, params)

    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(26, 54, 93)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(55, 7, "Scenario", border=1, fill=True)
    pdf.cell(30, 7, "Mid. ROI", border=1, align="C", fill=True)
    pdf.cell(40, 7, "Winst Prima", border=1, align="C", fill=True)
    pdf.cell(40, 7, "Winst Seconda", border=1, align="C", fill=True)
    pdf.cell(25, 7, "Delta", border=1, align="C", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)

    for s in scenarios:
        delta = f"+{s['delta_roi']:.1f}%" if s["delta_roi"] >= 0 else f"{s['delta_roi']:.1f}%"
        pdf.cell(55, 6, s["scenario"], border=1)
        pdf.cell(30, 6, format_pct(s["midpoint_roi"]), border=1, align="R")
        pdf.cell(40, 6, format_eur(s["prima_profit"]), border=1, align="R")
        pdf.cell(40, 6, format_eur(s["seconda_profit"]), border=1, align="R")
        pdf.cell(25, 6, delta, border=1, align="R")
        pdf.ln()

    pdf.ln(4)

    # Verkoopprijsonderbouwing
    sale_estimate = analysis.get("sale_price_estimate", {})
    if sale_estimate:
        pdf.section_title("Verkoopprijsonderbouwing")
        justification = sale_estimate.get("justification_text", "")
        if justification:
            pdf.body_text(justification)

    # Locatieanalyse
    location = analysis.get("location_quality", {})
    if location:
        if pdf.get_y() > 200:
            pdf.add_page()
        pdf.section_title(f"Locatieanalyse (Score: {location.get('overall_score', '?')}/100)")
        pdf.body_text(location.get("summary", ""))

        for factor in location.get("factors", []):
            cat = factor.get("category", "neutraal")
            prefix = "+" if cat == "positief" else "-" if cat == "negatief" else "~"
            impact = factor.get("impact", 0)
            pdf.set_font("Helvetica", "B", 9)
            if cat == "positief":
                pdf.set_text_color(45, 138, 78)
            elif cat == "negatief":
                pdf.set_text_color(192, 57, 43)
            else:
                pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"{prefix} {factor['name']} ({impact:+d} punten)", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            pdf.multi_cell(0, 4, factor.get("explanation", ""))
            pdf.ln(1)

    pdf.ln(2)

    # Wijkcontext
    neighborhood = analysis.get("neighborhood_data", {})
    if neighborhood:
        if pdf.get_y() > 230:
            pdf.add_page()
        pdf.section_title("Wijkcontext")
        pdf.key_value("Wijk (matched):", neighborhood.get("matched_zone", "Onbekend"))
        pdf.key_value("Risico:", neighborhood.get("risk_level", "Onbekend").capitalize())
        pdf.key_value("Groei (j-o-j):", format_pct(neighborhood.get("yoy_growth", 0) * 100))
        pdf.key_value("Gem. verkooptijd:", f"{neighborhood.get('avg_selling_time_months', 0)} maanden")
        pdf.key_value("Gerenoveerd mid. prijs:", format_eur_per_m2(neighborhood.get("renovated_price_mid", 0)))
        if neighborhood.get("notes"):
            pdf.ln(2)
            pdf.body_text(neighborhood["notes"])
