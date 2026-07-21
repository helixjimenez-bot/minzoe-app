
with open('solicitudes_minzoe.py', encoding='utf-8') as f:
    content = f.read()

old_section_start = '        elif _cli_seccion == "equipos_ac":'
old_section_end   = '\n        elif _cli_seccion == "solicitudes":'

start_idx = content.find(old_section_start)
end_idx   = content.find(old_section_end)
print(f"Start: {start_idx}, End: {end_idx}")

new_block = '''        elif _cli_seccion == "equipos_ac":
            _ef = st.session_state.get("_cli_sede_filtro")
            _ac_vis = _mis_ac[_mis_ac["Sede"].str.strip().str.lower() == _ef.strip().lower()] if _ef and not _mis_ac.empty else _mis_ac
            _sede_eq_sel = st.session_state.get("_cli_sede_eq_sel")
            st.markdown(f"### ❄️ Aires Acondicionados — {len(_ac_vis)} equipo(s)")

            def _fila_eq(lbl, val):
                return (f"<tr><td style='background:#f8f9fa;font-weight:600;padding:7px 12px;"
                        f"border:1px solid #dee2e6;font-size:0.8rem;white-space:nowrap'>{lbl}</td>"
                        f"<td style='padding:7px 12px;border:1px solid #dee2e6;font-size:0.82rem'>{val or '—'}</td></tr>")

            _sedes_ac_lista = sorted(_ac_vis["Sede"].unique().tolist()) if not _ac_vis.empty else []

            # Tabla SEDE | CIUDAD | EQUIPOS | ACCION
            _filas_t = ""
            for _sd in _sedes_ac_lista:
                _ac_sd2  = _ac_vis[_ac_vis["Sede"] == _sd]
                _sd_info = _mis_sedes_df[_mis_sedes_df["Sede"] == _sd].iloc[0] if not _mis_sedes_df.empty and _sd in _mis_sedes_df["Sede"].values else None
                _ciudad  = _sd_info.get("Direccion_Sede", "—") if _sd_info is not None else "—"
                _row_bg  = "#fff5f5" if _sede_eq_sel == _sd else "white"
                _filas_t += (f"<tr style='background:{_row_bg}'>"
                             f"<td style='padding:8px 12px;border:1px solid #dee2e6;font-weight:600'>{_sd}</td>"
                             f"<td style='padding:8px 12px;border:1px solid #dee2e6;text-align:center'>{_ciudad}</td>"
                             f"<td style='padding:8px 12px;border:1px solid #dee2e6;text-align:center;"
                             f"font-weight:700;color:#dc2626'>{len(_ac_sd2)}</td>"
                             f"<td style='padding:8px 12px;border:1px solid #dee2e6;text-align:center'></td></tr>")

            st.markdown(f"""
            <table style="width:100%;border-collapse:collapse;margin-bottom:6px">
              <tr>
                <th style="background:#dc2626;color:white;padding:9px 14px;border:1px solid #c01c1c;text-align:left">SEDE</th>
                <th style="background:#dc2626;color:white;padding:9px 14px;border:1px solid #c01c1c;text-align:center">CIUDAD</th>
                <th style="background:#dc2626;color:white;padding:9px 14px;border:1px solid #c01c1c;text-align:center">EQUIPOS</th>
                <th style="background:#dc2626;color:white;padding:9px 14px;border:1px solid #c01c1c;text-align:center">ACCION</th>
              </tr>{_filas_t}
            </table>""", unsafe_allow_html=True)

            # Botones VER EQ. alineados con columna ACCION
            for _sd in _sedes_ac_lista:
                _c_esp, _c_btn = st.columns([6, 1])
                with _c_btn:
                    _lbl_b = "✕ Cerrar" if _sede_eq_sel == _sd else "VER EQ."
                    if st.button(_lbl_b, key=f"veq_{_sd}", use_container_width=True):
                        if _sede_eq_sel == _sd:
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

                for idx_eq, (_, _eq) in enumerate(_ac_detalle.iterrows()):
                    _prox = _eq.get("Proximo_Mantenimiento",""); _ult = _eq.get("Ultimo_Mantenimiento","")
                    try:
                        _d = (datetime.strptime(_prox, "%Y-%m-%d") - ahora_colombia()).days
                        _alerta = "🔴 Vencido" if _d < 0 else (f"🟡 En {_d}d" if _d <= 15 else f"🟢 En {_d}d")
                        _cbr = "#dc2626" if _d < 0 else ("#f59e0b" if _d <= 15 else "#16a34a")
                    except: _alerta, _cbr = "Sin fecha", "#9ca3af"

                    _serial_raw = _eq.get("Numero_Serie",""); _specs_raw = _eq.get("Especificaciones","")
                    _ubic_raw   = _eq.get("Ubicacion","");    _modelo_raw = _eq.get("Modelo","")
                    _ser_cond = _ser_evap = _serial_raw
                    if "Cond:" in _serial_raw and "|" in _serial_raw:
                        _pts = _serial_raw.split("|")
                        _ser_cond = _pts[0].replace("Cond:","").strip()
                        _ser_evap = _pts[1].replace("Evap:","").strip() if len(_pts) > 1 else "—"
                    _btu = _refrig = ""
                    if "|" in _specs_raw:
                        _sp = _specs_raw.split("|"); _btu = _sp[0].strip(); _refrig = _sp[1].strip()
                    else: _btu = _specs_raw
                    _ubic_evap = _ubic_cond = _ubic_raw
                    if "Evap:" in _ubic_raw and "|" in _ubic_raw:
                        _up = _ubic_raw.split("|")
                        _ubic_evap = _up[0].replace("Evap:","").strip()
                        _ubic_cond = _up[1].replace("Cond:","").strip() if len(_up) > 1 else "—"
                    _tipo_eq = ""; _solo_modelo = _modelo_raw
                    for _tk in ["Minisplit","Cassette","Split","Manejadora","Paquete","Chiller","VRF","Fan","Portátil","Ventilador","Extractor"]:
                        if _modelo_raw.startswith(_tk):
                            _tipo_eq = _tk; _solo_modelo = _modelo_raw[len(_tk):].strip(); break

                    if idx_eq > 0:
                        st.markdown("<hr style='margin:16px 0;border-color:#eee'>", unsafe_allow_html=True)

                    st.markdown(f"""
                    <table style='width:100%;border-collapse:collapse;margin-bottom:10px'>
                      <tr><th colspan='2' style='background:#dc2626;color:white;padding:9px 12px;
                          text-align:center;font-size:0.85rem;letter-spacing:1px'>
                        DATOS DEL EQUIPO — {_eq.get('ID_Item','')}
                      </th></tr>
                      {_fila_eq("TIPO DE EQUIPO",           _tipo_eq)}
                      {_fila_eq("MARCA",                    _eq.get("Marca",""))}
                      {_fila_eq("MODELO",                   _solo_modelo)}
                      {_fila_eq("SERIAL CONDENSADORA",      _ser_cond)}
                      {_fila_eq("SERIAL EVAPORADORA",       _ser_evap)}
                      {_fila_eq("CAPACIDAD EN BTU",         _btu)}
                      {_fila_eq("TIPO DE REFRIGERANTE",     _refrig)}
                      {_fila_eq("UBICACIÓN EVAPORADORA",    _ubic_evap)}
                      {_fila_eq("UBICACIÓN CONDENSADORA",   _ubic_cond)}
                      {_fila_eq("ÚLTIMO MANTENIMIENTO",     _ult)}
                      {_fila_eq("PRÓXIMO MANTENIMIENTO", f'<span style="color:{_cbr};font-weight:700">{_prox} — {_alerta}</span>' if _prox else "—")}
                    </table>""", unsafe_allow_html=True)

                    _ots_eq = mis_ots[
                        (mis_ots["Sede"].str.strip().str.lower() == _sede_eq_sel.strip().lower()) &
                        (mis_ots["Servicio"] == "Aires Acondicionados")
                    ] if not mis_ots.empty else pd.DataFrame()
                    with st.expander(f"📋 Ver historial de servicios ({len(_ots_eq)} registro(s))"):
                        if _ots_eq.empty:
                            st.info("Sin servicios registrados.")
                        else:
                            _c2 = [c for c in ["ID","Fecha_Creacion","Descripcion","Tecnico","Fecha_Ejecucion","Estado"] if c in _ots_eq.columns]
                            tabla_html(_ots_eq.sort_values("Fecha_Creacion", ascending=False)[_c2].reset_index(drop=True),
                                       color_col="Estado", colores_estado=COLORES_OT_CLI)
                            for _, _or in _ots_eq[_ots_eq["Estado"].isin(["Finalizada","En revisión"])].iterrows():
                                _rh, _ = cargar_reporte_sb(_or["ID"])
                                if _rh:
                                    st.download_button(f"⬇️ Reporte {_or['ID']}",
                                        data=_rh, file_name=f"Reporte_{_or['ID']}.html",
                                        mime="text/html", key=f"dl3_{_eq.get('ID_Item','x')}_{_or['ID']}")'''

new_content = content[:start_idx] + new_block + content[end_idx:]

with open('solicitudes_minzoe.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
print("Escrito OK")
