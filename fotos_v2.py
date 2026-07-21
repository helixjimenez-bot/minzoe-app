"""
Cambios fotos HVAC v2:
  A. Agrega placa_manj y placa_cond al inicio de la lista split (14 → 16 ítems)
  B. Mueve la UI de cámara para que aparezca DESPUÉS del formulario
     (después de Observaciones generales del técnico)
  C. Genera fotos en páginas separadas (6 por página, tabla 3×2)
  D. Reubica {_fotos_html} al final del HTML, después de las firmas
"""

with open('solicitudes_minzoe.py', encoding='utf-8') as f:
    src = f.read()

original_len = len(src)

# ═══ A: Agregar placa_manj y placa_cond al inicio de la lista split ═══════════

OLD_A = (
    '                            "split": [\n'
    '                                ("volt_manj",  "Voltaje manejadora"),\n'
)
NEW_A = (
    '                            "split": [\n'
    '                                ("placa_manj", "Foto placa manejadora"),\n'
    '                                ("placa_cond", "Foto placa condensadora"),\n'
    '                                ("volt_manj",  "Voltaje manejadora"),\n'
)
assert OLD_A in src, "A: texto NO encontrado"
assert src.count(OLD_A) == 1, "A: más de una coincidencia"
src = src.replace(OLD_A, NEW_A)
print("OK A: placa_manj y placa_cond agregados al inicio de split")

# ═══ B: Mover UI de cámara: quitar de posición actual ════════════════════════

