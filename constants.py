"""
Constantes compartidas del dashboard
"""

MESES_NOMBRES = {
    1: 'ENERO', 2: 'FEBRERO', 3: 'MARZO', 4: 'ABRIL',
    5: 'MAYO', 6: 'JUNIO', 7: 'JULIO', 8: 'AGOSTO',
    9: 'SEPTIEMBRE', 10: 'OCTUBRE', 11: 'NOVIEMBRE', 12: 'DICIEMBRE'
}

MESES_CORTOS = {
    1: 'ENE', 2: 'FEB', 3: 'MAR', 4: 'ABR',
    5: 'MAY', 6: 'JUN', 7: 'JUL', 8: 'AGO',
    9: 'SEP', 10: 'OCT', 11: 'NOV', 12: 'DIC'
}

# (key, label, unit, tipo)
# tipo: 'total' | 'promedio' | 'promedio_inverted'
FITNESS_METRICS = [
    ('steps_avg',   'Steps Daily Avg',    '',  'promedio'),
    ('activities',  'Activities / Mes',   '',  'total'),
    ('strength',    'Strength Training',  '',  'total'),
    ('hr_zone_1_3', 'HR Zones 1-3',       'h', 'total'),
    ('hr_zone_4_5', 'HR Zones 4-5',       'h', 'total'),
]

SLEEP_METRICS = [
    ('sleep_hours_avg',  'Sleep Duration',     'h',   'promedio'),
    ('recovery_score',   'Recovery Score',     '%',   'promedio'),
    ('resting_hr',       'Resting HR',         'bpm', 'promedio_inverted'),
    ('sleep_consistency','Sleep Consistency',  '%',   'promedio'),
]

MIND_METRICS = [
    ('meditation_sessions', 'Sesiones Meditacion', '',    'total'),
    ('meditation_minutes',  'Minutos Meditacion',  'min', 'total'),
]

ALL_METRIC_KEYS = [m[0] for m in FITNESS_METRICS + SLEEP_METRICS + MIND_METRICS]
