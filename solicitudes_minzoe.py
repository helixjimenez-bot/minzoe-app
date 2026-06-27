import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import hashlib
import gspread
from google.oauth2.service_account import Credentials

USUARIOS_FILE     = r"D:\Escritorio\LA ASISTENTE MINZOE\usuarios.csv"

# ── Rutas de guardado de reportes ─────────────────────────────────────────────
BASE_REPORTES = r"H:\03_CLIENTES"

CLIENTES_CARPETA = {
    "ALTIPAL":        "01_Altipal",
    "PAGAFACIL":      "00_Pagafacil",
    "CORRESPONSALES": "00_Pagafacil",  # Pagafacil es el nombre comercial de Corresponsales
}

MESES_CARPETA = {
    "01":"01_enero","02":"02_febrero","03":"03_marzo","04":"04_abril",
    "05":"05_mayo","06":"06_junio","07":"07_julio","08":"08_agosto",
    "09":"09_septiembre","10":"10_octubre","11":"11_noviembre","12":"12_diciembre",
}
SOLICITUDES_FILE  = "solicitudes.csv"
CLIENTES_FILE     = "clientes.csv"
OTS_FILE          = "ordenes_trabajo.csv"
CONTRATOS_FILE    = "contratos_aires.csv"
EQUIPOS_FILE      = "equipos_aires.csv"
COMPRAS_FILE      = "compras_ventas.csv"
VENTAS_FILE       = "ventas.csv"
COSTOS_FILE       = "costos.csv"

SERVICIOS = [
    "Productos de Aseo",
    "Obra Civil",
    "Aires Acondicionados",
    "UPS y Plantas Eléctricas",
    "Cámaras de Seguridad",
    "Arreglos Locativos",
]
ESTADOS  = ["Pendiente", "Aprobado", "Completado", "Cancelado"]
SLA      = ["Programado", "Urgencia", "Emergencia"]
CANALES  = ["📱 WhatsApp", "📧 Correo", "📞 Teléfono", "🔵 Otro"]

TIPOS_SERVICIO = [
    "Preventivo",
    "Correctivo",
    "Emergencia",
    "Diagnóstico",
    "Suministro e Instalación",
    "Visita Técnica",
]

COLS_SOL = [
    "ID", "Fecha", "Creado_Por", "Cliente", "NIT", "Direccion_Empresa",
    "Sede", "Direccion_Sede", "Nombre_Contacto", "Correo_Contacto", "Celular_Contacto",
    "Servicio", "Tipo_Servicio", "Descripcion", "SLA", "Ciudad", "Zona", "Canal", "Estado",
    "Email_Message_ID",
]
COLS_CLI = [
    "Empresa", "NIT", "Direccion_Empresa",
    "Sede", "Direccion_Sede",
    "Nombre_Contacto", "Correo_Contacto", "Celular_Contacto",
]

ESTADOS_OT   = ["Programada", "En ejecución", "En revisión", "Finalizada", "Cancelada"]
FRECUENCIAS  = ["Mensual", "Bimestral (2 meses)", "Cada 4 meses", "Trimestral (3 meses)", "Semestral (6 meses)"]
FREQ_MESES   = {"Mensual": 1, "Bimestral (2 meses)": 2, "Cada 4 meses": 4, "Trimestral (3 meses)": 3, "Semestral (6 meses)": 6}
REFRIGERANTES = ["R-22", "R-410A", "R-32", "R-407C", "R-134A", "Otro"]

COLS_CV = [
    "ID_Registro", "Fecha", "OT_Ref", "SOL_Ref", "Cliente", "Servicio",
    "Cotizacion_Siigo", "Valor_Antes_IVA", "IVA_19", "Valor_Total_Cobrado",
    "Valor_Tecnico", "Valor_Materiales", "Factura_Materiales",
    "Utilidad", "Margen_Pct",
]

COLS_VENTA = [
    "ID_Factura", "Fecha_Facturacion", "Fecha_Vencimiento",
    "OT_Ref", "SOL_Ref", "Cliente", "Servicio",
    "Cotizacion_Siigo", "Orden_Compra",
    "Valor_Antes_IVA", "IVA", "Retefuente", "Retica",
    "Total_A_Pagar", "Estado_Pago",
]

COLS_COSTO = [
    "ID_Costo", "Fecha", "OT_Ref", "SOL_Ref", "Cliente", "Servicio",
    "Valor_Tecnico", "Valor_Materiales", "Factura_Materiales", "Total_Costo",
]

ESTADOS_PAGO = ["Pendiente", "Pagada", "Vencida", "Anulada"]


def ahora_colombia():
    """Retorna datetime actual en hora Colombia (UTC-5)."""
    return datetime.utcnow() - timedelta(hours=5)


def festivos_colombia(año):
    """Festivos nacionales de Colombia para el año dado (set de date)."""
    from datetime import date
    f = set()
    # Fijos
    f.add(date(año, 1, 1))   # Año Nuevo
    f.add(date(año, 5, 1))   # Día del Trabajo
    f.add(date(año, 7, 20))  # Independencia
    f.add(date(año, 8, 7))   # Batalla de Boyacá
    f.add(date(año, 12, 8))  # Inmaculada Concepción
    f.add(date(año, 12, 25)) # Navidad

    def sig_lunes(d):
        """Ley Emiliani: mueve al siguiente lunes si no cae en lunes."""
        dias = (7 - d.weekday()) % 7
        return d + timedelta(days=dias if dias else 7) if d.weekday() != 0 else d

    # Movibles (Ley Emiliani)
    f.add(sig_lunes(date(año, 1, 6)))    # Reyes Magos
    f.add(sig_lunes(date(año, 3, 19)))   # San José
    f.add(sig_lunes(date(año, 6, 29)))   # San Pedro y San Pablo
    f.add(sig_lunes(date(año, 8, 15)))   # Asunción de la Virgen
    f.add(sig_lunes(date(año, 10, 12)))  # Día de la Raza
    f.add(sig_lunes(date(año, 11, 1)))   # Todos los Santos
    f.add(sig_lunes(date(año, 11, 11)))  # Independencia de Cartagena

    # Pascua (algoritmo de Meeus/Jones/Butcher)
    a = año % 19
    b = año // 100; c = año % 100
    d_ = b // 4;    e = b % 4
    ff = (b + 8) // 25
    g = (b - ff + 1) // 3
    h = (19*a + b - d_ - g + 15) % 30
    i = c // 4;     k = c % 4
    l = (32 + 2*e + 2*i - h - k) % 7
    m = (a + 11*h + 22*l) // 451
    mes_p = (h + l - 7*m + 114) // 31
    dia_p = ((h + l - 7*m + 114) % 31) + 1
    from datetime import date as _date
    pascua = _date(año, mes_p, dia_p)
    f.add(pascua - timedelta(days=3))                   # Jueves Santo
    f.add(pascua - timedelta(days=2))                   # Viernes Santo
    f.add(sig_lunes(pascua + timedelta(days=39)))       # Ascensión
    f.add(sig_lunes(pascua + timedelta(days=60)))       # Corpus Christi
    f.add(sig_lunes(pascua + timedelta(days=68)))       # Sagrado Corazón
    return f


def es_dia_laboral(dt):
    """True si la fecha es día laboral: lunes a sábado, sin festivos colombianos."""
    d = dt.date() if isinstance(dt, datetime) else dt
    if d.weekday() == 6:  # domingo
        return False
    return d not in festivos_colombia(d.year)


def sumar_horas_laborales(desde, horas):
    """Suma N horas avanzando solo en días laborales (lun-sáb, no festivos).
    Domingos y festivos se saltan por completo al siguiente día laboral."""
    dt = desde
    pendientes = float(horas)
    while pendientes > 0:
        # Si el día actual no es laboral, saltar al inicio del siguiente día
        if not es_dia_laboral(dt):
            dt = datetime(dt.year, dt.month, dt.day) + timedelta(days=1)
            continue
        # Horas que quedan hasta la medianoche de este día laboral
        sig = datetime(dt.year, dt.month, dt.day) + timedelta(days=1)
        horas_dia = (sig - dt).total_seconds() / 3600
        if pendientes <= horas_dia:
            dt = dt + timedelta(hours=pendientes)
            pendientes = 0
        else:
            pendientes -= horas_dia
            dt = sig
    # Si el resultado cae en día no laboral, mover al inicio del próximo laboral
    while not es_dia_laboral(dt):
        dt = datetime(dt.year, dt.month, dt.day) + timedelta(days=1)
    return dt


COLS_COUNTERS    = ["tipo", "prefijo", "ultimo_num"]
COLS_HISTORIAL   = ["ID_Log","Fecha","Usuario","Entidad","Entidad_ID","Campo","Valor_Anterior","Valor_Nuevo"]
COLS_COMENTARIOS = ["ID_Com","Fecha","Usuario","Entidad","Entidad_ID","Comentario"]

def load_counters():
    return sb_load("contadores", COLS_COUNTERS)

def save_counters(df):
    sb_save("contadores", df)

def load_historial():
    return sb_load("historial", COLS_HISTORIAL)

def load_comentarios():
    return sb_load("comentarios", COLS_COMENTARIOS)

def _sb_insert(tabla, registro):
    """Inserta un único registro sin truncar la tabla (para historial y comentarios)."""
    try:
        get_sb().table(tabla).insert(registro).execute()
        return True
    except Exception:
        return False

def guardar_reporte_sb(ot_id, tipo, cliente, fecha, html):
    """Guarda el reporte en Supabase sin el logo embebido (ahorra espacio)."""
    import re
    html_sin_logo = re.sub(
        r'<img src="data:image/[^"]+base64,[^""]+"[^>]*style="height:60px[^"]*"[^>]*>',
        '<span style="font-size:1.1rem;font-weight:900;color:#dc2626">CONSTRUCCIONES MINZOE SAS</span>',
        html
    )
    try:
        get_sb().table("reportes_ot").upsert({
            "ot_id":   ot_id,
            "tipo":    tipo,
            "fecha":   fecha,
            "cliente": cliente,
            "html":    html_sin_logo,
        }).execute()
        return True
    except Exception:
        return False

def cargar_reporte_sb(ot_id):
    """Carga el reporte guardado y restaura el logo actual."""
    try:
        resp = get_sb().table("reportes_ot").select("*").eq("ot_id", ot_id).execute()
        if resp.data:
            html = resp.data[0]["html"]
            logo_b64 = get_logo_base64()
            if logo_b64:
                logo_tag = f'<img src="{logo_b64}" style="height:60px;object-fit:contain">'
                html = html.replace(
                    '<span style="font-size:1.1rem;font-weight:900;color:#dc2626">CONSTRUCCIONES MINZOE SAS</span>',
                    logo_tag
                )
            return html, resp.data[0]
        return None, None
    except Exception:
        return None, None

def registrar_cambio(entidad, entidad_id, campo, val_ant, val_nuevo):
    """Registra un cambio en el historial de auditoría."""
    _sb_insert("historial", {
        "ID_Log":         f"LOG-{ahora_colombia().strftime('%y%m%d%H%M%S')}",
        "Fecha":          ahora_colombia().strftime("%Y-%m-%d %H:%M"),
        "Usuario":        st.session_state.get("user_nombre", ""),
        "Entidad":        entidad,
        "Entidad_ID":     entidad_id,
        "Campo":          campo,
        "Valor_Anterior": str(val_ant),
        "Valor_Nuevo":    str(val_nuevo),
    })

def agregar_comentario(entidad, entidad_id, texto):
    """Agrega un comentario interno a una SOL u OT."""
    return _sb_insert("comentarios", {
        "ID_Com":     f"COM-{ahora_colombia().strftime('%y%m%d%H%M%S')}",
        "Fecha":      ahora_colombia().strftime("%Y-%m-%d %H:%M"),
        "Usuario":    st.session_state.get("user_nombre", ""),
        "Entidad":    entidad,
        "Entidad_ID": entidad_id,
        "Comentario": texto.strip(),
    })

def siguiente_id(tipo, prefijo, df_existente=None):
    """Genera el siguiente ID único e irrepetible para SOL u OT."""
    try:
        contadores = load_counters()
        mask = (contadores["tipo"] == tipo) & (contadores["prefijo"] == prefijo) if not contadores.empty else None

        if contadores.empty or mask is None or not mask.any():
            num = 1
            # Verificar registros existentes para no repetir
            if df_existente is not None and not df_existente.empty:
                ids_pre = df_existente[df_existente["ID"].str.startswith(prefijo, na=False)]["ID"]
                if not ids_pre.empty:
                    nums_ex = ids_pre.str.extract(r"-(\d{3})$")[0].dropna().astype(int)
                    if not nums_ex.empty:
                        num = int(nums_ex.max()) + 1
            nuevo = pd.DataFrame([{"tipo": tipo, "prefijo": prefijo, "ultimo_num": str(num)}])
            contadores = pd.concat([contadores, nuevo], ignore_index=True)
        else:
            num = int(contadores.loc[mask, "ultimo_num"].values[0]) + 1
            contadores.loc[mask, "ultimo_num"] = str(num)

        save_counters(contadores)
        return f"{prefijo}{num:03d}"
    except Exception:
        # Fallback: usar timestamp para garantizar unicidad
        return f"{prefijo}{ahora_colombia().strftime('%H%M%S')}"


COLS_CONTRATO = [
    "ID_Contrato", "Fecha_Inicio", "Fecha_Fin", "Cliente", "NIT", "Sede",
    "Nombre_Contacto", "Celular_Contacto", "Servicio", "Frecuencia",
    "Tecnico", "Valor_Contrato", "Estado_Contrato",
]
COLS_EQUIPO = [
    "ID_Item", "ID_Contrato", "Cliente", "Sede", "Servicio",
    "Marca", "Modelo", "Numero_Serie", "Especificaciones", "Ubicacion",
    "Ultimo_Mantenimiento", "Proximo_Mantenimiento",
]

# Servicios que requieren registro de equipos individuales
SERVICIOS_CON_EQUIPOS = ["Aires Acondicionados", "UPS y Plantas Eléctricas", "Cámaras de Seguridad"]

# Horas en formato 12h cada 30 minutos
HORAS_12 = []
for _h in range(24):
    for _m in [0, 30]:
        _period = "AM" if _h < 12 else "PM"
        _h12    = _h % 12 or 12
        HORAS_12.append(f"{_h12:02d}:{_m:02d} {_period}")

ZONAS = [
    "Z0 — 0 a 10 km (Ciudad principal)",
    "Z1 — 11 a 30 km (Aledaña real)",
    "Z2 — 31 a 70 km (Regional)",
    "Z3 — 71 a 120 km (Regional extendida)",
    "Z4 — 121 a 200 km (Foránea corta)",
    "Z5 — +200 km (Foránea larga)",
]

ZONA_LABEL = {
    "Z0": "Z0 — Ciudad principal (0-10 km)",
    "Z1": "Z1 — Aledaña real (11-30 km)",
    "Z2": "Z2 — Regional (31-70 km)",
    "Z3": "Z3 — Regional extendida (71-120 km)",
    "Z4": "Z4 — Foránea corta (121-200 km)",
    "Z5": "Z5 — Foránea larga (+200 km)",
}

# Ciudades Colombia → Zona (distancia desde la capital del departamento)
CIUDADES_ZONAS = {
    # ── BOGOTÁ D.C. ───────────────────────────────────────────
    "Bogotá D.C.": "Z0",
    # Cundinamarca (ref: Bogotá)
    "Soacha": "Z0", "Bosa": "Z0",
    "Mosquera": "Z1", "Madrid (Cundinamarca)": "Z1", "Funza": "Z1",
    "Chía": "Z1", "Cajicá": "Z1", "Zipaquirá": "Z1", "Facatativá": "Z1",
    "La Calera": "Z1", "Sibaté": "Z1", "Tocancipá": "Z1", "Sopó": "Z1",
    "Cota": "Z1", "Tenjo": "Z1", "Tabio": "Z2", "Subachoque": "Z2",
    "El Rosal": "Z2", "Bojacá": "Z2", "Fusagasugá": "Z2",
    "Girardot": "Z2", "Villeta": "Z2", "Guatavita": "Z2",
    "Suesca": "Z2", "Chocontá": "Z2", "Ubaté": "Z2", "Cáqueza": "Z2",
    "Cómbita": "Z1", "Samacá": "Z1", "Guateque": "Z2",
    "Medina (Cundinamarca)": "Z3",
    # ── ANTIOQUIA (ref: Medellín) ────────────────────────────
    "Medellín": "Z0", "Bello": "Z0", "Itagüí": "Z0", "Envigado": "Z0",
    "Sabaneta": "Z0", "La Estrella": "Z0", "Caldas (Antioquia)": "Z0",
    "Copacabana": "Z0", "Girardota": "Z1", "Barbosa (Antioquia)": "Z1",
    "Amagá": "Z1", "Angelópolis": "Z2", "Sopetrán": "Z2",
    "Santa Fe de Antioquia": "Z2", "Fredonia": "Z2",
    "Rionegro": "Z2", "La Ceja": "Z2", "El Retiro": "Z2",
    "Marinilla": "Z2", "Guarne": "Z2", "El Carmen de Viboral": "Z2",
    "Santa Rosa de Osos": "Z3", "Yarumal": "Z3", "Caucasia": "Z4",
    "Apartadó": "Z4", "Turbo": "Z5", "Carepa": "Z4", "Chigorodó": "Z4",
    "Andes": "Z3", "Jericó": "Z3", "Jardín": "Z3",
    "Ciudad Bolívar (Antioquia)": "Z3", "Puerto Berrío": "Z4",
    "Segovia": "Z4", "Remedios": "Z4",
    # ── VALLE DEL CAUCA (ref: Cali) ─────────────────────────
    "Cali": "Z0", "Yumbo": "Z0",
    "Palmira": "Z1", "Jamundí": "Z1", "Candelaria": "Z1",
    "Florida (Valle)": "Z1", "Pradera": "Z1",
    "Tuluá": "Z2", "Buga": "Z2", "Dagua": "Z2", "La Cumbre": "Z2",
    "Cartago": "Z3", "Zarzal": "Z3", "Roldanillo": "Z3",
    "La Unión (Valle)": "Z3", "Sevilla": "Z3", "Caicedonia": "Z3",
    "Buenaventura": "Z3",
    # ── ATLÁNTICO (ref: Barranquilla) ───────────────────────
    "Barranquilla": "Z0", "Soledad": "Z0", "Malambo": "Z0", "Galapa": "Z0",
    "Baranoa": "Z1", "Sabanagrande": "Z1", "Puerto Colombia": "Z1",
    "Usiacurí": "Z1", "Palmar de Varela": "Z1", "Sabanalarga": "Z2",
    # ── BOLÍVAR (ref: Cartagena) ─────────────────────────────
    "Cartagena": "Z0", "Turbaco": "Z1", "Arjona": "Z1",
    "María La Baja": "Z2", "El Carmen de Bolívar": "Z3", "Magangué": "Z4",
    # ── SANTANDER (ref: Bucaramanga) ────────────────────────
    "Bucaramanga": "Z0", "Floridablanca": "Z0", "Girón": "Z0",
    "Piedecuesta": "Z0", "Lebrija": "Z1",
    "Barbosa (Santander)": "Z2", "San Gil": "Z2", "Socorro": "Z2",
    "Los Santos": "Z2", "Barichara": "Z2",
    "Barrancabermeja": "Z3", "Puerto Wilches": "Z3",
    "Sabana de Torres": "Z3", "Málaga": "Z3", "Vélez": "Z3",
    # ── BOYACÁ (ref: Tunja) ──────────────────────────────────
    "Tunja": "Z0", "Motavita": "Z1", "Ramiriquí": "Z1",
    "Paipa": "Z1", "Cómbita (Boyacá)": "Z1",
    "Duitama": "Z2", "Sogamoso": "Z2", "Nobsa": "Z2",
    "Tibasosa": "Z2", "Villa de Leyva": "Z2", "Moniquirá": "Z2",
    "Chiquinquirá": "Z2", "Guateque (Boyacá)": "Z2",
    "Soatá": "Z3",
    # ── CALDAS (ref: Manizales) ─────────────────────────────
    "Manizales": "Z0", "Villamaría": "Z0",
    "Chinchiná": "Z1", "Palestina": "Z1", "Neira": "Z1",
    "Anserma": "Z2", "Salamina": "Z2", "Riosucio": "Z2", "Supía": "Z2",
    "La Dorada": "Z3", "Manzanares": "Z3", "Aguadas": "Z3",
    # ── RISARALDA (ref: Pereira) ─────────────────────────────
    "Pereira": "Z0", "Dosquebradas": "Z0",
    "Santa Rosa de Cabal": "Z1", "La Virginia": "Z1", "Marsella": "Z1",
    "Quinchía": "Z2", "Santuario": "Z2", "Apía": "Z2",
    "Belén de Umbría": "Z2",
    # ── QUINDÍO (ref: Armenia) ──────────────────────────────
    "Armenia": "Z0", "Montenegro": "Z1", "Calarcá": "Z1",
    "La Tebaida": "Z1", "Circasia": "Z1", "Filandia": "Z1",
    "Quimbaya": "Z1", "Salento": "Z2", "Génova": "Z2",
    # ── TOLIMA (ref: Ibagué) ─────────────────────────────────
    "Ibagué": "Z0",
    "Espinal": "Z2", "Flandes": "Z2", "Melgar": "Z2", "Guamo": "Z2",
    "Honda": "Z3", "Chaparral": "Z3", "Líbano": "Z3",
    "Mariquita": "Z3", "Fresno": "Z3", "Purificación": "Z3",
    "Armero-Guayabal": "Z3",
    # ── HUILA (ref: Neiva) ───────────────────────────────────
    "Neiva": "Z0", "Campoalegre": "Z1", "Rivera": "Z1", "Palermo": "Z1",
    "Garzón": "Z2", "La Plata": "Z2", "Gigante": "Z2",
    "Pitalito": "Z3", "Timaná": "Z3", "San Agustín": "Z4",
    # ── NARIÑO (ref: Pasto) ──────────────────────────────────
    "Pasto": "Z0", "Sandoná": "Z1", "Tangua": "Z1", "La Florida": "Z1",
    "Ipiales": "Z2", "Túquerres": "Z2", "Samaniego": "Z2",
    "La Unión (Nariño)": "Z3", "Tumaco": "Z4",
    # ── CAUCA (ref: Popayán) ─────────────────────────────────
    "Popayán": "Z0", "Timbío": "Z1", "Piendamó": "Z1",
    "Santander de Quilichao": "Z2", "Miranda": "Z2", "El Tambo": "Z2",
    "Silvia": "Z2", "Puerto Tejada": "Z2",
    "Bolívar (Cauca)": "Z3",
    # ── NORTE DE SANTANDER (ref: Cúcuta) ────────────────────
    "Cúcuta": "Z0", "Villa del Rosario": "Z0", "Los Patios": "Z0",
    "El Zulia": "Z1", "Sardinata": "Z2", "Pamplona": "Z2",
    "Tibú": "Z3", "Ocaña": "Z3",
    # ── CESAR (ref: Valledupar) ──────────────────────────────
    "Valledupar": "Z0", "La Paz (Cesar)": "Z1",
    "Agustín Codazzi": "Z2", "Bosconia": "Z2",
    "Aguachica": "Z3", "Curumaní": "Z3",
    # ── MAGDALENA (ref: Santa Marta) ────────────────────────
    "Santa Marta": "Z0", "Ciénaga": "Z1",
    "Aracataca": "Z2", "Fundación": "Z2", "Zona Bananera": "Z2",
    "Plato": "Z3", "El Banco": "Z4",
    # ── CÓRDOBA (ref: Montería) ──────────────────────────────
    "Montería": "Z0", "Cereté": "Z1", "San Pelayo": "Z1",
    "Sahagún": "Z2", "Lorica": "Z2", "Ciénaga de Oro": "Z2",
    "Montelíbano": "Z3", "Tierralta": "Z3",
    # ── SUCRE (ref: Sincelejo) ───────────────────────────────
    "Sincelejo": "Z0", "Corozal": "Z1", "Sampués": "Z1", "Morroa": "Z1",
    "Tolú": "Z2", "San Marcos": "Z2",
    # ── LA GUAJIRA (ref: Riohacha) ──────────────────────────
    "Riohacha": "Z0", "Manaure": "Z1",
    "Maicao": "Z2", "Uribia": "Z2", "San Juan del Cesar": "Z2",
    "Fonseca": "Z2", "Barrancas": "Z2", "Albania (La Guajira)": "Z2",
    # ── META (ref: Villavicencio) ────────────────────────────
    "Villavicencio": "Z0", "Acacías": "Z1", "Cumaral": "Z1",
    "Restrepo (Meta)": "Z1", "Puerto López": "Z2",
    "Castilla la Nueva": "Z2", "San Martín (Meta)": "Z3",
    "Granada (Meta)": "Z3",
    # ── CASANARE (ref: Yopal) ────────────────────────────────
    "Yopal": "Z0", "Aguazul": "Z1", "Tauramena": "Z2",
    "Villanueva (Casanare)": "Z2", "Paz de Ariporo": "Z2",
    # ── ARAUCA (ref: Arauca) ─────────────────────────────────
    "Arauca": "Z0", "Saravena": "Z2", "Tame": "Z2", "Arauquita": "Z2",
    # ── PUTUMAYO (ref: Mocoa) ────────────────────────────────
    "Mocoa": "Z0", "Puerto Asís": "Z2", "Orito": "Z2",
    "Valle del Guamuez": "Z2", "Sibundoy": "Z2",
    # ── CAQUETÁ (ref: Florencia) ─────────────────────────────
    "Florencia": "Z0", "Belén de los Andaquíes": "Z1",
    "La Montañita": "Z2", "San Vicente del Caguán": "Z3",
    # ── CHOCÓ (ref: Quibdó) ──────────────────────────────────
    "Quibdó": "Z0", "Istmina": "Z2", "Tadó": "Z2",
    # ── OTROS DEPARTAMENTOS (capitales) ─────────────────────
    "Leticia (Amazonas)": "Z0", "Puerto Carreño (Vichada)": "Z0",
    "Inírida (Guainía)": "Z0", "San José del Guaviare": "Z0",
    "Mitú (Vaupés)": "Z0", "San Andrés": "Z0",
}

SLA_HORAS = {
    "Programado": {"Z0": 48,  "Z1": 72,  "Z2": 96,  "Z3": 120, "Z4": 144, "Z5": None},
    "Urgencia":   {"Z0": 24,  "Z1": 36,  "Z2": 48,  "Z3": 72,  "Z4": 96,  "Z5": None},
    "Emergencia": {"Z0": 4,   "Z1": 6,   "Z2": 10,  "Z3": 16,  "Z4": 24,  "Z5": None},
}

TEXTO_Z5 = {
    "Programado": "Programado bajo agenda",
    "Urgencia":   "Bajo disponibilidad",
    "Emergencia": "No aplica emergencia",
}

COLS_OT = [
    "ID", "Origen", "Creado_Por", "SOL_Ref", "Fecha_Creacion", "Fecha_Limite", "Cliente", "NIT", "Sede",
    "Nombre_Contacto", "Celular_Contacto",
    "Servicio", "Descripcion", "SLA", "Zona", "Tecnico", "Celular_Tecnico",
    "Fecha_Ejecucion", "Hora_Inicio", "Hora_Final", "Horas_Laboradas",
    "Materiales", "Valor_COP", "Estado", "Observaciones",
]


# ── Google Sheets ─────────────────────────────────────────────────────────────

@st.cache_resource
def get_gc():
    return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))

# ── Supabase ──────────────────────────────────────────────────────────────────
@st.cache_resource
def get_sb():
    from supabase import create_client
    return create_client(st.secrets["supabase_url"], st.secrets["supabase_key"])

def sb_load(table_name, cols):
    """Carga datos desde Supabase paginando de 1000 en 1000 (sin límite)."""
    try:
        sb       = get_sb()
        all_data = []
        PAGE     = 1000
        offset   = 0
        while True:
            resp = sb.table(table_name).select("*").range(offset, offset + PAGE - 1).execute()
            if resp.data:
                all_data.extend(resp.data)
                if len(resp.data) < PAGE:
                    break
                offset += PAGE
            else:
                break
        if all_data:
            df = pd.DataFrame(all_data).fillna("").astype(str)
            for c in list(cols):
                if c not in df.columns:
                    df[c] = ""
            return df[list(cols)]
        return pd.DataFrame(columns=list(cols))
    except Exception:
        return pd.DataFrame(columns=list(cols))

def sb_save(table_name, df):
    """Guarda dataframe en Supabase (truncate + insert por lotes de 200)."""
    try:
        sb = get_sb()
        sb.rpc("truncate_table", {"table_name": table_name}).execute()
        if not df.empty:
            records = df.fillna("").astype(str).to_dict("records")
            for i in range(0, len(records), 200):
                sb.table(table_name).insert(records[i:i+200]).execute()
        return True
    except Exception as e:
        st.error(f"❌ Error Supabase '{table_name}': {e}")
        return False

def get_sheet(tab_name):
    gc = get_gc()
    sid = (st.secrets.get("spreadsheet_id") or
           st.secrets["gcp_service_account"].get("spreadsheet_id"))
    sh = gc.open_by_key(sid)
    try:
        return sh.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        return sh.add_worksheet(title=tab_name, rows=1000, cols=30)

@st.cache_data(ttl=1800)
def gs_load(tab_name, cols_tuple, _v=0):
    """Carga datos de Google Sheets con caché de 10 min por tabla."""
    cols = list(cols_tuple)
    try:
        ws   = get_sheet(tab_name)
        data = ws.get_all_records()
        if data:
            df = pd.DataFrame(data).astype(str).fillna("")
            for c in cols:
                if c not in df.columns:
                    df[c] = ""
            return df[cols]
        return pd.DataFrame(columns=cols)
    except Exception:
        return pd.DataFrame(columns=cols)

def _ver_cache(tab_name):
    """Retorna la versión actual del caché de una tabla."""
    return st.session_state.get(f"_cv_{tab_name}", 0)

def _invalidar_cache(tab_name):
    """Incrementa la versión del caché solo de la tabla afectada."""
    st.session_state[f"_cv_{tab_name}"] = _ver_cache(tab_name) + 1

def gs_save(tab_name, df):
    try:
        ws   = get_sheet(tab_name)
        data = [df.columns.tolist()] + df.fillna("").astype(str).values.tolist()
        ws.clear()
        ws.update("A1", data)
        _invalidar_cache(tab_name)  # Solo invalida esta tabla
        return True
    except Exception as e:
        st.error(f"❌ Error guardando '{tab_name}': {e}")
        return False


# ── Carga / guardado ──────────────────────────────────────────────────────────

def load_sol():
    return sb_load("solicitudes", COLS_SOL)

def save_sol(df):
    sb_save("solicitudes", df)
    _invalidar_cache("solicitudes")

def load_cli():
    df = sb_load("clientes", COLS_CLI)
    for col in df.columns:
        df[col] = df[col].str.strip()
    return df[df["Empresa"] != ""].reset_index(drop=True)

def save_cli(df):
    sb_save("clientes", df)
    _invalidar_cache("clientes")

def load_ots():
    return sb_load("ordenes_trabajo", COLS_OT)

def save_ots(df):
    sb_save("ordenes_trabajo", df)
    _invalidar_cache("ordenes_trabajo")


def load_cv():
    return sb_load("compras_ventas", COLS_CV)

def save_cv(df):
    sb_save("compras_ventas", df)

def gen_cv_id(df):
    hoy = ahora_colombia().strftime("%y%m%d")
    pre = f"CV-{hoy}-"
    ids = df[df["ID_Registro"].str.startswith(pre, na=False)]["ID_Registro"] if not df.empty else pd.Series(dtype=str)
    return f"{pre}001" if ids.empty else f"{pre}{ids.str.extract(r'CV-\d{6}-(\d{3})')[0].astype(int).max()+1:03d}"

def load_ventas():
    return sb_load("ventas", COLS_VENTA)

def save_ventas(df):
    sb_save("ventas", df)

def gen_fac_id(df):
    hoy = ahora_colombia().strftime("%y%m%d")
    pre = f"FAC-{hoy}-"
    ids = df[df["ID_Factura"].str.startswith(pre, na=False)]["ID_Factura"] if not df.empty else pd.Series(dtype=str)
    return f"{pre}001" if ids.empty else f"{pre}{ids.str.extract(r'FAC-\d{6}-(\d{3})')[0].astype(int).max()+1:03d}"

def load_costos():
    return sb_load("costos", COLS_COSTO)

def save_costos(df):
    sb_save("costos", df)

def gen_costo_id(df):
    hoy = ahora_colombia().strftime("%y%m%d")
    pre = f"COS-{hoy}-"
    ids = df[df["ID_Costo"].str.startswith(pre, na=False)]["ID_Costo"] if not df.empty else pd.Series(dtype=str)
    return f"{pre}001" if ids.empty else f"{pre}{ids.str.extract(r'COS-\d{6}-(\d{3})')[0].astype(int).max()+1:03d}"


def to_num(val):
    try:
        return float(str(val).replace(",", "").replace(".", "").replace(" ", "") or 0)
    except Exception:
        return 0.0


def load_contratos():
    return sb_load("contratos", COLS_CONTRATO)

def save_contratos(df):
    ok = sb_save("contratos", df)
    _invalidar_cache("contratos")
    return ok

def load_equipos():
    return sb_load("equipos", COLS_EQUIPO)

def save_equipos(df):
    sb_save("equipos", df)


def gen_contrato_id(df):
    hoy = ahora_colombia().strftime("%y%m%d")
    pre = f"CON-{hoy}-"
    return siguiente_id("CON", pre, df)


def gen_item_id(df):
    # Renombrar columna para que siguiente_id la encuentre como "ID"
    df_tmp = df.rename(columns={"ID_Item": "ID"}) if not df.empty and "ID_Item" in df.columns else df
    return siguiente_id("ITEM", "ITEM-", df_tmp)


def proxima_fecha(desde_str, frecuencia):
    """Calcula la próxima fecha de mantenimiento."""
    try:
        desde = datetime.strptime(desde_str, "%Y-%m-%d")
        meses = FREQ_MESES.get(frecuencia, 1)
        mes   = desde.month - 1 + meses
        anio  = desde.year + mes // 12
        mes   = mes % 12 + 1
        return datetime(anio, mes, min(desde.day, 28)).strftime("%Y-%m-%d")
    except Exception:
        return ""


def generate_ot_id(df):
    hoy     = ahora_colombia().strftime("%y%m%d")
    prefijo = f"OT-{hoy}-"
    return siguiente_id("OT", prefijo, df)


def carpeta_cliente(cliente_nombre):
    """Devuelve el nombre de carpeta del cliente o crea uno genérico."""
    nombre_up = cliente_nombre.upper()
    for key, carpeta in CLIENTES_CARPETA.items():
        if key in nombre_up:
            return carpeta
    # Cliente no mapeado → crear carpeta con nombre normalizado
    limpio = "".join(c for c in cliente_nombre.title() if c.isalnum() or c == " ").strip()
    return "00_" + "_".join(limpio.split()[:3])

def carpeta_sede(sede_nombre):
    """Convierte nombre de sede a formato de carpeta: 00_Cedi_Cartagena"""
    limpio = "".join(c for c in sede_nombre if c.isalnum() or c in " _-").strip()
    return "00_" + "_".join(w.capitalize() for w in limpio.split())

def _guardar_en_enviados(imap, msg_bytes):
    """Guarda copia en carpeta Enviados de Hostinger."""
    import time as _time, imaplib as _imap
    ts = _imap.Time2Internaldate(_time.time())
    try:
        imap.append("Enviados", "\\Seen", ts, msg_bytes)
    except Exception:
        try:
            imap.append("Sent", "\\Seen", ts, msg_bytes)
        except Exception:
            pass


def enviar_confirmacion_sol(sol_id, cliente, servicio, tipo_servicio, sla, contacto_nombre, correo_destino, fecha, dominio="construminzoe.com"):
    """Envía correo de confirmación al cliente con el código de la solicitud."""
    import smtplib, ssl
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    try:
        # Usar el correo del usuario logueado
        usuario_correo = st.session_state.get("user_correo", "")
        email_user     = usuario_correo
        # Buscar contraseña según el usuario activo
        passwords      = st.secrets.get("email_passwords", {})
        email_pwd      = passwords.get(usuario_correo, "")
        if not email_user or not email_pwd:
            return False, f"Credenciales de correo no configuradas para {email_user}."

        asunto = f"✅ Solicitud {sol_id} recibida — Construcciones Minzoe SAS"

        hora   = ahora_colombia().hour
        saludo = "Buenos días" if hora < 12 else ("Buenas tardes" if hora < 18 else "Buenas noches")

        cuerpo = f"""
<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;margin:0">
<div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;
     overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.1)">

  <!-- Header -->
  <div style="background:#dc2626;padding:24px 32px">
    <h1 style="color:white;margin:0;font-size:20px">🏗️ CONSTRUCCIONES MINZOE SAS</h1>
    <p style="color:#fca5a5;margin:4px 0 0 0;font-size:13px">
      Soluciones integrales en construcción, mantenimiento y climatización
    </p>
  </div>

  <!-- Body -->
  <div style="padding:32px">
    <p style="color:#111;font-size:15px">{saludo}.</p>

    <p style="color:#333;font-size:14px;line-height:1.6">
      Hemos recibido su solicitud satisfactoriamente.
    </p>

    <p style="color:#333;font-size:14px;line-height:1.6">
      La novedad ha sido registrada y asignada bajo el código:
    </p>

    <div style="background:#fff5f5;border-left:4px solid #dc2626;
         border-radius:8px;padding:16px 24px;margin:20px 0;text-align:center">
      <p style="margin:0 0 4px 0;font-size:12px;color:#999;text-transform:uppercase;letter-spacing:1px">
        Código de solicitud
      </p>
      <p style="margin:0;font-size:32px;font-weight:900;color:#dc2626;letter-spacing:3px">
        {sol_id}
      </p>
    </div>

    <p style="color:#333;font-size:14px;line-height:1.8">
      para su respectivo seguimiento y gestión.
    </p>

    <p style="color:#333;font-size:14px;line-height:1.8">
      Cualquier actualización será informada oportunamente a través de los canales establecidos.
    </p>

    <p style="color:#111;font-size:14px;margin-top:24px">
      Cordialmente,
    </p>

    <div style="border-top:2px solid #dc2626;padding-top:16px;margin-top:8px">
      <p style="margin:0;font-weight:bold;color:#111;font-size:14px">CONSTRUCCIONES MINZOE SAS</p>
      <p style="margin:4px 0 0 0;font-size:12px;color:#555">
        📍 Cra 5 # 8a-18 &nbsp;|&nbsp; 📞 3175102668 – 3173748665
      </p>
      <p style="margin:4px 0 0 0;font-size:12px;color:#555">
        ✉️ jeyson.jimenez@construminzoe.com
      </p>
    </div>
  </div>

  <!-- Footer -->
  <div style="background:#1a1a1a;padding:14px 32px;text-align:center">
    <p style="color:#777;font-size:11px;margin:0">
      Este es un mensaje automático, por favor no responda a este correo.
    </p>
  </div>
</div>
</body></html>
"""
        # ID fijo basado en la SOL — no necesita guardarse en base de datos
        message_id = f"<{sol_id}@{dominio}>"

        msg = MIMEMultipart("alternative")
        msg["Subject"]    = asunto
        msg["From"]       = f"Construcciones Minzoe SAS <{email_user}>"
        msg["To"]         = correo_destino
        msg["Bcc"]        = email_user  # Copia a tu bandeja de entrada
        msg["Message-ID"] = message_id
        msg.attach(MIMEText(cuerpo, "html", "utf-8"))

        context   = ssl.create_default_context()
        msg_bytes = msg.as_bytes()

        with smtplib.SMTP_SSL("smtp.hostinger.com", 465, context=context) as server:
            server.login(email_user, email_pwd)
            server.sendmail(email_user, [correo_destino, email_user], msg_bytes)

        return True, f"Confirmación enviada a {correo_destino}", message_id
    except Exception as e:
        return False, str(e)


