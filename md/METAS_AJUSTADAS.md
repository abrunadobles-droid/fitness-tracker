# Metas Ajustadas Feature

## What It Does
Shows what monthly goals you need for the remaining months of the year to hit your annual targets, based on your year-to-date performance.

Example: If your monthly steps goal is 10,000 and your Jan-Feb average was 9,000, then for Mar-Dec you need ~10,200/month to still hit 10,000 annual average.

## Where It Lived
In the HISTORICO view of `dashboard.py`, after the "PROMEDIO ANUAL" section.
See `md/dashboard_old_with_all_features.py` lines 618-681.

## The Logic
```python
remaining = 12 - n  # months left in the year
# For each metric:
adjusted = (goal * 12 - avg_val * n) / remaining
adjusted = max(adjusted, 0)  # can't be negative

# Color coding:
diff_pct = ((adjusted - goal) / goal * 100)
# diff_pct <= 0  → GREEN (on track, goal is same or easier)
# diff_pct <= 30 → YELLOW (need to push +1-30% harder)
# diff_pct > 30  → RED (need to push +30%+ harder)
```

## Full Code (from commit f8c8091)

```python
# ---- METAS AJUSTADAS ----
remaining = 12 - n
if remaining > 0:
    adjusted_metrics = [
        ("STEPS AVG", avg_data['steps_avg'], metas['steps_avg'], "", True),
        ("ACTIVITIES", avg_data['activities'], metas['activities'], "", False),
        ("STRENGTH", avg_data['strength'], metas['strength'], "", False),
        ("SLEEP", avg_data['sleep_hours_avg'], metas['sleep_hours_avg'], "h", True),
        ("HR Z1-3", avg_data['hr_zone_1_3'], metas['hr_zone_1_3'], "h", False),
        ("HR Z4-5", avg_data['hr_zone_4_5'], metas['hr_zone_4_5'], "h", False),
    ]

    adj_rows = ""
    any_behind = False
    for nombre, avg_val, goal, unidad, is_avg in adjusted_metrics:
        adjusted = (goal * 12 - avg_val * n) / remaining
        adjusted = max(adjusted, 0)

        if is_avg:
            adjusted_r = round(adjusted, 1)
        else:
            adjusted_r = round(adjusted, 1)

        diff_pct = ((adjusted - goal) / goal * 100) if goal > 0 else 0

        if diff_pct <= 0:
            color = "#22c55e"
            arrow = "&#9660;"
            status = "ON TRACK"
        elif diff_pct <= 30:
            color = "#f59e0b"
            arrow = "&#9650;"
            status = f"+{diff_pct:.0f}%"
            any_behind = True
        else:
            color = "#ef4444"
            arrow = "&#9650;"
            status = f"+{diff_pct:.0f}%"
            any_behind = True

        adj_display = f"{adjusted_r:,}" if (not unidad and isinstance(adjusted_r, (int, float)) and adjusted_r >= 1000) else f"{adjusted_r}{unidad}"
        goal_display = f"{goal:,}" if (not unidad and isinstance(goal, (int, float)) and goal >= 1000) else f"{goal}{unidad}"

        adj_rows += f'<div style="display:flex;align-items:center;padding:12px 0;border-bottom:1px solid rgba(255,255,255,0.06);">'
        adj_rows += f'<span style="font-family:Space Mono,monospace;font-size:0.55rem;color:#cbd5e1;text-transform:uppercase;letter-spacing:1px;width:24%;">{nombre}</span>'
        adj_rows += f'<span style="font-family:Space Mono,monospace;font-size:0.55rem;color:#94a3b8;width:18%;text-align:center;">META: {goal_display}</span>'
        adj_rows += f'<span style="font-family:Space Mono,monospace;font-size:0.55rem;color:#94a3b8;width:6%;text-align:center;">&#8594;</span>'
        adj_rows += f'<span style="font-family:Inter,sans-serif;font-size:0.9rem;font-weight:700;color:{color};width:22%;text-align:center;">{adj_display}</span>'
        adj_rows += f'<span style="font-family:Space Mono,monospace;font-size:0.55rem;color:{color};width:18%;text-align:right;">{arrow} {status}</span>'
        adj_rows += '</div>'

    border_color = "rgba(245,158,11,0.3)" if any_behind else "rgba(34,197,94,0.3)"
    title_color = "#f59e0b" if any_behind else "#22c55e"

    adj_html = f'<div class="glass-card" style="border-color:{border_color};">'
    adj_html += f'<div style="font-family:Inter,sans-serif;font-size:1.1rem;font-weight:700;letter-spacing:3px;color:{title_color};margin-bottom:6px;">// METAS AJUSTADAS</div>'
    adj_html += f'<div style="font-family:Space Mono,monospace;font-size:0.5rem;color:#94a3b8;letter-spacing:1px;margin-bottom:16px;line-height:1.6;">PARA CUMPLIR TUS METAS ANUALES, ESTOS SON LOS OBJETIVOS<br>MENSUALES QUE NECESITAS EN LOS {remaining} MESES RESTANTES</div>'
    adj_html += adj_rows
    adj_html += '</div>'
    st.markdown(adj_html, unsafe_allow_html=True)
```

## Notes for Re-implementation
- The old version only had 6 metrics. Current version has 9 (added Recovery Score, Resting HR, Sleep Consistency from WHOOP)
- Need to add the 3 new WHOOP metrics to the adjusted_metrics list
- For "inverted" metrics (like Resting HR where lower is better), the adjusted goal logic needs to be inverted too
- The `glass-card` CSS class was from the old design. Current design uses `avg-section` with green border. Adapt styling accordingly.
