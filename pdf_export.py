"""
Generador de PDF para reporte histórico del Fitness Tracker.
Usa fpdf2 (Python puro, sin binarios externos). Tema Dark Neon.
"""

from fpdf import FPDF
from datetime import datetime
from constants import DASHBOARD_METRICS, MESES_NOMBRES, MESES_CORTOS
from helpers import fmt, get_pct, get_status_class, calculate_averages, is_metric_met


# Colores del tema Dark Neon
BG = (10, 10, 15)
CARD_BG = (26, 26, 46)
CARD_BG_ALT = (31, 31, 54)
HEADER_BG = (21, 21, 37)
CYAN = (6, 182, 212)
PURPLE = (139, 92, 246)
TEXT = (226, 232, 240)
TEXT_DIM = (130, 145, 170)
GREEN = (16, 185, 129)
YELLOW = (245, 158, 11)
RED = (239, 68, 68)
WHITE = (241, 245, 249)

STATUS_COLORS = {'green': GREEN, 'yellow': YELLOW, 'red': RED}


class FitnessReport(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'Letter')
        self.set_auto_page_break(auto=True, margin=16)

    def header(self):
        # Fondo oscuro en cada página + línea de acento arriba
        self.set_fill_color(*BG)
        self.rect(0, 0, self.w, self.h, 'F')
        self.set_fill_color(*CYAN)
        self.rect(0, 0, self.w * 0.55, 1.6, 'F')
        self.set_fill_color(*PURPLE)
        self.rect(self.w * 0.55, 0, self.w * 0.45, 1.6, 'F')

    def footer(self):
        self.set_y(-11)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(*TEXT_DIM)
        self.cell(0, 5,
                  f'FITNESS TRACKER  ·  Generado {datetime.now().strftime("%d/%m/%Y")}  ·  pag. {self.page_no()}',
                  align='C')

    # ---------- bloques de diseño ----------

    def banner(self, title, subtitle):
        self.ln(6)
        self.set_font('Helvetica', 'B', 26)
        self.set_text_color(*WHITE)
        self.cell(0, 12, title, align='C', ln=True)
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*CYAN)
        self.cell(0, 6, subtitle, align='C', ln=True)
        self.ln(4)

    def section(self, text):
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*CYAN)
        self.cell(0, 9, f'// {text}', ln=True)
        self.set_draw_color(*CYAN)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3.5)

    def summary_cards(self, cards):
        """cards: lista de (valor, label). Se dibujan en una fila centrada."""
        n = len(cards)
        gap = 5
        avail = self.w - self.l_margin - self.r_margin
        cw = (avail - gap * (n - 1)) / n
        ch = 22
        x = self.l_margin
        y = self.get_y()
        for value, label in cards:
            self.set_fill_color(*CARD_BG)
            self.rect(x, y, cw, ch, 'F')
            self.set_draw_color(*HEADER_BG)
            self.rect(x, y, cw, ch)
            self.set_xy(x, y + 4)
            self.set_font('Helvetica', 'B', 16)
            self.set_text_color(*CYAN)
            self.cell(cw, 8, str(value), align='C')
            self.set_xy(x, y + 13)
            self.set_font('Helvetica', 'B', 6.5)
            self.set_text_color(*TEXT_DIM)
            self.cell(cw, 5, label.upper(), align='C')
            x += cw + gap
        self.set_y(y + ch + 7)

    def table(self, headers, rows, widths, statuses=None, cell_colors=None, highlight_last=False):
        """
        Tabla estilizada con zebra rows.
        - statuses: lista opcional (una por fila) con 'green'/'yellow'/'red' para
          dibujar un dot al inicio de la primera celda.
        - cell_colors: dict {(fila, col): (r,g,b)} para colorear texto de celdas.
        - highlight_last: resalta la última fila (para SCORE).
        """
        line_h = 7

        # Header
        self.set_fill_color(*HEADER_BG)
        self.set_font('Helvetica', 'B', 7.5)
        self.set_text_color(*TEXT_DIM)
        for i, h in enumerate(headers):
            self.cell(widths[i], line_h, h, border=0, fill=True, align='L' if i == 0 else 'C')
        self.ln()

        for r, row in enumerate(rows):
            is_last_highlight = highlight_last and r == len(rows) - 1
            if is_last_highlight:
                self.set_fill_color(*HEADER_BG)
            else:
                self.set_fill_color(*(CARD_BG if r % 2 == 0 else CARD_BG_ALT))

            # Dot de status en la primera celda
            if statuses and r < len(statuses) and statuses[r]:
                x0, y0 = self.get_x(), self.get_y()
                self.set_fill_color(*STATUS_COLORS.get(statuses[r], TEXT_DIM))
                # pintar primero el fondo de la celda, luego el dot encima
                self.set_fill_color(*(CARD_BG if r % 2 == 0 else CARD_BG_ALT))
                self.rect(x0, y0, widths[0], line_h, 'F')
                self.set_fill_color(*STATUS_COLORS.get(statuses[r], TEXT_DIM))
                self.ellipse(x0 + 2, y0 + line_h / 2 - 1.25, 2.5, 2.5, 'F')
                self.set_fill_color(*(CARD_BG if r % 2 == 0 else CARD_BG_ALT))

            for i, cell in enumerate(row):
                if is_last_highlight:
                    self.set_font('Helvetica', 'B', 8)
                    color = CYAN
                elif cell_colors and (r, i) in cell_colors:
                    self.set_font('Helvetica', 'B', 8)
                    color = cell_colors[(r, i)]
                else:
                    self.set_font('Helvetica', 'B' if i > 0 else '', 8)
                    color = WHITE if i > 0 else TEXT
                self.set_text_color(*color)
                text = f'   {cell}' if (i == 0 and statuses) else str(cell)
                self.cell(widths[i], line_h, text, border=0, fill=True, align='L' if i == 0 else 'C')
            self.ln()