# Bloque completo a mover: desde la línea blank+_fotos_oblig_key hasta el
# último st.rerun() de miniaturas (inclusive la línea blank final)
OLD_B = (
    '\n'
    '                        _fotos_oblig_key = f"fotos_oblig_{id_ot_sel}"\n'
    '                        _fotos_extra_key = f"fotos_extra_{id_ot_sel}"\n'
    '                        if _fotos_oblig_key not in st.session_state:\n'
    '                            st.session_state[_fotos_oblig_key] = {}\n'
    '                        if _fotos_extra_key not in st.session_state:\n'
    '                            st.session_state[_fotos_extra_key] = []\n'
    '\n'
    '                        _fotos_oblig_d = st.session_state[_fotos_oblig_key]\n'
    '                        _fotos_extra_l = st.session_state[_fotos_extra_key]\n'
    '                        _n_total_fotos = len(_fotos_oblig_d) + len(_fotos_extra_l)\n'
    '\n'
    '                        st.divider()\n'
    '                        _n_oblig_ok = sum(1 for _k, _ in _items_oblig if _k in _fotos_oblig_d)\n'
    '                        st.markdown(\n'
    '                            f"**📷 Registro fotográfico** — {_n_total_fotos}/25 "\n'
    '                            f"&nbsp;|&nbsp; Obligatorias: {_n_oblig_ok}/{len(_items_oblig)}"\n'
    '                        )\n'
    '\n'
    '                        # Grid de estado por ítem obligatorio\n'
    '                        _g_cols = st.columns(4)\n'
    '                        for _gi, (_gk, _gl) in enumerate(_items_oblig):\n'
    '                            with _g_cols[_gi % 4]:\n'
    '                                _gok = _gk in _fotos_oblig_d\n'
    "                                st.markdown(\n"
    "                                    f\"<div style='font-size:11px;padding:3px 5px;border-radius:4px;\"\n"
    "                                    f\"background:{'#d1fae5' if _gok else '#fee2e2'};\"\n"
    "                                    f\"border:1px solid {'#6ee7b7' if _gok else '#fca5a5'};margin:2px'>\"\n"
    "                                    f\"{'✅' if _gok else '❌'} {_gl}</div>\",\n"
    '                                    unsafe_allow_html=True,\n'
    '                                )\n'
    '\n'
    '                        # Selector del ítem + cámara (fuera del form — requerido por Streamlit)\n'
    '                        _pending_items = [(_k, _l) for _k, _l in _items_oblig if _k not in _fotos_oblig_d]\n'
    '                        _hay_espacio   = _n_total_fotos < 25\n'
    '                        _opcs_foto = (\n'
    '                            [("-- Selecciona el ítem a fotografiar --", "")]\n'
    '                            + [(f"⚠️ {_l}", _k) for _k, _l in _pending_items]\n'
    '                            + ([("➕ Foto adicional", "__extra__")] if _hay_espacio else [])\n'
    '                        )\n'
    '                        if len(_opcs_foto) > 1:\n'
    '                            _lbl_opcs = [_o[0] for _o in _opcs_foto]\n'
    '                            _sel_idx = st.selectbox(\n'
    '                                "¿Qué ítem vas a fotografiar?",\n'
    '                                options=range(len(_lbl_opcs)),\n'
    '                                format_func=lambda _i: _lbl_opcs[_i],\n'
    '                                key=f"sel_item_foto_{id_ot_sel}",\n'
    '                            )\n'
    '                            _sel_item_key = _opcs_foto[_sel_idx][1]\n'
    '                            _cam_oblig = st.camera_input(\n'
    '                                "Tomar foto",\n'
    '                                key=f"cam_oblig_{id_ot_sel}_{_n_total_fotos}",\n'
    '                                disabled=(_sel_item_key == ""),\n'
    '                            )\n'
    '                            if _cam_oblig and _sel_item_key:\n'
    '                                import base64 as _b64mod\n'
    '                                _b64 = _b64mod.b64encode(_cam_oblig.getvalue()).decode()\n'
    '                                if _sel_item_key == "__extra__":\n'
    '                                    st.session_state[_fotos_extra_key].append(_b64)\n'
    '                                else:\n'
    '                                    st.session_state[_fotos_oblig_key][_sel_item_key] = _b64\n'
    '                                st.rerun()\n'
    '                        else:\n'
    '                            st.success("✅ Todas las fotos obligatorias tomadas.")\n'
    '                            if _hay_espacio:\n'
    '                                _cam_extra = st.camera_input(\n'
    '                                    "Foto adicional (opcional)",\n'
    '                                    key=f"cam_extra_{id_ot_sel}_{_n_total_fotos}",\n'
    '                                )\n'
    '                                if _cam_extra:\n'
    '                                    import base64 as _b64mod\n'
    '                                    _b64 = _b64mod.b64encode(_cam_extra.getvalue()).decode()\n'
    '                                    st.session_state[_fotos_extra_key].append(_b64)\n'
    '                                    st.rerun()\n'
    '\n'
    '                        # Miniaturas con opción de borrar\n'
    '                        if _fotos_oblig_d or _fotos_extra_l:\n'
    '                            _n_oblig_disp = len(_fotos_oblig_d)\n'
    '                            _all_disp = (\n'
    '                                [(_k, _fotos_oblig_d[_k]) for _k, _ in _items_oblig if _k in _fotos_oblig_d]\n'
    '                                + [("__extra__", _fb) for _fb in _fotos_extra_l]\n'
    '                            )\n'
    '                            _td_cols = st.columns(4)\n'
    '                            for _ti, (_tk, _tfb) in enumerate(_all_disp):\n'
    '                                with _td_cols[_ti % 4]:\n'
    '                                    _cap = (next((_l for _k, _l in _items_oblig if _k == _tk), "Extra")\n'
    '                                            if _tk != "__extra__" else "Extra")\n'
    '                                    st.image(f"data:image/jpeg;base64,{_tfb}",\n'
    '                                             use_container_width=True, caption=_cap)\n'
    '                                    if st.button("🗑️", key=f"del_foto_{id_ot_sel}_{_ti}",\n'
    '                                                 use_container_width=True):\n'
    '                                        if _tk == "__extra__":\n'
    '                                            _idx_ex = _ti - _n_oblig_disp\n'
    '                                            if 0 <= _idx_ex < len(st.session_state[_fotos_extra_key]):\n'
    '                                                st.session_state[_fotos_extra_key].pop(_idx_ex)\n'
    '                                        else:\n'
    '                                            st.session_state[_fotos_oblig_key].pop(_tk, None)\n'
    '                                        st.rerun()\n'
)

assert OLD_B in src, "B: bloque UI cámara NO encontrado en posición original"
assert src.count(OLD_B) == 1, "B: más de una coincidencia"
src = src.replace(OLD_B, '\n')   # queda solo un \n (línea en blanco)
print("OK B1: UI de cámara removida de posición original")

# ═══ B2: Insertar UI de cámara DESPUÉS del formulario (antes de FUERA del form) ═

ANCHOR_B2 = '                        # ── FUERA del form: guardar ──────────────────────\n'
assert ANCHOR_B2 in src, "B2: ancla FUERA del form NO encontrada"

