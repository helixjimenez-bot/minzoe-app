"""
Locativos:
  A. Mueve UI de fotos para después del formulario (después de Observaciones generales del técnico)
  B. Quita columna Observaciones del checklist de ítems (UI + HTML)
  C. Mueve {_fotos_html} al final del HTML (después de firmas), como en HVAC
"""

with open('solicitudes_minzoe.py', encoding='utf-8') as f:
    src = f.read()

original_len = len(src)

# ═══ A1: Quitar UI de fotos de posición actual (antes del form) ══════════════

OLD_A1 = (
    '                        # ── Fotos del trabajo Locativos (máx. 25) ─────────\n'
    '                        _fotos_key = f"fotos_rep_{id_ot_sel}"\n'
    '                        if _fotos_key not in st.session_state:\n'
    '                            st.session_state[_fotos_key] = []\n'
    '                        _n_fotos = len(st.session_state[_fotos_key])\n'
    '                        st.divider()\n'
    '                        st.markdown(f"**📷 Fotos del trabajo** — {_n_fotos}/25")\n'
    '                        _cam_foto = st.camera_input("Tomar foto", key=f"cam_rep_{id_ot_sel}_{_n_fotos}")\n'
    '                        if _cam_foto:\n'
    '                            _fc1, _fc2 = st.columns([1, 3])\n'
    '                            with _fc1:\n'
    '                                if st.button("📷 Agregar foto", key=f"add_foto_{id_ot_sel}",\n'
    '                                             disabled=_n_fotos >= 25, use_container_width=True):\n'
    '                                    import base64 as _b64mod\n'
    '                                    _b64 = _b64mod.b64encode(_cam_foto.getvalue()).decode()\n'
    '                                    st.session_state[_fotos_key].append(_b64)\n'
    '                                    st.rerun()\n'
    '                            with _fc2:\n'
    '                                if _n_fotos >= 25:\n'
    '                                    st.warning("Máximo 25 fotos alcanzado.")\n'
    '                        if st.session_state[_fotos_key]:\n'
    '                            _thumb_cols = st.columns(4)\n'
    '                            for _fi, _fb in enumerate(st.session_state[_fotos_key]):\n'
    '                                with _thumb_cols[_fi % 4]:\n'
    '                                    st.image(f"data:image/jpeg;base64,{_fb}", use_container_width=True)\n'
    '                                    if st.button("🗑️", key=f"del_foto_{id_ot_sel}_{_fi}",\n'
    '                                                 use_container_width=True):\n'
    '                                        st.session_state[_fotos_key].pop(_fi)\n'
    '                                        st.rerun()\n'
    '                        st.divider()\n'
    '\n'
    '                        with st.form(f"form_reporte_loc_{id_ot_sel}", clear_on_submit=False):\n'
)

NEW_A1 = (
    '                        with st.form(f"form_reporte_loc_{id_ot_sel}", clear_on_submit=False):\n'
)

assert OLD_A1 in src, "A1: bloque fotos Locativos NO encontrado"
assert src.count(OLD_A1) == 1, "A1: más de una coincidencia"
src = src.replace(OLD_A1, NEW_A1)
print("OK A1: UI de fotos removida de posición original Locativos")

# ═══ A2: Insertar UI de fotos antes de "FUERA del form: guardar locativos" ═══

ANCHOR_A2 = '                        # ── FUERA del form: guardar locativos ─────────────\n'
assert ANCHOR_A2 in src, "A2: ancla FUERA del form locativos NO encontrada"

FOTO_LOC_UI = (
    '                        # ── Fotos del trabajo Locativos (después de Observaciones) ──\n'
    '                        _fotos_key = f"fotos_rep_{id_ot_sel}"\n'
    '                        if _fotos_key not in st.session_state:\n'
    '                            st.session_state[_fotos_key] = []\n'
    '                        _n_fotos = len(st.session_state[_fotos_key])\n'
    '                        st.divider()\n'
    '                        st.markdown(f"**📷 Fotos del trabajo** — {_n_fotos}/25")\n'
    '                        _cam_foto = st.camera_input("Tomar foto", key=f"cam_rep_{id_ot_sel}_{_n_fotos}")\n'
    '                        if _cam_foto:\n'
    '                            _fc1, _fc2 = st.columns([1, 3])\n'
    '                            with _fc1:\n'
    '                                if st.button("📷 Agregar foto", key=f"add_foto_{id_ot_sel}",\n'
    '                                             disabled=_n_fotos >= 25, use_container_width=True):\n'
    '                                    import base64 as _b64mod\n'
    '                                    _b64 = _b64mod.b64encode(_cam_foto.getvalue()).decode()\n'
    '                                    st.session_state[_fotos_key].append(_b64)\n'
    '                                    st.rerun()\n'
    '                            with _fc2:\n'
    '                                if _n_fotos >= 25:\n'
    '                                    st.warning("Máximo 25 fotos alcanzado.")\n'
    '                        if st.session_state[_fotos_key]:\n'
    '                            _thumb_cols = st.columns(4)\n'
    '                            for _fi, _fb in enumerate(st.session_state[_fotos_key]):\n'
    '                                with _thumb_cols[_fi % 4]:\n'
    '                                    st.image(f"data:image/jpeg;base64,{_fb}", use_container_width=True)\n'
    '                                    if st.button("🗑️", key=f"del_foto_{id_ot_sel}_{_fi}",\n'
    '                                                 use_container_width=True):\n'
    '                                        st.session_state[_fotos_key].pop(_fi)\n'
    '                                        st.rerun()\n'
    '\n'
)