def _pct_status_color(pct):
    if pct >= 100:
        return GREEN
    if pct >= 70:
        return YELLOW
    return RED


def generate_historico_pdf(all_data, metas, meses_cerrados, current_year):
    """Genera el PDF del reporte histórico. Returns: bytes."""
    pdf = FitnessReport()
    all_metrics = DASHBOARD_METRICS
    dashboard_keys = [m[0] for m in DASHBOARD_METRICS]
    total_metrics = len(DASHBOARD_METRICS)
    n = len(all_data)

    def _score(d):
        return sum(is_metric_met(k, d[k], metas[k]) for k in dashboard_keys if k in d and k in metas)

    avg_data = calculate_averages(all_data)
    avg_score = _score(avg_data)

    periodo = f"{MESES_CORTOS[meses_cerrados[0]]} - {MESES_CORTOS[meses_cerrados[-1]]}" if n > 1 else MESES_CORTOS[meses_cerrados[0]]

    # ============ PAGINA 1: RESUMEN ============
    pdf.add_page()
    pdf.banner('FITNESS TRACKER', f'REPORTE {current_year}  ·  {periodo}  ·  {n} {"MES" if n == 1 else "MESES"} CERRADOS')

    pdf.summary_cards([
        (f'{avg_score}/{total_metrics}', 'Metas promedio'),
        (f"{avg_data['steps_avg']:,}", 'Steps / dia'),
        (f"{fmt(avg_data['recovery_score'], '%')}", 'Recovery'),
        (f"{fmt(avg_data['sleep_hours_avg'], 'h')}", 'Sueno'),
    ])

    # Promedio general con dots y % coloreado
    pdf.section(f'PROMEDIO GENERAL ({n} {"MES" if n == 1 else "MESES"})')
    headers = ['Metrica', 'Promedio', 'Meta', '%']
    widths = [80, 35, 35, 25]
    rows, statuses, cell_colors = [], [], {}
    for r, (key, label, unit, tipo) in enumerate(all_metrics):
        valor = avg_data[key]
        meta = metas[key]
        pct = get_pct(key, valor, meta, tipo)
        statuses.append(get_status_class(pct))
        cell_colors[(r, 3)] = _pct_status_color(pct)
        rows.append([label, fmt(valor, unit), fmt(meta, unit), f'{pct:.0f}%'])
    pdf.table(headers, rows, widths, statuses=statuses, cell_colors=cell_colors)

    # ============ PAGINA 2: COMPARATIVA MENSUAL (horizontal) ============
    pdf.add_page(orientation='L')
    pdf.section('COMPARATIVA MENSUAL')

    avail = pdf.w - pdf.l_margin - pdf.r_margin
    metric_col, prom_col, meta_col = 62, 24, 24
    month_col = (avail - metric_col - prom_col - meta_col) / max(n, 1)
    widths = [metric_col] + [month_col] * n + [prom_col, meta_col]
    headers = ['Metrica'] + [MESES_CORTOS[m] for m in meses_cerrados] + ['PROM', 'META']

    rows, cell_colors = [], {}
    for r, (key, label, unit, tipo) in enumerate(all_metrics):
        row = [label]
        for c, d in enumerate(all_data):
            row.append(fmt(d[key], unit))
            if is_metric_met(key, d[key], metas[key]):
                cell_colors[(r, c + 1)] = GREEN
        row.append(fmt(avg_data[key], unit))
        row.append(fmt(metas[key], unit))
        cell_colors[(r, n + 2)] = TEXT_DIM
        rows.append(row)

    score_row = ['SCORE']
    for d in all_data:
        score_row.append(f'{_score(d)}/{total_metrics}')
    score_row.append(f'{avg_score}/{total_metrics}')
    score_row.append(f'{total_metrics}/{total_metrics}')
    rows.append(score_row)

    pdf.table(headers, rows, widths, cell_colors=cell_colors, highlight_last=True)
    pdf.set_font('Helvetica', 'I', 7)
    pdf.set_text_color(*TEXT_DIM)
    pdf.ln(3)
    pdf.cell(0, 5, 'Valores en verde = meta cumplida ese mes', ln=True)

    # ============ PAGINAS 3+: DETALLE POR MES ============
    pdf.add_page()
    pdf.section('DETALLE POR MES')

    for mes, data in zip(meses_cerrados, all_data):
        # Salto de página si no cabe el bloque del mes (~100mm)
        if pdf.get_y() > pdf.h - 110:
            pdf.add_page()

        score = _score(data)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(*WHITE)
        pdf.set_fill_color(*HEADER_BG)
        pdf.cell(0, 9, f'  {MESES_NOMBRES[mes]} {current_year}', fill=True)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*CYAN)
        pdf.set_x(pdf.w - pdf.r_margin - 40)
        pdf.cell(40, 9, f'{score}/{total_metrics} metas  ', align='R', ln=True)
        pdf.ln(1)

        headers = ['Metrica', 'Valor', 'Meta', '%']
        widths = [80, 35, 35, 25]
        rows, statuses, cell_colors = [], [], {}
        for r, (key, label, unit, tipo) in enumerate(all_metrics):
            pct = get_pct(key, data[key], metas[key], tipo)
            statuses.append(get_status_class(pct))
            cell_colors[(r, 3)] = _pct_status_color(pct)
            rows.append([label, fmt(data[key], unit), fmt(metas[key], unit), f'{pct:.0f}%'])
        pdf.table(headers, rows, widths, statuses=statuses, cell_colors=cell_colors)
        pdf.ln(6)

    return bytes(pdf.output())
