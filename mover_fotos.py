"""
Mueve la UI de fotos HVAC para que aparezca DESPUÉS del formulario.

Situación actual:
  [Tipo de mantenimiento]
  [Foto obligatorias UI — grid + cámara]     ← aquí (antes del form)
  [Form: datos equipo → medición → checklist → observaciones → submit]

Resultado:
  [Tipo de mantenimiento]
  [Solo definición del dict + _items_oblig]  ← para que el else: del form lo vea
  [Form: datos equipo → medición → checklist → observaciones → submit]
  [Foto obligatorias UI — grid + cámara]     ← AQUÍ (después del form / después de observaciones)
  [FUERA del form: guardar]
"""

with open('solicitudes_minzoe.py', encoding='utf-8') as f:
    src = f.read()

original_len = len(src)

# ─── Parte 1: conservar solo la definición en la posición original ─────────

# Bloque completo actual (dict + UI completa), desde la sesión de init hasta el último rerun
OLD_FULL = (
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
    '                                st.markdown(\n'
    '                                    f"<div style=\'font-size:11px;padding:3px 5px;border-radius:4px;"\n'
    '                                    f"background:{\'#d1fae5\' if _gok else \'#fee2e2\'};"\n'
    '                                    f"border:1px solid {\'#6ee7b7\' if _gok else \'#fca5a5\'};margin:2px>"\n'
    '                                    f"{\'✅\' if _gok else \'❌\'} {_gl}</div>",\n'
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

assert OLD_FULL in src, "PARTE 1: bloque visual a remover NO encontrado"
assert src.count(OLD_FULL) == 1, "PARTE 1: más de una coincidencia"
src = src.replace(OLD_FULL, '\n')
print("OK Parte 1: bloque visual removido de posición original")

# ─── Parte 2: actualizar el comentario del bloque que quedó ──────────────────

OLD_CMT = '                        # ── Fotos obligatorias por tipo de equipo (máx. 25) ──\n'
NEW_CMT = '                        # ── Definición de fotos obligatorias (UI más abajo, tras el formulario) ──\n'
assert OLD_CMT in src, "PARTE 2: comentario NO encontrado"
src = src.replace(OLD_CMT, NEW_CMT, 1)
print("OK Parte 2: comentario actualizado")

# ─── Parte 3: insertar la UI de fotos ANTES de "FUERA del form" ──────────────

ANCHOR = '                        # ── FUERA del form: guardar ──────────────────────\n'
assert ANCHOR in src, "PARTE 3: ancla 'FUERA del form' NO encontrada"

FOTO_UI_AFTER = (
    '                        # ── Fotos del trabajo (va después de Observaciones generales) ──\n'
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
    '                                st.markdown(\n'
    '                                    f"<div style=\'font-size:11px;padding:3px 5px;border-radius:4px;"\n'
    '                                    f"background:{\'#d1fae5\' if _gok else \'#fee2e2\'};"\n'
    '                                    f"border:1px solid {\'#6ee7b7\' if _gok else \'#fca5a5\'};margin:2px>"\n'
    '                                    f"{\'✅\' if _gok else \'❌\'} {_gl}</div>",\n'
    '                                    unsafe_allow_html=True,\n'
    '                                )\n'
    '\n'
    '                        # Selector del ítem + cámara (debe estar fuera del form)\n'
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

src = src.replace(ANCHOR, FOTO_UI_AFTER + ANCHOR, 1)
print("OK Parte 3: UI de fotos insertada después del formulario")

# ─── Verificar sintaxis ───────────────────────────────────────────────────────

import ast
try:
    ast.parse(src)
    print("OK Sintaxis Python correcta")
except SyntaxError as e:
    print(f"ERROR de sintaxis en linea {e.lineno}: {e.msg}")
    lines = src.splitlines()
    for j in range(max(0, e.lineno - 5), min(len(lines), e.lineno + 4)):
        print(f"  {j+1}: {lines[j]}")
    raise

with open('solicitudes_minzoe.py', 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\nArchivo guardado. Original: {original_len} -> nuevo: {len(src)} bytes")