FOTO_UI_NUEVA = (
    '                        # ── Fotos del trabajo (después de Observaciones generales) ──\n'
    '                        _fotos_oblig_key = f"fotos_oblig_{id_ot_sel}"\n'
    '                        _fotos_extra_key = f"fotos_extra_{id_ot_sel}"\n'
    '                        if _fotos_oblig_key not in st.session_state:\n'
    '                            st.session_state[_fotos_oblig_key] = {}\n'
    '                        if _fotos_extra_key not in st.session_state:\n'
    '                            st.session_state[_fotos_extra_key] = []\n'
    '                        _fotos_oblig_d = st.session_state[_fotos_oblig_key]\n'
    '                        _fotos_extra_l = st.session_state[_fotos_extra_key]\n'
    '                        _n_total_fotos = len(_fotos_oblig_d) + len(_fotos_extra_l)\n'
    '\n'
    '                        st.divider()\n'
    '                        _n_oblig_ok = sum(1 for _k, _ in _items_oblig if _k in _fotos_oblig_d)\n'
    '                        st.markdown(\n'
    '                            f"**📷 Fotos del trabajo** — {_n_total_fotos}/25 "\n'
    '                            f"&nbsp;|&nbsp; Obligatorias: {_n_oblig_ok}/{len(_items_oblig)}"\n'
    '                        )\n'
    '\n'
    '                        # Grid de estado por ítem obligatorio\n'
    '                        _g_cols = st.columns(4)\n'
    '                        for _gi, (_gk, _gl) in enumerate(_items_oblig):\n'
    '                            with _g_cols[_gi % 4]:\n'
    '                                _gok = _gk in _fotos_oblig_d\n'
    "                                st.markdown(\n"
    "                                    f\"<div style='font-size:11px;padding:3px 5px;border-radius:4px;\"\n"
    "                                    f\"background:{'#d1fae5' if _gok else '#fee2e2'};\"\n"
    "                                    f\"border:1px solid {'#6ee7b7' if _gok else '#fca5a5'};margin:2px'>\"\n"
    "                                    f\"{'✅' if _gok else '❌'} {_gl}</div>\",\n"
    '                                    unsafe_allow_html=True,\n'
    '                                )\n'
    '\n'
    '                        # Selector del ítem + cámara\n'
    '                        _pending_items = [(_k, _l) for _k, _l in _items_oblig if _k not in _fotos_oblig_d]\n'
    '                        _hay_espacio   = _n_total_fotos < 25\n'
    '                        _opcs_foto = (\n'
    '                            [("-- Selecciona el ítem a fotografiar --", "")]\n'
    '                            + [(f"⚠️ {_l}", _k) for _k, _l in _pending_items]\n'
    '                            + ([("➕ Foto adicional", "__extra__")] if _hay_espacio else [])\n'
    '                        )\n'
    '                        if len(_opcs_foto) > 1:\n'
    '                            _lbl_opcs = [_o[0] for _o in _opcs_foto]\n'
    '                            _sel_idx = st.selectbox(\n'
    '                                "¿Qué ítem vas a fotografiar?",\n'
    '                                options=range(len(_lbl_opcs)),\n'
    '                                format_func=lambda _i: _lbl_opcs[_i],\n'
    '                                key=f"sel_item_foto_{id_ot_sel}",\n'
    '                            )\n'
    '                            _sel_item_key = _opcs_foto[_sel_idx][1]\n'
    '                            _cam_oblig = st.camera_input(\n'
    '                                "Tomar foto",\n'
    '                                key=f"cam_oblig_{id_ot_sel}_{_n_total_fotos}",\n'
    '                                disabled=(_sel_item_key == ""),\n'
    '                            )\n'
    '                            if _cam_oblig and _sel_item_key:\n'
    '                                import base64 as _b64mod\n'
    '                                _b64 = _b64mod.b64encode(_cam_oblig.getvalue()).decode()\n'
    '                                if _sel_item_key == "__extra__":\n'
    '                                    st.session_state[_fotos_extra_key].append(_b64)\n'
    '                                else:\n'
    '                                    st.session_state[_fotos_oblig_key][_sel_item_key] = _b64\n'
    '                                st.rerun()\n'
    '                        else:\n'
    '                            st.success("✅ Todas las fotos obligatorias tomadas.")\n'
    '                            if _hay_espacio:\n'
    '                                _cam_extra = st.camera_input(\n'
    '                                    "Foto adicional (opcional)",\n'
    '                                    key=f"cam_extra_{id_ot_sel}_{_n_total_fotos}",\n'
    '                                )\n'
    '                                if _cam_extra:\n'
    '                                    import base64 as _b64mod\n'
    '                                    _b64 = _b64mod.b64encode(_cam_extra.getvalue()).decode()\n'
    '                                    st.session_state[_fotos_extra_key].append(_b64)\n'
    '                                    st.rerun()\n'
    '\n'
    '                        # Miniaturas con opción de borrar\n'
    '                        if _fotos_oblig_d or _fotos_extra_l:\n'
    '                            _n_oblig_disp = len(_fotos_oblig_d)\n'
    '                            _all_disp = (\n'
    '                                [(_k, _fotos_oblig_d[_k]) for _k, _ in _items_oblig if _k in _fotos_oblig_d]\n'
    '                                + [("__extra__", _fb) for _fb in _fotos_extra_l]\n'
    '                            )\n'
    '                            _td_cols = st.columns(4)\n'
    '                            for _ti, (_tk, _tfb) in enumerate(_all_disp):\n'
    '                                with _td_cols[_ti % 4]:\n'
    '                                    _cap = (next((_l for _k, _l in _items_oblig if _k == _tk), "Extra")\n'
    '                                            if _tk != "__extra__" else "Extra")\n'
    '                                    st.image(f"data:image/jpeg;base64,{_tfb}",\n'
    '                                             use_container_width=True, caption=_cap)\n'
    '                                    if st.button("🗑️", key=f"del_foto_{id_ot_sel}_{_ti}",\n'
    '                                                 use_container_width=True):\n'
    '                                        if _tk == "__extra__":\n'
    '                                            _idx_ex = _ti - _n_oblig_disp\n'
    '                                            if 0 <= _idx_ex < len(st.session_state[_fotos_extra_key]):\n'
    '                                                st.session_state[_fotos_extra_key].pop(_idx_ex)\n'
    '                                        else:\n'
    '                                            st.session_state[_fotos_oblig_key].pop(_tk, None)\n'
    '                                        st.rerun()\n'
    '\n'
)

