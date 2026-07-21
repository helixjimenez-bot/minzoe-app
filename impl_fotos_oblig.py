"""
Implementa fotos obligatorias por tipo de equipo en reporte HVAC.
Actualiza Locativos de máx 12 a máx 25 fotos.

Cambios:
  1. Reemplaza sección de fotos genéricas HVAC (líneas ~4284-4313)
     con UI estructurada de ítems obligatorios.
  2. Agrega validación de fotos al inicio del bloque else: del form HVAC.
  3. Reemplaza bloque _fotos_list en else: HVAC con galería etiquetada.
  4. Envuelve el save+rerun final de HVAC con guarda de fotos completas.
  5. Actualiza cleanup HVAC Fase 2 para limpiar fotos_oblig_ y fotos_extra_.
  6. Actualiza máximo Locativos de 12 a 25.
"""

with open('solicitudes_minzoe.py', encoding='utf-8') as f:
    src = f.read()

original_len = len(src)

# ─── CAMBIO 1: Reemplaza sección fotos genéricas HVAC ────────────────────────

OLD1 = '''                        # ── Fotos del trabajo (máx. 12) ───────────────────
                        _fotos_key = f"fotos_rep_{id_ot_sel}"
                        if _fotos_key not in st.session_state:
                            st.session_state[_fotos_key] = []
                        _n_fotos = len(st.session_state[_fotos_key])
                        st.divider()
                        st.markdown(f"**📷 Fotos del trabajo** — {_n_fotos}/12")
                        _cam_foto = st.camera_input("Tomar foto", key=f"cam_rep_{id_ot_sel}_{_n_fotos}")
                        if _cam_foto:
                            _fc1, _fc2 = st.columns([1, 3])
                            with _fc1:
                                if st.button("📷 Agregar foto", key=f"add_foto_{id_ot_sel}",
                                             disabled=_n_fotos >= 12, use_container_width=True):
                                    import base64 as _b64mod
                                    _b64 = _b64mod.b64encode(_cam_foto.getvalue()).decode()
                                    st.session_state[_fotos_key].append(_b64)
                                    st.rerun()
                            with _fc2:
                                if _n_fotos >= 12:
                                    st.warning("Máximo 12 fotos alcanzado.")
                        if st.session_state[_fotos_key]:
                            _thumb_cols = st.columns(4)
                            for _fi, _fb in enumerate(st.session_state[_fotos_key]):
                                with _thumb_cols[_fi % 4]:
                                    st.image(f"data:image/jpeg;base64,{_fb}", use_container_width=True)
                                    if st.button("🗑️", key=f"del_foto_{id_ot_sel}_{_fi}",
                                                 use_container_width=True):
                                        st.session_state[_fotos_key].pop(_fi)
                                        st.rerun()'''