src = src.replace(ANCHOR_A2, FOTO_LOC_UI + ANCHOR_A2, 1)
print("OK A2: UI de fotos insertada después del formulario Locativos")

# ═══ B1: Quitar columna Observaciones del encabezado UI ══════════════════════

OLD_B1 = (
    '                            l_act = {}\n'
    '                            hdr = st.columns([2,1,1,1,1,3])\n'
    '                            hdr[0].markdown("**Ítem**")\n'
    '                            hdr[1].markdown("**Buen Estado**")\n'
    '                            hdr[2].markdown("**Mal Estado**")\n'
    '                            hdr[3].markdown("**Req. Reparación**")\n'
    '                            hdr[4].markdown("**Inst. Repuestos**")\n'
    '                            hdr[5].markdown("**Observaciones**")\n'
    '                            for item in ITEMS_LOC:\n'
    '                                k = item.lower().replace(" ","_").replace(".","_").replace(".","").replace(" ","_")\n'
    '                                cols = st.columns([2,1,1,1,1,3])\n'
)

# El replace de k puede tener variantes, leamos exactamente qué hay
import re as _re
match = _re.search(r'                            l_act = \{\}\n                            hdr = st\.columns\(\[2,1,1,1,1,3\]\).*?                            for item in ITEMS_LOC:\n                                k = (.*?)\n                                cols = st\.columns\(\[2,1,1,1,1,3\]\)\n', src, _re.DOTALL)
if match:
    k_line = match.group(1)
    print(f"  B1: línea k encontrada: {repr(k_line)}")
else:
    print("  B1: buscando por alternativa")

# Busqueda más flexible
OLD_B1_HDR = '                            hdr = st.columns([2,1,1,1,1,3])\n'
OLD_B1_COLS = '                                cols = st.columns([2,1,1,1,1,3])\n'
assert OLD_B1_HDR in src, "B1: hdr columns NO encontrado"
assert OLD_B1_COLS in src, "B1: cols columns NO encontrado"

src = src.replace(OLD_B1_HDR, '                            hdr = st.columns([3,1,1,2,2])\n', 1)
src = src.replace(OLD_B1_COLS, '                                cols = st.columns([3,1,1,2,2])\n', 1)
print("OK B1a: columnas UI actualizadas (sin Observaciones)")

OLD_B1_H5 = '                            hdr[5].markdown("**Observaciones**")\n'
assert OLD_B1_H5 in src, "B1: hdr[5] Observaciones NO encontrado"
src = src.replace(OLD_B1_H5, '', 1)
print("OK B1b: hdr[5] Observaciones eliminado")

# ═══ B2: Quitar obs del widget y del dict ════════════════════════════════════

OLD_B2 = (
    '                                inst = cols[4].checkbox("", key=f"l_i_{k}")\n'
    '                                obs  = cols[5].text_input("", key=f"l_o_{k}", label_visibility="collapsed")\n'
    '                                l_act[item] = {"buen":buen,"mal":mal,"req":req,"inst":inst,"obs":obs}\n'
)
NEW_B2 = (
    '                                inst = cols[4].checkbox("", key=f"l_i_{k}")\n'
    '                                l_act[item] = {"buen":buen,"mal":mal,"req":req,"inst":inst}\n'
)
assert OLD_B2 in src, "B2: widget obs y dict NO encontrado"
src = src.replace(OLD_B2, NEW_B2, 1)
print("OK B2: obs removido del widget y del dict")

# ═══ B3: Quitar <td> de observaciones en filas_act HTML ══════════════════════