src = src.replace(ANCHOR_B2, FOTO_UI_NUEVA + ANCHOR_B2, 1)
print("OK B2: UI de cámara insertada después del formulario")

# ═══ C: Galería de fotos en páginas de 6 (tabla 3×2, page-break entre páginas) ═

OLD_C = (
    '                                    # Galería etiquetada de fotos para el reporte\n'
    '                                    _fotos_oblig_rep = st.session_state.get(f"fotos_oblig_{id_ot_sel}", {})\n'
    '                                    _fotos_extra_rep  = st.session_state.get(f"fotos_extra_{id_ot_sel}", [])\n'
    '                                    _fotos_html_items = []\n'
    '                                    for _fk, _fl in _items_oblig:\n'
    '                                        if _fk in _fotos_oblig_rep:\n'
    '                                            _fotos_html_items.append(\n'
    "                                                f'<div style=\"text-align:center;margin:4px\">'\n"
    "                                                f'<img src=\"data:image/jpeg;base64,{_fotos_oblig_rep[_fk]}\" '\n"
    "                                                f'style=\"width:160px;height:120px;object-fit:cover;'\n"
    "                                                f'border:1px solid #ccc;border-radius:3px\">'\n"
    "                                                f'<div style=\"font-size:7.5px;margin-top:2px;color:#555\">{_fl}</div>'\n"
    "                                                f'</div>'\n"
    '                                            )\n'
    '                                    for _fexb in _fotos_extra_rep:\n'
    '                                        _fotos_html_items.append(\n'
    "                                            f'<div style=\"text-align:center;margin:4px\">'\n"
    "                                            f'<img src=\"data:image/jpeg;base64,{_fexb}\" '\n"
    "                                            f'style=\"width:160px;height:120px;object-fit:cover;'\n"
    "                                            f'border:1px solid #ccc;border-radius:3px\">'\n"
    "                                            f'<div style=\"font-size:7.5px;margin-top:2px;color:#555\">Adicional</div>'\n"
    "                                            f'</div>'\n"
    '                                        )\n'
    '                                    if _fotos_html_items:\n'
    '                                        _fotos_html = (\n'
    "                                            '<div class=\"section\">REGISTRO FOTOGRÁFICO</div>'\n"
    "                                            '<div style=\"display:flex;flex-wrap:wrap;gap:4px;margin:4px 0\">'\n"
    '                                            + "".join(_fotos_html_items) + \'</div>\'\n'
    '                                        )\n'
    '                                    else:\n'
    '                                        _fotos_html = ""\n'
)