NEW1 = '''                        # ── Fotos obligatorias por tipo de equipo (máx. 25) ──
                        _FOTOS_OBLIG_AC = {
                            "split": [
                                ("volt_manj",  "Voltaje manejadora"),
                                ("amp_manj",   "Amperaje manejadora"),
                                ("volt_cond",  "Voltaje condensadora"),
                                ("amp_cond",   "Amperaje condensadora"),
                                ("temp_sum",   "Temperatura suministro"),
                                ("temp_ret",   "Temperatura retorno"),
                                ("temp_amb",   "Temperatura ambiente"),
                                ("lav_filt",   "Lavado filtros (manj.)"),
                                ("lav_serp_m", "Lavado serpentines (manj.)"),
                                ("limp_m",     "Limpieza int/ext (manj.)"),
                                ("rub_m",      "Revisión rubatex (manj.)"),
                                ("lav_serp_c", "Lavado serpentín (cond.)"),
                                ("limp_c",     "Limpieza int/ext (cond.)"),
                                ("rub_c",      "Revisión rubatex (cond.)"),
                            ],
                            "portatil": [
                                ("volt_unit",  "Voltaje unidad"),
                                ("amp_unit",   "Amperaje unidad"),
                                ("temp_sum",   "Temperatura suministro"),
                                ("temp_ret",   "Temperatura retorno"),
                                ("temp_amb",   "Temperatura ambiente"),
                                ("lav_filt",   "Lavado de filtros"),
                                ("limp_unit",  "Limpieza int/ext"),
                                ("rev_dren",   "Revisión drenaje"),
                            ],
                            "ventilador": [
                                ("volt_unit",  "Voltaje unidad"),
                                ("amp_unit",   "Amperaje unidad"),
                                ("limp_unit",  "Limpieza int/ext"),
                                ("rev_fij",    "Revisión fijaciones"),
                            ],
                        }
                        _cat_foto_ac = ("portatil" if _es_portatil
                                        else "ventilador" if _es_vent_ext
                                        else "split")
                        _items_oblig = _FOTOS_OBLIG_AC[_cat_foto_ac]

                        _fotos_oblig_key = f"fotos_oblig_{id_ot_sel}"
                        _fotos_extra_key = f"fotos_extra_{id_ot_sel}"
                        if _fotos_oblig_key not in st.session_state:
                            st.session_state[_fotos_oblig_key] = {}
                        if _fotos_extra_key not in st.session_state:
                            st.session_state[_fotos_extra_key] = []

                        _fotos_oblig_d = st.session_state[_fotos_oblig_key]
                        _fotos_extra_l = st.session_state[_fotos_extra_key]
                        _n_total_fotos = len(_fotos_oblig_d) + len(_fotos_extra_l)

                        st.divider()
                        _n_oblig_ok = sum(1 for _k, _ in _items_oblig if _k in _fotos_oblig_d)
                        st.markdown(
                            f"**📷 Registro fotográfico** — {_n_total_fotos}/25 "
                            f"&nbsp;|&nbsp; Obligatorias: {_n_oblig_ok}/{len(_items_oblig)}"
                        )

                        # Grid de estado por ítem obligatorio
                        _g_cols = st.columns(4)
                        for _gi, (_gk, _gl) in enumerate(_items_oblig):
                            with _g_cols[_gi % 4]:
                                _gok = _gk in _fotos_oblig_d
                                st.markdown(
                                    f"<div style='font-size:11px;padding:3px 5px;border-radius:4px;"
                                    f"background:{'#d1fae5' if _gok else '#fee2e2'};"
                                    f"border:1px solid {'#6ee7b7' if _gok else '#fca5a5'};margin:2px'>"
                                    f"{'✅' if _gok else '❌'} {_gl}</div>",
                                    unsafe_allow_html=True,
                                )

                        # Selector del ítem + cámara (fuera del form — requerido por Streamlit)
                        _pending_items = [(_k, _l) for _k, _l in _items_oblig if _k not in _fotos_oblig_d]
                        _hay_espacio   = _n_total_fotos < 25
                        _opcs_foto = (
                            [("-- Selecciona el ítem a fotografiar --", "")]
                            + [(f"⚠️ {_l}", _k) for _k, _l in _pending_items]
                            + ([("➕ Foto adicional", "__extra__")] if _hay_espacio else [])
                        )
                        if len(_opcs_foto) > 1:
                            _lbl_opcs = [_o[0] for _o in _opcs_foto]
                            _sel_idx = st.selectbox(
                                "¿Qué ítem vas a fotografiar?",
                                options=range(len(_lbl_opcs)),
                                format_func=lambda _i: _lbl_opcs[_i],
                                key=f"sel_item_foto_{id_ot_sel}",
                            )
                            _sel_item_key = _opcs_foto[_sel_idx][1]
                            _cam_oblig = st.camera_input(
                                "Tomar foto",
                                key=f"cam_oblig_{id_ot_sel}_{_n_total_fotos}",
                                disabled=(_sel_item_key == ""),
                            )
                            if _cam_oblig and _sel_item_key:
                                import base64 as _b64mod
                                _b64 = _b64mod.b64encode(_cam_oblig.getvalue()).decode()
                                if _sel_item_key == "__extra__":
                                    st.session_state[_fotos_extra_key].append(_b64)
                                else:
                                    st.session_state[_fotos_oblig_key][_sel_item_key] = _b64
                                st.rerun()
                        else:
                            st.success("✅ Todas las fotos obligatorias tomadas.")
                            if _hay_espacio:
                                _cam_extra = st.camera_input(
                                    "Foto adicional (opcional)",
                                    key=f"cam_extra_{id_ot_sel}_{_n_total_fotos}",
                                )
                                if _cam_extra:
                                    import base64 as _b64mod
                                    _b64 = _b64mod.b64encode(_cam_extra.getvalue()).decode()
                                    st.session_state[_fotos_extra_key].append(_b64)
                                    st.rerun()

                        # Miniaturas con opción de borrar
                        if _fotos_oblig_d or _fotos_extra_l:
                            _n_oblig_disp = len(_fotos_oblig_d)
                            _all_disp = (
                                [(_k, _fotos_oblig_d[_k]) for _k, _ in _items_oblig if _k in _fotos_oblig_d]
                                + [("__extra__", _fb) for _fb in _fotos_extra_l]
                            )
                            _td_cols = st.columns(4)
                            for _ti, (_tk, _tfb) in enumerate(_all_disp):
                                with _td_cols[_ti % 4]:
                                    _cap = (next((_l for _k, _l in _items_oblig if _k == _tk), "Extra")
                                            if _tk != "__extra__" else "Extra")
                                    st.image(f"data:image/jpeg;base64,{_tfb}",
                                             use_container_width=True, caption=_cap)
                                    if st.button("🗑️", key=f"del_foto_{id_ot_sel}_{_ti}",
                                                 use_container_width=True):
                                        if _tk == "__extra__":
                                            _idx_ex = _ti - _n_oblig_disp
                                            if 0 <= _idx_ex < len(st.session_state[_fotos_extra_key]):
                                                st.session_state[_fotos_extra_key].pop(_idx_ex)
                                        else:
                                            st.session_state[_fotos_oblig_key].pop(_tk, None)
                                        st.rerun()'''

