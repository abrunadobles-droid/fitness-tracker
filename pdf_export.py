"""
Generador de PDF para reporte histórico del Fitness Tracker.
Usa fpdf2 (Python puro, sin binarios externos).
"""

from fpdf import FPDF
from datetime import datetime
from constants import FITNESS_METRICS, SLEEP_METRICS, ALL_METRIC_KEYS, MESES_NOMBRES, MESES_CORTOS
from helpers import fmt, get_pct, get_status_class, calculate_score, calculate_averages, is_metric_met


# Colores del tema Dark Neon
BG = (10, 10, 15)
CARD_BG = (26, 26, 46)
HEADER_BG = (21, 21, 37)
CYAN = (6, 182, 212)
PURPLE = (139, 92, 246)
TEXT = (226, 232, 240)
TEXT_DIM = (100, 116, 139)
GREEN = (16, 185, 129)
YELLOW = (245, 158, 11)
RED = (239, 68, 68)
WHITE = (241, 245, 249)

STATUS_COLORS = {'green': GREEN, 'yellow': YELLOW, 'red': RED}


class FitnessReport(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'Letter')
        self.set_auto_page_break(auto=True, margin=15)

    def _bg(self):
        self.set_fill_color(*BG)
        self.rect(0, 0, self.w, self.h, 'F')

    def header(self):
        self._bg()

    def footer(self):
        self.set_y(-10)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(*TEXT_DIM)
        self.cell(0, 5, f'Generado {datetime.now().strftime("%d/%m/%Y %H:%M")}  |  Fitness Tracker', align='C')

    def _title_section(self, text):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(*CYAN)
        self.cell(0, 8, f'// {text}', ln=True)
        self.set_draw_color(*CYAN)
        self.set_line_width(0.2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def _status_dot(self, x, y, color_name):
        color = STATUS_COLORS.get(color_name, TEXT_DIM)
        self.set_fill_color(*color)
        self.ellipse(x, y, 3, 3, 'F')

    def _table(self, headers, rows, col_widths=None):
        if col_widths is None:
            available = self.w - self.l_margin - self.r_margin
            col_widths = [available / len(headers)] * len(headers)

        # Header row
        self.set_fill_color(*HEADER_BG)
        self.set_font('Helvetica', 'B', 7)
        self.set_text_color(*TEXT_DIM)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=0, fill=True, align='L' if i == 0 else 'C')
        self.ln()

        # Data rows
        self.set_font('Helvetica', '', 8)
        for row in rows:
            self.set_fill_color(*CARD_BG)
            for i, cell in enumerate(row):
                color = WHITE if i > 0 else TEXT
                self.set_text_color(*color)
                self.cell(col_widths[i], 6.5, str(cell), border=0, fill=True, align='L' if i == 0 else 'C')
            self.ln(0.3)
            self.ln()


def generate_historico_pdf(all_data, metas, meses_cerrados, current_year):
    """
    Genera PDF con reporte histórico completo.
    Returns: bytes del PDF
    """
    pdf = FitnessReport()
    all_metrics = FITNESS_METRICS + SLEEP_METRICS
    total_metrics = len(ALL_METRIC_KEYS)

    avg_data = calculate_averages(all_data)
    avg_score = sum(is_metric_met(key, avg_data[key], metas[key]) for key in ALL_METRIC_KEYS)

    # ============ PAGINA 1: HEADER + PROMEDIO GENERAL ============
    pdf.add_page()

    # Title
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 12, 'FITNESS TRACKER', align='C', ln=True)

    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*TEXT_DIM)
    n = len(all_data)
    pdf.cell(0, 6, f'REPORTE {current_year}  |  {n} MESES  |  {avg_score}/{total_metrics} METAS PROMEDIO', align='C', ln=True)
    pdf.ln(8)

    # Promedio General
    pdf._title_section(f'PROMEDIO GENERAL ({n} MESES)')

    headers = ['Metrica', 'Promedio', 'Meta', '%', 'Status']
    widths = [55, 30, 30, 20, 20]
    rows = []
    for key, label, unit, tipo in all_metrics:
        valor = avg_data[key]
        meta = metas[key]
        pct = get_pct(key, valor, meta, tipo)
        status = get_status_class(pct)
        dot = '+++' if status == 'green' else ('++' if status == 'yellow' else '+')
        rows.append([f'  {label}', fmt(valor, unit), fmt(meta, unit), f'{pct:.0f}%', dot])

    pdf._table(headers, rows, widths)
    pdf.ln(5)

    # Score summary
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*CYAN)
    pdf.cell(0, 8, f'SCORE PROMEDIO: {avg_score} / {total_metrics} metas cumplidas', align='C', ln=True)

    # ============ PAGINA 2: DETALLE POR MES ============
    pdf.add_page()
    pdf._title_section('DETALLE POR MES')

    for i, (mes, data) in enumerate(zip(meses_cerrados, all_data)):
        score = calculate_score(data, metas)

        # Check if we need a new page (if less than 80mm remaining)
        if pdf.get_y() > 210:
            pdf.add_page()

        # Month header
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(*WHITE)
        pdf.set_fill_color(*CARD_BG)
        pdf.cell(0, 8, f'  {MESES_NOMBRES[mes]} {current_year}  -  {score}/{total_metrics} metas', fill=True, ln=True)
        pdf.ln(1)

        headers = ['Metrica', 'Valor', 'Meta', '%']
        widths = [60, 35, 35, 25]
        rows = []
        for key, label, unit, tipo in all_metrics:
            pct = get_pct(key, data[key], metas[key], tipo)
            status = get_status_class(pct)
            indicator = '[OK]' if status == 'green' else ('[~]' if status == 'yellow' else '[X]')
            rows.append([f'{indicator} {label}', fmt(data[key], unit), fmt(metas[key], unit), f'{pct:.0f}%'])

        pdf._table(headers, rows, widths)
        pdf.ln(4)

    # ============ PAGINA 3: COMPARATIVA MENSUAL ============
    pdf.add_page()
    pdf._title_section('COMPARATIVA MENSUAL')

    # Calculate column widths based on number of months
    n_months = len(meses_cerrados)
    metric_col = 42
    month_col = (pdf.w - pdf.l_margin - pdf.r_margin - metric_col - 24 - 24) / max(n_months, 1)
    widths = [metric_col] + [month_col] * n_months + [24, 24]

    month_headers = [MESES_CORTOS[m] for m in meses_cerrados]
    headers = ['Metrica'] + month_headers + ['Prom', 'Meta']

    rows = []
    for key, label, unit, tipo in all_metrics:
        row = [label]
        for d in all_data:
            row.append(fmt(d[key], unit))
        row.append(fmt(avg_data[key], unit))
        row.append(fmt(metas[key], unit))
        rows.append(row)

    # Score row
    score_row = ['SCORE']
    for d in all_data:
        s = calculate_score(d, metas)
        score_row.append(f'{s}/{total_metrics}')
    score_row.append(f'{avg_score}/{total_metrics}')
    score_row.append(f'{total_metrics}/{total_metrics}')
    rows.append(score_row)

    pdf._table(headers, rows, widths)

    return pdf.output()