OLD_B3 = (
    '                                filas_act = "".join(\n'
    '                                    f"<tr>"\n'
    '                                    f"<td style=\'white-space:nowrap\'>{item}</td>"\n'
    '                                    f"<td style=\'text-align:center;font-size:10pt\'>{ck(v[\'buen\'])}</td>"\n'
    '                                    f"<td style=\'text-align:center;font-size:10pt\'>{ck(v[\'mal\'])}</td>"\n'
    '                                    f"<td style=\'text-align:center;font-size:10pt\'>{ck(v[\'req\'])}</td>"\n'
    '                                    f"<td style=\'text-align:center;font-size:10pt\'>{ck(v[\'inst\'])}</td>"\n'
    '                                    f"<td style=\'word-wrap:break-word\'>{v[\'obs\']}</td>"\n'
    '                                    f"</tr>"\n'
    '                                    for item,v in l_act.items()\n'
    '                                )\n'
)
NEW_B3 = (
    '                                filas_act = "".join(\n'
    '                                    f"<tr>"\n'
    '                                    f"<td style=\'white-space:nowrap\'>{item}</td>"\n'
    '                                    f"<td style=\'text-align:center;font-size:10pt\'>{ck(v[\'buen\'])}</td>"\n'
    '                                    f"<td style=\'text-align:center;font-size:10pt\'>{ck(v[\'mal\'])}</td>"\n'
    '                                    f"<td style=\'text-align:center;font-size:10pt\'>{ck(v[\'req\'])}</td>"\n'
    '                                    f"<td style=\'text-align:center;font-size:10pt\'>{ck(v[\'inst\'])}</td>"\n'
    '                                    f"</tr>"\n'
    '                                    for item,v in l_act.items()\n'
    '                                )\n'
)
assert OLD_B3 in src, "B3: filas_act con obs NO encontrado"
src = src.replace(OLD_B3, NEW_B3, 1)
print("OK B3: <td> obs eliminado de filas_act")

# ═══ B4: Actualizar colgroup y <th> Observaciones en HTML template ════════════

OLD_B4 = (
    '<colgroup>\n'
    '  <col style="width:22%">\n'
    '  <col style="width:9%">\n'
    '  <col style="width:9%">\n'
    '  <col style="width:12%">\n'
    '  <col style="width:12%">\n'
    '  <col style="width:36%">\n'
    '</colgroup>\n'
    '<tr>\n'
    '  <th>Ítem</th>\n'
    '  <th style="text-align:center">Buen Estado</th>\n'
    '  <th style="text-align:center">Mal Estado</th>\n'
    '  <th style="text-align:center">Req. Reparación</th>\n'
    '  <th style="text-align:center">Inst. Repuestos</th>\n'
    '  <th>Observaciones</th>\n'
    '</tr>\n'
)
NEW_B4 = (
    '<colgroup>\n'
    '  <col style="width:30%">\n'
    '  <col style="width:14%">\n'
    '  <col style="width:14%">\n'
    '  <col style="width:21%">\n'
    '  <col style="width:21%">\n'
    '</colgroup>\n'
    '<tr>\n'
    '  <th>Ítem</th>\n'
    '  <th style="text-align:center">Buen Estado</th>\n'
    '  <th style="text-align:center">Mal Estado</th>\n'
    '  <th style="text-align:center">Req. Reparación</th>\n'
    '  <th style="text-align:center">Inst. Repuestos</th>\n'
    '</tr>\n'
)
assert OLD_B4 in src, "B4: colgroup+th Observaciones NO encontrado"
src = src.replace(OLD_B4, NEW_B4, 1)
print("OK B4: colgroup y th Observaciones eliminados del HTML")

# ═══ C: Mover {_fotos_html} al final del HTML Locativos (después de firmas) ══

OLD_C = (
    '{_fotos_html}\n'
    '\n'
    '<div style="display:flex;justify-content:space-between;margin-top:20px">\n'
    '  <div>\n'
    '    <div class="firma-box" style="width:180px">&nbsp;<br>FIRMA TÉCNICO</div>\n'
)
NEW_C = (
    '<div style="display:flex;justify-content:space-between;margin-top:20px">\n'
    '  <div>\n'
    '    <div class="firma-box" style="width:180px">&nbsp;<br>FIRMA TÉCNICO</div>\n'
)
assert OLD_C in src, "C: {_fotos_html} antes de firmas Locativos NO encontrado"
src = src.replace(OLD_C, NEW_C, 1)
print("OK C1: {_fotos_html} removido de antes de firmas Locativos")

