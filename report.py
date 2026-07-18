"""
PastoSmart PreProcessor v1.0
Geração de relatório PDF com ReportLab.
Layout compatível com o modelo definido no projeto.
"""

import os
import io
import datetime
import numpy as np
import matplotlib
matplotlib.use("Agg")   # backend sem janela
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.lib            import colors
from reportlab.lib.units      import cm
from reportlab.platypus       import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums  import TA_CENTER, TA_LEFT

from typing import Dict, Any


# ── Paleta de cores do PDF ──────────────────────────────────────────
GREEN_DARK  = colors.HexColor("#0B7A4E")
GREEN_LIGHT = colors.HexColor("#12B76A")
GRAY_BG     = colors.HexColor("#F4F6F4")
GRAY_LINE   = colors.HexColor("#CCCCCC")
BLACK       = colors.black
WHITE       = colors.white


class ReportGenerator:
    """
    Gera relatório PDF do processamento.

    Parâmetros
    ----------
    stats       : dict — estatísticas por banda
    index_maps  : dict — arrays dos índices calculados
    bands_norm  : dict — bandas normalizadas
    mask        : np.ndarray — máscara de pixels válidos
    src_path    : str — caminho da imagem original
    out_dir     : str — pasta de saída
    """

    def __init__(self, stats, index_maps, bands_norm, mask, src_path, out_dir):
        self.stats      = stats
        self.index_maps = index_maps
        self.bands_norm = bands_norm
        self.mask       = mask
        self.src_path   = src_path
        self.out_dir    = out_dir

    def generate(self, filename: str = "Relatorio.pdf"):
        out_path = os.path.join(self.out_dir, filename)
        doc = SimpleDocTemplate(
            out_path,
            pagesize=A4,
            leftMargin=2*cm, rightMargin=2*cm,
            topMargin=2*cm,  bottomMargin=2*cm,
            title="PastoSmart PreProcessor – Relatório"
        )

        styles = getSampleStyleSheet()
        story  = []

        # ── Estilos personalizados ──────────────────────────────
        title_style = ParagraphStyle(
            "PastoTitle",
            fontSize=18, leading=22,
            textColor=WHITE,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
            spaceAfter=4,
        )
        sub_style = ParagraphStyle(
            "PastoSub",
            fontSize=10, leading=14,
            textColor=colors.HexColor("#D0FFE8"),
            alignment=TA_CENTER,
            fontName="Helvetica",
        )
        section_style = ParagraphStyle(
            "PastoSection",
            fontSize=12, leading=16,
            textColor=GREEN_DARK,
            fontName="Helvetica-Bold",
            spaceBefore=12, spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "PastoBody",
            fontSize=9, leading=14,
            textColor=BLACK,
            fontName="Helvetica",
        )
        check_style = ParagraphStyle(
            "PastoCheck",
            fontSize=9, leading=14,
            textColor=GREEN_DARK,
            fontName="Helvetica-Bold",
        )

        # ── Cabeçalho ───────────────────────────────────────────
        header_data = [[
            Paragraph("🌿  PastoSmart PreProcessor", title_style),
        ]]
        header_table = Table(header_data, colWidths=[17*cm])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), GREEN_DARK),
            ("ROWPADDING", (0,0), (-1,-1), 12),
            ("ROUNDEDCORNERS", [6]),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.3*cm))

        # ── Informações da imagem ────────────────────────────────
        story.append(Paragraph("Informações da Imagem", section_style))
        story.append(HRFlowable(width="100%", color=GRAY_LINE))
        story.append(Spacer(1, 0.2*cm))

        img_name  = os.path.basename(self.src_path)
        now_str   = datetime.datetime.now().strftime("%d/%m/%Y  %H:%M")
        info_data = [
            ["Arquivo",  img_name],
            ["Processado em", now_str],
            ["Bandas",   ", ".join(self.bands_norm.keys())],
            ["Resolução", self._get_resolution()],
        ]
        info_table = Table(info_data, colWidths=[4*cm, 13*cm])
        info_table.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (0,-1), GRAY_BG),
            ("TEXTCOLOR",   (0,0), (0,-1), GREEN_DARK),
            ("FONTNAME",    (0,0), (0,-1), "Helvetica-Bold"),
            ("FONTNAME",    (1,0), (1,-1), "Helvetica"),
            ("FONTSIZE",    (0,0), (-1,-1), 9),
            ("GRID",        (0,0), (-1,-1), 0.5, GRAY_LINE),
            ("ROWPADDING",  (0,0), (-1,-1), 5),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.4*cm))

        # ── Estatísticas por banda ───────────────────────────────
        story.append(Paragraph("Estatísticas por Banda", section_style))
        story.append(HRFlowable(width="100%", color=GRAY_LINE))
        story.append(Spacer(1, 0.2*cm))

        for band_name, s in self.stats.items():
            story.append(Paragraph(band_name, ParagraphStyle(
                "BandTitle", fontSize=10, leading=14,
                textColor=GREEN_LIGHT, fontName="Helvetica-Bold",
                spaceBefore=6,
            )))
            rows = self._stats_to_rows(s)
            if rows:
                t = Table(rows, colWidths=[5*cm, 5*cm, 5*cm, 2*cm])
                t.setStyle(TableStyle([
                    ("BACKGROUND",  (0,0), (-1,0), GREEN_DARK),
                    ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
                    ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
                    ("FONTNAME",    (0,1), (-1,-1), "Helvetica"),
                    ("FONTSIZE",    (0,0), (-1,-1), 8),
                    ("ALIGN",       (0,0), (-1,-1), "CENTER"),
                    ("GRID",        (0,0), (-1,-1), 0.5, GRAY_LINE),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, GRAY_BG]),
                    ("ROWPADDING",  (0,0), (-1,-1), 4),
                ]))
                story.append(t)

        story.append(Spacer(1, 0.4*cm))

        # ── Índices calculados ───────────────────────────────────
        story.append(Paragraph("Índices de Vegetação", section_style))
        story.append(HRFlowable(width="100%", color=GRAY_LINE))
        story.append(Spacer(1, 0.2*cm))

        idx_rows = [["Índice", "Média", "Mín", "Máx", "Status"]]
        for idx_name, arr in self.index_maps.items():
            valid = arr[self.mask & ~np.isnan(arr)]
            if valid.size > 0:
                mean_v = f"{np.nanmean(valid):.4f}"
                min_v  = f"{np.nanmin(valid):.4f}"
                max_v  = f"{np.nanmax(valid):.4f}"
                status = "✔ OK"
            else:
                mean_v = min_v = max_v = "—"
                status = "⚠ Sem dados"
            idx_rows.append([idx_name, mean_v, min_v, max_v, status])

        idx_table = Table(idx_rows, colWidths=[3*cm, 3.5*cm, 3.5*cm, 3.5*cm, 3.5*cm])
        idx_table.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), GREEN_DARK),
            ("TEXTCOLOR",   (0,0), (-1,