assert OLD1 in src, "CAMBIO 1: texto antiguo NO encontrado"
assert src.count(OLD1) == 1, "CAMBIO 1: más de una coincidencia"
src = src.replace(OLD1, NEW1)
print("✅ Cambio 1 aplicado (fotos obligatorias HVAC UI)")

# ─── CAMBIO 2: Agrega validación fotos al inicio del bloque else: del form ───
# (solo en HVAC, la línea tiene 32 espacios, Locativos tiene 28)

OLD2 = (
    '                                else:\n'
    '                                    tipo_mto = " | ".join(filter(None,[\n'
    '                                        "Preventivo" if r_prev else "",\n'
    '                                        "Correctivo" if r_corr else "",\n'
    '                                        "Visita Técnica" if r_vis else "",\n'
    '                                        "Emergencia" if r_emer else "",\n'
    '                                        "Instalación" if r_inst else "",\n'
    '                                    ]))\n'
)

NEW2 = (
    '                                else:\n'
    '                                    # Validar fotos obligatorias\n'
    '                                    _fotos_oblig_chk = st.session_state.get(f"fotos_oblig_{id_ot_sel}", {})\n'
    '                                    _fotos_faltantes_subm = [\n'
    '                                        _l for _k, _l in _items_oblig if _k not in _fotos_oblig_chk\n'
    '                                    ]\n'
    '                                    if _fotos_faltantes_subm:\n'
    '                                        st.error(\n'
    '                                            f"⚠️ Faltan **{len(_fotos_faltantes_subm)}** foto(s) obligatoria(s). "\n'
    '                                            f"Tómalas antes de guardar el reporte:\\n\\n"\n'
    '                                            + "\\n".join(f"• {_l}" for _l in _fotos_faltantes_subm)\n'
    '                                        )\n'
    '                                    tipo_mto = " | ".join(filter(None,[\n'
    '                                        "Preventivo" if r_prev else "",\n'
    '                                        "Correctivo" if r_corr else "",\n'
    '                                        "Visita Técnica" if r_vis else "",\n'
    '                                        "Emergencia" if r_emer else "",\n'
    '                                        "Instalación" if r_inst else "",\n'
    '                                    ]))\n'
)

assert OLD2 in src, "CAMBIO 2: texto antiguo NO encontrado"
assert src.count(OLD2) == 1, "CAMBIO 2: más de una coincidencia"
src = src.replace(OLD2, NEW2)
print("✅ Cambio 2 aplicado (validación fotos en form submit HVAC)")

# ─── CAMBIO 3: Reemplaza _fotos_list en else: HVAC con galería etiquetada ────