# Insertar {_fotos_html} al final del HTML Locativos
OLD_C2 = (
    '</div>\n'
    '</body></html>"""'
)
# Esta es la segunda ocurrencia (Locativos viene después de HVAC)
count_c2 = src.count(OLD_C2)
print(f"  C2: {count_c2} ocurrencias de </div></body></html>")
# La primera es HVAC (ya tiene {_fotos_html}), la segunda es Locativos
idx = src.find(OLD_C2)           # primera (HVAC, ya tiene _fotos_html)
idx2 = src.find(OLD_C2, idx + 1) # segunda (Locativos)
assert idx2 != -1, "C2: segunda ocurrencia de </div></body></html> NO encontrada"
src = src[:idx2] + OLD_C2.replace('</div>\n</body></html>"""',
    '</div>\n{_fotos_html}\n</body></html>"""') + src[idx2 + len(OLD_C2):]
print("OK C2: {_fotos_html} insertado al final del HTML Locativos")

# ═══ D: Actualizar galería de fotos Locativos a páginas de 6 ═════════════════

OLD_D = (
    '                                # Galería de fotos para el reporte\n'
    '                                _fotos_list = st.session_state.get(f"fotos_rep_{id_ot_sel}", [])\n'
    '                                if _fotos_list:\n'
    '                                    _fotos_imgs = "".join(\n'
    "                                        f'<img src=\"data:image/jpeg;base64,{_fb}\" '\n"
    "                                        f'style=\"width:165px;height:124px;object-fit:cover;'\n"
    "                                        f'border:1px solid #ccc;border-radius:3px;margin:3px\">'\n"
    '                                        for _fb in _fotos_list\n'
    '                                    )\n'
    '                                    _fotos_html = (\n'
    "                                        '<div class=\"section\">REGISTRO FOTOGRÁFICO</div>'\n"
    "                                        f'<div style=\"display:flex;flex-wrap:wrap;gap:4px;margin:4px 0\">'\n"
    "                                        f'{_fotos_imgs}</div>'\n"
    '                                    )\n'
    '                                else:\n'
    '                                    _fotos_html = ""\n'
)
NEW_D = (
    '                                # Fotos Locativos: páginas de 6, tabla 3×2\n'
    '                                _fotos_list = st.session_state.get(f"fotos_rep_{id_ot_sel}", [])\n'
    '                                if _fotos_list:\n'
    '                                    _loc_foto_pages = []\n'
    '                                    for _p0 in range(0, len(_fotos_list), 6):\n'
    '                                        _chunk = _fotos_list[_p0:_p0 + 6]\n'
    '                                        _rows_html = ""\n'
    '                                        for _r in range(0, len(_chunk), 3):\n'
    '                                            _three = _chunk[_r:_r + 3]\n'
    '                                            _tds = "".join(\n'
    "                                                f'<td style=\"width:33%;padding:5px;text-align:center;vertical-align:top\">'\n"
    "                                                f'<img src=\"data:image/jpeg;base64,{_fb}\" '\n"
    "                                                f'style=\"width:99%;height:175px;object-fit:cover;'\n"
    "                                                f'border:1px solid #ccc;border-radius:3px\">'\n"
    "                                                f'</td>'\n"
    '                                                for _fb in _three\n'
    '                                            )\n'
    '                                            for _ in range(3 - len(_three)):\n'
    "                                                _tds += '<td></td>'\n"
    '                                            _rows_html += f\'<tr>{_tds}</tr>\'\n'
    '                                        _pnum = _p0 // 6 + 1\n'
    '                                        _loc_foto_pages.append(\n'
    "                                            f'<div style=\"page-break-before:always;padding:4px\">'\n"
    "                                            f'<div class=\"section\">REGISTRO FOTOGRÁFICO — Página {_pnum}</div>'\n"
    "                                            f'<table style=\"width:100%;border-collapse:collapse\">{_rows_html}</table>'\n"
    "                                            f'</div>'\n"
    '                                        )\n'
    '                                    _fotos_html = "".join(_loc_foto_pages)\n'
    '                                else:\n'
    '                                    _fotos_html = ""\n'
)
assert OLD_D in src, "D: galería fotos Locativos NO encontrada"
src = src.replace(OLD_D, NEW_D, 1)
print("OK D: galería Locativos actualizada a páginas de 6")

# ═══ Verificar sintaxis ═══════════════════════════════════════════════════════

import ast
try:
    ast.parse(src)
    print("OK Sintaxis Python correcta")
except SyntaxError as e:
    print(f"ERROR sintaxis linea {e.lineno}: {e.msg}")
    lines = src.splitlines()
    for j in range(max(0, e.lineno - 5), min(len(lines), e.lineno + 4)):
        print(f"  {j+1}: {lines[j]}")
    raise

with open('solicitudes_minzoe.py', 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\nArchivo guardado. Original: {original_len} -> nuevo: {len(src)} bytes")