def enviar_actualizacion_ot(sol_id, ot_id, cliente, contacto_nombre, correo_destino, fecha, reply_to_id=None, dominio="construminzoe.com"):
    """Envía correo de actualización al cliente cuando la SOL es aprobada y se crea la OT."""
    import smtplib, ssl, imaplib, time
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    try:
        usuario_correo = st.session_state.get("user_correo", "")
        email_user     = usuario_correo
        passwords      = st.secrets.get("email_passwords", {})
        email_pwd      = passwords.get(usuario_correo, "")
        if not email_user or not email_pwd:
            return False, f"Credenciales no configuradas para {email_user}."

        hora   = ahora_colombia().hour
        saludo = "Buenos días" if hora < 12 else ("Buenas tardes" if hora < 18 else "Buenas noches")
        asunto = f"📋 Actualización Solicitud {sol_id} — Construcciones Minzoe SAS"

        cuerpo = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;padding:20px;margin:0">
<div style="max-width:600px;margin:0 auto;background:white;border-radius:12px;
     overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.1)">

  <div style="background:#dc2626;padding:24px 32px">
    <h1 style="color:white;margin:0;font-size:20px">🏗️ CONSTRUCCIONES MINZOE SAS</h1>
    <p style="color:#fca5a5;margin:4px 0 0 0;font-size:13px">
      Soluciones integrales en construcción, mantenimiento y climatización
    </p>
  </div>

  <div style="padding:32px">
    <p style="color:#111;font-size:15px">{saludo}.</p>

    <p style="color:#333;font-size:14px;line-height:1.6">
      Le informamos que la solicitud registrada ha sido asignada bajo la OTS No.
    </p>

    <div style="background:#fff5f5;border-left:4px solid #dc2626;
         border-radius:8px;padding:16px 24px;margin:20px 0;text-align:center">
      <p style="margin:0 0 4px 0;font-size:12px;color:#999;text-transform:uppercase;letter-spacing:1px">
        Número de OTS
      </p>
      <p style="margin:0;font-size:28px;font-weight:900;color:#dc2626;letter-spacing:2px">
        {ot_id}
      </p>
    </div>

    <table style="width:100%;border-collapse:collapse;font-size:13px;margin:16px 0">
      <tr style="border-bottom:1px solid #f0f0f0">
        <td style="padding:8px 0;color:#777;width:40%">Solicitud</td>
        <td style="padding:8px 0;color:#111;font-weight:bold">{sol_id}</td>
      </tr>
      <tr style="border-bottom:1px solid #f0f0f0">
        <td style="padding:8px 0;color:#777">Estado</td>
        <td style="padding:8px 0;color:#16a34a;font-weight:bold">✅ Asignada para gestión</td>
      </tr>
      <tr>
        <td style="padding:8px 0;color:#777">Fecha de asignación</td>
        <td style="padding:8px 0;color:#111">{fecha}</td>
      </tr>
    </table>

    <p style="color:#333;font-size:14px;line-height:1.8">
      Nuestro equipo se encuentra realizando las validaciones y coordinaciones
      correspondientes para la atención del requerimiento.
    </p>

    <p style="color:#333;font-size:14px;line-height:1.8">
      Agradecemos su atención y quedamos atentos a cualquier inquietud adicional.
    </p>

    <div style="border-top:2px solid #dc2626;padding-top:16px;margin-top:24px">
      <p style="margin:0;font-weight:bold;color:#111;font-size:14px">CONSTRUCCIONES MINZOE SAS</p>
      <p style="margin:4px 0 0 0;font-size:12px;color:#555">
        📍 Cra 5 # 8a-18 &nbsp;|&nbsp; 📞 3175102668 – 3173748665
      </p>
      <p style="margin:4px 0 0 0;font-size:12px;color:#555">
        ✉️ {email_user}
      </p>
    </div>
  </div>

  <div style="background:#1a1a1a;padding:14px 32px;text-align:center">
    <p style="color:#777;font-size:11px;margin:0">
      Este es un mensaje automático, por favor no responda a este correo.
    </p>
  </div>