OLD3 = (
    '                                    # Galería de fotos para el reporte\n'
    '                                    _fotos_list = st.session_state.get(f"fotos_rep_{id_ot_sel}", [])\n'
    '                                    if _fotos_list:\n'
    '                                        _fotos_imgs = "".join(\n'
    '                                            f\'<img src="data:image/jpeg;base64,{_fb}" \'\n'
    '                                            f\'style="width:165px;height:124px;object-fit:cover;\'\n'
    '                                            f\'border:1px solid #ccc;border-radius:3px;margin:3px">\'\n'
    '                                            for _fb in _fotos_list\n'
    '                                        )\n'
    '                                        _fotos_html = (\n'
    '                                            \'<div class="section">REGISTRO FOTOGRÁFICO</div>\'\n'
    '                                            f\'<div style="display:flex;flex-wrap:wrap;gap:4px;margin:4px 0">\'\n'
    '                                            f\'{_fotos_imgs}</div>\'\n'
    '                                        )\n'
    '                                    else:\n'
    '                                        _fotos_html = ""\n'
)

NEW3 = (
    '                                    # Galería etiquetada de fotos para el reporte\n'
    '                                    _fotos_oblig_rep = st.session_state.get(f"fotos_oblig_{id_ot_sel}", {})\n'
    '                                    _fotos_extra_rep  = st.session_state.get(f"fotos_extra_{id_ot_sel}", [])\n'
    '                                    _fotos_html_items = []\n'
    '                                    for _fk, _fl in _items_oblig:\n'
    '                                        if _fk in _fotos_oblig_rep:\n'
    '                                            _fotos_html_items.append(\n'
    '                                                f\'<div style="text-align:center;margin:4px">\'\n'
    '                                                f\'<img src="data:image/jpeg;base64,{_fotos_oblig_rep[_fk]}" \'\n'
    '                                                f\'style="width:160px;height:120px;object-fit:cover;\'\n'
    '                                                f\'border:1px solid #ccc;border-radius:3px">\'\n'
    '                                                f\'<div style="font-size:7.5px;margin-top:2px;color:#555">{_fl}</div>\'\n'
    '                                                f\'</div>\'\n'
    '                                            )\n'
    '                                    for _fexb in _fotos_extra_rep:\n'
    '                                        _fotos_html_items.append(\n'
    '                                            f\'<div style="text-align:center;margin:4px">\'\n'
    '                                            f\'<img src="data:image/jpeg;base64,{_fexb}" \'\n'
    '                                            f\'style="width:160px;height:120px;object-fit:cover;\'\n'
    '                                            f\'border:1px solid #ccc;border-radius:3px">\'\n'
    '                                            f\'<div style="font-size:7.5px;margin-top:2px;color:#555">Adicional</div>\'\n'
    '                                            f\'</div>\'\n'
    '                                        )\n'
    '                                    if _fotos_html_items:\n'
    '                                        _fotos_html = (\n'
    '                                            \'<div class="section">REGISTRO FOTOGRÁFICO</div>\'\n'
    '                                            \'<div style="display:flex;flex-wrap:wrap;gap:4px;margin:4px 0">\'\n'
    '                                            + "".join(_fotos_html_items) + \'</div>\'\n'
    '                                        )\n'
    '                                    else:\n'
    '                                        _fotos_html = ""\n'
)

assert OLD3 in src, "CAMBIO 3: texto antiguo NO encontrado"
assert src.count(OLD3) == 1, "CAMBIO 3: más de una coincidencia"
src = src.replace(OLD3, NEW3)
print("✅ Cambio 3 aplicado (galería etiquetada HVAC)")

# ─── CAMBIO 4: Envuelve save+rerun HVAC con guarda de fotos completas ─────────

OLD4 = (
    '                                    # Guardar HTML con placeholder — la firma se agrega en fase 2\n'
    '                                    st.session_state[f"hvac_html_raw_{id_ot_sel}"] = html\n'
    '                                    st.session_state[f"hvac_cli_{id_ot_sel}"]  = fila_ot["Cliente"]\n'
    '                                    st.session_state[f"hvac_sede_{id_ot_sel}"] = fila_ot.get("Sede","")\n'
    '                                    st.session_state[f"hvac_fec_{id_ot_sel}"]  = fila_ot.get("Fecha_Ejecucion","")\n'
    '                                    st.rerun()\n'
)

NEW4 = (
    '                                    # Guardar solo si todas las fotos obligatorias están presentes\n'
    '                                    if not _fotos_faltantes_subm:\n'
    '                                        st.session_state[f"hvac_html_raw_{id_ot_sel}"] = html\n'
    '                                        st.session_state[f"hvac_cli_{id_ot_sel}"]  = fila_ot["Cliente"]\n'
    '                                        st.session_state[f"hvac_sede_{id_ot_sel}"] = fila_ot.get("Sede","")\n'
    '                                        st.session_state[f"hvac_fec_{id_ot_sel}"]  = fila_ot.get("Fecha_Ejecucion","")\n'
    '                                        st.rerun()\n'
)