NEW_C = (
    '                                    # Fotos en páginas separadas: 6 por página, tabla 3×2\n'
    '                                    _fotos_oblig_rep = st.session_state.get(f"fotos_oblig_{id_ot_sel}", {})\n'
    '                                    _fotos_extra_rep  = st.session_state.get(f"fotos_extra_{id_ot_sel}", [])\n'
    '                                    _all_foto_pairs = (\n'
    '                                        [(_fl, _fotos_oblig_rep[_fk]) for _fk, _fl in _items_oblig if _fk in _fotos_oblig_rep]\n'
    '                                        + [("Adicional", _fb) for _fb in _fotos_extra_rep]\n'
    '                                    )\n'
    '                                    if _all_foto_pairs:\n'
    '                                        _foto_pages = []\n'
    '                                        for _p0 in range(0, len(_all_foto_pairs), 6):\n'
    '                                            _chunk = _all_foto_pairs[_p0:_p0 + 6]\n'
    '                                            _rows_html = ""\n'
    '                                            for _r in range(0, len(_chunk), 3):\n'
    '                                                _three = _chunk[_r:_r + 3]\n'
    '                                                _tds = "".join(\n'
    "                                                    f'<td style=\"width:33%;padding:5px;text-align:center;vertical-align:top\">'\n"
    "                                                    f'<img src=\"data:image/jpeg;base64,{_fb}\" '\n"
    "                                                    f'style=\"width:99%;height:175px;object-fit:cover;'\n"
    "                                                    f'border:1px solid #ccc;border-radius:3px\">'\n"
    "                                                    f'<div style=\"font-size:8px;margin-top:3px;font-weight:600;color:#444\">{_fl}</div>'\n"
    "                                                    f'</td>'\n"
    '                                                    for _fl, _fb in _three\n'
    '                                                )\n'
    '                                                for _ in range(3 - len(_three)):\n'
    "                                                    _tds += '<td></td>'\n"
    '                                                _rows_html += f\'<tr>{_tds}</tr>\'\n'
    '                                            _pnum = _p0 // 6 + 1\n'
    '                                            _foto_pages.append(\n'
    "                                                f'<div style=\"page-break-before:always;padding:4px\">'\n"
    "                                                f'<div class=\"section\">REGISTRO FOTOGRÁFICO — Página {_pnum}</div>'\n"
    "                                                f'<table style=\"width:100%;border-collapse:collapse\">{_rows_html}</table>'\n"
    "                                                f'</div>'\n"
    '                                            )\n'
    '                                        _fotos_html = "".join(_foto_pages)\n'
    '                                    else:\n'
    '                                        _fotos_html = ""\n'
)

assert OLD_C in src, "C: bloque galería NO encontrado"
assert src.count(OLD_C) == 1, "C: más de una coincidencia"
src = src.replace(OLD_C, NEW_C)
print("OK C: galería actualizada a páginas de 6 fotos")

# ═══ D: Mover {_fotos_html} al final del HTML (después de firmas) ════════════

# D1: Quitar del lugar actual (antes de las firmas)
OLD_D1 = '    {_fotos_html}\n\n    <div style="display:flex;justify-content:space-between;margin-top:20px">\n'
NEW_D1 = '    <div style="display:flex;justify-content:space-between;margin-top:20px">\n'
assert OLD_D1 in src, "D1: placeholder antes de firmas NO encontrado"
assert src.count(OLD_D1) == 1, "D1: más de una coincidencia"
src = src.replace(OLD_D1, NEW_D1)
print("OK D1: {_fotos_html} removido de antes de firmas")

# D2: Insertar DESPUÉS del div de cierre de pagina (antes de </body></html>)
OLD_D2 = '    </div>\n    </body></html>"""'
NEW_D2 = '    </div>\n    {_fotos_html}\n    </body></html>"""'
assert OLD_D2 in src, "D2: cierre </div></body></html> NO encontrado"
# Puede haber múltiples coincidencias (Locativos también tiene el mismo patrón)
count_D2 = src.count(OLD_D2)
print(f"  D2: {count_D2} coincidencia(s) de cierre HTML")
# Reemplazar solo la primera (HVAC viene primero en el archivo)
src = src.replace(OLD_D2, NEW_D2, 1)
print("OK D2: {_fotos_html} insertado al final del HTML HVAC (después de firmas)")

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