</div>
</body></html>"""

        import uuid
        msg = MIMEMultipart("alternative")
        # Re: para que sea hilo de respuesta
        msg["Subject"]    = f"Re: ✅ Solicitud {sol_id} recibida — Construcciones Minzoe SAS"
        msg["From"]       = f"Construcciones Minzoe SAS <{email_user}>"
        msg["To"]         = correo_destino
        msg["Message-ID"] = f"<{ot_id}.{uuid.uuid4().hex[:8]}@{dominio}>"
        # Encadenar con el correo original de la solicitud
        if reply_to_id:
            msg["In-Reply-To"] = reply_to_id
            msg["References"]  = reply_to_id
        msg["Bcc"] = email_user  # Copia a tu bandeja de entrada
        msg.attach(MIMEText(cuerpo, "html", "utf-8"))
        msg_bytes = msg.as_bytes()

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.hostinger.com", 465, context=context) as server:
            server.login(email_user, email_pwd)
            server.sendmail(email_user, [correo_destino, email_user], msg_bytes)

        return True, f"Actualización enviada a {correo_destino}"
    except Exception as e:
        return False, str(e)


@st.cache_data
def get_logo_base64():
    """Carga el logo de Minzoe en base64 para embeber en HTML."""
    import base64
    for ruta in ["logo.png", "LOGO MINZOE.png",
                 r"D:\Escritorio\LA ASISTENTE MINZOE\logo.png",
                 r"D:\Escritorio\LA ASISTENTE MINZOE\LOGO MINZOE.png"]:
        try:
            with open(ruta, "rb") as f:
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        except Exception:
            continue
    return ""


def css_formato_carta():
    """CSS estándar para formatos en tamaño carta con márgenes ICONTEC."""
    return """
  @page { size: letter; margin: 3cm 2cm 3cm 4cm; }
  * { box-sizing: border-box; }

  /* Pantalla: simula hoja blanca sobre fondo gris */
  @media screen {
    body { background: #c0c0c0; padding: 20px; margin: 0; }
    .pagina {
      background: white;
      width: 216mm;
      min-height: 279mm;
      margin: 0 auto;
      padding: 3cm 2cm 3cm 4cm;
      box-shadow: 0 4px 16px rgba(0,0,0,0.35);
    }
  }
  /* Impresión: márgenes ICONTEC, sin fondo gris */
  @media print {
    body { background: white; margin: 0; padding: 0; }
    .pagina { padding: 0; box-shadow: none; width: auto; }
    .no-print { display: none !important; }
  }

  body { font-family: Arial, sans-serif; font-size: 7.5pt; color: #000; line-height: 1.2; }
  .header { display:flex; justify-content:space-between; align-items:flex-start;
            border-bottom: 2pt solid #dc2626; padding-bottom: 4pt; margin-bottom: 6pt; }
  .logo { font-size: 11pt; font-weight: 900; color: #dc2626; }
  table { width:100%; border-collapse:collapse; margin-bottom:4pt; font-size:7pt; }
  td, th { border: 0.5pt solid #999; padding: 2pt 3pt; vertical-align: middle; }
  th { background:#dc2626; color:white; font-weight:bold; text-align:left; font-size:7pt; }
  .section { background:#dc2626; color:white; font-weight:bold;
             padding:2pt 4pt; font-size:7pt; margin:3pt 0 2pt 0; }
  .ck { width:12pt; text-align:center; font-weight:bold; }
  .firma-box { border-top:0.5pt solid #000; margin-top:12pt;
               font-size:7pt; text-align:center; padding-top:2pt; }
"""


def ocr_documento(file_bytes, mime_type):
    """Extrae texto de imagen o PDF usando Google Cloud Vision. Retorna (texto, confianza, error)."""
    try:
        from google.cloud import vision as gcv
        from google.oauth2.service_account import Credentials as SACredentials

        creds = SACredentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        client = gcv.ImageAnnotatorClient(credentials=creds)

        if mime_type == "application/pdf":
            try:
                import fitz
                doc      = fitz.open(stream=file_bytes, filetype="pdf")
                pag      = doc[0]
                mat      = fitz.Matrix(3.0, 3.0)  # 3x zoom para mejor lectura manuscrita
                pix      = pag.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
                img_bytes = pix.tobytes("png")
            except Exception as e_pdf:
                return "", 0.0, f"Error convirtiendo PDF: {e_pdf}"
        else:
            img_bytes = file_bytes

        imagen  = gcv.Image(content=img_bytes)
        context = gcv.ImageContext(language_hints=["es", "es-419"])
        # Usar document_text_detection — mejor para formularios con letra manuscrita
        resp = client.document_text_detection(image=imagen, image_context=context)

        if resp.error.message:
            return "", 0.0, f"Vision API error: {resp.error.message}"

        if not resp.full_text_annotation or not resp.full_text_annotation.text:
            return "", 0.0, "La API no detectó texto en el documento."

        texto     = resp.full_text_annotation.text
        confianza = min(len(texto) / 300, 1.0)
        return texto, confianza, ""
    except Exception as e:
        return "", 0.0, str(e)


def _buscar(texto, patrones):
    """Busca el primer patrón que haga match en el texto."""
    import re
    for pat in patrones:
        m = re.search(pat, texto, re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip().replace("\n", " ")
            return val[:80]  # max 80 chars
    return ""

def parsear_hvac(texto):
    """Extrae campos del formulario HVAC del texto OCR."""
    c = {}
    c["cliente"]    = _buscar(texto, [r"CLIENTE[:\s]+([^\n|]+)", r"^CLIENTE\s+(.+)$"])
    c["ciudad"]     = _buscar(texto, [r"CIUDAD[:\s]+([^\n|]+)"])
    c["sucursal"]   = _buscar(texto, [r"SUCURSAL[:\s]+([^\n|]+)", r"SEDE[:\s]+([^\n|]+)"])
    c["contacto"]   = _buscar(texto, [r"CONTACTO[:\s]+([^\n|]+)"])
    c["marca"]      = _buscar(texto, [r"MARCA[:\s]+([^\n|]+)"])
    c["modelo"]     = _buscar(texto, [r"MODELO[:\s]+([^\n|]+)"])
    c["ser_cond"]   = _buscar(texto, [r"SERIAL CONDENSADORA[:\s]+([^\n|]+)", r"SERIAL COND[:\s]+([^\n|]+)"])
    c["ser_evap"]   = _buscar(texto, [r"SERIAL EVAPORADORA[:\s]+([^\n|]+)", r"SERIAL EVAP[:\s]+([^\n|]+)"])
    c["btu"]        = _buscar(texto, [r"BTU[:\s]+([\d,.\s]+)", r"CAPACIDAD[:\s]+([^\n|]+)"])
    c["refrig"]     = _buscar(texto, [r"REFRIGERANTE[:\s]+([^\n|]+)", r"R-\d+[A-Z]?"])
    c["ubic_evap"]  = _buscar(texto, [r"UBICACI.N EVAPORADORA[:\s]+([^\n|]+)"])
    c["ubic_cond"]  = _buscar(texto, [r"UBICACI.N CONDENSADORA[:\s]+([^\n|]+)"])
    c["v_cond"]     = _buscar(texto, [r"VOLTAJE[\s\S]{0,30}?(\d{2,3})\s*V"])
    c["psi_a"]      = _buscar(texto, [r"PSI ALTA[:\s]+([\d.]+)", r"ALTA[:\s]+([\d.]+)\s*PSI"])
    c["psi_b"]      = _buscar(texto, [r"PSI BAJA[:\s]+([\d.]+)", r"BAJA[:\s]+([\d.]+)\s*PSI"])
    c["obs"]        = _buscar(texto, [r"OBSERVACIONES[:\s]+([^\n]{5,200})"])
    c["tecnico"]    = _buscar(texto, [r"NOMBRE TECNICO[:\s]+([^\n|]+)", r"T[EÉ]CNICO[:\s]+([^\n|]+)"])

    # Confianza: % de campos clave encontrados
    clave = ["cliente","marca","modelo","btu","refrig"]
    encontrados = sum(1 for k in clave if c.get(k,"").strip())
    confianza = encontrados / len(clave)
    return c, confianza


def parsear_locativos(texto):
    """Extrae campos del formulario Locativos del texto OCR."""
    c = {}
    c["cliente"]   = _buscar(texto, [r"CLIENTE[:\s]+([^\n|]+)"])
    c["ciudad"]    = _buscar(texto, [r"CIUDAD[:\s]+([^\n|]+)"])
    c["sucursal"]  = _buscar(texto, [r"SUCURSAL[:\s]+([^\n|]+)"])
    c["contacto"]  = _buscar(texto, [r"CONTACTO[:\s]+([^\n|]+)"])
    c["area"]      = _buscar(texto, [r"[AÁ]REA INTERVENIDA[:\s]+([^\n|]+)"])
    c["tecnico"]   = _buscar(texto, [r"NOMBRE TECNICO[:\s]+([^\n|]+)", r"T[EÉ]CNICO[:\s]+([^\n|]+)"])
    c["obs"]       = _buscar(texto, [r"OBSERVACIONES[:\s]+([^\n]{5,200})"])

    clave = ["cliente","sucursal","area"]
    encontrados = sum(1 for k in clave if c.get(k,"").strip())
    confianza = encontrados / len(clave)
    return c, confianza


def get_drive_service():
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

def drive_buscar_o_crear_carpeta(service, nombre, parent_id):
    q = (f"name='{nombre}' and '{parent_id}' in parents "
         f"and mimeType='application/vnd.google-apps.folder' and trashed=false")
    res = service.files().list(
        q=q, fields="files(id)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    meta = {"name": nombre, "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id]}
    folder = service.files().create(
        body=meta, fields="id", supportsAllDrives=True
    ).execute()
    return folder["id"]

def guardar_en_drive(html, cliente, sede, ot_id, fecha_ot):
    try:
        from googleapiclient.http import MediaInMemoryUpload
        service  = get_drive_service()
        root_id  = (st.secrets.get("drive_root_id") or
                    st.secrets["gcp_service_account"].get("drive_root_id",""))
        if not root_id:
            return False, "Falta 'drive_root_id' en los Secrets de Streamlit Cloud."

        # Obtener el driveId de la Unidad Compartida
        root_info = service.files().get(
            fileId=root_id, fields="id,driveId", supportsAllDrives=True
        ).execute()
        shared_drive_id = root_info.get("driveId", root_id)

        fecha  = fecha_ot or ahora_colombia().strftime("%Y-%m-%d")
        anio   = fecha[:4]
        mes    = fecha[5:7] if len(fecha) >= 7 else ahora_colombia().strftime("%m")

        cli_id  = drive_buscar_o_crear_carpeta(service, carpeta_cliente(cliente), root_id)
        anio_id = drive_buscar_o_crear_carpeta(service, f"01_{anio}", cli_id)
        mes_id  = drive_buscar_o_crear_carpeta(service, MESES_CARPETA.get(mes, f"{mes}_mes"), anio_id)
        sede_id = drive_buscar_o_crear_carpeta(service, carpeta_sede(sede), mes_id)

        nombre = f"{ot_id}_{carpeta_sede(sede)}_{fecha}.html"
        meta   = {"name": nombre, "parents": [sede_id]}
        if shared_drive_id:
            meta["driveId"] = shared_drive_id
        media  = MediaInMemoryUpload(html.encode("utf-8"), mimetype="text/html")
        service.files().create(
            body=meta, media_body=media, fields="id",
            supportsAllDrives=True
        ).execute()
        ruta = f"{carpeta_cliente(cliente)}/01_{anio}/{MESES_CARPETA.get(mes,'')}/{carpeta_sede(sede)}/{nombre}"
        return True, ruta
    except Exception as e:
        return False, str(e)


def guardar_reporte_local(html, cliente, sede, ot_id, fecha_ot):
    """Guarda el reporte en H:\\03_CLIENTES\\... Retorna (ok, ruta_o_error)."""
    try:
        if not os.path.exists(BASE_REPORTES):
            return False, f"No se encontró el disco H:\\ ({BASE_REPORTES})"
        fecha = fecha_ot or ahora_colombia().strftime("%Y-%m-%d")
        anio  = fecha[:4]
        mes   = fecha[5:7] if len(fecha) >= 7 else ahora_colombia().strftime("%m")
        ruta  = os.path.join(
            BASE_REPORTES,
            carpeta_cliente(cliente),
            f"01_{anio}",
            MESES_CARPETA.get(mes, f"{mes}_mes"),
            carpeta_sede(sede),
        )
        os.makedirs(ruta, exist_ok=True)
        nombre = f"{ot_id}_{carpeta_sede(sede)}_{fecha}.html"
        ruta_completa = os.path.join(ruta, nombre)
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write(html)
        return True, ruta_completa
    except Exception as e:
        return False, str(e)


def fmt_cop(val):
    """Formatea un valor numérico como pesos colombianos: $1.200.000"""
    try:
        n = float(str(val).replace(",", "").replace(".", "").strip())
        return f"${n:,.0f}".replace(",", ".")
    except Exception:
        return val if val else "—"


def tabla_html(df_vista, color_col=None, colores_estado=None, fmt_cols=None):
    """Renderiza un DataFrame como tabla HTML con encabezados rojos."""
    thead = "".join(
        f"<th style='background:#dc2626;color:#fff;padding:8px 10px;"
        f"font-weight:700;font-size:0.82rem;text-align:left;white-space:nowrap;'>{c}</th>"
        for c in df_vista.columns
    )
    rows = ""
    for i, row in df_vista.iterrows():
        bg = "#fff5f5" if i % 2 == 0 else "#ffffff"
        cells = ""
        for col, val in row.items():
            cell_bg = bg
            cell_color = "#111111"
            if col == color_col and colores_estado and val in colores_estado:
                cell_bg, cell_color = colores_estado[val]
            # Aplicar formato de pesos colombianos si corresponde
            display_val = fmt_cop(val) if fmt_cols and col in fmt_cols else val
            cells += (
                f"<td style='background:{cell_bg};color:{cell_color};"
                f"padding:7px 10px;font-size:0.83rem;border-bottom:1px solid #f0f0f0;"
                f"white-space:nowrap;'>{display_val}</td>"
            )
        rows += f"<tr>{cells}</tr>"
    html = (
        "<div style='overflow-x:auto;border:1px solid #dc2626;"
        "border-radius:8px;margin:4px 0;'>"
        f"<table style='border-collapse:collapse;width:100%;'>"
        f"<thead><tr>{thead}</tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def cerrar_sol_si_aplica(ot_row, df_sol):
    """Si la OT viene de una SOL, la marca como Completado."""
    sol_ref = str(ot_row.get("SOL_Ref", "")).strip()
    if sol_ref.startswith("SOL-") and sol_ref in df_sol["ID"].values:
        df_sol.loc[df_sol["ID"] == sol_ref, "Estado"] = "Completado"
        return df_sol, True
    return df_sol, False


def calcular_horas(inicio, final):
    """Calcula horas laboradas entre dos strings en formato 12h (ej: '08:00 AM')."""
    try:
        fmt = "%I:%M %p"
        t1  = datetime.strptime(inicio, fmt)
        t2  = datetime.strptime(final,  fmt)
        if t2 <= t1:
            t2 += timedelta(days=1)
        diff = (t2 - t1).seconds / 3600
        h, m = divmod(int((t2 - t1).seconds), 3600)
        return f"{h}h {m//60:02d}m" if m % 60 else f"{h}h"
    except Exception:
        return ""


def calcular_fecha_limite(sla, zona_completa, desde=None):
    """Retorna la fecha límite como string dado el SLA y la zona.
    El conteo de horas salta domingos y festivos colombianos."""
    desde = desde or ahora_colombia()
    clave = zona_completa[:2] if zona_completa else "Z0"
    horas = SLA_HORAS.get(sla, {}).get(clave)
    if horas is None:
        return TEXTO_Z5.get(sla, "Por definir")
    return sumar_horas_laborales(desde, horas).strftime("%Y-%m-%d %H:%M")


def crear_ot_desde_sol(sol, ots):
    """Crea una OT a partir de una fila de solicitud. Evita duplicados por SOL_Ref."""
    if not ots.empty and "SOL_Ref" in ots.columns and sol["ID"] in ots["SOL_Ref"].values:
        return ots, False  # Ya existe
    ahora = ahora_colombia()
    nueva_ot = {
        "ID":               generate_ot_id(ots),
        "Origen":           "Solicitud",
        "Creado_Por":       st.session_state.get("user_nombre",""),
        "SOL_Ref":          sol["ID"],
        "Fecha_Creacion":   ahora.strftime("%Y-%m-%d %H:%M"),
        "Fecha_Limite":     calcular_fecha_limite(sol.get("SLA", ""), sol.get("Zona", ""), ahora),
        "Cliente":          sol["Cliente"],
        "NIT":              sol["NIT"],
        "Sede":             sol["Sede"],
        "Nombre_Contacto":  sol["Nombre_Contacto"],
        "Celular_Contacto": sol["Celular_Contacto"],
        "Servicio":         sol["Servicio"],
        "Descripcion":      sol["Descripcion"],
        "SLA":              sol.get("SLA", ""),
        "Zona":             sol.get("Zona", ""),
        "Tecnico":          "",
        "Celular_Tecnico":  "",
        "Fecha_Ejecucion":  "",
        "Hora_Inicio":      "",
        "Hora_Final":       "",
        "Horas_Laboradas":  "",
        "Materiales":       "",
        "Valor_COP":        "",
        "Estado":           "Programada",
        "Observaciones":    "",
    }
    ots = pd.concat([ots, pd.DataFrame([nueva_ot])], ignore_index=True)
    return ots, True


def generate_id(df):
    hoy     = ahora_colombia().strftime("%y%m%d")
    prefijo = f"SOL-{hoy}-"
    return siguiente_id("SOL", prefijo, df)


def color_estado(val):
    p = {
        "Pendiente":  "background-color:#fff3cd; color:#000",
        "En proceso": "background-color:#cfe2ff; color:#000",
        "Completado": "background-color:#d1e7dd; color:#000",
        "Cancelado":  "background-color:#f8d7da; color:#000",
    }
    return p.get(val, "")


# ── Autenticación ─────────────────────────────────────────────────────────────

def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def load_usuarios():
    return sb_load("usuarios", ["nombre", "correo", "password_hash", "rol"])

def save_usuarios(df):
    sb_save("usuarios", df)

def verificar_login(correo, pwd, usuarios):
    u = usuarios[usuarios["correo"].str.lower() == correo.strip().lower()]
    if u.empty:
        return None
    if u.iloc[0]["password_hash"] == hash_pwd(pwd):
        return u.iloc[0]
    return None

def pagina_login():
    st.markdown("""
    <style>
    .login-box {
        max-width: 420px; margin: 60px auto; padding: 40px;
        background: #ffffff; border-radius: 16px;
        box-shadow: 0 8px 32px rgba(220,38,38,0.15);
        border-top: 5px solid #dc2626;
    }
    </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        for _rp in ["logo.png", "LOGO MINZOE.png",
                    r"D:\Escritorio\LA ASISTENTE MINZOE\logo.png",
                    r"D:\Escritorio\LA ASISTENTE MINZOE\LOGO MINZOE.png"]:
            if os.path.exists(_rp):
                st.image(_rp, width=180)
                break
        st.markdown("""
        <div style='text-align:center; margin-bottom:24px;'>
            <span style='color:#dc2626; font-size:1.5rem; font-weight:900;'>CONSTRUCCIONES MINZOE SAS</span><br>
            <span style='color:#555; font-size:0.9rem;'>Sistema de Gestión de Servicios</span>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_login"):
            correo_i = st.text_input("📧 Correo electrónico")
            pwd_i    = st.text_input("🔒 Contraseña", type="password")
            entrar   = st.form_submit_button("Iniciar sesión", type="primary", use_container_width=True)

        if entrar:
            usuarios = load_usuarios()
            if usuarios.empty:
                st.error("No hay usuarios registrados. Contacta al administrador.")
            else:
                user = verificar_login(correo_i, pwd_i, usuarios)
                if user is not None:
                    st.session_state["logged_in"]   = True
                    st.session_state["user_nombre"] = user["nombre"]
                    st.session_state["user_correo"] = user["correo"]
                    st.session_state["user_rol"]    = user["rol"]
                    st.rerun()
                else:
                    st.error("Correo o contraseña incorrectos.")


# ── Página ────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Construcciones Minzoe SAS", page_icon="🏗️", layout="wide")

# ── Tema Minzoe: Blanco | Negro | Rojo ───────────────────────────────────────
st.markdown("""
<style>
/* ── Fondo general ── */
.stApp { background-color: #ffffff !important; color: #111111 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 3px solid #dc2626 !important;
}
[data-testid="stSidebar"] * { color: #111111 !important; }

/* ── Botones sidebar ── */
[data-testid="stSidebar"] .stButton > button {
    background: #dc2626 !important; color: #000000 !important;
    border: none !important; border-radius: 8px !important;
    transition: all 0.2s !important; font-weight: 700 !important;
    font-size: 0.9rem !important; padding: 10px 14px !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #b91c1c !important; color: #000000 !important;
    transform: translateX(4px) !important;
    box-shadow: 0 3px 10px rgba(220,38,38,0.5) !important;
}
[data-testid="stSidebar"] .stButton > button p {
    color: #000000 !important; font-weight: 700 !important;
}

/* ── Botón primario global ── */
.stButton > button[kind="primary"],
button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #dc2626, #991b1b) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 700 !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #b91c1c, #7f1d1d) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(220,38,38,0.4) !important;
}

/* ── Botón secundario ── */
.stButton > button[kind="secondary"] {
    background: #ffffff !important; color: #111111 !important;
    border: 1px solid #dc2626 !important; border-radius: 8px !important;
}

/* ── Botón de descarga (download button) ── */
[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, #dc2626, #991b1b) !important;
    color: #ffffff !important; border: none !important;
    border-radius: 8px !important; font-weight: 700 !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, #b91c1c, #7f1d1d) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(220,38,38,0.4) !important;
}
[data-testid="stDownloadButton"] > button p {
    color: #ffffff !important;
}

/* ── Métricas ── */
[data-testid="metric-container"] {
    background: #fff5f5 !important; border: 1px solid #dc2626 !important;
    border-radius: 10px !important; padding: 12px !important;
}
[data-testid="metric-container"] label { color: #555555 !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #111111 !important; }

/* ── Inputs y selectbox ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    background: #ffffff !important; color: #111111 !important;
    border: 1px solid #dc2626 !important; border-radius: 6px !important;
    caret-color: #111111 !important;
}
.stNumberInput > div > div > input {
    background: #ffffff !important; color: #111111 !important;
    border: 1px solid #dc2626 !important; border-radius: 6px !important;
    caret-color: #111111 !important;
}

/* ── Campos deshabilitados (auto-relleno) ── */
.stTextInput > div > div > input:disabled,
.stTextArea > div > div > textarea:disabled {
    color: #111111 !important; -webkit-text-fill-color: #111111 !important;
    background: #f5f5f5 !important; opacity: 1 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #f8f8f8 !important; border-radius: 8px !important;
    border: 1px solid #e5e5e5 !important; gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    color: #111111 !important; border-radius: 6px !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab"] p,
.stTabs [data-baseweb="tab"] span,
.stTabs [data-baseweb="tab"] div {
    color: #111111 !important;
}
.stTabs [aria-selected="true"] {
    background: #dc2626 !important; color: #ffffff !important;
}
.stTabs [aria-selected="true"] p,
.stTabs [aria-selected="true"] span,
.stTabs [aria-selected="true"] div {
    color: #ffffff !important;
}
/* ── Radio buttons texto visible ── */
[data-testid="stRadio"] label p,
[data-testid="stRadio"] label span {
    color: #111111 !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #dc2626 !important; border-radius: 8px !important;
}
/* Encabezados: rojo con letra blanca */
[data-testid="stDataFrame"] thead tr th,
[data-testid="stDataFrame"] [data-testid="glideDataEditor"] .gdg-header,
.dvn-scroller .gdg-cell.gdg-header-cell {
    background-color: #dc2626 !important; color: #ffffff !important;
    font-weight: 700 !important;
}
/* Filas: fondo blanco letra negra */
[data-testid="stDataFrame"] tbody tr td,
[data-testid="stDataFrame"] .gdg-cell {
    background-color: #ffffff !important; color: #111111 !important;
}
[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
    background-color: #fff5f5 !important;
}

/* ── Divider ── */
hr { border-color: #dc2626 !important; opacity: 0.3 !important; }

/* ── Headers ── */
h1, h2, h3 { color: #dc2626 !important; }
h4, h5, h6 { color: #111111 !important; }

/* ── Subheader (st.subheader usa h2) ── */
[data-testid="stMarkdownContainer"] h3 { color: #dc2626 !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
    background: #fff5f5 !important; border: 1px solid #dc2626 !important;
    border-radius: 8px !important;
}

/* ── Form ── */
[data-testid="stForm"] {
    background: #fafafa !important; border: 1px solid #e8e8e8 !important;
    border-radius: 12px !important; padding: 16px !important;
    box-shadow: 0 2px 8px rgba(220,38,38,0.08) !important;
}

/* ── Multiselect tags ── */
[data-testid="stMultiSelect"] span {
    background: #dc2626 !important; color: white !important;
    border-radius: 4px !important;
}

/* ── Captions y texto secundario ── */
[data-testid="stCaptionContainer"] { color: #777777 !important; }

/* ── Info / Warning / Success boxes ── */
[data-testid="stAlert"] { border-radius: 8px !important; }
[data-testid="stAlert"] p,
[data-testid="stAlert"] span,
[data-testid="stAlert"] div { color: #111111 !important; }
div[data-testid="stWarning"] { background-color: #fffbeb !important; border-color: #d97706 !important; }
div[data-testid="stSuccess"] { background-color: #f0fdf4 !important; border-color: #16a34a !important; }
div[data-testid="stInfo"]    { background-color: #eff6ff !important; border-color: #2563eb !important; }
div[data-testid="stError"]   { background-color: #fef2f2 !important; border-color: #dc2626 !important; }

/* ── Radio ── */
[data-testid="stRadio"] label { color: #111111 !important; }

/* ── Checkbox ── */
[data-testid="stCheckbox"] label { color: #111111 !important; }

/* ── Etiquetas de campos (labels) ── */
label, .stTextInput label, .stTextArea label,
.stSelectbox label, .stDateInput label,
.stTimeInput label, .stNumberInput label,
[data-testid="stWidgetLabel"] {
    color: #111111 !important; font-weight: 600 !important;
}

/* ── Menús desplegables (selectbox options) ── */
[data-baseweb="popover"],
[data-baseweb="menu"],
ul[data-baseweb="menu"] {
    background-color: #ffffff !important;
    border: 1px solid #dc2626 !important;
    border-radius: 8px !important;
}
[data-baseweb="menu"] li,
ul[data-baseweb="menu"] li,
[data-baseweb="option"] {
    background-color: #ffffff !important;
    color: #111111 !important;
}
[data-baseweb="menu"] li:hover,
ul[data-baseweb="menu"] li:hover,
[data-baseweb="option"]:hover {
    background-color: #fff0f0 !important;
    color: #dc2626 !important;
}
/* Input de búsqueda dentro del selectbox */
[data-baseweb="select"] input {
    color: #111111 !important;
    background: #ffffff !important;
}

/* ── Campos de fecha y hora ── */
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input,
input[type="date"], input[type="time"] {
    background: #ffffff !important; color: #111111 !important;
    border: 1px solid #dc2626 !important; border-radius: 6px !important;
}
[data-testid="stDateInput"] > div,
[data-testid="stTimeInput"] > div {
    background: #ffffff !important;
}

/* ── Markdown dentro de forms (texto de sección) ── */
[data-testid="stForm"] p,
[data-testid="stForm"] span,
[data-testid="stForm"] label,
[data-testid="stForm"] div { color: #111111 !important; }

/* ══════════════════════════════════════════════════
   RESPONSIVE MÓVIL Y TABLET
   ══════════════════════════════════════════════════ */

/* ── Tablet (≤1024px) ── */
@media (max-width: 1024px) {
    /* Contenedor principal más aprovechado */
    .block-container { padding: 1rem 1.5rem !important; }

    /* Tablas HTML personalizadas: scroll horizontal */
    [data-testid="stMarkdownContainer"] table {
        display: block !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        white-space: nowrap !important;
        font-size: 0.82rem !important;
    }

    /* Botones más grandes para dedos */
    .stButton > button {
        min-height: 44px !important;
        font-size: 0.9rem !important;
    }
}

/* ── Celular (≤768px) ── */
@media (max-width: 768px) {
    /* Menos padding, más espacio útil */
    .block-container { padding: 0.75rem 0.75rem 2rem !important; max-width: 100% !important; }

    /* Tablas con scroll táctil */
    [data-testid="stMarkdownContainer"] table {
        display: block !important;
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
        white-space: nowrap !important;
        font-size: 0.78rem !important;
        border-radius: 6px !important;
    }

    /* Columnas de Streamlit en móvil: no tan apretadas */
    [data-testid="column"] { min-width: 140px !important; }

    /* Inputs y selectbox: más altos para tocar con dedo */
    input, textarea, select,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        font-size: 16px !important; /* evita zoom automático en iOS */
        min-height: 42px !important;
    }

    /* Botones primarios más grandes */
    .stButton > button {
        min-height: 48px !important;
        font-size: 0.95rem !important;
        border-radius: 8px !important;
    }

    /* Títulos más pequeños en móvil */
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1.05rem !important; }

    /* Métricas del sidebar más compactas */
    [data-testid="stMetric"] label { font-size: 0.75rem !important; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { font-size: 1.3rem !important; }

    /* Radio buttons más separados */
    [data-testid="stRadio"] label { padding: 6px 0 !important; }

    /* Checkboxes más grandes */
    [data-testid="stCheckbox"] label { padding: 4px 0 !important; font-size: 0.9rem !important; }

    /* Formularios sin tanto padding */
    [data-testid="stForm"] { padding: 10px !important; }

    /* Gráficas Plotly: scroll si son muy anchas */
    [data-testid="stPlotlyChart"] {
        overflow-x: auto !important;
        -webkit-overflow-scrolling: touch !important;
    }

    /* Expanders: texto más legible */
    [data-testid="stExpander"] summary { font-size: 0.9rem !important; }

    /* Tabs en móvil */
    [data-testid="stTabs"] [role="tab"] { font-size: 0.82rem !important; padding: 6px 10px !important; }
}

/* ── Celular muy pequeño (≤400px) ── */
@media (max-width: 400px) {
    .block-container { padding: 0.5rem 0.5rem 2rem !important; }
    [data-testid="stMarkdownContainer"] table { font-size: 0.72rem !important; }
    h2 { font-size: 1.1rem !important; }
    .stButton > button { font-size: 0.88rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Verificar login ──────────────────────────────────────────────────────────
usuarios = load_usuarios()

# Si no hay usuarios, crear admin por defecto automáticamente
if usuarios.empty:
    admin_default = pd.DataFrame([{
        "nombre":        "Administrador",
        "correo":        "helixjimenez@gmail.com",
        "password_hash": hash_pwd("Minzoe2026"),
        "rol":           "admin"
    }])
    save_usuarios(admin_default)
    usuarios = admin_default

# Si no ha iniciado sesión, mostrar pantalla de login
if not st.session_state.get("logged_in", False):
    pagina_login()
    st.stop()

# ── Usuario autenticado: carga lazy por página ───────────────────────────────
# Técnico entra directo a sus OTs, no al dashboard
_pagina_default = "ots" if st.session_state.get("user_rol") == "tecnico" else "resumen"
pagina = st.session_state.get("pagina", _pagina_default)

# Solo carga lo mínimo para el sidebar
_df_sidebar  = load_sol()
_ots_sidebar = load_ots()

def get_df():        return load_sol()
def get_cli():       return load_cli()
def get_ots():       return load_ots()
def get_contratos(): return load_contratos()
def get_equipos():   return load_equipos()
def get_cv():        return load_cv()
def get_ventas():    return load_ventas()
def get_costos():    return load_costos()

# ── Menú lateral ─────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    _logo_rutas = ["logo.png", "LOGO MINZOE.png",
                   r"D:\Escritorio\LA ASISTENTE MINZOE\logo.png",
                   r"D:\Escritorio\LA ASISTENTE MINZOE\LOGO MINZOE.png"]
    _logo_cargado = False
    for _ruta in _logo_rutas:
        if os.path.exists(_ruta):
            st.image(_ruta, use_container_width=True)
            _logo_cargado = True
            break
    if not _logo_cargado:
        st.markdown("""
        <div style='text-align:center; padding: 12px 0 4px 0;'>
            <span style='font-size:2.8rem;'>🏗️</span><br>
            <span style='color:#dc2626; font-size:1.1rem; font-weight:800;'>CONSTRUCCIONES</span><br>
            <span style='color:#ffffff; font-size:1.3rem; font-weight:900; letter-spacing:2px;'>MINZOE SAS</span>
        </div>
        """, unsafe_allow_html=True)
    st.divider()

    _rol_actual = st.session_state.get("user_rol", "usuario")
    _es_tecnico = _rol_actual == "tecnico"

    # ── GENERAL ──────────────────────────────────────────────────────────────
    if not _es_tecnico:
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state["pagina"] = "resumen"
            st.rerun()

    if not _es_tecnico:
        st.markdown("<p style='color:#aaa;font-size:0.72rem;font-weight:700;letter-spacing:1px;margin:6px 0 2px 4px;'>BASE DE DATOS</p>", unsafe_allow_html=True)
        if st.button("🏢 Clientes", use_container_width=True):
            st.session_state["pagina"] = "clientes"
            st.rerun()

    st.markdown("<p style='color:#aaa;font-size:0.72rem;font-weight:700;letter-spacing:1px;margin:6px 0 2px 4px;'>OPERACIONES</p>", unsafe_allow_html=True)

    if not _es_tecnico:
        if st.button("➕ Nueva Solicitud", use_container_width=True, type="primary"):
            for key in ["empresa_sel", "sede_sel"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state["pagina"] = "nueva"
            st.rerun()

        if st.button("📋 Ver Solicitudes", use_container_width=True):
            st.session_state["pagina"] = "ver"
            st.rerun()

    _lbl_ots = "🛠️ Mis OTs" if _es_tecnico else "🛠️ Órdenes de Trabajo"
    if st.button(_lbl_ots, use_container_width=True, type="primary" if _es_tecnico else "secondary"):
        st.session_state["pagina"] = "ots"
        st.session_state["accion_ot_radio"] = "📋 Ver OTs"
        st.rerun()

    if st.button("📅 Calendario de Visitas", use_container_width=True):
        st.session_state["pagina"] = "calendario"
        st.rerun()

    if not _es_tecnico:
        if st.button("📄 Contratos de Mantenimiento", use_container_width=True):
            st.session_state["pagina"] = "contratos_mto"
            st.rerun()

    if st.button("🗂️ Hojas de Vida Equipos", use_container_width=True):
        st.session_state["pagina"] = "hojas_vida"
        st.rerun()

    if not _es_tecnico:
        st.markdown("<p style='color:#aaa;font-size:0.72rem;font-weight:700;letter-spacing:1px;margin:6px 0 2px 4px;'>FINANCIERO</p>", unsafe_allow_html=True)
        if st.button("💰 Compras y Ventas", use_container_width=True):
            st.session_state["pagina"] = "compras_ventas"
            st.rerun()

    st.divider()
    if _es_tecnico:
        _nom_tec_sidebar = st.session_state.get("user_nombre", "")
        _mis_ots = _ots_sidebar[_ots_sidebar["Tecnico"].str.strip().str.lower() == _nom_tec_sidebar.strip().lower()] if not _ots_sidebar.empty else _ots_sidebar
        ots_activas = int((_mis_ots["Estado"].isin(["Programada","En ejecución"])).sum()) if not _mis_ots.empty else 0
        ots_hoy = int((_mis_ots["Fecha_Ejecucion"].str.startswith(ahora_colombia().strftime("%Y-%m-%d"), na=False)).sum()) if not _mis_ots.empty else 0
        st.metric("🛠️ Mis OTs Activas", ots_activas)
        st.metric("📅 Visitas hoy",     ots_hoy)
    else:
        pendientes  = int((_df_sidebar["Estado"] == "Pendiente").sum()) if not _df_sidebar.empty else 0
        ots_activas = int((_ots_sidebar["Estado"].isin(["Programada","En ejecución"])).sum()) if not _ots_sidebar.empty else 0
        st.metric("🟡 Sol. Pendientes", pendientes)
        st.metric("🛠️ OTs Activas",    ots_activas)
    st.divider()

    # Usuario actual
    st.markdown(f"""
    <div style='background:#fff5f5;border-radius:8px;padding:8px 12px;
    border-left:3px solid #dc2626;margin-bottom:8px;'>
    <span style='font-size:0.8rem;color:#555;'>Conectado como:</span><br>
    <span style='font-weight:700;color:#dc2626;'>{st.session_state.get('user_nombre','')}</span><br>
    <span style='font-size:0.75rem;color:#888;'>{st.session_state.get('user_correo','')}</span>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Cerrar sesión", use_container_width=True, type="secondary"):
        for k in ["logged_in","user_nombre","user_correo","user_rol"]:
            st.session_state.pop(k, None)
        st.rerun()

    # Solo admin puede gestionar usuarios y subir logo
    if st.session_state.get("user_rol") == "admin":
        st.markdown("<p style='color:#aaa;font-size:0.72rem;font-weight:700;letter-spacing:1px;margin:6px 0 2px 4px;'>ADMINISTRACIÓN</p>", unsafe_allow_html=True)
        if st.button("👥 Gestionar usuarios", use_container_width=True):
            st.session_state["pagina"] = "gestion_usuarios"
            st.rerun()
        if st.button("🔄 Migración", use_container_width=True):
            st.session_state["pagina"] = "usuarios"
            st.rerun()
        with st.expander("⚙️ Subir logo"):
            logo_up = st.file_uploader("Logo (PNG/JPG)", type=["png","jpg","jpeg"], key="logo_uploader")
            if logo_up:
                with open(r"D:\Escritorio\LA ASISTENTE MINZOE\LOGO MINZOE.png", "wb") as f:
                    f.write(logo_up.read())
                st.success("Logo guardado. Reinicia la app.")


st.markdown("""
<div style='background:#ffffff; border-radius:12px; padding:16px 24px;
     margin-bottom:8px; border-left:5px solid #dc2626;
     box-shadow: 0 2px 10px rgba(220,38,38,0.12);'>
  <span style='color:#dc2626; font-size:1.7rem; font-weight:900; letter-spacing:1px;'>
    CONSTRUCCIONES MINZOE SAS
  </span><br>
  <span style='color:#555555; font-size:0.9rem;'>Sistema de Gestión de Servicios</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: NUEVA SOLICITUD
# ══════════════════════════════════════════════════════════════════════════════
if pagina == "nueva":
    if st.session_state.get("user_rol") == "tecnico":
        st.warning("⛔ No tienes permiso para acceder a esta sección.")
        st.stop()
    df = get_df(); cli = get_cli(); ots = get_ots(); equipos = get_equipos()
    st.subheader("Registrar nueva solicitud")

    # ── SECCIÓN 1: INFORMACIÓN DE LA EMPRESA ─────────────────────────────────
    st.markdown("### 🏢 1. Información de la Empresa")

    empresas = sorted(cli["Empresa"].unique().tolist()) if not cli.empty else []
    opcion_nueva = "✏️  Empresa no registrada (ingresar manualmente)"
    opciones = empresas + [opcion_nueva]

    # Detectar cambio de empresa para resetear sede
    empresa_anterior = st.session_state.get("_empresa_anterior", None)

    empresa_sel = st.selectbox(
        "Nombre de la empresa *  (escribe para buscar)",
        opciones,
        index=None,
        placeholder="Escribe el nombre de la empresa...",
        key="empresa_sel",
    )

    # Si cambió la empresa, borrar la sede guardada en memoria
    if empresa_sel != empresa_anterior:
        st.session_state["_empresa_anterior"] = empresa_sel
        if "sede_sel" in st.session_state:
            del st.session_state["sede_sel"]
        st.rerun()

    # Valores por defecto
    nit_v = dir_emp_v = sede_v = dir_sede_v = ""
    nom_c_v = cor_c_v = cel_c_v = ""
    empresa_final = ""

    if empresa_sel and empresa_sel != opcion_nueva:
        empresa_final = empresa_sel
        filas_emp = cli[cli["Empresa"].str.strip().str.lower() == empresa_sel.strip().lower()]

        if filas_emp.empty:
            st.warning(f"No se encontraron datos para '{empresa_sel}'. Verifica la sección 🏢 Clientes.")
        else:
            primera  = filas_emp.iloc[0]
            nit_v    = primera["NIT"]
            dir_emp_v = primera["Direccion_Empresa"]

            c1, c2 = st.columns(2)
            with c1:
                st.text_input("NIT", value=nit_v, disabled=True, key="nit_dis")
            with c2:
                st.text_input("Dirección de la empresa", value=dir_emp_v, disabled=True, key="dir_dis")

            # Sede → empieza vacía, sin auto-selección
            sedes_lista = filas_emp["Sede"].tolist()
            sede_sel = st.selectbox(
                "Sede / Sucursal",
                sedes_lista,
                index=None,
                placeholder="Selecciona la sede...",
                key="sede_sel"
            )

            # Solo mostrar dirección y contacto cuando se seleccione una sede
            if sede_sel:
                fila_sede_df = filas_emp[filas_emp["Sede"] == sede_sel]
                if not fila_sede_df.empty:
                    fila_sede   = fila_sede_df.iloc[0]
                    dir_sede_v  = fila_sede["Direccion_Sede"]
                    nom_c_v     = fila_sede["Nombre_Contacto"]
                    cor_c_v     = fila_sede["Correo_Contacto"]
                    cel_c_v     = fila_sede["Celular_Contacto"]
                    sede_v      = sede_sel
                st.text_input("Dirección de la sede", value=dir_sede_v, disabled=True, key="dir_sede_dis")
                st.markdown("**Datos del contacto**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.text_input("Nombre del contacto", value=nom_c_v, disabled=True, key="nc_dis")
                with c2:
                    st.text_input("Correo del contacto", value=cor_c_v, disabled=True, key="cc_dis")
                with c3:
                    st.text_input("Celular del contacto", value=cel_c_v, disabled=True, key="cel_dis")

                # ── Equipos registrados en esta sede ──────────────────────
                if not equipos.empty:
                    _eq_sede = equipos[
                        (equipos["Cliente"].str.strip().str.lower() == empresa_sel.strip().lower()) &
                        (equipos["Sede"].str.strip().str.lower() == sede_sel.strip().lower())
                    ]
                    if not _eq_sede.empty:
                        st.markdown("**🔧 Equipos en esta sede:**")
                        _cols_eq = [c for c in ["ID_Item","Servicio","Marca","Modelo",
                                                 "Numero_Serie","Ubicacion","Ultimo_Mantenimiento"]
                                    if c in _eq_sede.columns]
                        for _srv in SERVICIOS_CON_EQUIPOS:
                            _eq_srv = _eq_sede[_eq_sede["Servicio"] == _srv]
                            if not _eq_srv.empty:
                                with st.expander(f"🔧 {_srv} — {len(_eq_srv)} equipo(s)"):
                                    tabla_html(_eq_srv[_cols_eq].reset_index(drop=True))

    elif empresa_sel == opcion_nueva:
        # Entrada manual
        c1, c2 = st.columns(2)
        with c1:
            empresa_final = st.text_input("Nombre de la empresa *", key="emp_manual")
            nit_v         = st.text_input("NIT", key="nit_manual")
            dir_emp_v     = st.text_input("Dirección de la empresa", key="dir_emp_manual")
        with c2:
            sede_v        = st.text_input("Sede / Sucursal", key="sede_manual")
            dir_sede_v    = st.text_input("Dirección de la sede", key="dir_sede_manual")

        st.markdown("**Datos del contacto**")
        c1, c2, c3 = st.columns(3)
        with c1:
            nom_c_v = st.text_input("Nombre del contacto", key="nc_manual")
        with c2:
            cor_c_v = st.text_input("Correo del contacto", key="cc_manual")
        with c3:
            cel_c_v = st.text_input("Celular del contacto", key="cel_manual")

    st.divider()

    # ── SECCIÓN 2: DETALLE DEL SERVICIO ──────────────────────────────────────
    st.markdown("### 🔧 2. Detalle del Servicio")

    # Ciudad fuera del form → zona se calcula reactivamente
    ciudades_lista = sorted(CIUDADES_ZONAS.keys()) + ["🔍 Otra ciudad (zona manual)"]
    ciudad_sel = st.selectbox(
        "Ciudad del cliente", ciudades_lista,
        index=None, placeholder="Escribe o selecciona la ciudad...",
        key="ciudad_sol",
    )
    if ciudad_sel and ciudad_sel != "🔍 Otra ciudad (zona manual)":
        zona_final = CIUDADES_ZONAS[ciudad_sel]
        st.info(f"📍 Zona asignada automáticamente: **{ZONA_LABEL[zona_final]}**")
    elif ciudad_sel == "🔍 Otra ciudad (zona manual)":
        zona_manual = st.selectbox("Selecciona la zona manualmente", ZONAS, key="zona_manual_sol")
        zona_final  = zona_manual[:2]
        ciudad_sel  = st.text_input("Nombre de la ciudad", key="ciudad_manual_sol") or ciudad_sel
    else:
        zona_final = ""

    with st.form("form_solicitud", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            servicio       = st.selectbox("Servicio solicitado *", SERVICIOS)
            tipo_servicio  = st.selectbox("Tipo de servicio", TIPOS_SERVICIO)
            descripcion    = st.text_area("Descripción del problema")
        with c2:
            sla   = st.selectbox("Nivel de SLA", SLA)
            canal = st.selectbox("Canal de comunicación", CANALES)

        st.divider()
        guardar = st.form_submit_button("💾 Guardar solicitud", type="primary", use_container_width=True)

        if guardar:
            if not empresa_final:
                st.error("Selecciona o ingresa el nombre de la empresa.")
            else:
                nueva = {
                    "ID":               generate_id(df),
                    "Fecha":            ahora_colombia().strftime("%Y-%m-%d %H:%M"),
                    "Creado_Por":       st.session_state.get("user_nombre",""),
                    "Cliente":          empresa_final,
                    "NIT":              nit_v,
                    "Direccion_Empresa": dir_emp_v,
                    "Sede":             sede_v,
                    "Direccion_Sede":   dir_sede_v,
                    "Nombre_Contacto":  nom_c_v,
                    "Correo_Contacto":  cor_c_v,
                    "Celular_Contacto": cel_c_v,
                    "Servicio":         servicio,
                    "Tipo_Servicio":    tipo_servicio,
                    "Descripcion":      descripcion.strip(),
                    "SLA":              sla,
                    "Ciudad":           ciudad_sel or "",
                    "Zona":             zona_final,
                    "Canal":            canal,
                    "Estado":           "Pendiente",
                }
                df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
                save_sol(df)
                msg_sol = f"✅ Solicitud **{nueva['ID']}** guardada para {empresa_final}."
                # Enviar confirmación por correo al contacto
                correo_cli = cor_c_v.strip() if cor_c_v.strip() else ""
                if correo_cli:
                    resultado_mail = enviar_confirmacion_sol(
                        sol_id          = nueva["ID"],
                        cliente         = empresa_final,
                        servicio        = servicio,
                        tipo_servicio   = tipo_servicio,
                        sla             = sla,
                        contacto_nombre = nom_c_v or empresa_final,
                        correo_destino  = correo_cli,
                        fecha           = nueva["Fecha"],
                    )
                    ok_mail  = resultado_mail[0]
                    res_mail = resultado_mail[1]
                    msg_id   = resultado_mail[2] if len(resultado_mail) > 2 else ""
                    # Guardar Message-ID en la SOL para encadenar el correo de OT
                    if ok_mail and msg_id:
                        df.loc[df["ID"] == nueva["ID"], "Email_Message_ID"] = msg_id
                        save_sol(df)
                    msg_sol += f" 📧 {res_mail}" if ok_mail else f" ⚠️ Correo no enviado: {res_mail}"
                st.success(msg_sol)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: VER SOLICITUDES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "ver":
    if st.session_state.get("user_rol") == "tecnico":
        st.warning("⛔ No tienes permiso para acceder a esta sección.")
        st.stop()
    import io
    df = get_df(); ots = get_ots()

    # Mostrar notificaciones guardadas del rerun anterior
    if "notif_sol" in st.session_state:
        for tipo, texto in st.session_state.pop("notif_sol"):
            if tipo == "success": st.success(texto)
            elif tipo == "warning": st.warning(texto)
            elif tipo == "error":  st.error(texto)
            else: st.info(texto)

    c_tit, c_ref = st.columns([5,1])
    c_tit.subheader("📋 Solicitudes registradas")
    if c_ref.button("🔄 Actualizar", use_container_width=True):
        _invalidar_cache("solicitudes")
        st.rerun()

    if df.empty:
        st.info("Aún no hay solicitudes registradas.")
    else:
        # ── FILTROS ───────────────────────────────────────────────────────────
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            f_estado   = st.multiselect("Estado", ESTADOS, default=ESTADOS)
        with c2:
            f_servicio = st.multiselect("Servicio", SERVICIOS, default=SERVICIOS)
        with c3:
            buscar = st.text_input("Buscar empresa")
        with c4:
            f_fecha_ini = st.date_input("Desde", value=None, key="sol_fecha_ini")
        with c5:
            f_fecha_fin = st.date_input("Hasta", value=None, key="sol_fecha_fin")

        vista = df.copy()
        if f_estado:
            vista = vista[vista["Estado"].isin(f_estado)]
        if f_servicio:
            vista = vista[vista["Servicio"].isin(f_servicio)]
        if buscar:
            vista = vista[vista["Cliente"].str.contains(buscar, case=False, na=False)]
        # Filtro por rango de fechas
        if f_fecha_ini:
            vista = vista[vista["Fecha"].str[:10] >= f_fecha_ini.strftime("%Y-%m-%d")]
        if f_fecha_fin:
            vista = vista[vista["Fecha"].str[:10] <= f_fecha_fin.strftime("%Y-%m-%d")]

        vista_ord = vista.sort_values("ID", ascending=False, key=lambda x: x.str.replace("SOL-", ""))

        COLS_TABLA = ["ID", "Fecha", "Creado_Por", "Cliente", "Sede", "Nombre_Contacto",
                      "Celular_Contacto", "Servicio", "Descripcion", "SLA", "Canal", "Estado"]
        cols_visibles = [c for c in COLS_TABLA if c in vista_ord.columns]

        COLORES_SOL = {
            "Pendiente":  ("#fff3cd", "#7d5a00"),
            "Aprobado":   ("#d1e7dd", "#0a5c36"),
            "Completado": ("#cfe2ff", "#0a3678"),
            "Cancelado":  ("#f8d7da", "#7f1d1d"),
        }
        tabla_html(vista_ord[cols_visibles].reset_index(drop=True),
                   color_col="Estado", colores_estado=COLORES_SOL)

        c1, c2 = st.columns([3, 1])
        with c1:
            st.caption(f"Mostrando {len(vista_ord)} de {len(df)} solicitudes.")
        with c2:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                vista_ord.to_excel(writer, index=False, sheet_name="Solicitudes")
            st.download_button(
                label="⬇️ Exportar a Excel",
                data=buf.getvalue(),
                file_name=f"solicitudes_minzoe_{ahora_colombia().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.divider()

        # ── ACCIONES POR SOLICITUD ────────────────────────────────────────────
        ids_lista = df.sort_values("ID", ascending=False, key=lambda x: x.str.replace("SOL-", ""))["ID"].tolist()
        id_sel    = st.selectbox("Selecciona una solicitud", ids_lista, key="id_accion")

        if id_sel:
            fila = df[df["ID"] == id_sel].iloc[0]

            acc1, acc2, acc_com, acc_hist, acc3 = st.tabs(["🔍 Ver detalle", "✏️ Editar", "💬 Comentarios", "📜 Historial", "🗑️ Eliminar"])

            # ── VER DETALLE ───────────────────────────────────────────────────
            with acc1:
                st.markdown(f"### {id_sel}")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**🏢 Empresa**")
                    st.write(f"**Nombre:** {fila['Cliente']}")
                    st.write(f"**NIT:** {fila['NIT']}")
                    st.write(f"**Dirección empresa:** {fila['Direccion_Empresa']}")
                    st.write(f"**Sede:** {fila['Sede']}")
                    st.write(f"**Dirección sede:** {fila['Direccion_Sede']}")
                    st.markdown("**👤 Contacto**")
                    st.write(f"**Nombre:** {fila['Nombre_Contacto']}")
                    st.write(f"**Correo:** {fila['Correo_Contacto']}")
                    st.write(f"**Celular:** {fila['Celular_Contacto']}")
                with c2:
                    st.markdown("**🔧 Servicio**")
                    st.write(f"**Servicio:** {fila['Servicio']}")
                    st.write(f"**Descripción:** {fila['Descripcion']}")
                    st.write(f"**SLA:** {fila['SLA']}")
                    st.write(f"**Canal:** {fila['Canal']}")
                    st.markdown("**📊 Estado**")
                    st.write(f"**Estado:** {fila['Estado']}")
                    st.write(f"**Fecha registro:** {fila['Fecha']}")

            # ── EDITAR ────────────────────────────────────────────────────────
            with acc2:
                st.markdown(f"### Editar {id_sel}")
                with st.form("form_editar", clear_on_submit=False):
                    st.markdown("**🏢 Empresa**")
                    c1, c2 = st.columns(2)
                    with c1:
                        e_cliente   = st.text_input("Empresa",            value=fila["Cliente"])
                        e_nit       = st.text_input("NIT",                value=fila["NIT"])
                        e_dir_emp   = st.text_input("Dirección empresa",  value=fila["Direccion_Empresa"])
                    with c2:
                        e_sede      = st.text_input("Sede",               value=fila["Sede"])
                        e_dir_sede  = st.text_input("Dirección sede",     value=fila["Direccion_Sede"])

                    st.markdown("**👤 Contacto**")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        e_nom_c = st.text_input("Nombre contacto",  value=fila["Nombre_Contacto"])
                    with c2:
                        e_cor_c = st.text_input("Correo contacto",  value=fila["Correo_Contacto"])
                    with c3:
                        e_cel_c = st.text_input("Celular contacto", value=fila["Celular_Contacto"])

                    st.markdown("**🔧 Servicio**")
                    c1, c2 = st.columns(2)
                    with c1:
                        e_serv  = st.selectbox("Servicio", SERVICIOS,
                                               index=SERVICIOS.index(fila["Servicio"]) if fila["Servicio"] in SERVICIOS else 0)
                        e_desc  = st.text_area("Descripción", value=fila["Descripcion"])
                    with c2:
                        e_sla   = st.selectbox("SLA", SLA,
                                               index=SLA.index(fila["SLA"]) if fila["SLA"] in SLA else 0)
                        e_canal = st.selectbox("Canal", CANALES,
                                               index=CANALES.index(fila["Canal"]) if fila["Canal"] in CANALES else 0)
                        e_estado = st.selectbox("Estado", ESTADOS,
                                                index=ESTADOS.index(fila["Estado"]) if fila["Estado"] in ESTADOS else 0)

                    if st.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True):
                        idx = df[df["ID"] == id_sel].index[0]
                        df.loc[idx, "Cliente"]          = e_cliente
                        df.loc[idx, "NIT"]              = e_nit
                        df.loc[idx, "Direccion_Empresa"] = e_dir_emp
                        df.loc[idx, "Sede"]             = e_sede
                        df.loc[idx, "Direccion_Sede"]   = e_dir_sede
                        df.loc[idx, "Nombre_Contacto"]  = e_nom_c
                        df.loc[idx, "Correo_Contacto"]  = e_cor_c
                        df.loc[idx, "Celular_Contacto"] = e_cel_c
                        df.loc[idx, "Servicio"]         = e_serv
                        df.loc[idx, "Descripcion"]      = e_desc
                        df.loc[idx, "SLA"]              = e_sla
                        df.loc[idx, "Canal"]            = e_canal
                        estado_ant = fila["Estado"]
                        df.loc[idx, "Estado"] = e_estado
                        save_sol(df)
                        if estado_ant != e_estado:
                            registrar_cambio("SOL", id_sel, "Estado", estado_ant, e_estado)
                        msg = f"✅ Solicitud {id_sel} actualizada."
                        notif = [("success", msg)]

                        if e_estado == "Aprobado":
                            try:
                                sol_row   = df[df["ID"] == id_sel].iloc[0]
                                ots_fresh = load_ots()
                                ots_fresh, creada = crear_ot_desde_sol(sol_row, ots_fresh)
                                if creada:
                                    save_ots(ots_fresh)
                                    ots = ots_fresh
                                    nueva_ot_id = ots.iloc[-1]["ID"]
                                    notif.append(("success",
                                        f"🛠️ Orden de Trabajo **{nueva_ot_id}** creada para "
                                        f"**{sol_row.get('Cliente','')}** — {sol_row.get('Servicio','')}"))

                                    correo_cli = sol_row.get("Correo_Contacto","").strip()
                                    if correo_cli:
                                        # Message-ID determinístico: siempre <SOL-ID@dominio>
                                        msg_id_orig = f"<{id_sel}@construminzoe.com>"
                                        ok_m, res_m = enviar_actualizacion_ot(
                                            sol_id          = id_sel,
                                            ot_id           = nueva_ot_id,
                                            cliente         = sol_row.get("Cliente",""),
                                            contacto_nombre = sol_row.get("Nombre_Contacto",""),
                                            correo_destino  = correo_cli,
                                            fecha           = ahora_colombia().strftime("%Y-%m-%d %H:%M"),
                                            reply_to_id     = msg_id_orig,
                                        )
                                        if ok_m:
                                            notif.append(("success", f"📧 Correo enviado a **{correo_cli}**"))
                                        else:
                                            notif.append(("warning", f"⚠️ Correo no enviado: {res_m}"))
                                    else:
                                        notif.append(("info", "ℹ️ Sin correo de contacto registrado."))
                                else:
                                    notif.append(("warning", "⚠️ Ya existe una OT para esta solicitud."))
                            except Exception as ex_ot:
                                notif.append(("error", f"❌ Error creando OT: {ex_ot}"))

                        # Guardar notificaciones en sesión para mostrar después del rerun
                        st.session_state["notif_sol"] = notif
                        st.rerun()

            # ── ELIMINAR ──────────────────────────────────────────────────────
            with acc_com:
                st.markdown(f"**💬 Comentarios internos — {id_sel}**")
                if st.button("🔄 Cargar comentarios", key=f"load_com_sol_{id_sel}"):
                    st.session_state[f"show_com_sol_{id_sel}"] = True
                coms_sol = pd.DataFrame()
                if st.session_state.get(f"show_com_sol_{id_sel}"):
                    coms_all = load_comentarios()
                    coms_sol = coms_all[(coms_all["Entidad"]=="SOL") & (coms_all["Entidad_ID"]==id_sel)] if not coms_all.empty else pd.DataFrame()
                if coms_sol.empty:
                    st.info("Sin comentarios aún.")
                else:
                    for _, c in coms_sol.sort_values("Fecha", ascending=False).iterrows():
                        st.markdown(f"""<div style='background:#fff5f5;border-left:3px solid #dc2626;
                            padding:8px 12px;border-radius:6px;margin:4px 0;font-size:13px'>
                            <b>{c['Usuario']}</b> <span style='color:#999;font-size:11px'>{c['Fecha']}</span><br>{c['Comentario']}
                            </div>""", unsafe_allow_html=True)
                with st.form(f"form_com_sol_{id_sel}", clear_on_submit=True):
                    nuevo_com = st.text_area("Agregar comentario", key=f"com_sol_{id_sel}")
                    if st.form_submit_button("💬 Agregar", type="primary"):
                        if nuevo_com.strip():
                            agregar_comentario("SOL", id_sel, nuevo_com)
                            st.success("Comentario agregado.")
                            st.rerun()

            with acc_hist:
                st.markdown(f"**📜 Historial de cambios — {id_sel}**")
                if st.button("🔄 Cargar historial", key=f"load_hist_sol_{id_sel}"):
                    st.session_state[f"show_hist_sol_{id_sel}"] = True
                hist_sol = pd.DataFrame()
                if st.session_state.get(f"show_hist_sol_{id_sel}"):
                    hist_all = load_historial()
                    hist_sol = hist_all[(hist_all["Entidad"]=="SOL") & (hist_all["Entidad_ID"]==id_sel)] if not hist_all.empty else pd.DataFrame()
                if hist_sol.empty:
                    st.info("Sin cambios registrados.")
                else:
                    tabla_html(hist_sol[["Fecha","Usuario","Campo","Valor_Anterior","Valor_Nuevo"]].sort_values("Fecha", ascending=False).reset_index(drop=True))

            with acc3:
                st.markdown(f"### Eliminar {id_sel}")
                st.warning(f"¿Seguro que deseas eliminar la solicitud **{id_sel}** de **{fila['Cliente']}**? Esta acción no se puede deshacer.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🗑️ Sí, eliminar", type="primary", use_container_width=True):
                        registrar_cambio("SOL", id_sel, "Estado", fila["Estado"], "ELIMINADA")
                        df = df[df["ID"] != id_sel].reset_index(drop=True)
                        save_sol(df)
                        st.success(f"Solicitud {id_sel} eliminada.")
                        st.rerun()
                with c2:
                    st.button("❌ Cancelar", use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "resumen":
    if st.session_state.get("user_rol") == "tecnico":
        st.session_state["pagina"] = "ots"
        st.rerun()
    import plotly.express as px
    import plotly.graph_objects as go
    df = get_df(); ots = get_ots(); cv = get_cv(); ventas = get_ventas(); costos = get_costos(); contratos = get_contratos()
    hoy_dash = ahora_colombia()
    mes_dash = hoy_dash.strftime("%Y-%m")

    # ── Estilos CSS ──────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    .dash-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px; padding: 28px 32px; margin-bottom: 24px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .dash-title { color: #e94560; font-size: 2rem; font-weight: 800; margin: 0; }
    .dash-sub   { color: #a8b2d8; font-size: 1rem; margin: 4px 0 0 0; }
    .dash-date  { color: #a8b2d8; font-size: 0.95rem; text-align: right; }

    .kpi-card {
        border-radius: 14px; padding: 20px 16px; text-align: center;
        margin: 4px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    .kpi-num   { font-size: 2.4rem; font-weight: 800; margin: 0; line-height: 1; }
    .kpi-label { font-size: 0.82rem; font-weight: 600; margin: 8px 0 0 0;
                 text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9; }

    .card-blue   { background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; }
    .card-yellow { background: linear-gradient(135deg, #92400e, #d97706); color: white; }
    .card-green  { background: linear-gradient(135deg, #14532d, #16a34a); color: white; }
    .card-red    { background: linear-gradient(135deg, #7f1d1d, #dc2626); color: white; }
    .card-purple { background: linear-gradient(135deg, #4c1d95, #7c3aed); color: white; }
    .card-teal   { background: linear-gradient(135deg, #134e4a, #0d9488); color: white; }
    .card-indigo { background: linear-gradient(135deg, #312e81, #4f46e5); color: white; }
    .card-orange { background: linear-gradient(135deg, #7c2d12, #ea580c); color: white; }

    .section-title {
        font-size: 1.1rem; font-weight: 700; color: #1e293b;
        border-left: 4px solid #e94560; padding-left: 10px;
        margin: 20px 0 12px 0;
    }
    .alert-box {
        border-radius: 10px; padding: 14px 18px; margin: 6px 0;
        font-size: 0.9rem;
    }
    .alert-red    { background: #fef2f2; border-left: 4px solid #dc2626; color: #7f1d1d; }
    .alert-yellow { background: #fffbeb; border-left: 4px solid #d97706; color: #78350f; }
    .alert-green  { background: #f0fdf4; border-left: 4px solid #16a34a; color: #14532d; }
    </style>
    """, unsafe_allow_html=True)

    # ── Banner principal ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="dash-header">
        <div>
            <p class="dash-title">🔧 Construcciones Minzoe SAS</p>
            <p class="dash-sub">Panel de Control General</p>
        </div>
        <div class="dash-date">
            📅 {hoy_dash.strftime('%d de %B de %Y')}<br>
            🕐 {hoy_dash.strftime('%H:%M')} hrs
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Calcular métricas ─────────────────────────────────────────────────────
    sol_pend  = int((df["Estado"] == "Pendiente").sum())  if not df.empty else 0
    sol_apro  = int((df["Estado"] == "Aprobado").sum())   if not df.empty else 0
    sol_comp  = int((df["Estado"] == "Completado").sum()) if not df.empty else 0
    sol_can   = int((df["Estado"] == "Cancelado").sum())  if not df.empty else 0
    sol_total = len(df)

    ot_prog   = int((ots["Estado"] == "Programada").sum())   if not ots.empty else 0
    ot_ejec   = int((ots["Estado"] == "En ejecución").sum()) if not ots.empty else 0
    ot_fin    = int((ots["Estado"] == "Finalizada").sum())   if not ots.empty else 0
    ot_total  = len(ots)

    cv_mes    = cv[cv["Fecha"].str.startswith(mes_dash, na=False)] if not cv.empty else pd.DataFrame()
    venta_mes = cv_mes["Valor_Antes_IVA"].apply(to_num).sum() if not cv_mes.empty else 0
    util_mes  = cv_mes["Utilidad"].apply(to_num).sum()        if not cv_mes.empty else 0
    venta_tot = cv["Valor_Antes_IVA"].apply(to_num).sum()     if not cv.empty else 0
    util_tot  = cv["Utilidad"].apply(to_num).sum()            if not cv.empty else 0
    margen    = (util_tot / venta_tot * 100) if venta_tot > 0 else 0
    con_act   = int((contratos["Estado_Contrato"] == "Activo").sum()) if not contratos.empty else 0

    # ── ALERTAS PRIMERO ───────────────────────────────────────────────────────
    st.markdown('<p class="section-title">🚨 ALERTAS Y PENDIENTES</p>', unsafe_allow_html=True)
    st.markdown("""<style>
    @keyframes parpadeo { 0%,100%{opacity:1;} 50%{opacity:0.3;} }
    </style>""", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**🔴 OTs que requieren atención**")
        st.markdown("""<div style='display:flex;background:#dc2626;color:white;border-radius:6px 6px 0 0;
            padding:5px 8px;gap:8px;font-size:12px;font-weight:700;'>
            <span style='min-width:20px'>⚠️</span><span style='min-width:110px'>ID</span>
            <span style='min-width:120px'>Vencimiento</span><span style='min-width:120px'>Cliente</span>
            <span style='flex:1'>Servicio</span><span style='min-width:80px'>Acción</span>
            </div>""", unsafe_allow_html=True)
        if not ots.empty and "Fecha_Limite" in ots.columns:
            def _il(val):
                try:
                    fl=datetime.strptime(val,"%Y-%m-%d %H:%M"); diff=(fl-hoy_dash).total_seconds()/3600
                    return ("vencida",fl.strftime("%d/%m/%Y %H:%M")) if diff<0 else (("proxima",fl.strftime("%d/%m/%Y %H:%M")) if diff<=24 else (None,""))
                except: return (None,"")
            ots_al=ots[(ots["Estado"].isin(["Programada","En ejecución"]))&(ots["Fecha_Limite"].apply(lambda x:_il(x)[0] is not None))].copy()
            if ots_al.empty:
                st.success("✅ Sin OTs vencidas ni próximas a vencer")
            else:
                for _,r in ots_al.head(8).iterrows():
                    tipo,fec=_il(r["Fecha_Limite"]); icono="🔴" if tipo=="vencida" else "🟡"
                    bg="#fee2e2" if tipo=="vencida" else "#fef9c3"; borde="2px solid #dc2626" if tipo=="vencida" else "1px solid #d97706"
                    anim="animation:parpadeo 1s infinite;" if tipo=="vencida" else ""
                    c1,c2=st.columns([5,1])
                    with c1:
                        st.markdown(f"""<div style='{anim}background:{bg};border:{borde};border-radius:6px;
                            padding:5px 8px;margin:2px 0;font-size:12px;display:flex;gap:8px;'>
                            <span style='min-width:20px'>{icono}</span><span style='min-width:110px;font-weight:700'>{r['ID']}</span>
                            <span style='min-width:120px'>{fec}</span><span style='min-width:120px'>{r['Cliente'][:20]}</span>
                            <span>{r['Servicio'][:18]}</span></div>""",unsafe_allow_html=True)
                    with c2:
                        if st.button("→ Ver OT",key=f"aot2_{r['ID']}",use_container_width=True):
                            st.session_state["pagina"]="ots"; st.session_state["accion_ot_radio"]="📋 Ver OTs"; st.session_state["ot_preselect"]=r["ID"]; st.rerun()
        else:
            st.success("✅ Sin alertas")

    with col_b:
        st.markdown("**🟡 Solicitudes pendientes más antiguas**")
        st.markdown("""<div style='display:flex;background:#dc2626;color:white;border-radius:6px 6px 0 0;
            padding:5px 8px;gap:8px;font-size:12px;font-weight:700;'>
            <span style='min-width:110px'>ID</span><span style='min-width:120px'>Fecha</span>
            <span style='min-width:120px'>Cliente</span><span style='flex:1'>Servicio</span>
            <span style='min-width:80px'>Acción</span></div>""", unsafe_allow_html=True)
        if not df.empty:
            pend_df2=df[df["Estado"]=="Pendiente"].sort_values("Fecha").head(5)
            if pend_df2.empty:
                st.success("✅ Sin solicitudes pendientes")
            else:
                for _,r in pend_df2.iterrows():
                    c1,c2=st.columns([5,1])
                    with c1:
                        st.markdown(f"""<div style='background:#fef9c3;border:1px solid #d97706;border-radius:6px;
                            padding:5px 8px;margin:2px 0;font-size:12px;display:flex;gap:8px;'>
                            <span style='min-width:110px;font-weight:700'>{r['ID']}</span>
                            <span style='min-width:120px'>{r['Fecha'][:16]}</span>
                            <span style='min-width:120px'>{r['Cliente'][:20]}</span>
                            <span>{r['Servicio'][:18]}</span></div>""",unsafe_allow_html=True)
                    with c2:
                        if st.button("→ Ver SOL",key=f"asol2_{r['ID']}",use_container_width=True):
                            st.session_state["pagina"]="ver"; st.rerun()
        else:
            st.success("✅ Sin pendientes")

    st.divider()

    # ── SECCIÓN 1: SOLICITUDES ────────────────────────────────────────────────
    st.markdown('<p class="section-title">📋 SOLICITUDES</p>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    cards_sol = [
        (c1, sol_total, "Total",       "card-blue"),
        (c2, sol_pend,  "Pendientes",  "card-yellow"),
        (c3, sol_apro,  "Aprobadas",   "card-indigo"),
        (c4, sol_comp,  "Completadas", "card-green"),
        (c5, sol_can,   "Canceladas",  "card-red"),
    ]
    for col, val, label, cls in cards_sol:
        col.markdown(f'<div class="kpi-card {cls}"><p class="kpi-num">{val}</p><p class="kpi-label">{label}</p></div>', unsafe_allow_html=True)

    # ── SECCIÓN 2: OTs ───────────────────────────────────────────────────────
    st.markdown('<p class="section-title">🛠️ ÓRDENES DE TRABAJO</p>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    cards_ot = [
        (c1, ot_total, "Total OTs",    "card-blue"),
        (c2, ot_prog,  "Programadas",  "card-purple"),
        (c3, ot_ejec,  "En Ejecución", "card-orange"),
        (c4, ot_fin,   "Finalizadas",  "card-green"),
        (c5, con_act,  "Contratos Activos", "card-teal"),
    ]
    for col, val, label, cls in cards_ot:
        col.markdown(f'<div class="kpi-card {cls}"><p class="kpi-num">{val}</p><p class="kpi-label">{label}</p></div>', unsafe_allow_html=True)

    # ── SECCIÓN 3: FINANZAS ───────────────────────────────────────────────────
    st.markdown(f'<p class="section-title">💰 FINANZAS — {hoy_dash.strftime("%B %Y").upper()}</p>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    fin_cards = [
        (c1, f"${venta_mes:,.0f}", f"Ventas {hoy_dash.strftime('%b')}", "card-blue"),
        (c2, f"${util_mes:,.0f}",  f"Utilidad {hoy_dash.strftime('%b')}", "card-green"),
        (c3, f"${venta_tot:,.0f}", "Ventas Acumuladas",   "card-indigo"),
        (c4, f"${util_tot:,.0f}",  f"Utilidad ({margen:.1f}% margen)", "card-teal"),
    ]
    for col, val, label, cls in fin_cards:
        col.markdown(f'<div class="kpi-card {cls}"><p class="kpi-num" style="font-size:1.6rem">{val}</p><p class="kpi-label">{label}</p></div>', unsafe_allow_html=True)

    st.divider()

    # ── SECCIÓN 5: GRÁFICAS PLOTLY ────────────────────────────────────────────
    st.markdown('<p class="section-title">📊 ANÁLISIS VISUAL</p>', unsafe_allow_html=True)

    ROJO   = "#dc2626"
    AZUL   = "#1e3a8a"
    VERDE  = "#064e3b"
    COLORES_GRAF = [ROJO,"#1e3a8a","#064e3b","#7c3aed","#ea580c","#0d9488","#d97706","#db2777"]

    def graf_bar(df_g, x, y, title, color=None, horizontal=False, colores=None):
        if df_g is None or df_g.empty: return
        ori = "h" if horizontal else "v"
        xx, yy = (y, x) if horizontal else (x, y)
        fig = px.bar(df_g, x=xx, y=yy, orientation=ori, title=title,
                     color=color, color_discrete_sequence=colores or [ROJO],
                     text=yy if horizontal else xx)
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, plot_bgcolor="white",
                          paper_bgcolor="white", font_color="#111",
                          title_font_color=ROJO, margin=dict(t=40,b=20,l=20,r=20))
        st.plotly_chart(fig, use_container_width=True)

    def graf_dona(df_g, names, values, title, colores_map=None):
        if df_g is None or df_g.empty: return
        kw = {"color": names, "color_discrete_map": colores_map} if colores_map else \
             {"color_discrete_sequence": COLORES_GRAF}
        fig = px.pie(df_g, names=names, values=values, title=title, hole=0.45, **kw)
        fig.update_layout(font_color="#111", title_font_color=ROJO,
                          paper_bgcolor="white", margin=dict(t=40,b=20,l=20,r=20))
        st.plotly_chart(fig, use_container_width=True)

    # ── FILA 1 ────────────────────────────────────────────────────────────────
    r1c1, r1c2, r1c3 = st.columns(3)

    with r1c1:  # Solicitudes por mes
        if not df.empty:
            try:
                df_t = df.copy()
                df_t["Mes"] = pd.to_datetime(df_t["Fecha"], errors="coerce").dt.strftime("%Y-%m")
                m = df_t.groupby("Mes").size().reset_index(name="N").sort_values("Mes")
                graf_bar(m, "Mes", "N", "📅 Solicitudes por mes")
            except Exception: pass

    with r1c2:  # Solicitudes por servicio
        if not df.empty:
            s = df["Servicio"].value_counts().reset_index()
            s.columns = ["Servicio","N"]
            graf_bar(s, "N", "Servicio", "🔧 Por servicio", horizontal=True,
                     colores=COLORES_GRAF)

    with r1c3:  # Estado solicitudes
        if not df.empty:
            e = df["Estado"].value_counts().reset_index()
            e.columns = ["Estado","N"]
            graf_dona(e, "Estado", "N", "📋 Estado solicitudes",
                      colores_map={"Pendiente":"#d97706","Aprobado":"#1e3a8a",
                                   "Completado":"#064e3b","Cancelado":ROJO})

    # ── FILA 2 ────────────────────────────────────────────────────────────────
    r2c1, r2c2, r2c3 = st.columns(3)

    with r2c1:  # Canal comunicación
        if not df.empty:
            c = df["Canal"].value_counts().reset_index()
            c.columns = ["Canal","N"]
            graf_dona(c, "Canal", "N", "📱 Canal de comunicación")

    with r2c2:  # OTs por estado
        if not ots.empty:
            o = ots["Estado"].value_counts().reset_index()
            o.columns = ["Estado","N"]
            graf_dona(o, "Estado", "N", "🛠️ OTs por estado",
                      colores_map={"Programada":"#7c3aed","En ejecución":"#ea580c",
                                   "Finalizada":VERDE,"Cancelada":ROJO})

    with r2c3:  # OTs por técnico
        if not ots.empty:
            t = ots[ots["Tecnico"].str.strip() != ""]["Tecnico"].value_counts().head(6).reset_index()
            t.columns = ["Técnico","OTs"]
            graf_bar(t, "OTs", "Técnico", "👷 OTs por técnico",
                     horizontal=True, colores=[AZUL])

    # ── FILA 3 ────────────────────────────────────────────────────────────────
    r3c1, r3c2, r3c3 = st.columns(3)

    with r3c1:  # Top clientes
        if not df.empty:
            cli_t = df["Cliente"].value_counts().head(6).reset_index()
            cli_t.columns = ["Cliente","N"]
            graf_bar(cli_t, "N", "Cliente", "🏆 Top clientes",
                     horizontal=True, colores=[ROJO])

    with r3c2:  # Ventas vs Costos
        try:
            if not ventas.empty:
                v_m = ventas.copy()
                v_m["Mes"] = pd.to_datetime(v_m["Fecha_Facturacion"], errors="coerce").dt.strftime("%Y-%m")
                v_m["V"]   = v_m["Valor_Antes_IVA"].apply(to_num)
                v_a = v_m.groupby("Mes")["V"].sum().reset_index()
                fin = v_a.rename(columns={"V":"Ventas"})
                if not costos.empty:
                    c_m = costos.copy()
                    c_m["Mes"] = pd.to_datetime(c_m["Fecha"], errors="coerce").dt.strftime("%Y-%m")
                    c_m["C"]   = c_m["Total_Costo"].apply(to_num)
                    c_a = c_m.groupby("Mes")["C"].sum().reset_index().rename(columns={"C":"Costos"})
                    fin = fin.merge(c_a, on="Mes", how="outer").fillna(0)
                fin = fin.sort_values("Mes")
                fig = go.Figure()
                fig.add_trace(go.Bar(name="Ventas", x=fin["Mes"], y=fin["Ventas"], marker_color=AZUL))
                if "Costos" in fin.columns:
                    fig.add_trace(go.Bar(name="Costos", x=fin["Mes"], y=fin["Costos"], marker_color=ROJO))
                fig.update_layout(title="💰 Ventas vs Costos", barmode="group",
                                  plot_bgcolor="white", paper_bgcolor="white",
                                  font_color="#111", title_font_color=ROJO,
                                  margin=dict(t=40,b=20,l=20,r=20))
                st.plotly_chart(fig, use_container_width=True)
        except Exception: pass

    with r3c3:  # SLA
        if not df.empty and "SLA" in df.columns:
            sl = df["SLA"].value_counts().reset_index()
            sl.columns = ["SLA","N"]
            graf_dona(sl, "SLA", "N", "⏱️ Distribución SLA",
                      colores_map={"Programado":VERDE,"Urgencia":"#d97706","Emergencia":ROJO})

    st.divider()

    # ── SECCIÓN 6: GESTIÓN POR USUARIO ───────────────────────────────────────
    if not df.empty and "Creado_Por" in df.columns:
        st.markdown('<p class="section-title">👤 GESTIÓN POR USUARIO</p>', unsafe_allow_html=True)
        mes_act = ahora_colombia().strftime("%Y-%m")
        df_mes  = df[df["Fecha"].str.startswith(mes_act, na=False)] if "Fecha" in df.columns else df
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Solicitudes creadas este mes por usuario**")
            if not df_mes.empty and df_mes["Creado_Por"].str.strip().any():
                graf_bar(
                    df_mes[df_mes["Creado_Por"].str.strip() != ""]["Creado_Por"].value_counts().reset_index().rename(columns={"Creado_Por":"Usuario","count":"Solicitudes"}),
                    "Solicitudes","Usuario","📋 Solicitudes por usuario",
                    horizontal=True, colores=["#dc2626","#1e3a8a"]
                )
        with c2:
            if not ots.empty and "Creado_Por" in ots.columns:
                st.markdown("**OTs creadas este mes por usuario**")
                ots_mes = ots[ots["Fecha_Creacion"].str.startswith(mes_act, na=False)] if "Fecha_Creacion" in ots.columns else ots
                if not ots_mes.empty and ots_mes["Creado_Por"].str.strip().any():
                    graf_bar(
                        ots_mes[ots_mes["Creado_Por"].str.strip() != ""]["Creado_Por"].value_counts().reset_index().rename(columns={"Creado_Por":"Usuario","count":"OTs"}),
                        "OTs","Usuario","🛠️ OTs por usuario",
                        horizontal=True, colores=["#7c3aed","#064e3b"]
                    )
        st.divider()

    # ── SECCIÓN 7: ACTIVIDAD RECIENTE ─────────────────────────────────────────
    st.markdown('<p class="section-title">🕐 ACTIVIDAD RECIENTE</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Últimas 5 solicitudes**")
        if not df.empty:
            tabla_html(df.sort_values("Fecha", ascending=False).head(5)
                       [["ID","Fecha","Cliente","Servicio","Estado"]].reset_index(drop=True),
                       color_col="Estado",
                       colores_estado={"Pendiente":("#fff3cd","#7d5a00"),
                                       "Aprobado":("#d1e7dd","#0a5c36"),
                                       "Completado":("#cfe2ff","#0a3678"),
                                       "Cancelado":("#f8d7da","#7f1d1d")})
        else:
            st.info("Sin solicitudes")
    with c2:
        st.markdown("**Últimas 5 OTs**")
        if not ots.empty:
            tabla_html(ots.sort_values("Fecha_Creacion", ascending=False).head(5)
                       [["ID","Fecha_Creacion","Cliente","Servicio","Estado"]].reset_index(drop=True),
                       color_col="Estado",
                       colores_estado={"Programada":("#e0e7ff","#1e3a8a"),
                                       "En ejecución":("#fef3c7","#78350f"),
                                       "Finalizada":("#d1fae5","#064e3b"),
                                       "Cancelada":("#fee2e2","#7f1d1d")})
        else:
            st.info("Sin OTs")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: CLIENTES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "clientes":
    if st.session_state.get("user_rol") == "tecnico":
        st.warning("⛔ No tienes permiso para acceder a esta sección.")
        st.stop()
    cli = get_cli()
    st.subheader("Registro de Empresas y Sedes")
    st.caption("Agrega aquí las empresas. Al crear solicitudes, sus datos se llenarán solos.")

    # ── IMPORTAR DESDE EXCEL ──────────────────────────────────────────────────
    with st.expander("📂 Importar clientes desde Excel", expanded=False):
        st.caption("Sube tu archivo Excel. Luego dinos qué columna corresponde a cada campo.")
        archivo = st.file_uploader("Selecciona el archivo Excel (.xlsx)", type=["xlsx", "xls"], key="upload_cli")

        if archivo:
            try:
                df_excel = pd.read_excel(archivo, dtype=str).fillna("")
                st.write("**Vista previa del archivo:**")
                st.dataframe(df_excel.head(5), use_container_width=True)

                cols_excel = ["(dejar vacío)"] + list(df_excel.columns)
                st.markdown("**Indica qué columna del Excel corresponde a cada campo:**")

                c1, c2 = st.columns(2)
                with c1:
                    m_empresa  = st.selectbox("Nombre de la empresa",  cols_excel, key="m_empresa")
                    m_nit      = st.selectbox("NIT",                    cols_excel, key="m_nit")
                    m_dir_emp  = st.selectbox("Dirección empresa",      cols_excel, key="m_dir_emp")
                    m_sede     = st.selectbox("Sede / Sucursal",        cols_excel, key="m_sede")
                with c2:
                    m_dir_sede = st.selectbox("Dirección sede",         cols_excel, key="m_dir_sede")
                    m_nom_c    = st.selectbox("Nombre contacto",        cols_excel, key="m_nom_c")
                    m_cor_c    = st.selectbox("Correo contacto",        cols_excel, key="m_cor_c")
                    m_cel_c    = st.selectbox("Celular contacto",       cols_excel, key="m_cel_c")

                def get_col(df, col_name):
                    if col_name == "(dejar vacío)":
                        return ""
                    return df[col_name] if col_name in df.columns else ""

                if st.button("⬆️ Importar clientes", type="primary"):
                    nuevos = pd.DataFrame({
                        "Empresa":           get_col(df_excel, m_empresa),
                        "NIT":               get_col(df_excel, m_nit),
                        "Direccion_Empresa": get_col(df_excel, m_dir_emp),
                        "Sede":              get_col(df_excel, m_sede),
                        "Direccion_Sede":    get_col(df_excel, m_dir_sede),
                        "Nombre_Contacto":   get_col(df_excel, m_nom_c),
                        "Correo_Contacto":   get_col(df_excel, m_cor_c),
                        "Celular_Contacto":  get_col(df_excel, m_cel_c),
                    })
                    # Omitir filas sin nombre de empresa
                    nuevos = nuevos[nuevos["Empresa"].str.strip() != ""]
                    cli = pd.concat([cli, nuevos], ignore_index=True)
                    save_cli(cli)
                    st.success(f"✅ {len(nuevos)} cliente(s) importados correctamente.")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")

    st.divider()
    st.subheader("Agregar empresa manualmente")
    with st.form("form_cliente", clear_on_submit=True):
        st.markdown("**Datos de la empresa**")
        c1, c2 = st.columns(2)
        with c1:
            emp_nombre  = st.text_input("Nombre de la empresa *")
            emp_nit     = st.text_input("NIT")
        with c2:
            emp_dir     = st.text_input("Dirección de la empresa")

        st.markdown("**Sede / Sucursal**")
        c1, c2 = st.columns(2)
        with c1:
            emp_sede    = st.text_input("Nombre de la sede")
        with c2:
            emp_dir_s   = st.text_input("Dirección de la sede")

        st.markdown("**Contacto de esta sede**")
        c1, c2, c3 = st.columns(3)
        with c1:
            emp_nom_c   = st.text_input("Nombre del contacto")
        with c2:
            emp_cor_c   = st.text_input("Correo del contacto")
        with c3:
            emp_cel_c   = st.text_input("Celular del contacto")

        agregar = st.form_submit_button("➕ Agregar empresa / sede", type="primary", use_container_width=True)

        if agregar:
            if not emp_nombre.strip():
                st.error("El nombre de la empresa es obligatorio.")
            else:
                nueva_cli = {
                    "Empresa":           emp_nombre.strip(),
                    "NIT":               emp_nit.strip(),
                    "Direccion_Empresa": emp_dir.strip(),
                    "Sede":              emp_sede.strip(),
                    "Direccion_Sede":    emp_dir_s.strip(),
                    "Nombre_Contacto":   emp_nom_c.strip(),
                    "Correo_Contacto":   emp_cor_c.strip(),
                    "Celular_Contacto":  emp_cel_c.strip(),
                }
                cli = pd.concat([cli, pd.DataFrame([nueva_cli])], ignore_index=True)
                save_cli(cli)
                st.success(f"✅ {emp_nombre} — sede '{emp_sede}' registrada.")

    st.divider()

    if not cli.empty:
        st.subheader("Empresas registradas")

        # ── Acciones rápidas ──────────────────────────────────────────────
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🧹 Eliminar duplicados", use_container_width=True, help="Borra filas repetidas automáticamente"):
                antes = len(cli)
                cli = cli.drop_duplicates().reset_index(drop=True)
                save_cli(cli)
                st.success(f"Se eliminaron {antes - len(cli)} duplicado(s). Quedaron {len(cli)} registros.")
                st.rerun()
        with c2:
            if st.button("🗑️ BORRAR TODO", use_container_width=True, type="secondary"):
                st.session_state["confirmar_borrar_todo"] = True

        if st.session_state.get("confirmar_borrar_todo"):
            st.warning("⚠️ ¿Seguro que quieres borrar TODAS las empresas? Esta acción no se puede deshacer.")
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("✅ Sí, borrar todo", type="primary", use_container_width=True):
                    cli = pd.DataFrame(columns=COLS_CLI)
                    save_cli(cli)
                    st.session_state["confirmar_borrar_todo"] = False
                    st.success("Todas las empresas fueron eliminadas.")
                    st.rerun()
            with cc2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state["confirmar_borrar_todo"] = False
                    st.rerun()

        st.divider()

        buscar_cli = st.text_input("🔍 Buscar empresa", key="buscar_cli")
        vista_cli  = cli if not buscar_cli else cli[cli["Empresa"].str.contains(buscar_cli, case=False, na=False)]

        # Resumen por empresa
        resumen_emp = (vista_cli.groupby("Empresa")
                       .agg(NIT=("NIT","first"), Sedes=("Sede","count"))
                       .reset_index())
        tabla_html(resumen_emp.reset_index(drop=True))
        st.caption(f"{len(resumen_emp)} empresa(s) — {len(vista_cli)} sede(s) en total")

        st.divider()

        # ── Ver sedes y editar ────────────────────────────────────────────
        st.subheader("🏢 Ver sedes y editar cliente")
        empresas_lista = sorted(cli["Empresa"].unique().tolist())
        emp_sel = st.selectbox("Selecciona la empresa", empresas_lista, key="emp_sel_edit")

        if emp_sel:
            sedes_emp = cli[cli["Empresa"].str.strip().str.lower() == emp_sel.strip().lower()].copy()
            st.markdown(f"**{len(sedes_emp)} sede(s) registradas para {emp_sel}:**")
            tabla_html(sedes_emp[["Sede","Direccion_Sede","Nombre_Contacto",
                                   "Correo_Contacto","Celular_Contacto"]].reset_index(drop=True))

            st.markdown("**✏️ Editar sede**")
            sedes_lista = sedes_emp["Sede"].tolist()
            sede_sel_edit = st.selectbox("Selecciona la sede a editar", sedes_lista, key="sede_sel_edit")

            if sede_sel_edit:
                idx_sede = sedes_emp[sedes_emp["Sede"] == sede_sel_edit].index[0]
                fs = cli.loc[idx_sede]

                with st.form("form_editar_cliente"):
                    st.markdown("**Datos de la empresa**")
                    c1, c2 = st.columns(2)
                    with c1:
                        ee_empresa = st.text_input("Nombre empresa",    value=fs.get("Empresa",""))
                        ee_nit     = st.text_input("NIT",               value=fs.get("NIT",""))
                    with c2:
                        ee_dir_emp = st.text_input("Dirección empresa", value=fs.get("Direccion_Empresa",""))

                    st.markdown("**Datos de la sede**")
                    c1, c2 = st.columns(2)
                    with c1:
                        ee_sede  = st.text_input("Nombre sede",     value=fs.get("Sede",""))
                    with c2:
                        ee_dir_s = st.text_input("Dirección sede",  value=fs.get("Direccion_Sede",""))

                    st.markdown("**Contacto**")
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        ee_nom_c = st.text_input("Nombre contacto",  value=fs.get("Nombre_Contacto",""))
                    with c2:
                        ee_cor_c = st.text_input("Correo contacto",  value=fs.get("Correo_Contacto",""))
                    with c3:
                        ee_cel_c = st.text_input("Celular contacto", value=fs.get("Celular_Contacto",""))

                    c_grd, c_eli = st.columns(2)
                    with c_grd:
                        guardar_edit = st.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True)
                    with c_eli:
                        eliminar_sede = st.form_submit_button("🗑️ Eliminar esta sede", use_container_width=True)

                    if guardar_edit:
                        cli.loc[idx_sede, "Empresa"]           = ee_empresa.strip()
                        cli.loc[idx_sede, "NIT"]               = ee_nit.strip()
                        cli.loc[idx_sede, "Direccion_Empresa"] = ee_dir_emp.strip()
                        cli.loc[idx_sede, "Sede"]              = ee_sede.strip()
                        cli.loc[idx_sede, "Direccion_Sede"]    = ee_dir_s.strip()
                        cli.loc[idx_sede, "Nombre_Contacto"]   = ee_nom_c.strip()
                        cli.loc[idx_sede, "Correo_Contacto"]   = ee_cor_c.strip()
                        cli.loc[idx_sede, "Celular_Contacto"]  = ee_cel_c.strip()
                        save_cli(cli)
                        st.success(f"✅ Sede **{sede_sel_edit}** actualizada.")
                        st.rerun()

                    if eliminar_sede:
                        cli = cli.drop(index=idx_sede).reset_index(drop=True)
                        save_cli(cli)
                        st.success(f"✅ Sede **{sede_sel_edit}** eliminada.")
                        st.rerun()

            # Agregar nueva sede a esta empresa
            st.divider()
            with st.expander("➕ Agregar nueva sede a esta empresa"):
                with st.form("form_nueva_sede"):
                    c1, c2 = st.columns(2)
                    with c1:
                        ns_sede  = st.text_input("Nombre de la sede *")
                        ns_dir   = st.text_input("Dirección de la sede")
                        ns_nom_c = st.text_input("Nombre contacto")
                    with c2:
                        ns_cor_c = st.text_input("Correo contacto")
                        ns_cel_c = st.text_input("Celular contacto")
                    if st.form_submit_button("➕ Agregar sede", type="primary", use_container_width=True):
                        if not ns_sede.strip():
                            st.error("El nombre de la sede es obligatorio.")
                        else:
                            fila_ref = cli[cli["Empresa"].str.strip().str.lower() == emp_sel.strip().lower()].iloc[0]
                            nueva_sede = {
                                "Empresa":           emp_sel,
                                "NIT":               fila_ref.get("NIT",""),
                                "Direccion_Empresa": fila_ref.get("Direccion_Empresa",""),
                                "Sede":              ns_sede.strip(),
                                "Direccion_Sede":    ns_dir.strip(),
                                "Nombre_Contacto":   ns_nom_c.strip(),
                                "Correo_Contacto":   ns_cor_c.strip(),
                                "Celular_Contacto":  ns_cel_c.strip(),
                            }
                            cli = pd.concat([cli, pd.DataFrame([nueva_sede])], ignore_index=True)
                            save_cli(cli)
                            st.success(f"✅ Sede **{ns_sede}** agregada a {emp_sel}.")
                            st.rerun()
    else:
        st.info("Aún no hay empresas registradas.")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: ÓRDENES DE TRABAJO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "ots":
    import io
    df = get_df(); ots = get_ots(); cli = get_cli(); equipos = get_equipos()
    _rol_ots     = st.session_state.get("user_rol", "usuario")
    _nom_tec_ots = st.session_state.get("user_nombre", "")
    # _tec_en_reporte: técnico abrió el formulario de reporte → mostrar vista completa
    _es_tec_ots  = _rol_ots == "tecnico" and not st.session_state.get("_tec_en_reporte")

    c_tit_ot, c_ref_ot = st.columns([5,1])
    c_tit_ot.subheader("🛠️ Mis OTs" if _es_tec_ots else "🛠️ Órdenes de Trabajo")
    if c_ref_ot.button("🔄 Actualizar", use_container_width=True, key="ref_ots"):
        _invalidar_cache("ordenes_trabajo")
        st.rerun()

    # Mantener selección después de guardar reporte
    if st.session_state.get("_ot_volver_ver"):
        st.session_state["accion_ot_radio"] = "📋 Ver OTs"
        st.session_state.pop("_ot_volver_ver", None)

    if _es_tec_ots:
        accion_ot = "📋 Ver OTs"
        # Filtrar OTs por técnico
        if not ots.empty and "Tecnico" in ots.columns:
            ots = ots[ots["Tecnico"].str.strip().str.lower() == _nom_tec_ots.strip().lower()].copy()
    elif _rol_ots == "tecnico":
        # Técnico en modo reporte: solo ver OTs, sin crear
        accion_ot = "📋 Ver OTs"
    else:
        accion_ot = st.radio("", ["➕ Nueva OT", "📋 Ver OTs"], horizontal=True,
                             label_visibility="collapsed", key="accion_ot_radio")
    st.divider()

    # ── NUEVA OT ──────────────────────────────────────────────────────────────
    if accion_ot == "➕ Nueva OT":
        st.markdown("### 🏢 1. Información de la Empresa")

        empresas_ot = sorted(cli["Empresa"].unique().tolist()) if not cli.empty else []
        opcion_manual_ot = "✏️  Empresa no registrada (ingresar manualmente)"
        opciones_ot = empresas_ot + [opcion_manual_ot]

        emp_ant_ot = st.session_state.get("_emp_ant_ot", None)
        empresa_ot = st.selectbox(
            "Nombre de la empresa * (escribe para buscar)",
            opciones_ot, index=None,
            placeholder="Escribe el nombre de la empresa...",
            key="empresa_ot",
        )
        if empresa_ot != emp_ant_ot:
            st.session_state["_emp_ant_ot"] = empresa_ot
            if "sede_ot" in st.session_state:
                del st.session_state["sede_ot"]
            st.rerun()

        nit_ot = sede_ot_v = dir_sede_ot = nom_c_ot = cel_c_ot = ""
        empresa_final_ot = ""

        if empresa_ot and empresa_ot != opcion_manual_ot:
            empresa_final_ot = empresa_ot
            filas_ot = cli[cli["Empresa"].str.strip().str.lower() == empresa_ot.strip().lower()]

            if not filas_ot.empty:
                primera_ot = filas_ot.iloc[0]
                nit_ot = primera_ot["NIT"]

                st.text_input("NIT", value=nit_ot, disabled=True, key="nit_ot_dis")

                sedes_ot = filas_ot["Sede"].tolist()
                sede_ot_sel = st.selectbox("Sede / Sucursal", sedes_ot, key="sede_ot")

                fila_s_ot = filas_ot[filas_ot["Sede"] == sede_ot_sel]
                if not fila_s_ot.empty:
                    fs = fila_s_ot.iloc[0]
                    sede_ot_v  = sede_ot_sel
                    nom_c_ot   = fs["Nombre_Contacto"]
                    cel_c_ot   = fs["Celular_Contacto"]

                c1, c2 = st.columns(2)
                with c1:
                    st.text_input("Nombre contacto", value=nom_c_ot, disabled=True, key="nc_ot_dis")
                with c2:
                    st.text_input("Celular contacto", value=cel_c_ot, disabled=True, key="cel_ot_dis")

                # ── Equipos registrados en esta sede ──────────────────────
                if not equipos.empty and sede_ot_v:
                    _eq_sede_ot = equipos[
                        (equipos["Cliente"].str.strip().str.lower() == empresa_ot.strip().lower()) &
                        (equipos["Sede"].str.strip().str.lower() == sede_ot_v.strip().lower())
                    ]
                    if not _eq_sede_ot.empty:
                        st.markdown("**🔧 Equipos en esta sede:**")
                        _cols_eq_ot = [c for c in ["ID_Item","Servicio","Marca","Modelo",
                                                    "Numero_Serie","Ubicacion","Ultimo_Mantenimiento"]
                                       if c in _eq_sede_ot.columns]
                        for _srv in SERVICIOS_CON_EQUIPOS:
                            _eq_srv_ot = _eq_sede_ot[_eq_sede_ot["Servicio"] == _srv]
                            if not _eq_srv_ot.empty:
                                with st.expander(f"🔧 {_srv} — {len(_eq_srv_ot)} equipo(s)"):
                                    tabla_html(_eq_srv_ot[_cols_eq_ot].reset_index(drop=True))
            else:
                st.warning(f"No se encontraron datos para '{empresa_ot}'.")

        elif empresa_ot == opcion_manual_ot:
            c1, c2 = st.columns(2)
            with c1:
                empresa_final_ot = st.text_input("Nombre de la empresa *", key="emp_ot_man")
                nit_ot           = st.text_input("NIT", key="nit_ot_man")
            with c2:
                sede_ot_v = st.text_input("Sede / Sucursal", key="sede_ot_man")
            c1, c2 = st.columns(2)
            with c1:
                nom_c_ot = st.text_input("Nombre contacto", key="nc_ot_man")
            with c2:
                cel_c_ot = st.text_input("Celular contacto", key="cel_ot_man")

        st.divider()
        st.markdown("### 🔧 2. Detalle del Trabajo")

        # Selector de equipo reactivo ANTES del form
        ot_equipo_id   = ""
        ot_equipo_desc = ""
        equipos_ot     = get_equipos()

        # Mostrar selector solo si hay cliente/sede y el servicio es Aires
        if empresa_final_ot and not equipos_ot.empty:
            eq_sede = equipos_ot[
                (equipos_ot["Cliente"].str.strip().str.lower() == empresa_final_ot.strip().lower()) &
                (equipos_ot["Servicio"] == "Aires Acondicionados")
            ]
            if not eq_sede.empty:
                # Filtrar por sede si está seleccionada
                if sede_ot_v and sede_ot_v.strip():
                    eq_sede = eq_sede[eq_sede["Sede"].str.strip().str.lower() == sede_ot_v.strip().lower()]
                if not eq_sede.empty:
                    st.markdown("### ❄️ Equipo de Aire Acondicionado")
                    opciones_eq = ["Sin vincular a equipo específico"] + [
                        f"{r['ID_Item']} — {r['Marca']} {r['Modelo']} | {r['Ubicacion'][:40]}"
                        for _, r in eq_sede.iterrows()
                    ]
                    eq_sel = st.selectbox("Selecciona el equipo afectado", opciones_eq, key="ot_eq_sel")
                    if eq_sel != "Sin vincular a equipo específico":
                        ot_equipo_id   = eq_sel.split(" — ")[0]
                        eq_row         = eq_sede[eq_sede["ID_Item"] == ot_equipo_id].iloc[0]
                        ot_equipo_desc = f"{eq_row['Marca']} {eq_row['Modelo']} — Serial: {eq_row['Numero_Serie']} — {eq_row['Especificaciones']}"
                        st.info(f"**Equipo:** {ot_equipo_desc}")

        st.divider()
        st.markdown("### 🔧 Detalle del Trabajo")

        with st.form("form_nueva_ot", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                ot_servicio  = st.selectbox("Servicio", SERVICIOS)
                ot_desc      = st.text_area("Descripción del trabajo")
                ot_tecnico   = st.text_input("Técnico asignado")
                ot_cel_tec   = st.text_input("📱 Celular del técnico", placeholder="Ej: 3001234567")
            with c2:
                ot_fecha      = st.date_input("Fecha de ejecución", value=ahora_colombia().date())
                ot_hora_ini   = st.selectbox("Hora de inicio", HORAS_12, index=16)  # 08:00 AM
                ot_hora_fin   = st.selectbox("Hora final",     HORAS_12, index=32)  # 04:00 PM
                ot_estado     = st.selectbox("Estado", ESTADOS_OT)
                ot_valor      = st.text_input("Valor del servicio (COP)", placeholder="Ej: 250000")

            ot_materiales  = st.text_area("Materiales / Repuestos utilizados")
            ot_obs         = st.text_area("Observaciones")

            guardar_ot = st.form_submit_button("💾 Guardar OT", type="primary", use_container_width=True)

            if guardar_ot:
                if not empresa_final_ot:
                    st.error("Selecciona o ingresa el nombre de la empresa.")
                else:
                    nueva_ot = {
                        "ID":              generate_ot_id(ots),
                        "Origen":          "Manual",
                        "Creado_Por":      st.session_state.get("user_nombre",""),
                        "SOL_Ref":         "",
                        "Fecha_Creacion":  ahora_colombia().strftime("%Y-%m-%d %H:%M"),
                        "Cliente":         empresa_final_ot,
                        "NIT":             nit_ot,
                        "Sede":            sede_ot_v,
                        "Nombre_Contacto": nom_c_ot,
                        "Celular_Contacto": cel_c_ot,
                        "Servicio":        ot_servicio,
                        "Descripcion":     ot_desc.strip(),
                        "Tecnico":         ot_tecnico.strip(),
                        "Celular_Tecnico": ot_cel_tec.strip(),
                        "Fecha_Ejecucion": ot_fecha.strftime("%Y-%m-%d"),
                        "Hora_Inicio":     ot_hora_ini,
                        "Hora_Final":      ot_hora_fin,
                        "Horas_Laboradas": calcular_horas(ot_hora_ini, ot_hora_fin),
                        "Materiales":      ot_materiales.strip(),
                        "Valor_COP":       ot_valor.strip(),
                        "Estado":          ot_estado,
                        "Observaciones":   (f"Equipo: {ot_equipo_id} — {ot_equipo_desc}\n" if ot_equipo_id else "") + ot_obs.strip(),
                    }
                    # Actualizar último/próximo mantenimiento si se vinculó un equipo
                    if ot_equipo_id and not equipos_ot.empty:
                        idx_eq = equipos_ot[equipos_ot["ID_Item"] == ot_equipo_id].index
                        if len(idx_eq) > 0:
                            freq_eq = contratos[contratos["ID_Contrato"] == equipos_ot.loc[idx_eq[0],"ID_Contrato"]]["Frecuencia"].values
                            freq    = freq_eq[0] if len(freq_eq) > 0 else "Mensual"
                            equipos_ot.loc[idx_eq[0], "Ultimo_Mantenimiento"]  = ahora_colombia().strftime("%Y-%m-%d")
                            equipos_ot.loc[idx_eq[0], "Proximo_Mantenimiento"] = proxima_fecha(ahora_colombia().strftime("%Y-%m-%d"), freq)
                            save_equipos(equipos_ot)
                    ots = pd.concat([ots, pd.DataFrame([nueva_ot])], ignore_index=True)
                    save_ots(ots)
                    msg_ot = f"✅ OT **{nueva_ot['ID']}** guardada para {empresa_final_ot}."
                    if ot_equipo_id:
                        msg_ot += f" Vinculada al equipo **{ot_equipo_id}**."
                    st.success(msg_ot)

    # ── VER OTs ───────────────────────────────────────────────────────────────
    else:
        if ots.empty:
            st.info("Aún no hay órdenes de trabajo registradas.")

        # ── VISTA ESPECIAL TÉCNICO ────────────────────────────────────────────
        elif _es_tec_ots:
            ots_activas = ots[~ots["Estado"].isin(["Finalizada", "En revisión", "Cancelada"])].copy()
            ots_todas   = ots.copy()

            # Clasificar por urgencia según fecha límite
            def _urgencia(fl_str):
                try:
                    fl = datetime.strptime(fl_str, "%Y-%m-%d %H:%M")
                    h  = (fl - ahora_colombia()).total_seconds() / 3600
                    if h < 0:    return 0   # vencida
                    elif h <= 24: return 1  # próxima
                    else:         return 2  # ok
                except Exception:
                    return 2

            ots_activas["_urg"] = ots_activas["Fecha_Limite"].apply(_urgencia)
            ots_activas = ots_activas.sort_values("_urg")

            # Encabezado
            st.markdown("""
            <div style='background:#dc2626;color:#fff;padding:9px 16px;
                        border-radius:8px 8px 0 0;font-weight:700;font-size:0.95rem;
                        margin-bottom:0'>
              ⚠&nbsp;&nbsp;OTs que requieren atención
            </div>
            <div style='display:flex;background:#b91c1c;color:#fca5a5;
                        padding:5px 16px;font-size:0.76rem;font-weight:700;
                        gap:0;border-bottom:2px solid #dc2626'>
              <span style='flex:0 0 18px'></span>
              <span style='flex:1 1 120px;padding-left:4px'>ID</span>
              <span style='flex:1 1 130px'>Vencimiento</span>
              <span style='flex:1 1 150px'>Cliente</span>
              <span style='flex:1 1 150px'>Sede</span>
              <span style='flex:1 1 130px'>Servicio</span>
              <span style='flex:0 0 95px;text-align:center'>Acción</span>
            </div>
            """, unsafe_allow_html=True)

            # Filas
            _tec_ot_sel = st.session_state.get("tec_ot_sel", None)
            for _, row in ots_activas.iterrows():
                urg = row["_urg"]
                if urg == 0:
                    dot, bg, brd = "#dc2626", "#fff5f5", "#dc2626"
                elif urg == 1:
                    dot, bg, brd = "#f59e0b", "#fffbeb", "#f59e0b"
                else:
                    dot, bg, brd = "#9ca3af", "#ffffff", "#e5e7eb"

                cli_txt  = str(row.get("Cliente", ""))[:20]
                sede_txt = str(row.get("Sede", ""))[:20]
                srv_txt  = str(row.get("Servicio", ""))[:16]
                fl_txt   = str(row.get("Fecha_Limite", ""))

                c_row, c_btn = st.columns([6, 1])
                with c_row:
                    st.markdown(f"""
                    <div style='background:{bg};border:1px solid {brd};
                                border-left:5px solid {brd};padding:9px 14px;
                                display:flex;align-items:center;gap:10px;margin:2px 0;
                                border-radius:0 4px 4px 0'>
                      <span style='color:{dot};font-size:1.1rem;flex:0 0 14px'>●</span>
                      <span style='font-weight:700;font-size:0.83rem;flex:1 1 120px;color:#111'>{row['ID']}</span>
                      <span style='font-size:0.81rem;flex:1 1 130px;color:#555'>{fl_txt}</span>
                      <span style='font-size:0.81rem;flex:1 1 150px;color:#333'>{cli_txt}</span>
                      <span style='font-size:0.81rem;flex:1 1 150px;color:#333;font-weight:600'>{sede_txt}</span>
                      <span style='font-size:0.81rem;flex:1 1 130px;color:#333'>{srv_txt}</span>
                    </div>""", unsafe_allow_html=True)
                with c_btn:
                    if st.button("→ Ver OT", key=f"vtec_{row['ID']}",
                                 use_container_width=True):
                        st.session_state["_tec_en_reporte"] = True
                        st.session_state["_tec_viewing_ot"] = row["ID"]
                        st.rerun()

            # OTs entregadas (En revisión, Finalizada, Cancelada)
            ots_fin = ots_todas[ots_todas["Estado"].isin(["En revisión", "Finalizada", "Cancelada"])]
            if not ots_fin.empty:
                with st.expander(f"📁 Historial ({len(ots_fin)} OTs entregadas / finalizadas)"):
                    tabla_html(ots_fin[["ID","Fecha_Creacion","Cliente","Servicio","Estado","Fecha_Ejecucion"]].reset_index(drop=True))

            # Detalle de la OT seleccionada
            if _tec_ot_sel and _tec_ot_sel in ots["ID"].values:
                st.divider()
                fila_ot = ots[ots["ID"] == _tec_ot_sel].iloc[0]
                st.markdown(f"### 📋 {_tec_ot_sel} — {fila_ot.get('Cliente','')}")

                tab_act, tab_rep = st.tabs(["📋 Actualizar", "📄 Reportar"])

                with tab_act:
                    d1, d2 = st.columns(2)
                    with d1:
                        st.markdown(f"**Cliente:** {fila_ot.get('Cliente','')}")
                        st.markdown(f"**Sede:** {fila_ot.get('Sede','')}")
                        st.markdown(f"**Servicio:** {fila_ot.get('Servicio','')}")
                        st.markdown(f"**Descripción:** {fila_ot.get('Descripcion','')}")
                    with d2:
                        st.markdown(f"**Estado:** {fila_ot.get('Estado','')}")
                        st.markdown(f"**Fecha límite:** {fila_ot.get('Fecha_Limite','')}")
                        st.markdown(f"**Fecha ejecución:** {fila_ot.get('Fecha_Ejecucion','')}")
                        st.markdown(f"**Observaciones:** {fila_ot.get('Observaciones','')}")
                    st.divider()
                    with st.form(f"form_tec_ot_{_tec_ot_sel}"):
                        st.markdown("**Actualizar esta OT**")
                        fc1, fc2 = st.columns(2)
                        with fc1:
                            nuevo_est = st.selectbox("Estado", ESTADOS_OT,
                                index=ESTADOS_OT.index(fila_ot["Estado"]) if fila_ot["Estado"] in ESTADOS_OT else 0)
                            fecha_ej  = st.text_input("Fecha ejecución", value=fila_ot.get("Fecha_Ejecucion",""))
                        with fc2:
                            hora_ini  = st.text_input("Hora inicio", value=fila_ot.get("Hora_Inicio",""))
                            hora_fin  = st.text_input("Hora fin",    value=fila_ot.get("Hora_Final",""))
                        obs_tec = st.text_area("Observaciones", value=fila_ot.get("Observaciones",""))
                        if st.form_submit_button("💾 Guardar", type="primary", use_container_width=True):
                            ots_all = get_ots()
                            idx_tec = ots_all[ots_all["ID"] == _tec_ot_sel].index[0]
                            ots_all.loc[idx_tec, "Estado"]          = nuevo_est
                            ots_all.loc[idx_tec, "Fecha_Ejecucion"] = fecha_ej
                            ots_all.loc[idx_tec, "Hora_Inicio"]     = hora_ini
                            ots_all.loc[idx_tec, "Hora_Final"]      = hora_fin
                            ots_all.loc[idx_tec, "Observaciones"]   = obs_tec
                            sb_save("ordenes_trabajo", ots_all)
                            _invalidar_cache("ordenes_trabajo")
                            st.success("✅ OT actualizada.")
                            st.rerun()

                with tab_rep:
                    srv = fila_ot.get("Servicio", "")
                    if srv in ["Aires Acondicionados", "Arreglos Locativos"]:
                        st.info(f"Haz clic para abrir el formulario de reporte de **{srv}**.")
                        if st.button("📄 Abrir formulario de reporte", type="primary",
                                     key=f"btn_rep_tec_{_tec_ot_sel}", use_container_width=True):
                            st.session_state["_tec_en_reporte"] = True
                            st.session_state["_tec_viewing_ot"] = _tec_ot_sel
                            st.session_state.pop("tec_ot_sel", None)
                            st.rerun()
                    else:
                        st.info(f"El reporte de formato para **{srv}** no está disponible aún.\n\n"
                                "Usa la pestaña **Actualizar** para registrar observaciones.")

                if st.button("✖ Cerrar detalle", key="cerrar_det_tec"):
                    st.session_state.pop("tec_ot_sel", None)
                    st.rerun()

        # ── VISTA NORMAL (admin / usuario / técnico en modo reporte) ─────────
        else:
            # Botón volver si el técnico está en modo reporte
            if st.session_state.get("_tec_en_reporte"):
                if st.button("← Volver a Mis OTs", key="tec_volver_ots",
                             use_container_width=False):
                    for _k in ["_tec_en_reporte", "_tec_viewing_ot", "ot_preselect"]:
                        st.session_state.pop(_k, None)
                    st.rerun()
                st.divider()

            # ── Técnico en modo reporte: saltar tabla/filtros, ir directo al detalle ──
            _tec_modo_rep = st.session_state.get("_tec_en_reporte")
            # _tec_viewing_ot es persistente (no se hace pop), sobrevive reruns del canvas
            _tec_ot_id    = st.session_state.get("_tec_viewing_ot")
            ot_pre        = st.session_state.pop("ot_preselect", None) or _tec_ot_id

            if _tec_modo_rep and _tec_ot_id and _tec_ot_id in ots["ID"].values:
                id_ot_sel = _tec_ot_id
            else:
                ORIGENES  = ["Solicitud", "Manual", "Contrato Mantenimiento"]
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    f_est_ot  = st.multiselect("Estado",   ESTADOS_OT, default=ESTADOS_OT, key="f_est_ot")
                with c2:
                    f_ser_ot  = st.multiselect("Servicio", SERVICIOS,  default=SERVICIOS,  key="f_ser_ot")
                with c3:
                    f_orig_ot = st.multiselect("Origen",   ORIGENES,   default=ORIGENES,   key="f_orig_ot")
                with c4:
                    buscar_ot = st.text_input("Buscar empresa", key="buscar_ot")

                vista_ot = ots.copy()
                if f_est_ot:
                    vista_ot = vista_ot[vista_ot["Estado"].isin(f_est_ot)]
                if f_ser_ot:
                    vista_ot = vista_ot[vista_ot["Servicio"].isin(f_ser_ot)]
                if f_orig_ot and "Origen" in vista_ot.columns:
                    vista_ot = vista_ot[vista_ot["Origen"].isin(f_orig_ot)]
                if buscar_ot:
                    vista_ot = vista_ot[vista_ot["Cliente"].str.contains(buscar_ot, case=False, na=False)]

                vista_ot_ord = vista_ot.sort_values("ID", ascending=False, key=lambda x: x.str.replace("OT-", ""))

                COLS_TABLA_OT = ["ID", "Origen", "Creado_Por", "Fecha_Creacion", "Fecha_Limite", "Cliente", "Sede",
                                 "Servicio", "SLA", "Zona", "Tecnico", "Fecha_Ejecucion", "Valor_COP", "Estado"]
                cols_vis_ot = [c for c in COLS_TABLA_OT if c in vista_ot_ord.columns]

                def color_limite(val):
                    try:
                        limite = datetime.strptime(val, "%Y-%m-%d %H:%M")
                        diff   = (limite - datetime.now()).total_seconds() / 3600
                        if diff < 0:
                            return "background-color:#f8d7da; color:#000"
                        elif diff <= 24:
                            return "background-color:#fff3cd; color:#000"
                        return "background-color:#d1e7dd; color:#000"
                    except Exception:
                        return ""

                COLORES_OT = {
                    "Programada":   ("#e0e7ff", "#1e3a8a"),
                    "En ejecución": ("#fef3c7", "#78350f"),
                    "En revisión":  ("#ede9fe", "#4c1d95"),
                    "Finalizada":   ("#d1fae5", "#064e3b"),
                    "Cancelada":    ("#fee2e2", "#7f1d1d"),
                }
                # Paginación de 50 OTs
                _POR_PAG_OT = 50
                _total_ots  = len(vista_ot_ord)
                _total_pags_ot = max(1, -(-_total_ots // _POR_PAG_OT))
                _pag_ot = st.session_state.get("pag_ot", 1)
                _ini_ot = (_pag_ot - 1) * _POR_PAG_OT
                _fin_ot = _ini_ot + _POR_PAG_OT

                tabla_html(vista_ot_ord[cols_vis_ot].iloc[_ini_ot:_fin_ot].reset_index(drop=True),
                           color_col="Estado", colores_estado=COLORES_OT,
                           fmt_cols=["Valor_COP"])

                c1, c2, c3, c4, c5 = st.columns([1, 1, 3, 1, 1])
                with c1:
                    if st.button("◀ Anterior", key="ot_prev", disabled=_pag_ot <= 1):
                        st.session_state["pag_ot"] = _pag_ot - 1
                        st.rerun()
                with c2:
                    if st.button("▶ Siguiente", key="ot_next", disabled=_pag_ot >= _total_pags_ot):
                        st.session_state["pag_ot"] = _pag_ot + 1
                        st.rerun()
                with c3:
                    st.caption(f"Página {_pag_ot} de {_total_pags_ot} — Mostrando {min(_fin_ot,_total_ots)-_ini_ot} de {_total_ots} OTs")
                with c4:
                    buf_ot = io.BytesIO()
                    with pd.ExcelWriter(buf_ot, engine="openpyxl") as w:
                        vista_ot_ord.to_excel(w, index=False, sheet_name="OTs")
                    st.download_button(
                        "⬇️ Excel", data=buf_ot.getvalue(),
                        file_name=f"OTs_minzoe_{ahora_colombia().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

                st.divider()
                ids_ot_lista = ots.sort_values("ID", ascending=False, key=lambda x: x.str.replace("OT-", ""))["ID"].tolist()
                idx_pre = ids_ot_lista.index(ot_pre) if ot_pre and ot_pre in ids_ot_lista else 0
                id_ot_sel = st.selectbox("Selecciona una OT", ids_ot_lista,
                                         index=idx_pre, key="id_ot_sel")

            if id_ot_sel:
                fila_ot = ots[ots["ID"] == id_ot_sel].iloc[0]
                # Si viene del dashboard abrir directamente en Editar
                tab_ini = 1 if ot_pre else 0
                if st.session_state.get("_tec_en_reporte"):
                    det, rep, ot_com, ot_hist = st.tabs(["🔍 Ver detalle", "📄 Reportar", "💬 Comentarios", "📜 Historial"])
                    edi = None; eli = None
                else:
                    det, edi, rep, ot_com, ot_hist, eli = st.tabs(["🔍 Ver detalle", "✏️ Editar", "📄 Reportar", "💬 Comentarios", "📜 Historial", "🗑️ Eliminar"])

                with det:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("**🏢 Empresa**")
                        st.write(f"**Cliente:** {fila_ot['Cliente']}")
                        st.write(f"**NIT:** {fila_ot['NIT']}")
                        st.write(f"**Sede:** {fila_ot['Sede']}")
                        st.write(f"**Contacto:** {fila_ot['Nombre_Contacto']} — {fila_ot['Celular_Contacto']}")
                    with c2:
                        st.markdown("**🔧 Trabajo**")
                        st.write(f"**Servicio:** {fila_ot['Servicio']}")
                        st.write(f"**Descripción:** {fila_ot['Descripcion']}")
                        st.write(f"**Técnico:** {fila_ot['Tecnico']}")
                        st.write(f"**Fecha:** {fila_ot['Fecha_Ejecucion']}")
                        st.write(f"**Hora inicio:** {fila_ot.get('Hora_Inicio','—')}  |  **Hora final:** {fila_ot.get('Hora_Final','—')}")
                        st.write(f"**Horas laboradas:** {fila_ot.get('Horas_Laboradas','—')}")
                        st.write(f"**Valor:** ${fila_ot['Valor_COP']} COP")
                        st.write(f"**Estado:** {fila_ot['Estado']}")
                        # Alerta fecha límite
                        fl = fila_ot.get("Fecha_Limite", "")
                        try:
                            limite_dt = datetime.strptime(fl, "%Y-%m-%d %H:%M")
                            diff_h = (limite_dt - datetime.now()).total_seconds() / 3600
                            if diff_h < 0:
                                st.error(f"⛔ VENCIDA — Fecha límite: {fl}")
                            elif diff_h <= 24:
                                st.warning(f"⚠️ Próxima a vencer — Fecha límite: {fl}")
                            else:
                                st.success(f"✅ Fecha límite: {fl}")
                        except Exception:
                            if fl:
                                st.info(f"📋 Fecha límite: {fl}")
                    st.markdown("**🔩 Materiales**")
                    st.write(fila_ot["Materiales"] or "—")
                    st.markdown("**📝 Observaciones**")
                    st.write(fila_ot["Observaciones"] or "—")

                    # ── MENSAJE WHATSAPP ──────────────────────────────────
                    st.divider()
                    celular_tec = fila_ot.get("Celular_Tecnico", "").strip()
                    mensaje_wa = (
                        f"🛠️ *ORDEN DE TRABAJO - Construcciones Minzoe SAS*\n\n"
                        f"*OT:* {fila_ot['ID']}\n"
                        f"*Fecha creación:* {fila_ot['Fecha_Creacion']}\n\n"
                        f"🏢 *CLIENTE*\n"
                        f"Empresa: {fila_ot['Cliente']}\n"
                        f"Sede: {fila_ot['Sede']}\n\n"
                        f"🔧 *TRABAJO*\n"
                        f"Servicio: {fila_ot['Servicio']}\n"
                        f"Descripción: {fila_ot['Descripcion']}\n"
                        f"Fecha ejecución: {fila_ot.get('Fecha_Ejecucion','')} {fila_ot.get('Hora_Inicio','')} - {fila_ot.get('Hora_Final','')}\n\n"
                        f"🔩 *Materiales:* {fila_ot.get('Materiales') or 'Por definir'}\n"
                        f"💵 *Valor:* ${fila_ot.get('Valor_COP', '')} COP\n"
                        f"📋 *Estado:* {fila_ot['Estado']}\n\n"
                        f"📝 *Observaciones:* {fila_ot.get('Observaciones') or '—'}"
                    )
                    st.markdown("**📱 Mensaje para WhatsApp**")
                    if celular_tec:
                        st.info(f"Enviar al técnico: **{celular_tec}**")
                    else:
                        st.caption("Agrega el celular del técnico en ✏️ Editar para tenerlo a la mano.")
                    st.text_area("Copia este mensaje y pégalo en WhatsApp:", value=mensaje_wa, height=300, key="msg_wa")

                if edi is not None:
                 with edi:
                    with st.form("form_editar_ot"):
                        c1, c2 = st.columns(2)
                        with c1:
                            ee_serv   = st.selectbox("Servicio", SERVICIOS, index=SERVICIOS.index(fila_ot["Servicio"]) if fila_ot["Servicio"] in SERVICIOS else 0)
                            ee_desc   = st.text_area("Descripción", value=fila_ot["Descripcion"])
                            ee_tec    = st.text_input("Técnico asignado", value=fila_ot.get("Tecnico", ""))
                            ee_cel_tec = st.text_input("📱 Celular del técnico", value=fila_ot.get("Celular_Tecnico", ""), placeholder="Ej: 3001234567")
                        with c2:
                            ee_estado = st.selectbox("Estado", ESTADOS_OT, index=ESTADOS_OT.index(fila_ot["Estado"]) if fila_ot["Estado"] in ESTADOS_OT else 0)
                            ee_valor  = st.text_input("Valor COP", value=fila_ot.get("Valor_COP", ""))
                            # Fecha de ejecución — maneja campo vacío
                            fecha_actual = fila_ot.get("Fecha_Ejecucion", "")
                            try:
                                fecha_default = datetime.strptime(fecha_actual, "%Y-%m-%d").date() if fecha_actual else datetime.today().date()
                            except Exception:
                                fecha_default = datetime.today().date()
                            ee_fecha = st.date_input("Fecha de ejecución", value=fecha_default)
                            # Hora inicio
                            ini_actual = fila_ot.get("Hora_Inicio", HORAS_12[16])
                            idx_ini = HORAS_12.index(ini_actual) if ini_actual in HORAS_12 else 16
                            ee_hora_ini = st.selectbox("Hora de inicio", HORAS_12, index=idx_ini, key="ee_hora_ini")
                            # Hora final
                            fin_actual = fila_ot.get("Hora_Final", HORAS_12[32])
                            idx_fin = HORAS_12.index(fin_actual) if fin_actual in HORAS_12 else 32
                            ee_hora_fin = st.selectbox("Hora final", HORAS_12, index=idx_fin, key="ee_hora_fin")
                            # Horas laboradas (calculado)
                            horas_calc = calcular_horas(ee_hora_ini, ee_hora_fin)
                            st.info(f"⏱️ Horas laboradas: **{horas_calc}**")
                        ee_mat = st.text_area("Materiales / Repuestos", value=fila_ot.get("Materiales", ""))
                        ee_obs = st.text_area("Observaciones", value=fila_ot.get("Observaciones", ""))

                        if st.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True):
                            idx_ot = ots[ots["ID"] == id_ot_sel].index[0]
                            ots.loc[idx_ot, "Servicio"]       = ee_serv
                            ots.loc[idx_ot, "Descripcion"]    = ee_desc
                            ots.loc[idx_ot, "Tecnico"]        = ee_tec
                            ots.loc[idx_ot, "Celular_Tecnico"] = ee_cel_tec
                            estado_ot_ant = fila_ot.get("Estado","")
                            ots.loc[idx_ot, "Estado"]         = ee_estado
                            if estado_ot_ant != ee_estado:
                                registrar_cambio("OT", id_ot_sel, "Estado", estado_ot_ant, ee_estado)
                            ots.loc[idx_ot, "Valor_COP"]      = ee_valor
                            ots.loc[idx_ot, "Fecha_Ejecucion"]  = ee_fecha.strftime("%Y-%m-%d")
                            ots.loc[idx_ot, "Hora_Inicio"]      = ee_hora_ini
                            ots.loc[idx_ot, "Hora_Final"]       = ee_hora_fin
                            ots.loc[idx_ot, "Horas_Laboradas"]  = calcular_horas(ee_hora_ini, ee_hora_fin)
                            ots.loc[idx_ot, "Materiales"]     = ee_mat
                            ots.loc[idx_ot, "Observaciones"]  = ee_obs
                            save_ots(ots)
                            msg = f"✅ OT {id_ot_sel} actualizada."
                            if ee_estado == "Finalizada":
                                ot_row = ots[ots["ID"] == id_ot_sel].iloc[0]
                                df, cerrada = cerrar_sol_si_aplica(ot_row, df)
                                if cerrada:
                                    save_sol(df)
                                    msg += f" Solicitud **{ot_row['SOL_Ref']}** marcada como Completado."
                            st.success(msg)
                            st.rerun()

                with rep:
                    servicio_ot = fila_ot.get("Servicio", "")

                    # ── Reporte guardado en Supabase ──────────────────────
                    _rep_sb_html, _rep_sb_meta = cargar_reporte_sb(id_ot_sel)
                    if _rep_sb_html:
                        st.success(f"✅ Reporte guardado — {_rep_sb_meta.get('tipo','')} | {_rep_sb_meta.get('fecha','')}")
                        st.download_button(
                            "📥 Descargar reporte guardado",
                            data=_rep_sb_html.encode("utf-8"),
                            file_name=f"Reporte_{id_ot_sel}.html",
                            mime="text/html",
                            use_container_width=True,
                            key=f"dl_rep_sb_{id_ot_sel}",
                        )
                        st.divider()
                        if not st.checkbox("Generar nuevo reporte (sobreescribe el anterior)", key=f"nuevo_rep_{id_ot_sel}"):
                            st.stop()

                    # ── Selector Automático / Manual (solo admin/usuario) ──
                    if st.session_state.get("user_rol") == "tecnico":
                        modo = "✏️ Manual"
                    else:
                        modo = st.radio("¿Cómo quieres llenar el informe?",
                                        ["✏️ Manual", "🤖 Automático (leer documento)"],
                                        horizontal=True, key=f"modo_rep_{id_ot_sel}")

                    datos_ocr = {}
                    if modo == "🤖 Automático (leer documento)":
                        archivo_ocr = st.file_uploader(
                            "Sube la orden de servicio (PDF o imagen)",
                            type=["pdf","png","jpg","jpeg"],
                            key=f"ocr_file_{id_ot_sel}"
                        )
                        if archivo_ocr:
                            with st.spinner("Leyendo documento con Google Vision..."):
                                mime = archivo_ocr.type
                                texto_ocr, conf_ocr, err_ocr = ocr_documento(archivo_ocr.read(), mime)

                            if err_ocr:
                                st.error(f"❌ Error al leer: {err_ocr}")
                                modo = "✏️ Manual"
                            elif conf_ocr < 0.1 or not texto_ocr.strip():
                                st.error("❌ No se detectó texto en el documento. Llena el informe manualmente.")
                                modo = "✏️ Manual"
                            else:
                                if servicio_ot == "Aires Acondicionados":
                                    datos_ocr, conf_campos = parsear_hvac(texto_ocr)
                                else:
                                    datos_ocr, conf_campos = parsear_locativos(texto_ocr)

                                if conf_campos >= 0.8:
                                    st.success(f"✅ Documento leído correctamente ({int(conf_campos*100)}% de campos detectados). Revisa y ajusta si es necesario.")
                                else:
                                    st.error(f"❌ Solo se detectó el {int(conf_campos*100)}% de los campos (mínimo 80%). Llena el informe manualmente.")
                                    datos_ocr = {}
                                    modo = "✏️ Manual"

                    if servicio_ot == "Aires Acondicionados":
                        # Buscar datos del equipo: primero por contrato, luego por cliente+sede
                        equipos = get_equipos()
                        eq_data = {}
                        if not equipos.empty:
                            # Intento 1: por ID_Contrato == SOL_Ref
                            eq_match = equipos[equipos["ID_Contrato"] == fila_ot.get("SOL_Ref","")]
                            # Intento 2: por Cliente + Sede si el 1 falla
                            if eq_match.empty:
                                eq_match = equipos[
                                    (equipos["Cliente"].str.strip().str.lower() == fila_ot.get("Cliente","").strip().lower()) &
                                    (equipos["Sede"].str.strip().str.lower()    == fila_ot.get("Sede","").strip().lower()) &
                                    (equipos["Servicio"] == "Aires Acondicionados")
                                ]
                            if not eq_match.empty:
                                eq_data = eq_match.iloc[0].to_dict()

                        # Parsear campos combinados del equipo
                        def _parse_serial(s):
                            """'Cond: ABC | Evap: XYZ' → (cond, evap)"""
                            cond = evap = s
                            if "|" in str(s):
                                partes = [p.strip() for p in str(s).split("|")]
                                for p in partes:
                                    if p.upper().startswith("COND"):
                                        cond = p.split(":",1)[-1].strip()
                                    elif p.upper().startswith("EVAP"):
                                        evap = p.split(":",1)[-1].strip()
                            return cond, evap

                        def _parse_ubicacion(u):
                            """'Evap: HALL | Cond: EXTERIOR' → (evap, cond)"""
                            evap = cond = u
                            if "|" in str(u):
                                partes = [p.strip() for p in str(u).split("|")]
                                for p in partes:
                                    if p.upper().startswith("EVAP"):
                                        evap = p.split(":",1)[-1].strip()
                                    elif p.upper().startswith("COND"):
                                        cond = p.split(":",1)[-1].strip()
                            return evap, cond

                        def _parse_specs(e):
                            """'MINISPLIT 18.000 BTU | R-410A' → (tipo, btu, refrig)"""
                            tipo = btu = refrig = ""
                            if "|" in str(e):
                                partes = [p.strip() for p in str(e).split("|")]
                                tipo_btu = partes[0]
                                refrig   = partes[1] if len(partes) > 1 else ""
                                # Separar tipo y BTU
                                if "BTU" in tipo_btu.upper():
                                    idx = tipo_btu.upper().find("BTU")
                                    btu  = tipo_btu[:idx].strip().split()[-1] + " BTU"
                                    tipo = " ".join(tipo_btu[:idx].strip().split()[:-1])
                                else:
                                    tipo = tipo_btu
                            else:
                                tipo = str(e)
                            return tipo.strip(), btu.strip(), refrig.strip()

                        _eq_ser_cond, _eq_ser_evap  = _parse_serial(eq_data.get("Numero_Serie",""))
                        _eq_ubic_evap, _eq_ubic_cond = _parse_ubicacion(eq_data.get("Ubicacion",""))
                        _eq_tipo, _eq_btu, _eq_refrig = _parse_specs(eq_data.get("Especificaciones",""))

                        st.markdown(f"### 📄 Reporte HVAC — {id_ot_sel}")

                        # ── Fase 2: canvas de firma (aparece después de guardar el form) ──
                        _hvac_raw_key = f"hvac_html_raw_{id_ot_sel}"
                        if _hvac_raw_key in st.session_state:
                            st.success("✅ Datos técnicos guardados. Ahora el cliente llena la encuesta y firma.")

                            # ── Encuesta de satisfacción (FASE 2 — la llena el cliente) ──
                            st.markdown("""
                            <div style='background:#dc2626;color:#fff;padding:10px 16px;
                                        border-radius:8px 8px 0 0;font-weight:700;font-size:0.95rem'>
                              📋 Encuesta de satisfacción del servicio
                              <span style='font-size:0.78rem;font-weight:400;color:#fca5a5'>
                                &nbsp;— la llena el cliente
                              </span>
                            </div>""", unsafe_allow_html=True)
                            enc1, enc2, enc3, enc4, enc5, enc6 = st.columns(6)
                            enc_exp = enc1.number_input("Experiencia técnicos", 0, 20, 0, key=f"enc_exp_{id_ot_sel}")
                            enc_cal = enc2.number_input("Calidad servicio",     0, 20, 0, key=f"enc_cal_{id_ot_sel}")
                            enc_cum = enc3.number_input("Cumplimiento",         0, 20, 0, key=f"enc_cum_{id_ot_sel}")
                            enc_pre = enc4.number_input("Presentación personal",0, 20, 0, key=f"enc_pre_{id_ot_sel}")
                            enc_com = enc5.number_input("Comunicación",         0, 20, 0, key=f"enc_com_{id_ot_sel}")
                            enc_total = enc_exp + enc_cal + enc_cum + enc_pre + enc_com
                            _enivel = "Bueno ✅" if enc_total >= 85 else ("Regular ⚠️" if enc_total >= 51 else "Malo ❌")
                            _ecol = "#166534" if enc_total >= 85 else ("#92400e" if enc_total >= 51 else "#7f1d1d")
                            _ebg  = "#dcfce7" if enc_total >= 85 else ("#fef3c7" if enc_total >= 51 else "#fee2e2")
                            enc6.markdown(f"""
                            <div style='background:{_ebg};border:2px solid {_ecol};border-radius:8px;
                                        padding:8px;text-align:center;margin-top:20px'>
                              <div style='font-size:1.6rem;font-weight:900;color:{_ecol}'>{enc_total}</div>
                              <div style='font-size:0.7rem;color:{_ecol}'>/ 100</div>
                              <div style='font-size:0.75rem;font-weight:700;color:{_ecol}'>{_enivel}</div>
                            </div>""", unsafe_allow_html=True)
                            enc_obs_cli = st.text_input("Observaciones del cliente", key=f"enc_obs_{id_ot_sel}")
                            st.divider()

                            st.markdown("**✍️ Firma del cliente** — El cliente firma aquí con el dedo o el mouse")
                            _canvas_hvac2 = None
                            try:
                                from streamlit_drawable_canvas import st_canvas as _st_canvas2
                                _canvas_hvac2 = _st_canvas2(
                                    stroke_width=2, stroke_color="#000000",
                                    background_color="#FFFFFF", height=130, width=450,
                                    drawing_mode="freedraw",
                                    key=f"canvas_hvac2_{id_ot_sel}",
                                )
                            except Exception:
                                st.info("Librería de firma no disponible.")
                            c_gen1, c_gen2 = st.columns([1, 1])
                            with c_gen1:
                                if st.button("📄 Generar Reporte PDF", type="primary",
                                             use_container_width=True, key=f"gen_hvac_pdf_{id_ot_sel}"):
                                    _firma_img = ""
                                    try:
                                        if _canvas_hvac2 is not None and _canvas_hvac2.image_data is not None:
                                            from PIL import Image as _PI; import io as _io2, base64 as _b2
                                            _arr2 = _canvas_hvac2.image_data
                                            if _arr2[:,:,3].any():
                                                _im2 = _PI.fromarray(_arr2.astype('uint8'), 'RGBA')
                                                _bf2 = _io2.BytesIO(); _im2.save(_bf2, format='PNG')
                                                _firma_img = f'<img src="data:image/png;base64,{_b2.b64encode(_bf2.getvalue()).decode()}" style="width:220px;height:80px;object-fit:contain;display:block;border-bottom:1px solid #333">'
                                    except Exception:
                                        pass
                                    if not _firma_img:
                                        _firma_img = '<div style="width:220px;height:80px;border-bottom:1px solid #333"></div>'
                                    _html_final = st.session_state[_hvac_raw_key].replace("<!--FIRMA_CLIENTE-->", _firma_img)
                                    st.session_state[f"hvac_html_{id_ot_sel}"] = _html_final
                                    # Guardar en Supabase permanentemente
                                    guardar_reporte_sb(
                                        ot_id   = id_ot_sel,
                                        tipo    = "HVAC",
                                        cliente = st.session_state.get(f"hvac_cli_{id_ot_sel}", fila_ot.get("Cliente","")),
                                        fecha   = st.session_state.get(f"hvac_fec_{id_ot_sel}", ""),
                                        html    = _html_final,
                                    )
                                    del st.session_state[_hvac_raw_key]
                                    st.rerun()
                            with c_gen2:
                                if st.button("✏️ Editar datos del reporte", use_container_width=True,
                                             key=f"editar_hvac_{id_ot_sel}"):
                                    del st.session_state[_hvac_raw_key]
                                    st.rerun()
                            st.stop()

                        # ── Selector tipo de equipo FUERA del form (controla secciones) ──
                        TIPOS_AC   = ["Minisplit", "Cassette", "Split Ducto",
                                      "Manejadora de Aire", "Paquete / Roof Top",
                                      "Chiller", "VRF / VRV", "Fan Coil", "Otro AC"]
                        TIPOS_PORT = ["Portátil"]
                        TIPOS_VENT = ["Ventilador", "Extractor"]
                        _tipos_hvac = TIPOS_AC + TIPOS_PORT + TIPOS_VENT
                        _tipo_eq_sel = st.selectbox(
                            "Tipo de equipo *",
                            _tipos_hvac,
                            key=f"tipo_eq_sel_{id_ot_sel}",
                        )
                        _es_vent_ext = _tipo_eq_sel in TIPOS_VENT
                        _es_portatil = _tipo_eq_sel in TIPOS_PORT

                        # ── Tipo de mantenimiento (fuera del form) ────────
                        st.markdown("**Tipo de mantenimiento**")
                        tc1,tc2,tc3,tc4,tc5 = st.columns(5)
                        tc1.checkbox("Preventivo",    key=f"r_prev_{id_ot_sel}", value=fila_ot.get("Tipo_Servicio","")=="Preventivo")
                        tc2.checkbox("Correctivo",    key=f"r_corr_{id_ot_sel}", value=fila_ot.get("Tipo_Servicio","")=="Correctivo")
                        tc3.checkbox("Visita Técnica",key=f"r_vis_{id_ot_sel}")
                        tc4.checkbox("Emergencia",    key=f"r_emer_{id_ot_sel}")
                        tc5.checkbox("Instalación",   key=f"r_inst_{id_ot_sel}")

                        st.divider()
                        # ── Datos del equipo ──────────────────────────────
                        st.markdown("**🔧 Datos del equipo**")

                        with st.form(f"form_reporte_aires_{id_ot_sel}", clear_on_submit=False):

                            if not _es_vent_ext and not _es_portatil:
                                # ── MODO AC SPLIT ─────────────────────────
                                dc1, dc2 = st.columns(2)
                                with dc1:
                                    r_marca     = st.text_input("Marca",               value=eq_data.get("Marca",""))
                                    r_modelo    = st.text_input("Modelo",              value=eq_data.get("Modelo",""))
                                    r_ser_cond  = st.text_input("Serial Condensadora", value=_eq_ser_cond)
                                    r_ser_evap  = st.text_input("Serial Evaporadora",  value=_eq_ser_evap)
                                with dc2:
                                    r_btu       = st.text_input("Capacidad BTU/CFM",   value=_eq_btu)
                                    r_refrig    = st.text_input("Tipo de refrigerante", value=_eq_refrig)
                                    r_ubic_evap = st.text_input("Ubicación Evaporadora", value=_eq_ubic_evap)
                                    r_ubic_cond = st.text_input("Ubicación Condensadora", value=_eq_ubic_cond)
                                r_serial_vent = ""; r_ubic_vent = ""
                            elif _es_portatil:
                                # ── MODO PORTÁTIL ─────────────────────────
                                dc1, dc2 = st.columns(2)
                                with dc1:
                                    r_marca     = st.text_input("Marca",           value=eq_data.get("Marca",""))
                                    r_modelo    = st.text_input("Modelo",          value=eq_data.get("Modelo",""))
                                    r_ser_cond  = st.text_input("Serial",          value=eq_data.get("Numero_Serie",""))
                                with dc2:
                                    r_btu       = st.text_input("Capacidad BTU",   value=_eq_btu)
                                    r_refrig    = st.text_input("Tipo de refrigerante", value=_eq_refrig)
                                    r_ubic_evap = st.text_input("Ubicación",       value=eq_data.get("Ubicacion",""))
                                r_ser_evap = r_ubic_cond = r_serial_vent = r_ubic_vent = ""
                            else:
                                # ── MODO VENTILADOR / EXTRACTOR ───────────
                                dc1, dc2 = st.columns(2)
                                with dc1:
                                    r_marca       = st.text_input("Marca",   value=eq_data.get("Marca",""))
                                    r_modelo      = st.text_input("Modelo",  value=eq_data.get("Modelo",""))
                                    r_serial_vent = st.text_input("Serial",  value=eq_data.get("Numero_Serie",""))
                                with dc2:
                                    r_ubic_vent   = st.text_input("Ubicación", value=eq_data.get("Ubicacion",""))
                                r_ser_cond = r_ser_evap = r_btu = r_refrig = ""
                                r_ubic_evap = r_ubic_cond = ""

                            st.divider()
                            # ── Datos de medición ─────────────────────────
                            st.markdown("**📊 Datos de medición**")

                            if not _es_vent_ext and not _es_portatil:
                                # ── MEDICIÓN AC ──────────────────────────
                                mc1, mc2, mc3 = st.columns(3)
                                with mc1:
                                    st.markdown("*Unidad Condensadora*")
                                    m_cond_v   = st.text_input("Voltaje",              key="m_cv")
                                    m_cond_a   = st.text_input("Amperaje",             key="m_ca")
                                    m_cond_f   = st.text_input("N° de Fase",           key="m_cf")
                                    m_vcond_v  = st.text_input("Voltaje Motor Vent.",  key="m_vcv")
                                    m_vcond_a  = st.text_input("Amperaje Motor Vent.", key="m_vca")
                                    m_vcond_hp = st.text_input("HP",                   key="m_vchp")
                                    m_vcond_r  = st.text_input("RPM",                  key="m_vcr")
                                with mc2:
                                    st.markdown("*Unidad Manejadora*")
                                    m_evap_v  = st.text_input("Voltaje",              key="m_ev")
                                    m_evap_a  = st.text_input("Amperaje",             key="m_ea")
                                    m_evap_f  = st.text_input("N° de Fase",           key="m_ef")
                                    m_vevap_v = st.text_input("Voltaje Motor Vent.",  key="m_vev")
                                    m_vevap_a = st.text_input("Amperaje Motor Vent.", key="m_vea")
                                    m_vevap_h = st.text_input("HP",                   key="m_vehp")
                                    m_vevap_r = st.text_input("RPM",                  key="m_ver")
                                with mc3:
                                    st.markdown("*Presiones de Refrigerante*")
                                    m_psi_a = st.text_input("PSI Alta",              key="m_pa")
                                    m_psi_b = st.text_input("PSI Baja",              key="m_pb")
                                    m_psi_f = st.text_input("Fecha última medición", key="m_pf")
                                    st.markdown("*Temperatura*")
                                    m_t_sum = st.text_input("Suministro", key="m_ts")
                                    m_t_ret = st.text_input("Retorno",    key="m_tr")
                                    m_t_amb = st.text_input("Ambiente",   key="m_ta")
                                # Variables no usadas en nueva estructura
                                m_vcond_f = m_vevap_f = ""
                                m_ext_v = m_ext_a = m_ext_f = m_ext_h = m_ext_r = m_caudal = ""

                            elif _es_portatil:
                                # ── MEDICIÓN PORTÁTIL ─────────────────────
                                mp1, mp2 = st.columns(2)
                                with mp1:
                                    st.markdown("*Eléctricos*")
                                    m_cond_v = st.text_input("Voltaje",    key="m_cv")
                                    m_cond_a = st.text_input("Amperaje",   key="m_ca")
                                    m_cond_f = st.text_input("N° de Fase", key="m_cf")
                                with mp2:
                                    st.markdown("*Temperatura*")
                                    m_t_sum  = st.text_input("Suministro", key="m_ts")
                                    m_t_ret  = st.text_input("Retorno",    key="m_tr")
                                    m_t_amb  = st.text_input("Ambiente",   key="m_ta")
                                # Campos no aplica para portátil
                                m_vcond_v = m_vcond_a = m_vcond_f = m_vcond_hp = m_vcond_r = ""
                                m_psi_a = m_psi_b = m_psi_f = ""
                                m_evap_v = m_evap_a = m_evap_f = ""
                                m_vevap_v = m_vevap_a = m_vevap_f = m_vevap_h = m_vevap_r = ""
                                m_ext_v = m_ext_a = m_ext_f = m_ext_h = m_ext_r = m_caudal = ""
                            else:
                                # ── MEDICIÓN VENTILADOR / EXTRACTOR ──────
                                mv1, mv2 = st.columns(2)
                                with mv1:
                                    st.markdown("*Eléctricos*")
                                    m_ext_v = st.text_input("Voltaje",    key="m_xv")
                                    m_ext_a = st.text_input("Amperaje",   key="m_xa")
                                    m_ext_f = st.text_input("N° de Fase", key="m_xf")
                                    m_ext_h = st.text_input("HP",         key="m_xhp")
                                    m_ext_r = st.text_input("RPM",        key="m_xr")
                                with mv2:
                                    st.markdown("*Ductos / Rejillas*")
                                    m_caudal = st.text_input("Caudal de Aire", key="m_caudal")
                                m_cond_v = m_cond_a = m_cond_f = ""
                                m_vcond_v = m_vcond_a = m_vcond_f = m_vcond_hp = m_vcond_r = ""
                                m_psi_a = m_psi_b = m_psi_f = ""
                                m_evap_v = m_evap_a = m_evap_f = ""
                                m_vevap_v = m_vevap_a = m_vevap_f = m_vevap_h = m_vevap_r = ""
                                m_t_sum = m_t_ret = m_t_amb = ""

                            st.divider()
                            # ── Checklist ─────────────────────────────────
                            st.markdown("**✅ Lista de chequeo**")
                            cc1, cc2, cc3 = st.columns(3)

                            with cc1:
                                st.markdown("*EVAPORADORA*")
                                ck_ev = {
                                    "Ajuste de Prisioneros y Rotores":        st.checkbox("Ajuste de Prisioneros y Rotores",     key="e1"),
                                    "Ajuste General de Tornillos":            st.checkbox("Ajuste General de Tornillos",         key="e2"),
                                    "Lavado de Filtros":                      st.checkbox("Lavado de Filtros",                   key="e3"),
                                    "Lavado de Serpentines":                  st.checkbox("Lavado de Serpentines",               key="e4"),
                                    "Limpieza Interior y Exterior":           st.checkbox("Limpieza Interior y Exterior",        key="e5"),
                                    "Revisión de Rodamientos":                st.checkbox("Revisión de Rodamientos",             key="e6"),
                                    "Revisión de Rubatex":                    st.checkbox("Revisión de Rubatex",                 key="e7"),
                                    "Revisión de Válvulas":                   st.checkbox("Revisión de Válvulas",                key="e8"),
                                    "Revisión y Ajuste Termostato":           st.checkbox("Revisión y Ajuste Termostato",        key="e9"),
                                    "Rev. y Limp. Accesorios Eléctricos":    st.checkbox("Rev. y Limp. Accesorios Eléctricos",  key="e10"),
                                    "Rev. y Limp. Bomba de Condensado":       st.checkbox("Rev. y Limp. Bomba de Condensado",    key="e11"),
                                    "Tensión y Cambio de Correa":             st.checkbox("Tensión y Cambio de Correa",          key="e12"),
                                }
                                st.markdown("*TUBERÍA REFRIGERACIÓN*")
                                ck_tub = {
                                    "Aislamiento Térmico":                    st.checkbox("Aislamiento Térmico",                 key="t1"),
                                    "Diámetro de Tuberías":                   st.checkbox("Diámetro de Tuberías",                key="t2"),
                                    "Longitud de las Tuberías":               st.checkbox("Longitud de las Tuberías",            key="t3"),
                                    "Puntos de Soporte":                      st.checkbox("Puntos de Soporte",                   key="t4"),
                                    "Revisión de Soldaduras y Conexiones":    st.checkbox("Revisión de Soldaduras y Conexiones", key="t5"),
                                    "Revisión de Tuberías de Drenaje":        st.checkbox("Revisión de Tuberías de Drenaje",     key="t6"),
                                    "Tapa de las Válvulas":                   st.checkbox("Tapa de las Válvulas",                key="t7"),
                                    "Válvulas de Servicio":                   st.checkbox("Válvulas de Servicio",                key="t8"),
                                }

                            with cc2:
                                st.markdown("*CONDENSADORA*")
                                ck_co = {
                                    "Ajuste de Motores Ventiladores":         st.checkbox("Ajuste de Motores Ventiladores",      key="c1"),
                                    "Ajuste General de Tornillos":            st.checkbox("Ajuste General de Tornillos",         key="c2"),
                                    "Lavado de Serpentín":                    st.checkbox("Lavado de Serpentín",                 key="c3"),
                                    "Limpieza de Rejillas":                   st.checkbox("Limpieza de Rejillas",                key="c4"),
                                    "Limpieza Interior y Exterior":           st.checkbox("Limpieza Interior y Exterior",        key="c5"),
                                    "Lubricación de Rodamientos":             st.checkbox("Lubricación de Rodamientos",          key="c6"),
                                    "Pruebas de Protección Alta":             st.checkbox("Pruebas de Protección Alta",          key="c7"),
                                    "Pruebas de Protección Baja":             st.checkbox("Pruebas de Protección Baja",          key="c8"),
                                    "Revisión de Rejillas":                   st.checkbox("Revisión de Rejillas",                key="c9"),
                                    "Revisión Rubatex Existente":             st.checkbox("Revisión Rubatex Existente",          key="c10"),
                                    "Rev. y Limp. Accesorios Eléctricos":    st.checkbox("Rev. y Limp. Accesorios Eléctricos",  key="c11"),
                                    "Verificación de Fugas de Gas":          st.checkbox("Verificación de Fugas de Gas",        key="c12"),
                                    "Verificación de Presiones":              st.checkbox("Verificación de Presiones",           key="c13"),
                                    "Verificación de Soportería":             st.checkbox("Verificación de Soportería",          key="c14"),
                                }

                            with cc3:
                                st.markdown("*VENTILADORES Y EXTRACTORES*")
                                ck_vent = {
                                    "Verificación de Vibraciones":            st.checkbox("Verificación de Vibraciones",         key="v1"),
                                    "Revisión de Correas":                    st.checkbox("Revisión de Correas",                 key="v2"),
                                    "Revisión de Ejes":                       st.checkbox("Revisión de Ejes",                    key="v3"),
                                    "Revisión y Limpieza de Motores":         st.checkbox("Revisión y Limpieza de Motores",      key="v4"),
                                    "Revisión de Chumaceras":                 st.checkbox("Revisión de Chumaceras",              key="v5"),
                                    "Lubricación de Chumaceras y Bujes":      st.checkbox("Lubricación de Chumaceras y Bujes",   key="v6"),
                                    "Ajuste de Cuñas y Prisioneros":          st.checkbox("Ajuste de Cuñas y Prisioneros",       key="v7"),
                                    "Rev. y Limp. Contactos Eléctricos":     st.checkbox("Rev. y Limp. Contactos Eléctricos",   key="v8"),
                                }
                                st.markdown("*DUCTOS Y REJILLAS*")
                                ck_duc = {
                                    "Limpieza Externa":                       st.checkbox("Limpieza Externa",                    key="d1"),
                                    "Limpieza Interna":                       st.checkbox("Limpieza Interna",                    key="d2"),
                                    "Verificación de Obstrucciones":          st.checkbox("Verificación de Obstrucciones",       key="d3"),
                                    "Ajuste de Tornillería":                  st.checkbox("Ajuste de Tornillería",               key="d4"),
                                }

                            st.divider()
                            # ── Observaciones generales del técnico ────────
                            st.markdown("**📝 Observaciones generales del técnico**")
                            r_obs = st.text_area("Describe lo que evidenciaste durante el mantenimiento",
                                                  value=fila_ot.get("Observaciones",""), height=100)

                            st.divider()
                            # ── Tiempo de servicio ──────────────────────────
                            st.markdown("**⏱️ Tiempo de servicio**")
                            fc1, fc2, fc3 = st.columns(3)
                            with fc1:
                                _ini_idx = HORAS_12.index(fila_ot.get("Hora_Inicio","08:00 AM")) if fila_ot.get("Hora_Inicio","") in HORAS_12 else 16
                                r_hora_lleg = st.selectbox("Hora de llegada", HORAS_12, index=_ini_idx, key="r_hlleg")
                                _sal_idx = HORAS_12.index(fila_ot.get("Hora_Final","05:00 PM")) if fila_ot.get("Hora_Final","") in HORAS_12 else 34
                                r_hora_sal  = st.selectbox("Hora de salida",  HORAS_12, index=_sal_idx, key="r_hsal")
                            with fc2:
                                r_pend = st.radio("Trabajo pendiente",   ["Sí","No"], horizontal=True)
                            with fc3:
                                r_oper = st.radio("Equipo en operación", ["Sí","No"], horizontal=True)

                            st.markdown("**✍️ Firmas**")
                            sc1, sc2, sc3 = st.columns(3)
                            with sc1:
                                r_nom_tec  = st.text_input("Nombre técnico",   value=fila_ot.get("Tecnico",""))
                                r_superv   = st.text_input("Supervisor")
                            with sc2:
                                r_nom_cli  = st.text_input("Nombre cliente",   value=fila_ot.get("Nombre_Contacto",""))
                                r_fec_firma= st.text_input("Fecha",            value=fila_ot.get("Fecha_Ejecucion",""))

                            generar = st.form_submit_button("✅ Finalizar y Guardar", type="primary", use_container_width=True)

                            if generar:
                                def ck(val): return "✔" if val else ""
                                # Leer checkboxes desde session_state (están fuera del form)
                                r_prev = st.session_state.get(f"r_prev_{id_ot_sel}", False)
                                r_corr = st.session_state.get(f"r_corr_{id_ot_sel}", False)
                                r_vis  = st.session_state.get(f"r_vis_{id_ot_sel}",  False)
                                r_emer = st.session_state.get(f"r_emer_{id_ot_sel}", False)
                                r_inst = st.session_state.get(f"r_inst_{id_ot_sel}", False)
                                # Encuesta: se leerá en fase 2 desde session_state
                                enc_exp = st.session_state.get(f"enc_exp_{id_ot_sel}", 0)
                                enc_cal = st.session_state.get(f"enc_cal_{id_ot_sel}", 0)
                                enc_cum = st.session_state.get(f"enc_cum_{id_ot_sel}", 0)
                                enc_pre = st.session_state.get(f"enc_pre_{id_ot_sel}", 0)
                                enc_com = st.session_state.get(f"enc_com_{id_ot_sel}", 0)
                                enc_total = enc_exp + enc_cal + enc_cum + enc_pre + enc_com
                                enc_obs_cli = st.session_state.get(f"enc_obs_{id_ot_sel}", "")

                                # ── Validación campos obligatorios de medición ──
                                _campos_vacios = []
                                if not _es_vent_ext and not _es_portatil:
                                    _req_med = [
                                        (m_cond_v,  "Voltaje Unidad Condensadora"),
                                        (m_cond_a,  "Amperaje Unidad Condensadora"),
                                        (m_cond_f,  "N° Fase Unidad Condensadora"),
                                        (m_vcond_v, "Voltaje Motor Vent. Condensadora"),
                                        (m_vcond_a, "Amperaje Motor Vent. Condensadora"),
                                        (m_vcond_hp,"HP Motor Vent. Condensadora"),
                                        (m_vcond_r, "RPM Motor Vent. Condensadora"),
                                        (m_psi_b,   "PSI Baja"),
                                        (m_psi_f,   "Fecha última medición PSI"),
                                        (m_evap_v,  "Voltaje Unidad Manejadora"),
                                        (m_evap_a,  "Amperaje Unidad Manejadora"),
                                        (m_evap_f,  "N° Fase Unidad Manejadora"),
                                        (m_vevap_v, "Voltaje Motor Vent. Manejadora"),
                                        (m_vevap_a, "Amperaje Motor Vent. Manejadora"),
                                        (m_vevap_h, "HP Motor Vent. Manejadora"),
                                        (m_vevap_r, "RPM Motor Vent. Manejadora"),
                                        (m_t_sum,   "Temperatura Suministro"),
                                        (m_t_ret,   "Temperatura Retorno"),
                                        (m_t_amb,   "Temperatura Ambiente"),
                                    ]
                                elif _es_portatil:
                                    _req_med = [
                                        (m_cond_v, "Voltaje"),
                                        (m_cond_a, "Amperaje"),
                                        (m_cond_f, "N° de Fase"),
                                        (m_t_sum,  "Temperatura Suministro"),
                                        (m_t_ret,  "Temperatura Retorno"),
                                        (m_t_amb,  "Temperatura Ambiente"),
                                    ]
                                else:
                                    _req_med = [
                                        (m_ext_v, "Voltaje"),
                                        (m_ext_a, "Amperaje"),
                                        (m_ext_f, "N° de Fase"),
                                        (m_ext_h, "HP"),
                                        (m_ext_r, "RPM"),
                                    ]
                                for _val, _nom in _req_med:
                                    if not str(_val).strip():
                                        _campos_vacios.append(_nom)

                                if _campos_vacios:
                                    st.error(
                                        f"⚠️ Faltan **{len(_campos_vacios)}** campo(s) de medición obligatorio(s). "
                                        f"Si no puedes tomar el dato escribe **N/A**:\n\n"
                                        + "\n".join(f"• {c}" for c in _campos_vacios)
                                    )
                                    st.stop()
                                tipo_mto = " | ".join(filter(None,[
                                    "Preventivo" if r_prev else "",
                                    "Correctivo" if r_corr else "",
                                    "Visita Técnica" if r_vis else "",
                                    "Emergencia" if r_emer else "",
                                    "Instalación" if r_inst else "",
                                ]))
                                _logo_b64 = get_logo_base64()
                                _logo_tag = f'<img src="{_logo_b64}" style="height:60px;object-fit:contain">' if _logo_b64 else ""

                                # La firma se agrega en fase 2 (después del form)
                                _firma_hvac_html = "<!--FIRMA_CLIENTE-->"

                                # ── Filas dinámicas cliente/equipo (solo campos con valor) ──
                                _cli_rows = []
                                if fila_ot.get('Cliente',''): _cli_rows.append(("Cliente:", fila_ot['Cliente']))
                                if fila_ot.get('Sede',''): _cli_rows.append(("Sucursal:", fila_ot.get('Sede','')))
                                if fila_ot.get('Nombre_Contacto',''): _cli_rows.append(("Contacto:", fila_ot.get('Nombre_Contacto','')))

                                _eq_rows = []
                                if _tipo_eq_sel.strip(): _eq_rows.append(("Tipo de equipo:", _tipo_eq_sel))
                                if r_marca.strip(): _eq_rows.append(("Marca:", r_marca))
                                if r_modelo.strip(): _eq_rows.append(("Modelo:", r_modelo))
                                if not _es_vent_ext:
                                    if r_ser_cond.strip(): _eq_rows.append(("Serial Condensadora:", r_ser_cond))
                                    if r_ser_evap.strip(): _eq_rows.append(("Serial Evaporadora:", r_ser_evap))
                                    if r_btu.strip(): _eq_rows.append(("Capacidad BTU/CFM:", r_btu))
                                    if r_refrig.strip(): _eq_rows.append(("Tipo de Refrigerante:", r_refrig))
                                    if r_ubic_evap.strip(): _eq_rows.append(("Ubic. Evaporadora:", r_ubic_evap))
                                    if r_ubic_cond.strip(): _eq_rows.append(("Ubic. Condensadora:", r_ubic_cond))
                                else:
                                    if r_serial_vent.strip(): _eq_rows.append(("Serial:", r_serial_vent))
                                    if r_ubic_vent.strip():   _eq_rows.append(("Ubicación:", r_ubic_vent))

                                _rows_ce = ""
                                for _i in range(max(len(_cli_rows), len(_eq_rows))):
                                    _cl = f"<td><b>{_cli_rows[_i][0]}</b></td><td>{_cli_rows[_i][1]}</td>" if _i < len(_cli_rows) else "<td></td><td></td>"
                                    _eq = f"<td><b>{_eq_rows[_i][0]}</b></td><td>{_eq_rows[_i][1]}</td>" if _i < len(_eq_rows) else "<td></td><td></td>"
                                    _rows_ce += f"<tr>{_cl}{_eq}</tr>\n"

                                # Sección medición según tipo de equipo
                                if not _es_vent_ext and not _es_portatil:
                                    # Medición AC completa
                                    _med_vals = [m_cond_v,m_cond_a,m_cond_f,m_vcond_v,m_vcond_a,
                                                 m_vcond_f,m_vcond_hp,m_vcond_r,m_psi_a,m_psi_b,
                                                 m_psi_f,m_evap_v,m_evap_a,m_evap_f,m_vevap_v,
                                                 m_vevap_a,m_vevap_f,m_vevap_h,m_vevap_r,
                                                 m_t_sum,m_t_ret,m_t_amb]
                                    if any(v.strip() for v in _med_vals):
                                        _seccion_medicion = (
                                            '<div class="section">DATOS DE MEDICIÓN</div>'
                                            '<table><tr>'
                                            '<th colspan="2">Unidad Condensadora</th>'
                                            '<th colspan="2">Unidad Manejadora</th>'
                                            '<th colspan="2">Presiones Refrig.</th>'
                                            '<th colspan="2">Temperatura</th>'
                                            f'</tr><tr>'
                                            f'<td>Voltaje</td><td>{m_cond_v}</td>'
                                            f'<td>Voltaje</td><td>{m_evap_v}</td>'
                                            f'<td>PSI Alta</td><td>{m_psi_a}</td>'
                                            f'<td>Suministro</td><td>{m_t_sum}</td>'
                                            f'</tr><tr>'
                                            f'<td>Amperaje</td><td>{m_cond_a}</td>'
                                            f'<td>Amperaje</td><td>{m_evap_a}</td>'
                                            f'<td>PSI Baja</td><td>{m_psi_b}</td>'
                                            f'<td>Retorno</td><td>{m_t_ret}</td>'
                                            f'</tr><tr>'
                                            f'<td>N° Fase</td><td>{m_cond_f}</td>'
                                            f'<td>N° Fase</td><td>{m_evap_f}</td>'
                                            f'<td>Últ. Med.</td><td>{m_psi_f}</td>'
                                            f'<td>Ambiente</td><td>{m_t_amb}</td>'
                                            f'</tr><tr>'
                                            f'<td>V. Motor Vent.</td><td>{m_vcond_v}</td>'
                                            f'<td>V. Motor Vent.</td><td>{m_vevap_v}</td>'
                                            '<td></td><td></td><td></td><td></td>'
                                            f'</tr><tr>'
                                            f'<td>A. Motor Vent.</td><td>{m_vcond_a}</td>'
                                            f'<td>A. Motor Vent.</td><td>{m_vevap_a}</td>'
                                            '<td></td><td></td><td></td><td></td>'
                                            f'</tr><tr>'
                                            f'<td>HP</td><td>{m_vcond_hp}</td>'
                                            f'<td>HP</td><td>{m_vevap_h}</td>'
                                            '<td></td><td></td><td></td><td></td>'
                                            f'</tr><tr>'
                                            f'<td>RPM</td><td>{m_vcond_r}</td>'
                                            f'<td>RPM</td><td>{m_vevap_r}</td>'
                                            '<td></td><td></td><td></td><td></td>'
                                            '</tr></table>'
                                        )
                                    else:
                                        _seccion_medicion = ""
                                elif _es_portatil:
                                    # Medición Portátil
                                    _med_vals_p = [m_cond_v, m_cond_a, m_cond_f, m_t_sum, m_t_ret, m_t_amb]
                                    if any(v.strip() for v in _med_vals_p):
                                        _seccion_medicion = (
                                            '<div class="section">DATOS DE MEDICIÓN</div>'
                                            '<table><tr>'
                                            '<th colspan="2">Eléctricos</th>'
                                            '<th colspan="2">Temperatura</th>'
                                            f'</tr><tr>'
                                            f'<td>Voltaje</td><td>{m_cond_v}</td>'
                                            f'<td>Suministro</td><td>{m_t_sum}</td>'
                                            f'</tr><tr>'
                                            f'<td>Amperaje</td><td>{m_cond_a}</td>'
                                            f'<td>Retorno</td><td>{m_t_ret}</td>'
                                            f'</tr><tr>'
                                            f'<td>N° de Fase</td><td>{m_cond_f}</td>'
                                            f'<td>Ambiente</td><td>{m_t_amb}</td>'
                                            '</tr></table>'
                                        )
                                    else:
                                        _seccion_medicion = ""
                                else:
                                    # Medición Ventilador / Extractor
                                    _med_vals_v = [m_ext_v, m_ext_a, m_ext_f, m_ext_h, m_ext_r, m_caudal]
                                    if any(v.strip() for v in _med_vals_v):
                                        _seccion_medicion = (
                                            '<div class="section">DATOS DE MEDICIÓN</div>'
                                            '<table><tr>'
                                            f'<th colspan="2">{_tipo_eq_sel}</th>'
                                            '<th colspan="2">Ductos / Rejillas</th>'
                                            f'</tr><tr>'
                                            f'<td>Voltaje</td><td>{m_ext_v}</td>'
                                            f'<td>Caudal de Aire</td><td>{m_caudal}</td>'
                                            f'</tr><tr>'
                                            f'<td>Amperaje</td><td>{m_ext_a}</td>'
                                            '<td></td><td></td>'
                                            f'</tr><tr>'
                                            f'<td>N° de Fase</td><td>{m_ext_f}</td>'
                                            '<td></td><td></td>'
                                            f'</tr><tr>'
                                            f'<td>HP</td><td>{m_ext_h}</td>'
                                            '<td></td><td></td>'
                                            f'</tr><tr>'
                                            f'<td>RPM</td><td>{m_ext_r}</td>'
                                            '<td></td><td></td>'
                                            '</tr></table>'
                                        )
                                    else:
                                        _seccion_medicion = ""

                                html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<title>Reporte HVAC {id_ot_sel}</title>
<style>{css_formato_carta()}</style>
</head><body>
<div class="pagina">
<div class="header">
  <div style="display:flex;align-items:center;gap:12px">
    {_logo_tag}
    <div>
      <div class="logo">CONSTRUCCIONES MINZOE SAS</div>
      <div>Soluciones integrales en construcción, mantenimiento y climatización.</div>
      <div>Cra 5 # 8a-18 &nbsp;|&nbsp; 3175102668 – 3173748665 &nbsp;|&nbsp; construminzoe@gmail.com</div>
    </div>
  </div>
  <div style="text-align:right">
    <b>FORMATO MANTENIMIENTO HVAC</b><br>
    <b>OT: {id_ot_sel}</b><br>
    Fecha: {r_fec_firma}
  </div>
</div>

<div style="margin-bottom:6px"><b>Tipo:</b> {tipo_mto}</div>

<table><tr>
  <th colspan="2">DATOS DEL CLIENTE</th>
  <th colspan="2">DATOS DEL EQUIPO</th>
</tr>
{_rows_ce}</table>

{_seccion_medicion}

<div class="section">LISTA DE CHEQUEO</div>
<table><tr>
  <th colspan="3">EVAPORADORA</th>
  <th colspan="3">CONDENSADORA</th>
  <th colspan="3">VENTILADORES Y EXTRACTORES</th>
</tr>
{''.join(f"<tr><td class='ck'>{ck(v)}</td><td>{k}</td><td></td>" +
         (f"<td class='ck'>{ck(list(ck_co.values())[i])}</td><td>{list(ck_co.keys())[i]}</td><td></td>" if i < len(ck_co) else "<td></td><td></td><td></td>") +
         (f"<td class='ck'>{ck(list(ck_vent.values())[i])}</td><td>{list(ck_vent.keys())[i]}</td><td></td></tr>" if i < len(ck_vent) else "<td></td><td></td><td></td></tr>")
         for i,(k,v) in enumerate(ck_ev.items()))}
</table>

<table><tr>
  <th colspan="3">TUBERÍA REFRIGERACIÓN Y DESAGÜE</th>
  <th colspan="3">DUCTOS Y REJILLAS</th>
</tr>
{''.join(f"<tr><td class='ck'>{ck(v)}</td><td>{k}</td><td></td>" +
         (f"<td class='ck'>{ck(list(ck_duc.values())[i])}</td><td>{list(ck_duc.keys())[i]}</td><td></td></tr>" if i < len(ck_duc) else "<td></td><td></td><td></td></tr>")
         for i,(k,v) in enumerate(ck_tub.items()))}
</table>

<div class="section">OBSERVACIONES GENERALES DEL TÉCNICO</div>
<table><tr><td style="min-height:50px">{r_obs}</td></tr></table>

<div class="section">ENCUESTA DE SATISFACCIÓN DEL SERVICIO</div>
<table>
<tr>
  <th style="width:22%">TÉCNICOS</th>
  <th>CONCEPTO</th>
  <th style="width:8%;text-align:center">PESO</th>
  <th style="width:10%;text-align:center">PUNTAJE</th>
  <th style="width:28%">OBSERVACIONES DEL SERVICIO</th>
</tr>
<tr>
  <td rowspan="5" style="vertical-align:middle;text-align:center">{r_nom_tec}</td>
  <td>Experiencia de los Técnicos</td><td style="text-align:center">20</td><td style="text-align:center">{enc_exp if enc_exp else ""}</td>
  <td rowspan="5" style="vertical-align:top">{enc_obs_cli}</td>
</tr>
<tr><td>Calidad de Servicio y Bienes</td><td style="text-align:center">20</td><td style="text-align:center">{enc_cal if enc_cal else ""}</td></tr>
<tr><td>Cumplimiento</td><td style="text-align:center">20</td><td style="text-align:center">{enc_cum if enc_cum else ""}</td></tr>
<tr><td>Presentación Personal</td><td style="text-align:center">20</td><td style="text-align:center">{enc_pre if enc_pre else ""}</td></tr>
<tr><td>Comunicación</td><td style="text-align:center">20</td><td style="text-align:center">{enc_com if enc_com else ""}</td></tr>
<tr><td></td><td><b>TOTAL</b></td><td style="text-align:center"><b>100</b></td><td style="text-align:center"><b>{enc_total if enc_total else ""}</b></td><td></td></tr>
</table>
<p style="font-size:7.5px;margin:3px 0">*La suma de los conceptos determinará la continuidad del personal: 0-50 Puntos: Malo &nbsp;|&nbsp; 51-84 Puntos: Regular &nbsp;|&nbsp; 85-100 Puntos: Bueno</p>

<table style="margin-top:6px"><tr>
  <th>TIEMPO DE SERVICIO</th><th>TRABAJO PENDIENTE</th><th>EQ. EN OPERACIÓN</th>
</tr><tr>
  <td>Llegada: {r_hora_lleg}<br>Salida: {r_hora_sal}</td>
  <td>{r_pend}</td>
  <td>{r_oper}</td>
</tr></table>

<div style="display:flex;justify-content:space-between;margin-top:20px">
  <div>
    <div class="firma-box" style="width:180px">&nbsp;<br>FIRMA TÉCNICO</div>
    <div style="font-size:9px;margin-top:3px">Nombre: {r_nom_tec}</div>
    <div style="font-size:9px">Supervisor: {r_superv}</div>
  </div>
  <div>
    <div>
      {_firma_hvac_html}
      <div style="font-size:9px;margin-top:2px;font-weight:600">FIRMA Y SELLO CLIENTE</div>
      <div style="font-size:9px;margin-top:2px">Nombre: {r_nom_cli}</div>
      <div style="font-size:9px">Fecha: {r_fec_firma}</div>
    </div>
  </div>
</div>

<div class="no-print" style="margin-top:16px;text-align:center">
  <button onclick="window.print()" style="background:#dc2626;color:white;border:none;padding:10px 30px;font-size:14px;border-radius:6px;cursor:pointer">
    🖨️ Imprimir / Guardar como PDF
  </button>
</div>
</div>
</body></html>"""

                                # Guardar HTML con placeholder — la firma se agrega en fase 2
                                st.session_state[f"hvac_html_raw_{id_ot_sel}"] = html
                                st.session_state[f"hvac_cli_{id_ot_sel}"]  = fila_ot["Cliente"]
                                st.session_state[f"hvac_sede_{id_ot_sel}"] = fila_ot.get("Sede","")
                                st.session_state[f"hvac_fec_{id_ot_sel}"]  = fila_ot.get("Fecha_Ejecucion","")

                        # ── FUERA del form: guardar ──────────────────────
                        _html_key = f"hvac_html_{id_ot_sel}"
                        if _html_key in st.session_state:
                            st.session_state["_ot_volver_ver"] = True
                            _html = st.session_state[_html_key]
                            _cli  = st.session_state.get(f"hvac_cli_{id_ot_sel}","")
                            _sede = st.session_state.get(f"hvac_sede_{id_ot_sel}","")
                            _fec  = st.session_state.get(f"hvac_fec_{id_ot_sel}","")
                            def _finalizar_ot_y_sol(ot_id):
                                """Técnico entregó reporte: pasa a En revisión (admin la cierra después)."""
                                ots.loc[ots["ID"] == ot_id, "Estado"] = "En revisión"
                                save_ots(ots)
                                return f"OT **{ot_id}** enviada a revisión. El administrador la cerrará definitivamente."

                            ok_h, res_h = guardar_reporte_local(_html, _cli, _sede, id_ot_sel, _fec)
                            msg_fin = _finalizar_ot_y_sol(id_ot_sel)
                            del st.session_state[_html_key]
                            if ok_h:
                                st.success(f"✅ Guardado en: `{res_h}`\n\n{msg_fin}")
                            else:
                                st.info(msg_fin)
                                fmt_h = st.radio("Formato de descarga",
                                    ["📄 HTML", "📕 PDF (imprimir desde el archivo)", "🖼️ PNG/TIFF (captura)"],
                                    horizontal=True, key="fmt_hvac")
                                st.download_button(
                                    "⬇️ Descargar Reporte",
                                    data=_html,
                                    file_name=f"Reporte_HVAC_{id_ot_sel}.html",
                                    mime="text/html",
                                    use_container_width=True,
                                    type="primary"
                                )
                                if fmt_h == "📕 PDF (imprimir desde el archivo)":
                                    st.info("💡 Abre el archivo HTML descargado → clic en **🖨️ Imprimir / Guardar como PDF** → elige destino **Guardar como PDF**.")
                                elif fmt_h == "🖼️ PNG/TIFF (captura)":
                                    st.info("💡 Abre el archivo HTML → presiona **Ctrl+P** → cambia el destino a **Microsoft Print to PDF** o toma una captura con la herramienta de recorte de Windows.")
                                if st.button("✅ Listo, cerrar", key="cerrar_hvac"):
                                    st.rerun()
                            if ok_h:
                                st.rerun()

                    else:
                        # ── FORMATO LOCATIVOS ─────────────────────────────
                        st.markdown(f"### 📄 Reporte Locativos — {id_ot_sel}")

                        # ── Fase 2: canvas de firma (aparece después de guardar el form) ──
                        _loc_raw_key = f"loc_html_raw_{id_ot_sel}"
                        if _loc_raw_key in st.session_state:
                            st.success("✅ Datos técnicos guardados. Ahora el cliente llena la encuesta y firma.")

                            # ── Encuesta satisfacción Locativos FASE 2 ────
                            st.markdown("""
                            <div style='background:#dc2626;color:#fff;padding:10px 16px;
                                        border-radius:8px 8px 0 0;font-weight:700;font-size:0.95rem'>
                              📋 Encuesta de satisfacción del servicio
                              <span style='font-size:0.78rem;font-weight:400;color:#fca5a5'>
                                &nbsp;— la llena el cliente
                              </span>
                            </div>""", unsafe_allow_html=True)
                            lenc1, lenc2, lenc3, lenc4, lenc5, lenc6 = st.columns(6)
                            l_enc_exp = lenc1.number_input("Experiencia técnicos", 0, 20, 0, key=f"l_enc_exp_{id_ot_sel}")
                            l_enc_cal = lenc2.number_input("Calidad servicio",     0, 20, 0, key=f"l_enc_cal_{id_ot_sel}")
                            l_enc_cum = lenc3.number_input("Cumplimiento",         0, 20, 0, key=f"l_enc_cum_{id_ot_sel}")
                            l_enc_pre = lenc4.number_input("Presentación personal",0, 20, 0, key=f"l_enc_pre_{id_ot_sel}")
                            l_enc_com = lenc5.number_input("Comunicación",         0, 20, 0, key=f"l_enc_com_{id_ot_sel}")
                            l_enc_total = l_enc_exp + l_enc_cal + l_enc_cum + l_enc_pre + l_enc_com
                            _lnivel = "Bueno ✅" if l_enc_total >= 85 else ("Regular ⚠️" if l_enc_total >= 51 else "Malo ❌")
                            _lcol = "#166534" if l_enc_total >= 85 else ("#92400e" if l_enc_total >= 51 else "#7f1d1d")
                            _lbg  = "#dcfce7" if l_enc_total >= 85 else ("#fef3c7" if l_enc_total >= 51 else "#fee2e2")
                            lenc6.markdown(f"""
                            <div style='background:{_lbg};border:2px solid {_lcol};border-radius:8px;
                                        padding:8px;text-align:center;margin-top:20px'>
                              <div style='font-size:1.6rem;font-weight:900;color:{_lcol}'>{l_enc_total}</div>
                              <div style='font-size:0.7rem;color:{_lcol}'>/ 100</div>
                              <div style='font-size:0.75rem;font-weight:700;color:{_lcol}'>{_lnivel}</div>
                            </div>""", unsafe_allow_html=True)
                            l_enc_obs = st.text_input("Observaciones del cliente", key=f"l_enc_obs_{id_ot_sel}")
                            st.divider()

                            st.markdown("**✍️ Firma del cliente** — El cliente firma aquí con el dedo o el mouse")
                            _canvas_loc2 = None
                            try:
                                from streamlit_drawable_canvas import st_canvas as _st_canvas3
                                _canvas_loc2 = _st_canvas3(
                                    stroke_width=2, stroke_color="#000000",
                                    background_color="#FFFFFF", height=130, width=450,
                                    drawing_mode="freedraw",
                                    key=f"canvas_loc2_{id_ot_sel}",
                                )
                            except Exception:
                                st.info("Librería de firma no disponible.")
                            c_loc1, c_loc2 = st.columns([1, 1])
                            with c_loc1:
                                if st.button("📄 Generar Reporte PDF", type="primary",
                                             use_container_width=True, key=f"gen_loc_pdf_{id_ot_sel}"):
                                    _firma_loc = ""
                                    try:
                                        if _canvas_loc2 is not None and _canvas_loc2.image_data is not None:
                                            from PIL import Image as _PI3; import io as _io3, base64 as _b3
                                            _arr3 = _canvas_loc2.image_data
                                            if _arr3[:,:,3].any():
                                                _im3 = _PI3.fromarray(_arr3.astype('uint8'), 'RGBA')
                                                _bf3 = _io3.BytesIO(); _im3.save(_bf3, format='PNG')
                                                _firma_loc = f'<img src="data:image/png;base64,{_b3.b64encode(_bf3.getvalue()).decode()}" style="width:220px;height:80px;object-fit:contain;display:block;border-bottom:1px solid #333">'
                                    except Exception:
                                        pass
                                    if not _firma_loc:
                                        _firma_loc = '<div style="width:220px;height:80px;border-bottom:1px solid #333"></div>'
                                    _html_loc_final = st.session_state[_loc_raw_key].replace("<!--FIRMA_CLIENTE-->", _firma_loc)
                                    st.session_state[f"loc_html_{id_ot_sel}"] = _html_loc_final
                                    # Guardar en Supabase permanentemente
                                    guardar_reporte_sb(
                                        ot_id   = id_ot_sel,
                                        tipo    = "Locativos",
                                        cliente = st.session_state.get(f"loc_cli_{id_ot_sel}", fila_ot.get("Cliente","")),
                                        fecha   = st.session_state.get(f"loc_fec_{id_ot_sel}", ""),
                                        html    = _html_loc_final,
                                    )
                                    del st.session_state[_loc_raw_key]
                                    st.rerun()
                            with c_loc2:
                                if st.button("✏️ Editar datos del reporte", use_container_width=True,
                                             key=f"editar_loc_{id_ot_sel}"):
                                    del st.session_state[_loc_raw_key]
                                    st.rerun()
                            st.stop()

                        with st.form(f"form_reporte_loc_{id_ot_sel}", clear_on_submit=False):

                            # Tipo de mantenimiento
                            st.markdown("**Tipo de mantenimiento**")
                            lc1,lc2,lc3,lc4 = st.columns(4)
                            l_prev = lc1.checkbox("Preventivo",  key="l_prev")
                            l_corr = lc2.checkbox("Correctivo",  key="l_corr")
                            l_vis  = lc3.checkbox("Visita Técnica", key="l_vis")
                            l_emer = lc4.checkbox("Emergencia",  key="l_emer")

                            st.divider()

                            # Datos del cliente + Sistema
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown("**📍 Datos del cliente**")
                                l_area = st.text_input("Área intervenida", value=datos_ocr.get("area",""), key="l_area")

                                st.markdown("**⚙️ Sistema**")
                                sc1, sc2 = st.columns(2)
                                with sc1:
                                    l_mec  = st.checkbox("Mecánico",    key="l_mec")
                                    l_neu  = st.checkbox("Neumático",   key="l_neu")
                                    l_ele  = st.checkbox("Eléctrico",   key="l_ele")
                                    l_hid  = st.checkbox("Hidráulico",  key="l_hid")
                                with sc2:
                                    l_elec = st.checkbox("Electrónico", key="l_elec")
                                    l_loc  = st.checkbox("Locativo",    key="l_loc")
                                    l_otro_sis = st.checkbox("Otro",    key="l_otro_sis")

                            st.divider()

                            # Actividades de trabajo
                            st.markdown("**🔧 Actividades de trabajo**")
                            ITEMS_LOC = [
                                "Pisos","Techos","Paredes","Puertas","Rejillas",
                                "Desagüas","Sanitarios","Tomas Eléctricas","Luminarias",
                                "Estanterías","Cajoneras","Cerraduras","Chapas",
                                "Sillas","Puestos de Trabajo","Otro",
                            ]
                            l_act = {}
                            hdr = st.columns([2,1,1,1,1,3])
                            hdr[0].markdown("**Ítem**")
                            hdr[1].markdown("**Buen Estado**")
                            hdr[2].markdown("**Mal Estado**")
                            hdr[3].markdown("**Req. Reparación**")
                            hdr[4].markdown("**Inst. Repuestos**")
                            hdr[5].markdown("**Observaciones**")
                            for item in ITEMS_LOC:
                                k = item.lower().replace(" ","_").replace(".","")
                                cols = st.columns([2,1,1,1,1,3])
                                cols[0].markdown(item)
                                buen = cols[1].checkbox("", key=f"l_b_{k}")
                                mal  = cols[2].checkbox("", key=f"l_m_{k}")
                                req  = cols[3].checkbox("", key=f"l_r_{k}")
                                inst = cols[4].checkbox("", key=f"l_i_{k}")
                                obs  = cols[5].text_input("", key=f"l_o_{k}", label_visibility="collapsed")
                                l_act[item] = {"buen":buen,"mal":mal,"req":req,"inst":inst,"obs":obs}

                            st.divider()
                            # ── Observaciones generales del técnico ────────
                            st.markdown("**📝 Observaciones generales del técnico**")
                            l_obs = st.text_area("Describe lo que evidenciaste durante el trabajo",
                                                  value=fila_ot.get("Observaciones",""), height=100, key="l_obs")

                            st.divider()
                            st.markdown("**⏱️ Tiempo de servicio**")
                            fc1, fc2, fc3 = st.columns(3)
                            with fc1:
                                _l_ini_idx = HORAS_12.index(fila_ot.get("Hora_Inicio","08:00 AM")) if fila_ot.get("Hora_Inicio","") in HORAS_12 else 16
                                l_lleg = st.selectbox("Hora llegada", HORAS_12, index=_l_ini_idx, key="l_lleg")
                                _l_sal_idx = HORAS_12.index(fila_ot.get("Hora_Final","05:00 PM")) if fila_ot.get("Hora_Final","") in HORAS_12 else 34
                                l_sal  = st.selectbox("Hora salida",  HORAS_12, index=_l_sal_idx,  key="l_sal")
                            with fc2:
                                l_pend = st.radio("Trabajo pendiente",   ["Sí","No"], horizontal=True, key="l_pend")
                            with fc3:
                                l_oper = st.radio("Equipo en operación", ["Sí","No"], horizontal=True, key="l_oper")

                            sc1, sc2, sc3 = st.columns(3)
                            l_nom_tec  = sc1.text_input("Nombre técnico",  value=fila_ot.get("Tecnico",""), key="l_ntec")
                            l_superv   = sc2.text_input("Supervisor",       key="l_sup")
                            l_nom_cli  = sc1.text_input("Nombre cliente",   value=fila_ot.get("Nombre_Contacto",""), key="l_ncli")
                            l_fec_fir  = sc2.text_input("Fecha firma",      value=fila_ot.get("Fecha_Ejecucion",""), key="l_ffir")

                            gen_loc = st.form_submit_button("✅ Finalizar y Guardar", type="primary", use_container_width=True)

                            if gen_loc:
                                def ck(v): return "✔" if v else ""
                                # Encuesta: se lee en fase 2 desde session_state
                                l_enc_exp   = st.session_state.get(f"l_enc_exp_{id_ot_sel}", 0)
                                l_enc_cal   = st.session_state.get(f"l_enc_cal_{id_ot_sel}", 0)
                                l_enc_cum   = st.session_state.get(f"l_enc_cum_{id_ot_sel}", 0)
                                l_enc_pre   = st.session_state.get(f"l_enc_pre_{id_ot_sel}", 0)
                                l_enc_com   = st.session_state.get(f"l_enc_com_{id_ot_sel}", 0)
                                l_enc_total = l_enc_exp + l_enc_cal + l_enc_cum + l_enc_pre + l_enc_com
                                l_enc_obs   = st.session_state.get(f"l_enc_obs_{id_ot_sel}", "")
                                tipo_mto = " | ".join(filter(None,[
                                    "Preventivo" if l_prev else "",
                                    "Correctivo" if l_corr else "",
                                    "Visita Técnica" if l_vis else "",
                                    "Emergencia" if l_emer else "",
                                ]))
                                sistemas = ", ".join(filter(None,[
                                    "Mecánico" if l_mec else "","Neumático" if l_neu else "",
                                    "Eléctrico" if l_ele else "","Hidráulico" if l_hid else "",
                                    "Electrónico" if l_elec else "","Locativo" if l_loc else "",
                                    "Otro" if l_otro_sis else "",
                                ]))
                                filas_act = "".join(
                                    f"<tr>"
                                    f"<td style='white-space:nowrap'>{item}</td>"
                                    f"<td style='text-align:center;font-size:10pt'>{ck(v['buen'])}</td>"
                                    f"<td style='text-align:center;font-size:10pt'>{ck(v['mal'])}</td>"
                                    f"<td style='text-align:center;font-size:10pt'>{ck(v['req'])}</td>"
                                    f"<td style='text-align:center;font-size:10pt'>{ck(v['inst'])}</td>"
                                    f"<td style='word-wrap:break-word'>{v['obs']}</td>"
                                    f"</tr>"
                                    for item,v in l_act.items()
                                )
                                _logo_b64 = get_logo_base64()
                                _logo_tag = f'<img src="{_logo_b64}" style="height:60px;object-fit:contain">' if _logo_b64 else ""

                                # La firma se agrega en fase 2 (después del form)
                                _firma_loc_html = "<!--FIRMA_CLIENTE-->"

                                html_loc = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8">
<title>Reporte Locativos {id_ot_sel}</title>
<style>{css_formato_carta()}</style>
</head><body>
<div class="pagina">

<div class="header">
  <div style="display:flex;align-items:center;gap:12px">
    {_logo_tag}
    <div>
      <div class="logo">CONSTRUCCIONES MINZOE SAS</div>
      <div>Soluciones integrales en construcción, mantenimiento y climatización.</div>
      <div>Cra 5 # 8a-18 &nbsp;|&nbsp; 3175102668 – 3173748665 &nbsp;|&nbsp; construminzoe@gmail.com</div>
    </div>
  </div>
  <div style="text-align:right">
    <b>FORMATO MANTENIMIENTO Y REPARACIONES LOCATIVAS</b><br>
    <b>OT: {id_ot_sel}</b><br>
    Fecha: {l_fec_fir}
  </div>
</div>

<div style="margin-bottom:6px"><b>Tipo:</b> {tipo_mto} &nbsp;&nbsp; <b>Sistema:</b> {sistemas}</div>

<table style="table-layout:fixed;width:100%"><tr>
  <th colspan="2">DATOS DEL CLIENTE</th>
</tr><tr>
  <td style="width:28%;white-space:nowrap;font-weight:bold">Cliente:</td>
  <td>{fila_ot['Cliente']}</td>
</tr><tr>
  <td style="font-weight:bold">Ciudad:</td>
  <td>{fila_ot.get('Sede','')}</td>
</tr><tr>
  <td style="font-weight:bold">Sucursal:</td>
  <td>{fila_ot.get('Sede','')}</td>
</tr><tr>
  <td style="font-weight:bold">Contacto:</td>
  <td>{fila_ot.get('Nombre_Contacto','')}</td>
</tr><tr>
  <td style="font-weight:bold">Área intervenida:</td>
  <td>{l_area}</td>
</tr></table>

<div style="background:#f8f8f8;border:0.5pt solid #ccc;padding:4pt;margin:4pt 0;font-size:7pt">
EL INTERVENTOR CERTIFICA QUE EL TRABAJO HA SIDO EJECUTADO A SATISFACCIÓN.
</div>

<div class="section">ACTIVIDADES DE TRABAJO</div>
<table style="table-layout:fixed;width:100%">
<colgroup>
  <col style="width:22%">
  <col style="width:9%">
  <col style="width:9%">
  <col style="width:12%">
  <col style="width:12%">
  <col style="width:36%">
</colgroup>
<tr>
  <th>Ítem</th>
  <th style="text-align:center">Buen Estado</th>
  <th style="text-align:center">Mal Estado</th>
  <th style="text-align:center">Req. Reparación</th>
  <th style="text-align:center">Inst. Repuestos</th>
  <th>Observaciones</th>
</tr>
{filas_act}
</table>

<div class="section">OBSERVACIONES GENERALES DEL TÉCNICO</div>
<table><tr><td style="min-height:50px">{l_obs}</td></tr></table>

<div class="section">ENCUESTA DE SATISFACCIÓN DEL SERVICIO</div>
<table>
<tr>
  <th style="width:22%">TÉCNICOS</th>
  <th>CONCEPTO</th>
  <th style="width:8%;text-align:center">PESO</th>
  <th style="width:10%;text-align:center">PUNTAJE</th>
  <th style="width:28%">OBSERVACIONES DEL SERVICIO</th>
</tr>
<tr>
  <td rowspan="5" style="vertical-align:middle;text-align:center">{l_nom_tec}</td>
  <td>Experiencia de los Técnicos</td><td style="text-align:center">20</td><td style="text-align:center">{l_enc_exp if l_enc_exp else ""}</td>
  <td rowspan="5" style="vertical-align:top">{l_enc_obs}</td>
</tr>
<tr><td>Calidad de Servicio y Bienes</td><td style="text-align:center">20</td><td style="text-align:center">{l_enc_cal if l_enc_cal else ""}</td></tr>
<tr><td>Cumplimiento</td><td style="text-align:center">20</td><td style="text-align:center">{l_enc_cum if l_enc_cum else ""}</td></tr>
<tr><td>Presentación Personal</td><td style="text-align:center">20</td><td style="text-align:center">{l_enc_pre if l_enc_pre else ""}</td></tr>
<tr><td>Comunicación</td><td style="text-align:center">20</td><td style="text-align:center">{l_enc_com if l_enc_com else ""}</td></tr>
<tr><td></td><td><b>TOTAL</b></td><td style="text-align:center"><b>100</b></td><td style="text-align:center"><b>{l_enc_total if l_enc_total else ""}</b></td><td></td></tr>
</table>
<p style="font-size:7.5px;margin:3px 0">*La suma de los conceptos determinará la continuidad del personal: 0-50 Puntos: Malo &nbsp;|&nbsp; 51-84 Puntos: Regular &nbsp;|&nbsp; 85-100 Puntos: Bueno</p>

<table style="margin-top:6px"><tr>
  <th>TIEMPO DE SERVICIO</th><th>TRABAJO PENDIENTE</th><th>EQ EN OPERACIÓN</th>
</tr><tr>
  <td>Llegada: {l_lleg}<br>Salida: {l_sal}</td>
  <td>{l_pend}</td>
  <td>{l_oper}</td>
</tr></table>

<div style="display:flex;justify-content:space-between;margin-top:20px">
  <div>
    <div class="firma-box" style="width:180px">&nbsp;<br>FIRMA TÉCNICO</div>
    <div style="font-size:9px;margin-top:3px">Nombre: {l_nom_tec}</div>
    <div style="font-size:9px">Supervisor: {l_superv}</div>
  </div>
  <div>
    <div>
      {_firma_loc_html}
      <div style="font-size:9px;margin-top:2px;font-weight:600">FIRMA Y SELLO CLIENTE</div>
      <div style="font-size:9px;margin-top:2px">Nombre: {l_nom_cli}</div>
      <div style="font-size:9px">Fecha: {l_fec_fir}</div>
    </div>
  </div>
</div>

<div class="no-print" style="margin-top:16px;text-align:center">
  <button onclick="window.print()" style="background:#dc2626;color:white;border:none;
    padding:10px 30px;font-size:14px;border-radius:6px;cursor:pointer">
    🖨️ Imprimir / Guardar como PDF
  </button>
</div>
</div>
</body></html>"""

                                st.session_state[f"loc_html_raw_{id_ot_sel}"] = html_loc
                                st.session_state[f"loc_cli_{id_ot_sel}"]  = fila_ot["Cliente"]
                                st.session_state[f"loc_sede_{id_ot_sel}"] = fila_ot.get("Sede","")
                                st.session_state[f"loc_fec_{id_ot_sel}"]  = fila_ot.get("Fecha_Ejecucion","")

                        # ── FUERA del form: guardar locativos ─────────────
                        _loc_key = f"loc_html_{id_ot_sel}"
                        if _loc_key in st.session_state:
                            st.session_state["_ot_volver_ver"] = True
                            _html_l = st.session_state[_loc_key]
                            _cli_l  = st.session_state.get(f"loc_cli_{id_ot_sel}","")
                            _sede_l = st.session_state.get(f"loc_sede_{id_ot_sel}","")
                            _fec_l  = st.session_state.get(f"loc_fec_{id_ot_sel}","")
                            ok_h, res_h = guardar_reporte_local(_html_l, _cli_l, _sede_l, id_ot_sel, _fec_l)
                            ots.loc[ots["ID"] == id_ot_sel, "Estado"] = "En revisión"
                            save_ots(ots)
                            del st.session_state[_loc_key]
                            if ok_h:
                                st.success(f"✅ Guardado en: `{res_h}`\n\nOT **{id_ot_sel}** enviada a revisión.")
                            else:
                                st.info(f"OT **{id_ot_sel}** enviada a revisión.")
                                fmt_l = st.radio("Formato de descarga",
                                    ["📄 HTML", "📕 PDF (imprimir desde el archivo)", "🖼️ PNG/TIFF (captura)"],
                                    horizontal=True, key="fmt_loc")
                                st.download_button(
                                    "⬇️ Descargar Reporte",
                                    data=_html_l,
                                    file_name=f"Reporte_Locativos_{id_ot_sel}.html",
                                    mime="text/html",
                                    use_container_width=True,
                                    type="primary"
                                )
                                if fmt_l == "📕 PDF (imprimir desde el archivo)":
                                    st.info("💡 Abre el archivo HTML → clic en **🖨️ Imprimir / Guardar como PDF** → elige destino **Guardar como PDF**.")
                                elif fmt_l == "🖼️ PNG/TIFF (captura)":
                                    st.info("💡 Abre el archivo HTML → **Ctrl+P** → destino **Microsoft Print to PDF**, o usa la herramienta de recorte de Windows.")
                                if st.button("✅ Listo, cerrar", key="cerrar_loc"):
                                    st.rerun()
                            if ok_h:
                                st.rerun()

                with ot_com:
                    st.markdown(f"**💬 Comentarios internos — {id_ot_sel}**")
                    if st.button("🔄 Cargar comentarios", key=f"load_com_ot_{id_ot_sel}"):
                        st.session_state[f"show_com_ot_{id_ot_sel}"] = True
                    coms_ot = pd.DataFrame()
                    if st.session_state.get(f"show_com_ot_{id_ot_sel}"):
                        coms_all = load_comentarios()
                        coms_ot  = coms_all[(coms_all["Entidad"]=="OT") & (coms_all["Entidad_ID"]==id_ot_sel)] if not coms_all.empty else pd.DataFrame()
                    if coms_ot.empty:
                        st.info("Sin comentarios aún.")
                    else:
                        for _, c in coms_ot.sort_values("Fecha", ascending=False).iterrows():
                            st.markdown(f"""<div style='background:#fff5f5;border-left:3px solid #dc2626;
                                padding:8px 12px;border-radius:6px;margin:4px 0;font-size:13px'>
                                <b>{c['Usuario']}</b> <span style='color:#999;font-size:11px'>{c['Fecha']}</span><br>{c['Comentario']}
                                </div>""", unsafe_allow_html=True)
                    with st.form(f"form_com_ot_{id_ot_sel}", clear_on_submit=True):
                        nuevo_com_ot = st.text_area("Agregar comentario", key=f"com_ot_{id_ot_sel}")
                        if st.form_submit_button("💬 Agregar", type="primary"):
                            if nuevo_com_ot.strip():
                                agregar_comentario("OT", id_ot_sel, nuevo_com_ot)
                                st.success("Comentario agregado.")
                                st.rerun()

                with ot_hist:
                    st.markdown(f"**📜 Historial de cambios — {id_ot_sel}**")
                    if st.button("🔄 Cargar historial", key=f"load_hist_ot_{id_ot_sel}"):
                        st.session_state[f"show_hist_ot_{id_ot_sel}"] = True
                    hist_ot = pd.DataFrame()
                    if st.session_state.get(f"show_hist_ot_{id_ot_sel}"):
                        hist_all = load_historial()
                        hist_ot  = hist_all[(hist_all["Entidad"]=="OT") & (hist_all["Entidad_ID"]==id_ot_sel)] if not hist_all.empty else pd.DataFrame()
                    if hist_ot.empty:
                        st.info("Sin cambios registrados.")
                    else:
                        tabla_html(hist_ot[["Fecha","Usuario","Campo","Valor_Anterior","Valor_Nuevo"]].sort_values("Fecha", ascending=False).reset_index(drop=True))

                if eli is not None:
                 with eli:
                    st.warning(f"¿Eliminar la OT **{id_ot_sel}** de **{fila_ot['Cliente']}**? No se puede deshacer.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("🗑️ Sí, eliminar", type="primary", use_container_width=True, key="eli_ot"):
                            registrar_cambio("OT", id_ot_sel, "Estado", fila_ot.get("Estado",""), "ELIMINADA")
                            ots = ots[ots["ID"] != id_ot_sel].reset_index(drop=True)
                            save_ots(ots)
                            st.success("OT eliminada.")
                            st.rerun()
                    with c2:
                        st.button("❌ Cancelar", use_container_width=True, key="cancel_eli_ot")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: CONTRATOS DE MANTENIMIENTO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "contratos_mto":
    if st.session_state.get("user_rol") == "tecnico":
        st.warning("⛔ No tienes permiso para acceder a esta sección.")
        st.stop()
    import io
    ots = get_ots(); contratos = get_contratos(); equipos = get_equipos(); cli = get_cli()
    st.subheader("📄 Contratos de Mantenimiento")

    tab_con, tab_equ, tab_gen = st.tabs([
        "📋 Contratos", "🔧 Equipos / Ítems", "⚡ Generar OTs del Mes"
    ])

    # ── TAB 1: CONTRATOS ─────────────────────────────────────────────────────
    with tab_con:
        st.subheader("Nuevo contrato de mantenimiento")

        # ── PASO 1: Empresa y Servicio ────────────────────────────────────
        empresas_con = sorted(cli["Empresa"].unique().tolist()) if not cli.empty else []
        c1, c2 = st.columns(2)
        with c1:
            con_cliente = st.selectbox("Empresa *", empresas_con,
                                       index=None, placeholder="Escribe la empresa...",
                                       key="con_cli_sel")
        with c2:
            con_servicio = st.selectbox("Tipo de servicio *", SERVICIOS, key="con_serv_sel")

        con_nit_v = con_contacto_v = con_celular_v = ""
        if con_cliente and not cli.empty:
            filas_c = cli[cli["Empresa"].str.strip().str.lower() == con_cliente.strip().lower()]
            if not filas_c.empty:
                primera_c = filas_c.iloc[0]
                con_nit_v      = primera_c.get("NIT","")
                con_contacto_v = primera_c.get("Nombre_Contacto","")
                con_celular_v  = primera_c.get("Celular_Contacto","")
                c1d, c2d, c3d = st.columns(3)
                c1d.text_input("NIT",             value=con_nit_v,      disabled=True, key="con_nit_dis")
                c2d.text_input("Nombre contacto", value=con_contacto_v, disabled=True, key="con_nom_dis")
                c3d.text_input("Celular contacto",value=con_celular_v,  disabled=True, key="con_cel_dis")

        if con_cliente and con_servicio:
            st.divider()

            # ── PASO 2: Sedes con equipos del servicio ────────────────────
            if con_servicio in SERVICIOS_CON_EQUIPOS:
                eq_cli_srv = pd.DataFrame()
                if not equipos.empty:
                    eq_cli_srv = equipos[
                        (equipos["Cliente"].str.strip().str.lower() == con_cliente.strip().lower()) &
                        (equipos["Servicio"] == con_servicio)
                    ]

                if eq_cli_srv.empty:
                    st.warning(f"No hay equipos de **{con_servicio}** registrados para **{con_cliente}**. "
                               f"Registra los equipos primero en la pestaña 🔧 Equipos / Ítems.")
                else:
                    sedes_disponibles = sorted(eq_cli_srv["Sede"].unique().tolist())
                    st.success(f"✅ Se encontraron **{len(sedes_disponibles)} sede(s)** con equipos de {con_servicio}")

                    # ── PASO 3: Asignar fecha de mantenimiento por sede ───
                    st.markdown("**📅 Asigna la fecha de mantenimiento a cada sede:**")
                    st.caption("Puedes asignar diferentes fechas a diferentes sedes. Desmarca las que no van en este contrato.")

                    sede_fechas = {}
                    for _sede in sedes_disponibles:
                        _n_eq = len(eq_cli_srv[eq_cli_srv["Sede"] == _sede])
                        c_chk, c_nom, c_dat = st.columns([1, 4, 3])
                        with c_chk:
                            _inc = st.checkbox("", value=True, key=f"inc_{_sede}")
                        with c_nom:
                            st.markdown(f"**{_sede}** — {_n_eq} equipo(s)")
                        with c_dat:
                            _fecha = st.date_input("Fecha mtto", key=f"fmto_{_sede}",
                                                   value=ahora_colombia().date(),
                                                   label_visibility="collapsed")
                        if _inc:
                            sede_fechas[_sede] = _fecha

                    st.divider()

                    # ── PASO 4: Datos comunes ─────────────────────────────
                    st.markdown("**⚙️ Datos del contrato**")
                    with st.form("form_contrato_wizard"):
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            con_tecnico = st.text_input("Técnico responsable")
                            con_freq    = st.selectbox("Frecuencia", FRECUENCIAS)
                        with c2:
                            con_valor   = st.text_input("Valor contrato (COP)", placeholder="Ej: 1200000")
                            con_estado  = st.selectbox("Estado", ["Activo","Inactivo"])
                        with c3:
                            con_inicio  = st.date_input("Fecha inicio contrato", value=ahora_colombia().date())
                            con_fin     = st.date_input("Fecha fin contrato")

                        crear = st.form_submit_button(
                            f"🚀 Crear contrato y OTs para {len(sede_fechas)} sede(s)",
                            type="primary", use_container_width=True
                        )

                        if crear:
                            if not sede_fechas:
                                st.error("Selecciona al menos una sede.")
                            else:
                                nuevos_cons = []
                                nuevas_ots  = []
                                for _sede, _fecha_mto in sede_fechas.items():
                                    _filas_s = cli[
                                        (cli["Empresa"].str.strip().str.lower() == con_cliente.strip().lower()) &
                                        (cli["Sede"] == _sede)
                                    ]
                                    _cont_c   = _filas_s.iloc[0].get("Nombre_Contacto","") if not _filas_s.empty else ""
                                    _cont_cel = _filas_s.iloc[0].get("Celular_Contacto","") if not _filas_s.empty else ""
                                    _id_con   = gen_contrato_id(
                                        pd.concat([contratos, pd.DataFrame(nuevos_cons)]) if nuevos_cons else contratos
                                    )
                                    nuevos_cons.append({
                                        "ID_Contrato":      _id_con,
                                        "Fecha_Inicio":     con_inicio.strftime("%Y-%m-%d"),
                                        "Fecha_Fin":        con_fin.strftime("%Y-%m-%d"),
                                        "Cliente":          con_cliente,
                                        "NIT":              con_nit_v,
                                        "Sede":             _sede,
                                        "Nombre_Contacto":  _cont_c,
                                        "Celular_Contacto": _cont_cel,
                                        "Servicio":         con_servicio,
                                        "Frecuencia":       con_freq,
                                        "Tecnico":          con_tecnico,
                                        "Valor_Contrato":   con_valor,
                                        "Estado_Contrato":  con_estado,
                                    })

                                    # ── OTs: UNA POR EQUIPO (Aires/UPS/CCTV) o UNA POR SEDE (Locativos/Aseo) ──
                                    _equipos_sede = eq_cli_srv[eq_cli_srv["Sede"] == _sede]
                                    if con_servicio in SERVICIOS_CON_EQUIPOS and not _equipos_sede.empty:
                                        for _, _eq in _equipos_sede.iterrows():
                                            _desc = (f"Mtto {con_freq.lower()} — "
                                                     f"{_eq.get('Marca','')} {_eq.get('Modelo','')} "
                                                     f"S/N:{_eq.get('Numero_Serie','')} "
                                                     f"Ubic:{_eq.get('Ubicacion','')}")
                                            nuevas_ots.append({
                                                "ID":              generate_ot_id(
                                                    pd.concat([ots, pd.DataFrame(nuevas_ots)]) if nuevas_ots else ots
                                                ),
                                                "Origen":          "Contrato Mantenimiento",
                                                "Creado_Por":      st.session_state.get("user_nombre",""),
                                                "SOL_Ref":         _id_con,
                                                "Fecha_Creacion":  ahora_colombia().strftime("%Y-%m-%d %H:%M"),
                                                "Fecha_Limite":    _fecha_mto.strftime("%Y-%m-%d") + " 18:00",
                                                "Cliente":         con_cliente, "NIT": con_nit_v,
                                                "Sede":            _sede,
                                                "Nombre_Contacto": _cont_c, "Celular_Contacto": _cont_cel,
                                                "Servicio":        con_servicio,
                                                "Descripcion":     _desc,
                                                "SLA": "Programado", "Zona": "Z0",
                                                "Tecnico": con_tecnico, "Celular_Tecnico": "",
                                                "Fecha_Ejecucion": _fecha_mto.strftime("%Y-%m-%d"),
                                                "Hora_Inicio": "", "Hora_Final": "",
                                                "Horas_Laboradas": "", "Materiales": "",
                                                "Valor_COP": con_valor,
                                                "Estado": "Programada", "Observaciones": "",
                                            })
                                    else:
                                        # Una OT por sede (Locativos, Aseo, Obra Civil, etc.)
                                        nuevas_ots.append({
                                            "ID":              generate_ot_id(
                                                pd.concat([ots, pd.DataFrame(nuevas_ots)]) if nuevas_ots else ots
                                            ),
                                            "Origen":          "Contrato Mantenimiento",
                                            "Creado_Por":      st.session_state.get("user_nombre",""),
                                            "SOL_Ref":         _id_con,
                                            "Fecha_Creacion":  ahora_colombia().strftime("%Y-%m-%d %H:%M"),
                                            "Fecha_Limite":    _fecha_mto.strftime("%Y-%m-%d") + " 18:00",
                                            "Cliente":         con_cliente, "NIT": con_nit_v,
                                            "Sede":            _sede,
                                            "Nombre_Contacto": _cont_c, "Celular_Contacto": _cont_cel,
                                            "Servicio":        con_servicio,
                                            "Descripcion":     f"Mantenimiento {con_freq.lower()} de {con_servicio}",
                                            "SLA": "Programado", "Zona": "Z0",
                                            "Tecnico": con_tecnico, "Celular_Tecnico": "",
                                            "Fecha_Ejecucion": _fecha_mto.strftime("%Y-%m-%d"),
                                            "Hora_Inicio": "", "Hora_Final": "",
                                            "Horas_Laboradas": "", "Materiales": "",
                                            "Valor_COP": con_valor,
                                            "Estado": "Programada", "Observaciones": "",
                                        })

                                contratos = pd.concat([contratos, pd.DataFrame(nuevos_cons)], ignore_index=True)
                                ots       = pd.concat([ots,       pd.DataFrame(nuevas_ots)],  ignore_index=True)
                                ok_con = save_contratos(contratos)
                                ok_ot  = save_ots(ots)
                                if ok_con is not False and ok_ot is not False:
                                    st.success(f"✅ Se crearon **{len(nuevos_cons)} contrato(s)** y "
                                               f"**{len(nuevas_ots)} OT(s)** de mantenimiento.")
                                else:
                                    st.error("❌ Hubo un error al guardar. Intenta de nuevo.")
                                st.rerun()

            else:
                # Servicio sin equipos: formulario simple
                with st.form("form_contrato_simple"):
                    c1, c2 = st.columns(2)
                    with c1:
                        con_sede    = st.text_input("Sede / Sucursal")
                        con_tecnico = st.text_input("Técnico responsable")
                        con_freq    = st.selectbox("Frecuencia", FRECUENCIAS)
                    with c2:
                        con_valor   = st.text_input("Valor del contrato (COP)")
                        con_inicio  = st.date_input("Fecha inicio", value=ahora_colombia().date())
                        con_fin     = st.date_input("Fecha fin")
                        con_estado  = st.selectbox("Estado", ["Activo", "Inactivo"])
                    if st.form_submit_button("💾 Guardar contrato", type="primary", use_container_width=True):
                        nuevo_con = {
                            "ID_Contrato":      gen_contrato_id(contratos),
                            "Fecha_Inicio":     con_inicio.strftime("%Y-%m-%d"),
                            "Fecha_Fin":        con_fin.strftime("%Y-%m-%d"),
                            "Cliente":          con_cliente, "NIT": con_nit_v,
                            "Sede":             con_sede,
                            "Nombre_Contacto":  con_contacto_v, "Celular_Contacto": con_celular_v,
                            "Servicio":         con_servicio, "Frecuencia": con_freq,
                            "Tecnico":          con_tecnico, "Valor_Contrato": con_valor,
                            "Estado_Contrato":  con_estado,
                        }
                        contratos = pd.concat([contratos, pd.DataFrame([nuevo_con])], ignore_index=True)
                        save_contratos(contratos)
                        st.success(f"✅ Contrato **{nuevo_con['ID_Contrato']}** registrado.")

        # ── Eliminar OTs por ID de contrato (siempre visible) ────────────
        st.divider()
        st.markdown("**🗑️ Eliminar OTs mal generadas**")
        if not ots.empty:
            ots_mto = ots[ots["Origen"] == "Contrato Mantenimiento"] if "Origen" in ots.columns else pd.DataFrame()
            if not ots_mto.empty:
                ids_con_ref = sorted(ots_mto["SOL_Ref"].unique().tolist())
                sel_con_ref = st.selectbox("Contrato (SOL_Ref de las OTs)", ids_con_ref, key="sel_con_ref_del")
                ots_a_borrar = ots_mto[ots_mto["SOL_Ref"] == sel_con_ref]
                st.caption(f"{len(ots_a_borrar)} OT(s) asociadas a este contrato")
                if not ots_a_borrar.empty:
                    tabla_html(ots_a_borrar[["ID","Sede","Servicio","Descripcion","Tecnico","Estado"]].reset_index(drop=True))
                if st.button("🗑️ Eliminar estas OTs", type="secondary",
                             use_container_width=True, key="btn_del_ots_ref"):
                    ots = ots[ots["SOL_Ref"] != sel_con_ref].reset_index(drop=True)
                    save_ots(ots)
                    st.success(f"✅ {len(ots_a_borrar)} OT(s) eliminadas.")
                    st.rerun()
            else:
                st.info("No hay OTs de contratos de mantenimiento registradas.")

        # ── Ver y editar contratos existentes ─────────────────────────────
        st.divider()
        st.markdown("**📋 Contratos registrados**")
        if not contratos.empty:
            f_srv_con = st.multiselect("Filtrar por servicio", SERVICIOS, default=SERVICIOS, key="f_srv_con")
            vista_con = contratos[contratos["Servicio"].isin(f_srv_con)] if f_srv_con else contratos
            tabla_html(vista_con[["ID_Contrato","Cliente","Sede","Servicio","Frecuencia",
                                   "Fecha_Inicio","Fecha_Fin","Tecnico","Estado_Contrato"]].reset_index(drop=True))
            st.caption(f"{len(contratos)} contrato(s) registrado(s).")

            st.divider()
            st.markdown("**🗑️ Eliminar OTs de un contrato**")
            st.caption("Usa esto para borrar OTs mal generadas y volver a crearlas correctamente.")
            ids_con_eli = contratos["ID_Contrato"].tolist()
            sel_eli_con = st.selectbox("Contrato a limpiar", ids_con_eli, key="sel_eli_con")
            if sel_eli_con:
                ots_del_con = ots[ots["SOL_Ref"] == sel_eli_con] if not ots.empty else pd.DataFrame()
                st.caption(f"{len(ots_del_con)} OT(s) asociadas a este contrato.")
                c_del1, c_del2 = st.columns(2)
                with c_del1:
                    if st.button("🗑️ Eliminar OTs de este contrato", type="secondary",
                                 use_container_width=True, key="btn_del_ots_con"):
                        if ots_del_con.empty:
                            st.warning("No hay OTs asociadas a este contrato.")
                        else:
                            ots = ots[ots["SOL_Ref"] != sel_eli_con].reset_index(drop=True)
                            save_ots(ots)
                            st.success(f"✅ {len(ots_del_con)} OT(s) eliminadas.")
                            st.rerun()
                with c_del2:
                    if st.button("🗑️ Eliminar contrato y sus OTs", type="secondary",
                                 use_container_width=True, key="btn_del_con_y_ots"):
                        ots = ots[ots["SOL_Ref"] != sel_eli_con].reset_index(drop=True)
                        contratos = contratos[contratos["ID_Contrato"] != sel_eli_con].reset_index(drop=True)
                        save_ots(ots)
                        save_contratos(contratos)
                        st.success(f"✅ Contrato y OTs eliminados.")
                        st.rerun()

            st.divider()
            st.markdown("**✏️ Editar contrato**")
            ids_con = contratos["ID_Contrato"].tolist()
            sel_con_edit = st.selectbox("Selecciona el contrato a editar", ids_con, key="sel_con_edit")
            if sel_con_edit:
                idx_con = contratos[contratos["ID_Contrato"] == sel_con_edit].index[0]
                fc = contratos.loc[idx_con]
                with st.form("form_editar_contrato"):
                    c1, c2 = st.columns(2)
                    with c1:
                        ec_cliente  = st.text_input("Cliente",  value=fc.get("Cliente",""))
                        ec_nit      = st.text_input("NIT",      value=fc.get("NIT",""))
                        ec_sede     = st.text_input("Sede",     value=fc.get("Sede",""))
                        ec_contacto = st.text_input("Contacto", value=fc.get("Nombre_Contacto",""))
                        ec_celular  = st.text_input("Celular",  value=fc.get("Celular_Contacto",""))
                        ec_tecnico  = st.text_input("Técnico",  value=fc.get("Tecnico",""))
                    with c2:
                        ec_servicio = st.selectbox("Servicio", SERVICIOS,
                                        index=SERVICIOS.index(fc["Servicio"]) if fc["Servicio"] in SERVICIOS else 0)
                        ec_freq     = st.selectbox("Frecuencia", FRECUENCIAS,
                                        index=FRECUENCIAS.index(fc["Frecuencia"]) if fc["Frecuencia"] in FRECUENCIAS else 0)
                        ec_valor    = st.text_input("Valor COP", value=fc.get("Valor_Contrato",""))
                        try:
                            ec_inicio = st.date_input("Fecha inicio",
                                value=datetime.strptime(fc["Fecha_Inicio"],"%Y-%m-%d").date() if fc.get("Fecha_Inicio") else ahora_colombia().date())
                            ec_fin = st.date_input("Fecha fin",
                                value=datetime.strptime(fc["Fecha_Fin"],"%Y-%m-%d").date() if fc.get("Fecha_Fin") else ahora_colombia().date())
                        except Exception:
                            ec_inicio = st.date_input("Fecha inicio", value=ahora_colombia().date())
                            ec_fin    = st.date_input("Fecha fin",    value=ahora_colombia().date())
                        ec_estado = st.selectbox("Estado", ["Activo","Inactivo"],
                                        index=0 if fc.get("Estado_Contrato","Activo")=="Activo" else 1)
                    if st.form_submit_button("💾 Guardar cambios", type="primary", use_container_width=True):
                        contratos.loc[idx_con, "Cliente"]          = ec_cliente
                        contratos.loc[idx_con, "NIT"]              = ec_nit
                        contratos.loc[idx_con, "Sede"]             = ec_sede
                        contratos.loc[idx_con, "Nombre_Contacto"]  = ec_contacto
                        contratos.loc[idx_con, "Celular_Contacto"] = ec_celular
                        contratos.loc[idx_con, "Tecnico"]          = ec_tecnico
                        contratos.loc[idx_con, "Servicio"]         = ec_servicio
                        contratos.loc[idx_con, "Frecuencia"]       = ec_freq
                        contratos.loc[idx_con, "Valor_Contrato"]   = ec_valor
                        contratos.loc[idx_con, "Fecha_Inicio"]     = ec_inicio.strftime("%Y-%m-%d")
                        contratos.loc[idx_con, "Fecha_Fin"]        = ec_fin.strftime("%Y-%m-%d")
                        contratos.loc[idx_con, "Estado_Contrato"]  = ec_estado
                        save_contratos(contratos)
                        st.success(f"✅ Contrato **{sel_con_edit}** actualizado.")
                        st.rerun()
        else:
            st.info("No hay contratos registrados aún.")

    # ── TAB 2: EQUIPOS / ÍTEMS ───────────────────────────────────────────────
    with tab_equ:
        st.subheader("Registrar equipo o ítem por contrato")

        contratos_eq = contratos[contratos["Servicio"].isin(SERVICIOS_CON_EQUIPOS)] if not contratos.empty else pd.DataFrame()

        if contratos_eq.empty:
            st.warning("No hay contratos de Aires, UPS o Cámaras registrados aún.")
        else:
            # ── Selector de contrato fuera del form (reactivo) ────────────
            opciones_con = contratos_eq.apply(
                lambda r: f"{r['ID_Contrato']} — {r['Servicio']} | {r['Cliente']}", axis=1
            ).tolist()
            item_con_sel = st.selectbox("Contrato *", opciones_con, key="item_con_sel")
            id_con_sel   = item_con_sel.split(" — ")[0]
            fila_con     = contratos[contratos["ID_Contrato"] == id_con_sel].iloc[0]
            frecuencia_con = fila_con.get("Frecuencia","Mensual")
            servicio_con   = fila_con.get("Servicio","")

            # ── Selector de sede (fuera del form, reactivo) ───────────────
            # Buscar sedes del cliente en la tabla de clientes
            sedes_cliente = []
            if not cli.empty:
                filas_cli = cli[cli["Empresa"].str.strip().str.lower() == fila_con["Cliente"].strip().lower()]
                sedes_cliente = filas_cli["Sede"].tolist()

            sede_sel = st.selectbox(
                "Sede / Sucursal *",
                sedes_cliente if sedes_cliente else ["Sin sedes registradas"],
                key="item_sede_sel"
            )

            # Auto-calcular fecha primer mantenimiento según frecuencia
            hoy_item    = ahora_colombia().date()
            meses_freq  = FREQ_MESES.get(frecuencia_con, 1)
            mes_sig     = hoy_item.month - 1 + meses_freq
            anio_sig    = hoy_item.year + mes_sig // 12
            mes_sig     = mes_sig % 12 + 1
            from datetime import date as _date
            fecha_sugerida = _date(anio_sig, mes_sig, min(hoy_item.day, 28))
            st.info(f"📅 Frecuencia del contrato: **{frecuencia_con}** — Primer mantenimiento sugerido: **{fecha_sugerida}**")

            with st.form("form_item", clear_on_submit=True):
                es_aire = servicio_con == "Aires Acondicionados"

                if es_aire:
                    st.markdown("**🔧 Datos del equipo de Aire Acondicionado**")
                    c1, c2 = st.columns(2)
                    with c1:
                        item_tipo_eq  = st.text_input("Tipo de equipo", placeholder="Ej: Mini Split, Cassette, Piso-techo")
                        item_marca    = st.text_input("Marca")
                        item_modelo   = st.text_input("Modelo")
                        item_ser_cond = st.text_input("Serial Condensadora")
                        item_ser_evap = st.text_input("Serial Evaporadora")
                    with c2:
                        item_btu      = st.text_input("Capacidad en BTU o CFM", placeholder="Ej: 12000 BTU / 1 TON")
                        item_refrig   = st.selectbox("Tipo de refrigerante", REFRIGERANTES)
                        item_ubic_ev  = st.text_input("Ubicación Evaporadora", placeholder="Ej: Oficina 301")
                        item_ubic_co  = st.text_input("Ubicación Condensadora", placeholder="Ej: Azotea piso 3")
                    item_specs = f"{item_btu} | {item_refrig}"
                    item_ubic  = f"Evap: {item_ubic_ev} | Cond: {item_ubic_co}"
                    item_serie = f"Cond: {item_ser_cond} | Evap: {item_ser_evap}"
                else:
                    st.markdown("**🔧 Datos del ítem**")
                    c1, c2 = st.columns(2)
                    with c1:
                        item_tipo_eq = st.text_input("Tipo de equipo")
                        item_marca   = st.text_input("Marca")
                        item_modelo  = st.text_input("Modelo")
                        item_serie   = st.text_input("Número de serie")
                    with c2:
                        item_specs   = st.text_input("Especificaciones")
                        item_ubic    = st.text_input("Ubicación dentro de la sede")

                item_primer = st.date_input("Fecha primer mantenimiento", value=fecha_sugerida)

                if st.form_submit_button("➕ Agregar ítem", type="primary", use_container_width=True):
                    primer_m   = item_primer.strftime("%Y-%m-%d")
                    nuevo_item = {
                        "ID_Item":              gen_item_id(equipos),
                        "ID_Contrato":          id_con_sel,
                        "Cliente":              fila_con["Cliente"],
                        "Sede":                 sede_sel,
                        "Servicio":             servicio_con,
                        "Marca":                item_marca,
                        "Modelo":               f"{item_tipo_eq} {item_modelo}".strip() if es_aire else item_modelo,
                        "Numero_Serie":         item_serie,
                        "Especificaciones":     item_specs,
                        "Ubicacion":            item_ubic,
                        "Ultimo_Mantenimiento":  "",
                        "Proximo_Mantenimiento": primer_m,
                    }
                    equipos = pd.concat([equipos, pd.DataFrame([nuevo_item])], ignore_index=True)
                    save_equipos(equipos)
                    st.success(f"✅ {nuevo_item['ID_Item']} registrado — próximo mantenimiento: **{primer_m}**")

            st.divider()
            if not equipos.empty:
                buscar_eq = st.text_input("Buscar", key="buscar_equ")
                vista_eq  = equipos if not buscar_eq else equipos[
                    equipos["Cliente"].str.contains(buscar_eq, case=False, na=False) |
                    equipos["Sede"].str.contains(buscar_eq, case=False, na=False)
                ]
                st.dataframe(vista_eq, use_container_width=True, hide_index=True)
                st.caption(f"{len(equipos)} ítem(s) registrado(s).")

    # ── TAB 3: GENERAR OTs DEL MES ────────────────────────────────────────────
    with tab_gen:
        hoy        = ahora_colombia()
        mes_actual = hoy.strftime("%Y-%m")
        st.subheader(f"Generar OTs del mes — {hoy.strftime('%B %Y').capitalize()}")

        def vence_este_mes(fecha_str):
            try:
                return datetime.strptime(fecha_str, "%Y-%m-%d").strftime("%Y-%m") <= mes_actual
            except Exception:
                return False

        # ── Contratos SIN equipos (visita directa) ───────────────────────────
        contratos_visita = contratos[
            ~contratos["Servicio"].isin(SERVICIOS_CON_EQUIPOS) &
            (contratos["Estado_Contrato"] == "Activo")
        ] if not contratos.empty else pd.DataFrame()

        # Filtrar los que no tienen OT generada este mes
        def ot_ya_existe_contrato(con_id):
            if ots.empty:
                return False
            return ((ots["SOL_Ref"] == con_id) &
                    (ots["Fecha_Creacion"].str.startswith(mes_actual, na=False))).any()

        pendientes_visita = contratos_visita[
            ~contratos_visita["ID_Contrato"].apply(ot_ya_existe_contrato)
        ] if not contratos_visita.empty else pd.DataFrame()

        # ── Ítems/equipos con mantenimiento este mes ─────────────────────────
        pendientes_items = equipos[equipos["Proximo_Mantenimiento"].apply(vence_este_mes)].copy() if not equipos.empty else pd.DataFrame()

        total_pendientes = len(pendientes_visita) + len(pendientes_items)

        if total_pendientes == 0:
            st.success("✅ No hay mantenimientos pendientes este mes.")
        else:
            if not pendientes_visita.empty:
                st.warning(f"📋 **{len(pendientes_visita)} contrato(s) de visita** pendiente(s):")
                st.dataframe(pendientes_visita[["ID_Contrato", "Servicio", "Cliente", "Sede", "Frecuencia"]],
                             use_container_width=True, hide_index=True)

            if not pendientes_items.empty:
                st.warning(f"🔧 **{len(pendientes_items)} equipo(s)/ítem(s)** pendiente(s):")
                st.dataframe(pendientes_items[["ID_Item", "Servicio", "Cliente", "Sede", "Marca",
                                               "Modelo", "Ubicacion", "Proximo_Mantenimiento"]],
                             use_container_width=True, hide_index=True)

            st.divider()
            if st.button(f"⚡ Generar {total_pendientes} OT(s) pendientes del mes",
                         type="primary", use_container_width=True):
                creadas = []

                # OTs por contrato de visita
                for _, con in pendientes_visita.iterrows():
                    nueva_ot = {
                        "ID":               generate_ot_id(ots),
                        "Origen":           "Contrato Mantenimiento",
                        "SOL_Ref":          con["ID_Contrato"],
                        "Fecha_Creacion":   hoy.strftime("%Y-%m-%d %H:%M"),
                        "Fecha_Limite":     "",
                        "Cliente":          con["Cliente"],
                        "NIT":              con["NIT"],
                        "Sede":             con["Sede"],
                        "Nombre_Contacto":  con["Nombre_Contacto"],
                        "Celular_Contacto": con["Celular_Contacto"],
                        "Servicio":         con["Servicio"],
                        "Descripcion":      f"Mantenimiento preventivo {con['Frecuencia'].lower()} — Contrato {con['ID_Contrato']}",
                        "SLA":              "Programado",
                        "Zona":             "",
                        "Tecnico":          con["Tecnico"],
                        "Celular_Tecnico":  "",
                        "Fecha_Ejecucion":  "",
                        "Hora_Inicio":      "",
                        "Hora_Final":       "",
                        "Horas_Laboradas":  "",
                        "Materiales":       "",
                        "Valor_COP":        con.get("Valor_Contrato", ""),
                        "Estado":           "Programada",
                        "Observaciones":    "",
                    }
                    ots = pd.concat([ots, pd.DataFrame([nueva_ot])], ignore_index=True)
                    creadas.append(nueva_ot["ID"])

                # OTs por ítem/equipo
                for _, item in pendientes_items.iterrows():
                    con_row    = contratos[contratos["ID_Contrato"] == item["ID_Contrato"]]
                    frecuencia = con_row.iloc[0]["Frecuencia"] if not con_row.empty else "Mensual"
                    tecnico    = con_row.iloc[0]["Tecnico"]    if not con_row.empty else ""
                    nueva_ot = {
                        "ID":               generate_ot_id(ots),
                        "Origen":           "Contrato Mantenimiento",
                        "SOL_Ref":          item["ID_Contrato"],
                        "Fecha_Creacion":   hoy.strftime("%Y-%m-%d %H:%M"),
                        "Fecha_Limite":     "",
                        "Cliente":          item["Cliente"],
                        "NIT":              con_row.iloc[0]["NIT"] if not con_row.empty else "",
                        "Sede":             item["Sede"],
                        "Nombre_Contacto":  con_row.iloc[0]["Nombre_Contacto"] if not con_row.empty else "",
                        "Celular_Contacto": con_row.iloc[0]["Celular_Contacto"] if not con_row.empty else "",
                        "Servicio":         item["Servicio"],
                        "Descripcion":      (
                            f"Mto. preventivo {frecuencia.lower()} — "
                            f"{item['Marca']} {item['Modelo']} | S/N: {item['Numero_Serie']} | "
                            f"{item['Especificaciones']} | Ubicación: {item['Ubicacion']}"
                        ),
                        "SLA":              "Programado",
                        "Zona":             "",
                        "Tecnico":          tecnico,
                        "Celular_Tecnico":  "",
                        "Fecha_Ejecucion":  "",
                        "Hora_Inicio":      "",
                        "Hora_Final":       "",
                        "Horas_Laboradas":  "",
                        "Materiales":       "",
                        "Valor_COP":        con_row.iloc[0].get("Valor_Contrato", "") if not con_row.empty else "",
                        "Estado":           "Programada",
                        "Observaciones":    f"Ítem: {item['ID_Item']}",
                    }
                    ots = pd.concat([ots, pd.DataFrame([nueva_ot])], ignore_index=True)
                    creadas.append(nueva_ot["ID"])
                    idx_i = equipos[equipos["ID_Item"] == item["ID_Item"]].index[0]
                    equipos.loc[idx_i, "Ultimo_Mantenimiento"]  = hoy.strftime("%Y-%m-%d")
                    equipos.loc[idx_i, "Proximo_Mantenimiento"] = proxima_fecha(hoy.strftime("%Y-%m-%d"), frecuencia)

                save_ots(ots)
                save_equipos(equipos)
                st.success(f"✅ {len(creadas)} OT(s) creadas: {', '.join(creadas)}")
                st.info("Encuéntralas en 🛠️ Órdenes de Trabajo con origen 'Contrato Mantenimiento'.")
                st.rerun()

        st.divider()
        st.subheader("Cronograma general de mantenimientos")
        if not equipos.empty:
            st.dataframe(
                equipos[["ID_Item", "Servicio", "Cliente", "Sede", "Marca", "Modelo",
                          "Ultimo_Mantenimiento", "Proximo_Mantenimiento"]].sort_values("Proximo_Mantenimiento"),
                use_container_width=True, hide_index=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: COMPRAS Y VENTAS (NUEVA VERSIÓN)
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "compras_ventas":
    if st.session_state.get("user_rol") == "tecnico":
        st.warning("⛔ No tienes permiso para acceder a esta sección.")
        st.stop()
    import io
    ots = get_ots(); ventas = get_ventas(); costos = get_costos(); cv = get_cv()
    st.subheader("💰 Compras y Ventas")

    tab_ven, tab_cos, tab_res = st.tabs(["📤 Ventas / Facturación", "📥 Costos / Compras", "📊 Rentabilidad"])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1: VENTAS / FACTURACIÓN
    # ════════════════════════════════════════════════════════════════════════
    with tab_ven:
        st.subheader("Registrar Factura de Venta")

        # Vincular a OT
        ots_fin_v = ots[ots["Estado"] == "Finalizada"] if not ots.empty else pd.DataFrame()
        ops_ot_v  = ["— Sin vincular —"] + (
            ots_fin_v.apply(lambda r: f"{r['ID']} | {r['Cliente']} | {r['Servicio']}", axis=1).tolist()
            if not ots_fin_v.empty else []
        )
        ot_sel_v = st.selectbox("Vincular a OT finalizada (opcional)", ops_ot_v, key="ot_sel_v")

        v_ot_ref = v_sol_ref = v_cliente = v_servicio = ""
        if ot_sel_v != "— Sin vincular —":
            ot_id_v    = ot_sel_v.split(" | ")[0]
            fila_ot_v  = ots[ots["ID"] == ot_id_v].iloc[0]
            v_ot_ref   = ot_id_v
            v_sol_ref  = fila_ot_v.get("SOL_Ref", "")
            v_cliente  = fila_ot_v["Cliente"]
            v_servicio = fila_ot_v["Servicio"]
            st.info(f"📋 **{v_cliente}** | {v_servicio}")

        with st.form("form_venta", clear_on_submit=True):
            st.markdown("**📄 Datos de la Factura**")
            c1, c2, c3 = st.columns(3)
            with c1:
                v_num_fac  = st.text_input("Número de Factura", placeholder="Ej: FV-001")
                v_cot      = st.text_input("Cotización Siigo", placeholder="Ej: COT-2026-001")
            with c2:
                v_fec_fac  = st.date_input("Fecha Facturación", value=ahora_colombia().date())
                v_fec_ven  = st.date_input("Fecha Vencimiento")
            with c3:
                v_oc       = st.text_input("Orden de Compra", placeholder="Ej: OC-12345")
                if not v_cliente:
                    v_cliente  = st.text_input("Cliente", key="v_cli_man")
                    v_servicio = st.selectbox("Servicio", SERVICIOS, key="v_ser_man")

            st.divider()
            st.markdown("**💵 Valores**")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                v_base     = st.text_input("Valor Antes de IVA", placeholder="0")
            with c2:
                v_aplica_iva = st.checkbox("Aplica IVA 19%", value=True)
            with c3:
                v_rete_pct = st.text_input("Retefuente %", value="3.5", placeholder="3.5")
            with c4:
                v_rica_pct = st.text_input("ReteICA %", value="0.414", placeholder="0.414")

            # Cálculo en tiempo real
            base_n  = to_num(v_base)
            iva_n   = base_n * 0.19 if v_aplica_iva else 0
            rete_n  = base_n * (to_num(v_rete_pct) / 100)
            rica_n  = base_n * (to_num(v_rica_pct)  / 100)
            total_n = base_n + iva_n - rete_n - rica_n

            if base_n > 0:
                st.divider()
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Valor Base",     f"${base_n:,.0f}")
                c2.metric("IVA 19%",        f"${iva_n:,.0f}")
                c3.metric("Retefuente",     f"-${rete_n:,.0f}")
                c4.metric("ReteICA",        f"-${rica_n:,.0f}")
                c5.metric("💰 Total a Pagar", f"${total_n:,.0f}")

            v_estado_p = st.selectbox("Estado de Pago", ESTADOS_PAGO)

            if st.form_submit_button("💾 Guardar Factura", type="primary", use_container_width=True):
                if not v_num_fac.strip():
                    st.error("El número de factura es obligatorio.")
                else:
                    nueva_v = {
                        "ID_Factura":        gen_fac_id(ventas),
                        "Fecha_Facturacion": v_fec_fac.strftime("%Y-%m-%d"),
                        "Fecha_Vencimiento": v_fec_ven.strftime("%Y-%m-%d"),
                        "OT_Ref":            v_ot_ref,
                        "SOL_Ref":           v_sol_ref,
                        "Cliente":           v_cliente,
                        "Servicio":          v_servicio,
                        "Cotizacion_Siigo":  v_cot.strip(),
                        "Orden_Compra":      v_oc.strip(),
                        "Valor_Antes_IVA":   f"{base_n:.0f}",
                        "IVA":               f"{iva_n:.0f}",
                        "Retefuente":        f"{rete_n:.0f}",
                        "Retica":            f"{rica_n:.0f}",
                        "Total_A_Pagar":     f"{total_n:.0f}",
                        "Estado_Pago":       v_estado_p,
                    }
                    ventas = pd.concat([ventas, pd.DataFrame([nueva_v])], ignore_index=True)
                    save_ventas(ventas)
                    st.success(f"✅ Factura **{v_num_fac}** guardada — Total a pagar: **${total_n:,.0f}**")

        st.divider()
        st.subheader("Facturas registradas")
        if ventas.empty:
            st.info("Aún no hay facturas registradas.")
        else:
            buscar_v = st.text_input("Buscar cliente", key="buscar_v")
            vista_v  = ventas if not buscar_v else ventas[
                ventas["Cliente"].str.contains(buscar_v, case=False, na=False)
            ]
            COLORES_PAGO = {
                "Pendiente": ("#fff3cd", "#7d5a00"),
                "Pagada":    ("#d1fae5", "#064e3b"),
                "Vencida":   ("#fee2e2", "#7f1d1d"),
                "Anulada":   ("#f3f4f6", "#374151"),
            }
            tabla_html(vista_v.reset_index(drop=True),
                       color_col="Estado_Pago", colores_estado=COLORES_PAGO,
                       fmt_cols=["Valor_Antes_IVA","IVA","Retefuente","Retica","Total_A_Pagar"])
            st.caption(f"{len(ventas)} factura(s) registrada(s).")

            buf_v = io.BytesIO()
            with pd.ExcelWriter(buf_v, engine="openpyxl") as w:
                vista_v.to_excel(w, index=False, sheet_name="Ventas")
            st.download_button("⬇️ Exportar Excel", data=buf_v.getvalue(),
                               file_name=f"ventas_{ahora_colombia().strftime('%Y%m%d')}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2: COSTOS / COMPRAS
    # ════════════════════════════════════════════════════════════════════════
    with tab_cos:
        st.subheader("Registrar Costo del Trabajo")

        ots_fin_c = ots[ots["Estado"] == "Finalizada"] if not ots.empty else pd.DataFrame()
        ops_ot_c  = ["— Sin vincular —"] + (
            ots_fin_c.apply(lambda r: f"{r['ID']} | {r['Cliente']} | {r['Servicio']}", axis=1).tolist()
            if not ots_fin_c.empty else []
        )
        ot_sel_c = st.selectbox("Vincular a OT finalizada (opcional)", ops_ot_c, key="ot_sel_c")

        c_ot_ref = c_sol_ref = c_cliente = c_servicio = c_val_tec = ""
        if ot_sel_c != "— Sin vincular —":
            ot_id_c    = ot_sel_c.split(" | ")[0]
            fila_ot_c  = ots[ots["ID"] == ot_id_c].iloc[0]
            c_ot_ref   = ot_id_c
            c_sol_ref  = fila_ot_c.get("SOL_Ref", "")
            c_cliente  = fila_ot_c["Cliente"]
            c_servicio = fila_ot_c["Servicio"]
            c_val_tec  = fila_ot_c.get("Valor_COP", "")
            st.info(f"📋 **{c_cliente}** | {c_servicio}")

        with st.form("form_costo", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                cc_tec = st.text_input("Valor asignado al técnico (COP)",
                                       value=c_val_tec, placeholder="Ej: 150000")
            with c2:
                cc_mat = st.text_input("Valor de materiales (COP)", placeholder="Ej: 80000")
            with c3:
                cc_fac = st.text_input("N° Factura materiales", placeholder="Ej: FAC-001")

            if not c_cliente:
                c1, c2 = st.columns(2)
                with c1:
                    c_cliente  = st.text_input("Cliente", key="c_cli_man")
                with c2:
                    c_servicio = st.selectbox("Servicio", SERVICIOS, key="c_ser_man")

            tec_n2  = to_num(cc_tec)
            mat_n2  = to_num(cc_mat)
            tot_cos = tec_n2 + mat_n2

            if tot_cos > 0:
                c1, c2, c3 = st.columns(3)
                c1.metric("Valor técnico",    f"${tec_n2:,.0f}")
                c2.metric("Valor materiales", f"${mat_n2:,.0f}")
                c3.metric("Total costo",      f"${tot_cos:,.0f}")

            if st.form_submit_button("💾 Guardar costo", type="primary", use_container_width=True):
                nuevo_cos = {
                    "ID_Costo":          gen_costo_id(costos),
                    "Fecha":             ahora_colombia().strftime("%Y-%m-%d %H:%M"),
                    "OT_Ref":            c_ot_ref,
                    "SOL_Ref":           c_sol_ref,
                    "Cliente":           c_cliente,
                    "Servicio":          c_servicio,
                    "Valor_Tecnico":     f"{tec_n2:.0f}",
                    "Valor_Materiales":  f"{mat_n2:.0f}",
                    "Factura_Materiales": cc_fac.strip(),
                    "Total_Costo":       f"{tot_cos:.0f}",
                }
                costos = pd.concat([costos, pd.DataFrame([nuevo_cos])], ignore_index=True)
                save_costos(costos)
                st.success(f"✅ Costo guardado — Total: **${tot_cos:,.0f}**")

        st.divider()
        st.subheader("Costos registrados")
        if costos.empty:
            st.info("Aún no hay costos registrados.")
        else:
            tabla_html(costos.reset_index(drop=True),
                       fmt_cols=["Valor_Tecnico","Valor_Materiales","Total_Costo"])
            buf_c = io.BytesIO()
            with pd.ExcelWriter(buf_c, engine="openpyxl") as w:
                costos.to_excel(w, index=False, sheet_name="Costos")
            st.download_button("⬇️ Exportar Excel", data=buf_c.getvalue(),
                               file_name=f"costos_{ahora_colombia().strftime('%Y%m%d')}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3: RENTABILIDAD
    # ════════════════════════════════════════════════════════════════════════
    with tab_res:
        st.subheader("Resumen de Rentabilidad")

        tot_venta  = ventas["Valor_Antes_IVA"].apply(to_num).sum() if not ventas.empty else 0
        tot_iva    = ventas["IVA"].apply(to_num).sum()             if not ventas.empty else 0
        tot_rete   = ventas["Retefuente"].apply(to_num).sum()      if not ventas.empty else 0
        tot_rica   = ventas["Retica"].apply(to_num).sum()          if not ventas.empty else 0
        tot_cobrar = ventas["Total_A_Pagar"].apply(to_num).sum()   if not ventas.empty else 0
        tot_costo  = costos["Total_Costo"].apply(to_num).sum()     if not costos.empty else 0
        utilidad   = tot_venta - tot_costo
        margen     = (utilidad / tot_venta * 100) if tot_venta > 0 else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Ventas (base)",  f"${tot_venta:,.0f}")
        c2.metric("IVA Generado",         f"${tot_iva:,.0f}")
        c3.metric("Retefuente",           f"${tot_rete:,.0f}")
        c4.metric("ReteICA",              f"${tot_rica:,.0f}")

        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total a Cobrar",       f"${tot_cobrar:,.0f}")
        c2.metric("Total Costos",         f"${tot_costo:,.0f}")
        c3.metric("Utilidad Bruta",       f"${utilidad:,.0f}")
        c4.metric("Margen",               f"{margen:.1f}%")

        if not ventas.empty:
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Ventas por servicio**")
                st.bar_chart(ventas.groupby("Servicio")["Valor_Antes_IVA"].apply(
                    lambda x: x.apply(to_num).sum()))
            with c2:
                st.write("**Estado de pagos**")
                st.bar_chart(ventas["Estado_Pago"].value_counts())



# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: HOJAS DE VIDA EQUIPOS AIRES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "hojas_vida":
    equipos    = get_equipos()
    contratos  = get_contratos()
    ots        = get_ots()

    st.subheader("🗂️ Hojas de Vida — Equipos de Aire Acondicionado")

    if equipos.empty:
        st.info("No hay equipos registrados. Ve a 📄 Contratos de Mantenimiento → 🔧 Equipos / Ítems para registrarlos.")
    else:
        # ── Filtros ────────────────────────────────────────────────────────
        equipos_aires = equipos[equipos["Servicio"] == "Aires Acondicionados"] if "Servicio" in equipos.columns else equipos

        clientes_eq = sorted(equipos_aires["Cliente"].unique().tolist()) if not equipos_aires.empty else []
        cli_sel = st.selectbox("Selecciona el cliente", clientes_eq, key="hv_cli")

        if cli_sel:
            sedes_eq = sorted(equipos_aires[equipos_aires["Cliente"] == cli_sel]["Sede"].unique().tolist())
            sede_sel = st.selectbox("Selecciona la sede", sedes_eq, key="hv_sede")

            if sede_sel:
                equipos_filtrados = equipos_aires[
                    (equipos_aires["Cliente"] == cli_sel) &
                    (equipos_aires["Sede"] == sede_sel)
                ].reset_index(drop=True)

                st.divider()
                st.markdown(f"**{len(equipos_filtrados)} equipo(s) registrado(s) en {sede_sel} — {cli_sel}**")

                # ── Lista de equipos ──────────────────────────────────────
                for _, eq in equipos_filtrados.iterrows():
                    # Contar mantenimientos realizados
                    id_item   = eq.get("ID_Item", eq.get("ID_Equipo",""))
                    id_cont   = eq.get("ID_Contrato","")
                    ots_eq    = ots[
                        (ots["SOL_Ref"] == id_cont) &
                        (ots["Observaciones"].str.contains(id_item, na=False))
                    ] if not ots.empty else pd.DataFrame()
                    n_mtos    = len(ots_eq)
                    ultimo    = eq.get("Ultimo_Mantenimiento","—")
                    proximo   = eq.get("Proximo_Mantenimiento","—")

                    # Alerta próximo mantenimiento
                    alerta = ""
                    try:
                        dias = (datetime.strptime(proximo, "%Y-%m-%d") - datetime.now()).days
                        if dias < 0:      alerta = "🔴 Vencido"
                        elif dias <= 15:  alerta = "🟡 Próximo"
                        else:             alerta = "🟢 Al día"
                    except Exception:
                        alerta = "⚪ Sin fecha"

                    with st.expander(
                        f"{alerta} **{id_item}** — {eq.get('Marca','')} {eq.get('Modelo','')} | "
                        f"{eq.get('Especificaciones','')} | {eq.get('Ubicacion','')} | "
                        f"{n_mtos} mantenimiento(s)"
                    ):
                        # Datos básicos
                        st.markdown("#### 🔧 Datos del equipo")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**ID:** {id_item}")
                            st.write(f"**Marca:** {eq.get('Marca','—')}")
                            st.write(f"**Modelo:** {eq.get('Modelo','—')}")
                            st.write(f"**Serial:** {eq.get('Numero_Serie','—')}")
                        with c2:
                            st.write(f"**Capacidad:** {eq.get('Especificaciones','—')}")
                            st.write(f"**Ubicación:** {eq.get('Ubicacion','—')}")
                            st.write(f"**Último mto.:** {ultimo}")
                            st.write(f"**Próximo mto.:** {proximo} {alerta}")

                        # Historial de mantenimientos
                        st.markdown("#### 📋 Historial de mantenimientos")
                        if ots_eq.empty:
                            st.info("Sin mantenimientos registrados aún.")
                        else:
                            hist_cols = ["ID","Fecha_Creacion","Servicio","Tecnico",
                                         "Fecha_Ejecucion","Estado","Observaciones"]
                            hist_vis  = [c for c in hist_cols if c in ots_eq.columns]
                            ots_ord   = ots_eq.sort_values("Fecha_Creacion", ascending=False).reset_index(drop=True)
                            tabla_html(
                                ots_ord[hist_vis],
                                color_col="Estado",
                                colores_estado={
                                    "Programada":  ("#e0e7ff","#1e3a8a"),
                                    "En ejecución":("#fef3c7","#78350f"),
                                    "Finalizada":  ("#d1fae5","#064e3b"),
                                    "Cancelada":   ("#fee2e2","#7f1d1d"),
                                }
                            )
                            st.caption(f"Total: {n_mtos} mantenimiento(s) | Último: {ots_ord.iloc[0]['Fecha_Creacion']}")

                        # Editar datos del equipo
                        with st.expander("✏️ Editar datos del equipo"):
                            with st.form(f"form_edit_eq_{id_item}"):
                                ec1, ec2 = st.columns(2)
                                with ec1:
                                    e_marca  = st.text_input("Marca",    value=eq.get("Marca",""))
                                    e_modelo = st.text_input("Modelo",   value=eq.get("Modelo",""))
                                    e_serial = st.text_input("Serial",   value=eq.get("Numero_Serie",""))
                                with ec2:
                                    e_specs  = st.text_input("Capacidad/Especificaciones", value=eq.get("Especificaciones",""))
                                    e_ubic   = st.text_input("Ubicación",value=eq.get("Ubicacion",""))
                                    e_prox   = st.text_input("Próximo mantenimiento (YYYY-MM-DD)", value=proximo)
                                if st.form_submit_button("💾 Guardar cambios", type="primary"):
                                    idx_e = equipos[(equipos["ID_Item"] == id_item) | (equipos.get("ID_Equipo","") == id_item)].index
                                    if len(idx_e) > 0:
                                        equipos.loc[idx_e[0], "Marca"]           = e_marca
                                        equipos.loc[idx_e[0], "Modelo"]          = e_modelo
                                        equipos.loc[idx_e[0], "Numero_Serie"]    = e_serial
                                        equipos.loc[idx_e[0], "Especificaciones"]= e_specs
                                        equipos.loc[idx_e[0], "Ubicacion"]       = e_ubic
                                        equipos.loc[idx_e[0], "Proximo_Mantenimiento"] = e_prox
                                        save_equipos(equipos)
                                        st.success(f"✅ Equipo {id_item} actualizado.")
                                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: CALENDARIO DE VISITAS
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "calendario":
    import plotly.express as px
    ots = get_ots()
    st.subheader("📅 Calendario de Visitas")

    if ots.empty:
        st.info("No hay OTs registradas.")
    else:
        # Filtros
        c1, c2, c3 = st.columns(3)
        with c1:
            mes_cal = st.selectbox("Mes", list(MESES_CARPETA.values()),
                                   index=ahora_colombia().month - 1, key="cal_mes")
        with c2:
            anio_cal = st.selectbox("Año", [2024, 2025, 2026, 2027, 2028, 2029, 2030],
                                    index=[2024,2025,2026,2027,2028,2029,2030].index(ahora_colombia().year),
                                    key="cal_anio")
        with c3:
            tecnicos_lista = ["Todos"] + sorted([t for t in ots["Tecnico"].dropna().unique().tolist() if t.strip()])
            tec_sel = st.selectbox("Técnico", tecnicos_lista, key="cal_tec")
            f_tec_cal = [] if tec_sel == "Todos" else [tec_sel]

        # Filtrar OTs con fecha de ejecución
        ots_cal = ots[ots["Fecha_Ejecucion"].str.strip() != ""].copy() if "Fecha_Ejecucion" in ots.columns else pd.DataFrame()

        if not ots_cal.empty:
            num_mes = list(MESES_CARPETA.keys())[list(MESES_CARPETA.values()).index(mes_cal)]
            prefijo_mes = f"{anio_cal}-{num_mes}"
            ots_cal = ots_cal[ots_cal["Fecha_Ejecucion"].str.startswith(prefijo_mes, na=False)]
            if f_tec_cal:
                ots_cal = ots_cal[ots_cal["Tecnico"].isin(f_tec_cal)]

        if ots_cal.empty:
            st.info(f"No hay visitas programadas en {mes_cal} {anio_cal}.")
        else:
            # Gantt / timeline de visitas
            COLORES_CAL = {
                "Programada":   "#7c3aed",
                "En ejecución": "#ea580c",
                "Finalizada":   "#16a34a",
                "Cancelada":    "#dc2626",
            }
            ots_cal["Color"] = ots_cal["Estado"].map(COLORES_CAL).fillna("#666")
            ots_cal["Inicio"] = pd.to_datetime(ots_cal["Fecha_Ejecucion"], errors="coerce")
            ots_cal["Fin"]    = ots_cal["Inicio"] + pd.Timedelta(hours=4)
            ots_cal["Label"]  = ots_cal["ID"] + " | " + ots_cal["Cliente"] + " | " + ots_cal["Tecnico"].fillna("Sin técnico")

            fig = px.timeline(
                ots_cal.dropna(subset=["Inicio"]),
                x_start="Inicio", x_end="Fin",
                y="Label", color="Estado",
                color_discrete_map=COLORES_CAL,
                title=f"📅 Visitas programadas — {mes_cal.split('_')[1].capitalize()} {anio_cal}",
                hover_data=["Cliente","Sede","Servicio","Tecnico","Estado"],
            )
            fig.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(color="#111111", size=12),
                title_font=dict(color="#dc2626", size=16),
                height=max(350, len(ots_cal) * 50 + 120),
                xaxis_title="Fecha", yaxis_title="",
                yaxis=dict(tickfont=dict(color="#111111", size=11)),
                xaxis=dict(tickfont=dict(color="#111111", size=11)),
                legend=dict(font=dict(color="#111111")),
            )
            fig.update_traces(textfont_color="#111111")
            st.plotly_chart(fig, use_container_width=True)

            st.divider()
            st.markdown(f"**{len(ots_cal)} visita(s) en {mes_cal.split('_')[1].capitalize()} {anio_cal}**")
            tabla_html(
                ots_cal[["ID","Fecha_Ejecucion","Hora_Inicio","Hora_Final","Cliente","Sede","Servicio","Tecnico","Estado"]].reset_index(drop=True),
                color_col="Estado",
                colores_estado={
                    "Programada":   ("#e0e7ff","#1e3a8a"),
                    "En ejecución": ("#fef3c7","#78350f"),
                    "Finalizada":   ("#d1fae5","#064e3b"),
                    "Cancelada":    ("#fee2e2","#7f1d1d"),
                }
            )


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: GESTIÓN DE USUARIOS (solo admin) — limpia, sin migración
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "gestion_usuarios":
    if st.session_state.get("user_rol") != "admin":
        st.error("Acceso restringido.")
        st.stop()
    st.subheader("👥 Gestión de Usuarios")
    usuarios = load_usuarios()

    with st.form("form_nuevo_usuario"):
        st.markdown("**Agregar nuevo usuario**")
        c1, c2 = st.columns(2)
        with c1:
            nu_nombre = st.text_input("Nombre completo")
            nu_correo = st.text_input("Correo electrónico")
        with c2:
            nu_pwd  = st.text_input("Contraseña", type="password")
            nu_rol  = st.selectbox("Rol", ["usuario", "tecnico", "admin"])
        if st.form_submit_button("➕ Agregar usuario", type="primary", use_container_width=True):
            if not nu_nombre or not nu_correo or not nu_pwd:
                st.error("Todos los campos son obligatorios.")
            elif nu_correo.lower() in usuarios["correo"].str.lower().values:
                st.error("Ese correo ya está registrado.")
            else:
                nuevo_u = {
                    "nombre":        nu_nombre,
                    "correo":        nu_correo,
                    "password_hash": hash_pwd(nu_pwd),
                    "rol":           nu_rol,
                }
                usuarios = pd.concat([usuarios, pd.DataFrame([nuevo_u])], ignore_index=True)
                save_usuarios(usuarios)
                st.success(f"✅ Usuario **{nu_nombre}** creado.")
                st.rerun()

    st.divider()
    st.subheader("Usuarios registrados")
    usuarios = load_usuarios()
    if not usuarios.empty:
        vista_u = usuarios[["nombre", "correo", "rol"]].copy()
        tabla_html(vista_u.reset_index(drop=True))
        st.caption(f"{len(usuarios)} usuario(s) registrado(s).")

        st.divider()
        st.subheader("Eliminar usuario")
        mi_correo = st.session_state.get("user_correo", "")
        otros = usuarios[usuarios["correo"].str.lower() != mi_correo.lower()]
        if otros.empty:
            st.info("No hay otros usuarios para eliminar.")
        else:
            ops = {f"{r['nombre']} — {r['correo']} ({r['rol']})": r['correo']
                   for _, r in otros.iterrows()}
            sel = st.selectbox("Selecciona el usuario a eliminar", list(ops.keys()))
            if st.button("🗑️ Eliminar usuario", type="secondary", use_container_width=True):
                correo_eli = ops[sel]
                usuarios = usuarios[usuarios["correo"].str.lower() != correo_eli.lower()].reset_index(drop=True)
                save_usuarios(usuarios)
                st.success(f"✅ Usuario eliminado.")
                st.rerun()

    st.divider()
    st.subheader("🔐 Cambiar contraseña")
    tab_pwd_propia, tab_pwd_otro = st.tabs(["Mi contraseña", "Contraseña de otro usuario"])

    with tab_pwd_propia:
        with st.form("form_cambiar_pwd_gu"):
            pwd_act  = st.text_input("Contraseña actual", type="password")
            pwd_new  = st.text_input("Nueva contraseña", type="password")
            pwd_new2 = st.text_input("Confirmar nueva contraseña", type="password")
            if st.form_submit_button("🔐 Cambiar mi contraseña", type="primary"):
                mi_correo2 = st.session_state.get("user_correo", "")
                usuarios = load_usuarios()
                idx_u = usuarios[usuarios["correo"].str.lower() == mi_correo2.lower()].index
                if idx_u.empty:
                    st.error("Usuario no encontrado.")
                elif usuarios.loc[idx_u[0], "password_hash"] != hash_pwd(pwd_act):
                    st.error("Contraseña actual incorrecta.")
                elif pwd_new != pwd_new2:
                    st.error("Las contraseñas nuevas no coinciden.")
                elif len(pwd_new) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                else:
                    usuarios.loc[idx_u[0], "password_hash"] = hash_pwd(pwd_new)
                    save_usuarios(usuarios)
                    st.success("✅ Tu contraseña fue actualizada.")

    with tab_pwd_otro:
        if st.session_state.get("user_rol") != "admin":
            st.warning("Solo el administrador puede cambiar contraseñas de otros usuarios.")
        else:
            usuarios_rec = load_usuarios()
            mi_correo_act = st.session_state.get("user_correo", "")
            otros_u = usuarios_rec[usuarios_rec["correo"].str.lower() != mi_correo_act.lower()]
            if otros_u.empty:
                st.info("No hay otros usuarios registrados.")
            else:
                ops_pwd = {f"{r['nombre']} — {r['correo']} ({r['rol']})": r['correo']
                           for _, r in otros_u.iterrows()}
                sel_pwd = st.selectbox("Selecciona el usuario", list(ops_pwd.keys()), key="sel_pwd_otro")
                with st.form("form_pwd_otro"):
                    new_pwd1 = st.text_input("Nueva contraseña", type="password")
                    new_pwd2 = st.text_input("Confirmar nueva contraseña", type="password")
                    if st.form_submit_button("🔐 Cambiar contraseña", type="primary", use_container_width=True):
                        if not new_pwd1:
                            st.error("Escribe la nueva contraseña.")
                        elif new_pwd1 != new_pwd2:
                            st.error("Las contraseñas no coinciden.")
                        elif len(new_pwd1) < 6:
                            st.error("Mínimo 6 caracteres.")
                        else:
                            correo_dest = ops_pwd[sel_pwd]
                            usuarios_rec = load_usuarios()
                            idx_o = usuarios_rec[usuarios_rec["correo"].str.lower() == correo_dest.lower()].index
                            if not idx_o.empty:
                                usuarios_rec.loc[idx_o[0], "password_hash"] = hash_pwd(new_pwd1)
                                save_usuarios(usuarios_rec)
                                nombre_dest = otros_u[otros_u["correo"].str.lower() == correo_dest.lower()]["nombre"].values[0]
                                st.success(f"✅ Contraseña de **{nombre_dest}** actualizada.")

# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: MIGRACIÓN (solo admin)
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "usuarios":
    usuarios = load_usuarios()
    if st.session_state.get("user_rol") != "admin":
        st.error("Acceso restringido.")
    else:
        # ── Migración Google Sheets → Supabase (solo una vez) ─────────────
        with st.expander("🔄 Migrar datos desde Google Sheets a Supabase", expanded=False):
            st.warning("Ejecuta esto UNA SOLA VEZ para copiar todos los datos existentes.")
            TABLAS_MIG = {
                "solicitudes":     COLS_SOL,
                "clientes":        COLS_CLI,
                "ordenes_trabajo": COLS_OT,
                "contratos":       COLS_CONTRATO,
                "equipos":         COLS_EQUIPO,
                "ventas":          COLS_VENTA,
                "costos":          COLS_COSTO,
                "contadores":      COLS_COUNTERS,
            }
            sel_tablas = st.multiselect(
                "¿Qué tablas migrar?",
                list(TABLAS_MIG.keys()),
                default=list(TABLAS_MIG.keys()),
            )
            if st.button("🚀 Iniciar migración", type="primary", use_container_width=True):
                tablas = [(t, TABLAS_MIG[t]) for t in sel_tablas]
                errores = []
                gc_mig = get_gc()
                for tab, cols in tablas:
                    try:
                        # Leer directo de Google Sheets sin caché
                        sh  = gc_mig.open_by_key(st.secrets["spreadsheet_id"] or
                                                  st.secrets["gcp_service_account"].get("spreadsheet_id",""))
                        ws  = sh.worksheet(tab)
                        data = ws.get_all_records()
                        if data:
                            df_gs = pd.DataFrame(data).astype(str).fillna("")
                            for c in cols:
                                if c not in df_gs.columns:
                                    df_gs[c] = ""
                            df_gs = df_gs[cols]
                            # Eliminar duplicados
                            # clientes: deduplicar por (Empresa, Sede) porque un cliente tiene muchas sedes
                            # otras tablas: deduplicar por la primera columna (ID)
                            antes = len(df_gs)
                            if tab == "clientes":
                                pk_cols = ["Empresa", "Sede"]
                                pk_cols = [c for c in pk_cols if c in df_gs.columns]
                            else:
                                pk_cols = [cols[0]]
                            df_gs = df_gs.drop_duplicates(subset=pk_cols).reset_index(drop=True)
                            if len(df_gs) < antes:
                                st.warning(f"⚠️ **{tab}**: {antes - len(df_gs)} duplicado(s) eliminado(s)")
                            ok = sb_save(tab, df_gs)
                            if ok:
                                st.success(f"✅ **{tab}**: {len(df_gs)} registros migrados")
                            else:
                                st.error(f"❌ **{tab}**: fallo al guardar")
                        else:
                            st.info(f"ℹ️ **{tab}**: sin datos en Google Sheets")
                    except Exception as e:
                        errores.append(tab)
                        st.error(f"❌ **{tab}**: {e}")
                if not errores:
                    st.success("🎉 ¡Migración completa! Todos los datos están en Supabase.")
        st.stop()

    st.subheader("👥 Gestión de Usuarios")
    usuarios = load_usuarios()

    # Agregar usuario
    with st.form("form_nuevo_usuario", clear_on_submit=True):
        st.markdown("**Agregar nuevo usuario**")
        c1, c2 = st.columns(2)
        with c1:
            nu_nombre = st.text_input("Nombre completo")
            nu_correo = st.text_input("Correo electrónico")
        with c2:
            nu_pwd    = st.text_input("Contraseña", type="password")
            nu_rol    = st.selectbox("Rol", ["usuario", "tecnico", "admin"])
        if st.form_submit_button("➕ Agregar usuario", type="primary", use_container_width=True):
            if not nu_nombre or not nu_correo or not nu_pwd:
                st.error("Todos los campos son obligatorios.")
            elif nu_correo.lower() in usuarios["correo"].str.lower().values:
                st.error("Ese correo ya está registrado.")
            else:
                nuevo_u = {
                    "nombre":        nu_nombre,
                    "correo":        nu_correo,
                    "password_hash": hash_pwd(nu_pwd),
                    "rol":           nu_rol,
                }
                usuarios = pd.concat([usuarios, pd.DataFrame([nuevo_u])], ignore_index=True)
                save_usuarios(usuarios)
                st.success(f"✅ Usuario **{nu_nombre}** creado.")
                st.rerun()

    st.divider()
    st.subheader("Usuarios registrados")

    # Recargar frescos para evitar problemas de caché
    usuarios = load_usuarios()

    if not usuarios.empty:
        vista_u = usuarios[["nombre", "correo", "rol"]].copy()
        tabla_html(vista_u.reset_index(drop=True))
        st.caption(f"{len(usuarios)} usuario(s) registrado(s). Sin límite máximo.")

        st.divider()
        st.subheader("Eliminar usuario")
        mi_correo = st.session_state.get("user_correo", "")
        otros = usuarios[usuarios["correo"].str.lower() != mi_correo.lower()]

        if otros.empty:
            st.info("No hay otros usuarios para eliminar. Agrega más usuarios primero.")
        else:
            ops = {f"{r['nombre']} — {r['correo']} ({r['rol']})": r['correo']
                   for _, r in otros.iterrows()}
            sel = st.selectbox("Selecciona el usuario a eliminar", list(ops.keys()))
            if st.button("🗑️ Eliminar usuario", type="secondary", use_container_width=True):
                correo_eli = ops[sel]
                usuarios = usuarios[usuarios["correo"].str.lower() != correo_eli.lower()].reset_index(drop=True)
                save_usuarios(usuarios)
                st.success(f"✅ Usuario **{sel}** eliminado.")
                st.rerun()
        st.divider()
        st.subheader("Cambiar mi contraseña")
        with st.form("form_cambiar_pwd"):
            pwd_act  = st.text_input("Contraseña actual", type="password")
            pwd_new  = st.text_input("Nueva contraseña", type="password")
            pwd_new2 = st.text_input("Confirmar nueva contraseña", type="password")
            if st.form_submit_button("🔐 Cambiar contraseña", type="primary"):
                mi_correo2 = st.session_state.get("user_correo")
                u_row = usuarios[usuarios["correo"] == mi_correo2]
                if u_row.empty or u_row.iloc[0]["password_hash"] != hash_pwd(pwd_act):
                    st.error("La contraseña actual no es correcta.")
                elif pwd_new != pwd_new2:
                    st.error("Las contraseñas nuevas no coinciden.")
                elif len(pwd_new) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                else:
                    usuarios.loc[usuarios["correo"] == mi_correo2, "password_hash"] = hash_pwd(pwd_new)
                    save_usuarios(usuarios)
                    st.success("✅ Contraseña actualizada correctamente.")
    else:
        st.warning("No hay usuarios registrados.")