assert OLD4 in src, "CAMBIO 4: texto antiguo NO encontrado"
assert src.count(OLD4) == 1, "CAMBIO 4: más de una coincidencia"
src = src.replace(OLD4, NEW4)
print("✅ Cambio 4 aplicado (save+rerun HVAC guardado)")

# ─── CAMBIO 5: Actualiza cleanup HVAC Fase 2 ──────────────────────────────────

OLD5 = (
    '                            for _k in ["_tec_en_reporte", "_tec_viewing_ot", "ot_preselect",\n'
    '                                       f"fotos_rep_{id_ot_sel}"]:\n'
    '                                st.session_state.pop(_k, None)\n'
    '                            st.session_state["_msg_tec_ok"] = f"✅ {msg_fin}"\n'
)

NEW5 = (
    '                            for _k in ["_tec_en_reporte", "_tec_viewing_ot", "ot_preselect",\n'
    '                                       f"fotos_oblig_{id_ot_sel}", f"fotos_extra_{id_ot_sel}"]:\n'
    '                                st.session_state.pop(_k, None)\n'
    '                            st.session_state["_msg_tec_ok"] = f"✅ {msg_fin}"\n'
)

assert OLD5 in src, "CAMBIO 5: texto antiguo NO encontrado"
assert src.count(OLD5) == 1, "CAMBIO 5: más de una coincidencia"
src = src.replace(OLD5, NEW5)
print("✅ Cambio 5 aplicado (cleanup HVAC Fase 2)")

# ─── CAMBIO 6: Actualiza Locativos máx 12 → 25 ────────────────────────────────

OLD6 = (
    '                        # ── Fotos del trabajo Locativos (máx. 12) ─────────\n'
    '                        _fotos_key = f"fotos_rep_{id_ot_sel}"\n'
    '                        if _fotos_key not in st.session_state:\n'
    '                            st.session_state[_fotos_key] = []\n'
    '                        _n_fotos = len(st.session_state[_fotos_key])\n'
    '                        st.divider()\n'
    '                        st.markdown(f"**📷 Fotos del trabajo** — {_n_fotos}/12")\n'
    '                        _cam_foto = st.camera_input("Tomar foto", key=f"cam_rep_{id_ot_sel}_{_n_fotos}")\n'
    '                        if _cam_foto:\n'
    '                            _fc1, _fc2 = st.columns([1, 3])\n'
    '                            with _fc1:\n'
    '                                if st.button("📷 Agregar foto", key=f"add_foto_{id_ot_sel}",\n'
    '                                             disabled=_n_fotos >= 12, use_container_width=True):\n'
    '                                    import base64 as _b64mod\n'
    '                                    _b64 = _b64mod.b64encode(_cam_foto.getvalue()).decode()\n'
    '                                    st.session_state[_fotos_key].append(_b64)\n'
    '                                    st.rerun()\n'
    '                            with _fc2:\n'
    '                                if _n_fotos >= 12:\n'
    '                                    st.warning("Máximo 12 fotos alcanzado.")\n'
)

NEW6 = (
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
)

assert OLD6 in src, "CAMBIO 6: texto antiguo NO encontrado"
assert src.count(OLD6) == 1, "CAMBIO 6: más de una coincidencia"
src = src.replace(OLD6, NEW6)
print("✅ Cambio 6 aplicado (Locativos máx 12→25)")

# ─── Verificar sintaxis ────────────────────────────────────────────────────────

assert len(src) > original_len, "ERROR: el archivo resultante es más pequeño (algo salió mal)"

import ast
try:
    ast.parse(src)
    print("✅ Sintaxis Python correcta")
except SyntaxError as e:
    print(f"❌ ERROR de sintaxis en línea {e.lineno}: {e.msg}")
    lines = src.splitlines()
    for j in range(max(0, e.lineno - 5), min(len(lines), e.lineno + 4)):
        print(f"  {j+1}: {lines[j]}")
    raise

with open('solicitudes_minzoe.py', 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n✅ Archivo guardado. Tamaño original: {original_len} → nuevo: {len(src)} bytes")
