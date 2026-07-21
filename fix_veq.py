
with open('solicitudes_minzoe.py', encoding='utf-8') as f:
    content = f.read()

OLD = '''            # Filas con botón VER EQ. en la celda correcta
            for _sd in _sedes_ac_lista:
                _ac_sd2  = _ac_vis[_ac_vis["Sede"] == _sd]
                _sd_info = _mis_sedes_df[_mis_sedes_df["Sede"] == _sd].iloc[0] if not _mis_sedes_df.empty and _sd in _mis_sedes_df["Sede"].values else None
                _ciudad  = _sd_info.get("Direccion_Sede","—") if _sd_info is not None else "—"
                _activo  = _sede_eq_sel == _sd
                _row_bg  = "#fff0f0" if _activo else ("white" if _sedes_ac_lista.index(_sd) % 2 == 0 else "#fafafa")
                _style   = f"background:{_row_bg};padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:0.82rem"

                _r1, _r2, _r3, _r4 = st.columns([5, 2, 1, 1])
                _r1.markdown(f"<div style='{_style};font-weight:600'>{_sd}</div>", unsafe_allow_html=True)
                _r2.markdown(f"<div style='{_style};text-align:center'>{_ciudad}</div>", unsafe_allow_html=True)
                _r3.markdown(f"<div style='{_style};text-align:center;font-weight:700;color:#dc2626'>{len(_ac_sd2)}</div>", unsafe_allow_html=True)
                with _r4:
                    _lbl_b = "✕ Cerrar" if _activo else "VER EQ."
                    if st.button(_lbl_b, key=f"veq_{_sd}", use_container_width=True):
                        if _activo:
                            st.session_state.pop("_cli_sede_eq_sel", None)
                        else:
                            st.session_state["_cli_sede_eq_sel"] = _sd
                        st.rerun()

            # Detalle equipos de la sede seleccionada
            if _sede_eq_sel and _sede_eq_sel in _sedes_ac_lista:
                _ac_detalle = _ac_vis[_ac_vis["Sede"] == _sede_eq_sel]
                st.markdown(f"""<div style="background:#fff0f0;border:2px solid #dc2626;
                    border-radius:10px;padding:8px 16px;margin:12px 0 8px;
                    font-weight:700;color:#dc2626">📍 {_sede_eq_sel} — {len(_ac_detalle)} equipo(s)</div>""",
                    unsafe_allow_html=True)

                for idx_eq, (_, _eq) in enumerate(_ac_detalle.iterrows()):'''

NEW = '''            # Filas con botón VER EQ. — detalle aparece inmediatamente debajo de la fila activa
            for _sd in _sedes_ac_lista:
                _ac_sd2  = _ac_vis[_ac_vis["Sede"] == _sd]
                _sd_info = _mis_sedes_df[_mis_sedes_df["Sede"] == _sd].iloc[0] if not _mis_sedes_df.empty and _sd in _mis_sedes_df["Sede"].values else None
                _ciudad  = _sd_info.get("Direccion_Sede","—") if _sd_info is not None else "—"
                _activo  = _sede_eq_sel == _sd
                _row_bg  = "#fff0f0" if _activo else ("white" if _sedes_ac_lista.index(_sd) % 2 == 0 else "#fafafa")
                _brd     = "2px solid #dc2626" if _activo else "1px solid #e5e7eb"
                _style   = f"background:{_row_bg};padding:9px 10px;border-bottom:{_brd};font-size:0.83rem"

                _r1, _r2, _r3, _r4 = st.columns([5, 2, 1, 1])
                _r1.markdown(f"<div style='{_style};font-weight:600'>{_sd}</div>", unsafe_allow_html=True)
                _r2.markdown(f"<div style='{_style};text-align:center'>{_ciudad}</div>", unsafe_allow_html=True)
                _r3.markdown(f"<div style='{_style};text-align:center;font-weight:700;color:#dc2626'>{len(_ac_sd2)}</div>", unsafe_allow_html=True)
                with _r4:
                    _lbl_b = "✕ Cerrar" if _activo else "VER EQ."
                    if st.button(_lbl_b, key=f"veq_{_sd}", use_container_width=True):
                        if _activo:
                            st.session_state.pop("_cli_sede_eq_sel", None)
                        else:
                            st.session_state["_cli_sede_eq_sel"] = _sd
                        st.rerun()

                # Detalle aparece justo debajo de la fila activa
                if _activo:
                    _ac_detalle = _ac_sd2
                    st.markdown(f"""<div style="background:#fff8f8;border-left:4px solid #dc2626;
                        padding:8px 16px;margin:0 0 6px;font-size:0.82rem;color:#555">
                        {len(_ac_detalle)} equipo(s) en esta sede</div>""", unsafe_allow_html=True)
                    for idx_eq, (_, _eq) in enumerate(_ac_detalle.iterrows()):'''

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    with open('solicitudes_minzoe.py', 'w', encoding='utf-8') as f:
        f.write(content)
    import ast
    try:
        ast.parse(content)
        print("OK - sintaxis correcta")
    except SyntaxError as e:
        print(f"Error linea {e.lineno}: {e.msg}")
else:
    print("ERROR: bloque no encontrado")
    idx = content.find('Filas con botón VER EQ.')
    print(f"Encontrado en pos: {idx}")
