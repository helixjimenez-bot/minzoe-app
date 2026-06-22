import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
import hashlib
import gspread
from google.oauth2.service_account import Credentials

USUARIOS_FILE     = r"D:\Escritorio\LA ASISTENTE MINZOE\usuarios.csv"
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
    "ID", "Fecha", "Cliente", "NIT", "Direccion_Empresa",
    "Sede", "Direccion_Sede", "Nombre_Contacto", "Correo_Contacto", "Celular_Contacto",
    "Servicio", "Tipo_Servicio", "Descripcion", "SLA", "Ciudad", "Zona", "Canal", "Estado",
]
COLS_CLI = [
    "Empresa", "NIT", "Direccion_Empresa",
    "Sede", "Direccion_Sede",
    "Nombre_Contacto", "Correo_Contacto", "Celular_Contacto",
]

ESTADOS_OT   = ["Programada", "En ejecución", "Finalizada", "Cancelada"]
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
    "ID", "Origen", "SOL_Ref", "Fecha_Creacion", "Fecha_Limite", "Cliente", "NIT", "Sede",
    "Nombre_Contacto", "Celular_Contacto",
    "Servicio", "Descripcion", "SLA", "Zona", "Tecnico", "Celular_Tecnico",
    "Fecha_Ejecucion", "Hora_Inicio", "Hora_Final", "Horas_Laboradas",
    "Materiales", "Valor_COP", "Estado", "Observaciones",
]


# ── Google Sheets ─────────────────────────────────────────────────────────────

@st.cache_resource
def get_gc():
    return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))

def get_sheet(tab_name):
    gc = get_gc()
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    try:
        return sh.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        return sh.add_worksheet(title=tab_name, rows=1000, cols=30)

def gs_load(tab_name, cols):
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
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar '{tab_name}': {e}")
        return pd.DataFrame(columns=cols)

def gs_save(tab_name, df):
    try:
        ws = get_sheet(tab_name)
        ws.clear()
        if not df.empty:
            data = [df.columns.tolist()] + df.fillna("").astype(str).values.tolist()
            ws.update("A1", data)
        return True
    except Exception as e:
        st.error(f"❌ Error guardando '{tab_name}': {e}")
        return False


# ── Carga / guardado ──────────────────────────────────────────────────────────

def load_sol():
    return gs_load("solicitudes", COLS_SOL)

def save_sol(df):
    gs_save("solicitudes", df)

def load_cli():
    df = gs_load("clientes", COLS_CLI)
    for col in df.columns:
        df[col] = df[col].str.strip()
    return df[df["Empresa"] != ""].reset_index(drop=True)

def save_cli(df):
    gs_save("clientes", df)

def load_ots():
    return gs_load("ordenes_trabajo", COLS_OT)

def save_ots(df):
    gs_save("ordenes_trabajo", df)


def load_cv():
    return gs_load("compras_ventas", COLS_CV)

def save_cv(df):
    gs_save("compras_ventas", df)

def gen_cv_id(df):
    hoy = datetime.now().strftime("%y%m%d")
    pre = f"CV-{hoy}-"
    ids = df[df["ID_Registro"].str.startswith(pre, na=False)]["ID_Registro"] if not df.empty else pd.Series(dtype=str)
    return f"{pre}001" if ids.empty else f"{pre}{ids.str.extract(r'CV-\d{6}-(\d{3})')[0].astype(int).max()+1:03d}"

def load_ventas():
    return gs_load("ventas", COLS_VENTA)

def save_ventas(df):
    gs_save("ventas", df)

def gen_fac_id(df):
    hoy = datetime.now().strftime("%y%m%d")
    pre = f"FAC-{hoy}-"
    ids = df[df["ID_Factura"].str.startswith(pre, na=False)]["ID_Factura"] if not df.empty else pd.Series(dtype=str)
    return f"{pre}001" if ids.empty else f"{pre}{ids.str.extract(r'FAC-\d{6}-(\d{3})')[0].astype(int).max()+1:03d}"

def load_costos():
    return gs_load("costos", COLS_COSTO)

def save_costos(df):
    gs_save("costos", df)

def gen_costo_id(df):
    hoy = datetime.now().strftime("%y%m%d")
    pre = f"COS-{hoy}-"
    ids = df[df["ID_Costo"].str.startswith(pre, na=False)]["ID_Costo"] if not df.empty else pd.Series(dtype=str)
    return f"{pre}001" if ids.empty else f"{pre}{ids.str.extract(r'COS-\d{6}-(\d{3})')[0].astype(int).max()+1:03d}"


def to_num(val):
    try:
        return float(str(val).replace(",", "").replace(".", "").replace(" ", "") or 0)
    except Exception:
        return 0.0


def load_contratos():
    return gs_load("contratos", COLS_CONTRATO)

def save_contratos(df):
    gs_save("contratos", df)

def load_equipos():
    return gs_load("equipos", COLS_EQUIPO)

def save_equipos(df):
    gs_save("equipos", df)


def gen_contrato_id(df):
    hoy = datetime.now().strftime("%y%m%d")
    pre = f"CON-{hoy}-"
    ids = df[df["ID_Contrato"].str.startswith(pre, na=False)]["ID_Contrato"] if not df.empty else pd.Series(dtype=str)
    return f"{pre}001" if ids.empty else f"{pre}{ids.str.extract(r'CON-\d{6}-(\d{3})')[0].astype(int).max()+1:03d}"


def gen_item_id(df):
    if df.empty:
        return "ITEM-001"
    nums = df["ID_Item"].str.extract(r"ITEM-(\d+)")[0].dropna().astype(int)
    return f"ITEM-{nums.max()+1:03d}" if not nums.empty else "ITEM-001"


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
    hoy     = datetime.now().strftime("%y%m%d")
    prefijo = f"OT-{hoy}-"
    ids_hoy = (
        df[df["ID"].str.startswith(prefijo, na=False)]["ID"]
        if not df.empty else pd.Series(dtype=str)
    )
    if ids_hoy.empty:
        return f"{prefijo}001"
    nums = ids_hoy.str.extract(r"OT-\d{6}-(\d{3})")[0].astype(int)
    return f"{prefijo}{nums.max() + 1:03d}"


def tabla_html(df_vista, color_col=None, colores_estado=None):
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
            cells += (
                f"<td style='background:{cell_bg};color:{cell_color};"
                f"padding:7px 10px;font-size:0.83rem;border-bottom:1px solid #f0f0f0;"
                f"white-space:nowrap;'>{val}</td>"
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
    """Retorna la fecha límite como string dado el SLA y la zona."""
    desde = desde or datetime.now()
    clave = zona_completa[:2] if zona_completa else "Z0"  # extrae "Z0", "Z1", etc.
    horas = SLA_HORAS.get(sla, {}).get(clave)
    if horas is None:
        return TEXTO_Z5.get(sla, "Por definir")
    return (desde + timedelta(hours=horas)).strftime("%Y-%m-%d %H:%M")


def crear_ot_desde_sol(sol, ots):
    """Crea una OT a partir de una fila de solicitud. Evita duplicados por SOL_Ref."""
    if not ots.empty and "SOL_Ref" in ots.columns and sol["ID"] in ots["SOL_Ref"].values:
        return ots, False  # Ya existe
    ahora = datetime.now()
    nueva_ot = {
        "ID":               generate_ot_id(ots),
        "Origen":           "Solicitud",
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
    hoy     = datetime.now().strftime("%y%m%d")
    prefijo = f"SOL-{hoy}-"
    ids_hoy = (
        df[df["ID"].str.startswith(prefijo, na=False)]["ID"]
        if not df.empty else pd.Series(dtype=str)
    )
    if ids_hoy.empty:
        return f"{prefijo}001"
    nums = ids_hoy.str.extract(r"SOL-\d{6}-(\d{3})")[0].astype(int)
    return f"{prefijo}{nums.max() + 1:03d}"


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
    return gs_load("usuarios", ["nombre", "correo", "password_hash", "rol"])

def save_usuarios(df):
    gs_save("usuarios", df)

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

    LOGO_PATH = r"D:\Escritorio\LA ASISTENTE MINZOE\LOGO MINZOE.png"
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=180)
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
</style>
""", unsafe_allow_html=True)

# ── Verificar login ──────────────────────────────────────────────────────────
usuarios = load_usuarios()

# Si no hay usuarios, mostrar pantalla de creación del primer admin
if usuarios.empty:
    st.markdown("""
    <div style='max-width:420px;margin:60px auto;padding:32px;background:#fff;
    border-radius:16px;box-shadow:0 8px 32px rgba(220,38,38,0.15);border-top:5px solid #dc2626;'>
    <h3 style='color:#dc2626;text-align:center;'>⚙️ Primera configuración</h3>
    <p style='color:#555;text-align:center;'>Crea el usuario administrador</p>
    </div>
    """, unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("form_primer_admin"):
            nombre_a = st.text_input("Tu nombre completo")
            correo_a = st.text_input("Correo electrónico")
            pwd_a    = st.text_input("Contraseña", type="password")
            pwd_a2   = st.text_input("Confirmar contraseña", type="password")
            crear    = st.form_submit_button("Crear administrador", type="primary", use_container_width=True)
            if crear:
                if not nombre_a or not correo_a or not pwd_a:
                    st.error("Todos los campos son obligatorios.")
                elif pwd_a != pwd_a2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    nuevo_u = pd.DataFrame([{
                        "nombre": nombre_a, "correo": correo_a,
                        "password_hash": hash_pwd(pwd_a), "rol": "admin"
                    }])
                    save_usuarios(nuevo_u)
                    st.success("✅ Administrador creado. Recarga la página para iniciar sesión.")
    st.stop()

# Si no ha iniciado sesión, mostrar pantalla de login
if not st.session_state.get("logged_in", False):
    pagina_login()
    st.stop()

# ── Usuario autenticado: cargar datos ────────────────────────────────────────
df         = load_sol()
cli        = load_cli()
ots        = load_ots()
contratos  = load_contratos()
equipos    = load_equipos()
cv         = load_cv()
ventas     = load_ventas()
costos     = load_costos()

# ── Menú lateral ─────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo
    LOGO_PATH = r"D:\Escritorio\LA ASISTENTE MINZOE\LOGO MINZOE.png"
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.markdown("""
        <div style='text-align:center; padding: 12px 0 4px 0;'>
            <span style='font-size:2.8rem;'>🏗️</span><br>
            <span style='color:#dc2626; font-size:1.1rem; font-weight:800;'>CONSTRUCCIONES</span><br>
            <span style='color:#ffffff; font-size:1.3rem; font-weight:900; letter-spacing:2px;'>MINZOE SAS</span>
        </div>
        """, unsafe_allow_html=True)
    st.divider()

    # ── GENERAL ──────────────────────────────────────────────────────────────
    if st.button("📊 Dashboard", use_container_width=True):
        st.session_state["pagina"] = "resumen"
        st.rerun()

    st.markdown("<p style='color:#aaa;font-size:0.72rem;font-weight:700;letter-spacing:1px;margin:6px 0 2px 4px;'>BASE DE DATOS</p>", unsafe_allow_html=True)

    if st.button("🏢 Clientes", use_container_width=True):
        st.session_state["pagina"] = "clientes"
        st.rerun()

    st.markdown("<p style='color:#aaa;font-size:0.72rem;font-weight:700;letter-spacing:1px;margin:6px 0 2px 4px;'>OPERACIONES</p>", unsafe_allow_html=True)

    if st.button("➕ Nueva Solicitud", use_container_width=True, type="primary"):
        for key in ["empresa_sel", "sede_sel"]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state["pagina"] = "nueva"
        st.rerun()

    if st.button("📋 Ver Solicitudes", use_container_width=True):
        st.session_state["pagina"] = "ver"
        st.rerun()

    if st.button("🛠️ Órdenes de Trabajo", use_container_width=True):
        st.session_state["pagina"] = "ots"
        st.rerun()

    if st.button("📄 Contratos de Mantenimiento", use_container_width=True):
        st.session_state["pagina"] = "contratos_mto"
        st.rerun()

    st.markdown("<p style='color:#aaa;font-size:0.72rem;font-weight:700;letter-spacing:1px;margin:6px 0 2px 4px;'>FINANCIERO</p>", unsafe_allow_html=True)

    if st.button("💰 Compras y Ventas", use_container_width=True):
        st.session_state["pagina"] = "compras_ventas"
        st.rerun()

    st.divider()
    pendientes  = (df["Estado"] == "Pendiente").sum() if not df.empty else 0
    ots_activas = int((ots["Estado"].isin(["Programada","En ejecución"])).sum()) if not ots.empty else 0
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
            st.session_state["pagina"] = "usuarios"
            st.rerun()
        with st.expander("⚙️ Subir logo"):
            logo_up = st.file_uploader("Logo (PNG/JPG)", type=["png","jpg","jpeg"], key="logo_uploader")
            if logo_up:
                with open(r"D:\Escritorio\LA ASISTENTE MINZOE\LOGO MINZOE.png", "wb") as f:
                    f.write(logo_up.read())
                st.success("Logo guardado. Reinicia la app.")


pagina = st.session_state.get("pagina", "nueva")

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

            # Sede → lista desplegable filtrada por empresa
            sedes_lista = filas_emp["Sede"].tolist()
            sede_sel = st.selectbox("Sede / Sucursal", sedes_lista, key="sede_sel")

            # Buscar datos de la sede seleccionada
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
                    "Fecha":            datetime.now().strftime("%Y-%m-%d %H:%M"),
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
                st.success(f"✅ Solicitud **{nueva['ID']}** guardada para {empresa_final}.")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: VER SOLICITUDES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "ver":
    import io
    st.subheader("📋 Solicitudes registradas")

    if df.empty:
        st.info("Aún no hay solicitudes registradas.")
    else:
        # ── FILTROS ───────────────────────────────────────────────────────────
        c1, c2, c3 = st.columns(3)
        with c1:
            f_estado   = st.multiselect("Estado", ESTADOS, default=ESTADOS)
        with c2:
            f_servicio = st.multiselect("Servicio", SERVICIOS, default=SERVICIOS)
        with c3:
            buscar = st.text_input("Buscar empresa")

        vista = df.copy()
        if f_estado:
            vista = vista[vista["Estado"].isin(f_estado)]
        if f_servicio:
            vista = vista[vista["Servicio"].isin(f_servicio)]
        if buscar:
            vista = vista[vista["Cliente"].str.contains(buscar, case=False, na=False)]

        vista_ord = vista.sort_values("ID", ascending=False, key=lambda x: x.str.replace("SOL-", ""))

        COLS_TABLA = ["ID", "Fecha", "Cliente", "Sede", "Nombre_Contacto",
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
                file_name=f"solicitudes_minzoe_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

        st.divider()

        # ── ACCIONES POR SOLICITUD ────────────────────────────────────────────
        ids_lista = df.sort_values("ID", ascending=False, key=lambda x: x.str.replace("SOL-", ""))["ID"].tolist()
        id_sel    = st.selectbox("Selecciona una solicitud", ids_lista, key="id_accion")

        if id_sel:
            fila = df[df["ID"] == id_sel].iloc[0]

            acc1, acc2, acc3 = st.tabs(["🔍 Ver detalle", "✏️ Editar", "🗑️ Eliminar"])

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
                        df.loc[idx, "Estado"]           = e_estado
                        save_sol(df)
                        msg = f"✅ Solicitud {id_sel} actualizada."
                        if e_estado == "Aprobado":
                            sol_row = df[df["ID"] == id_sel].iloc[0]
                            ots, creada = crear_ot_desde_sol(sol_row, ots)
                            if creada:
                                save_ots(ots)
                                msg += f" OT **{ots.iloc[-1]['ID']}** creada automáticamente."
                        st.success(msg)
                        st.rerun()

            # ── ELIMINAR ──────────────────────────────────────────────────────
            with acc3:
                st.markdown(f"### Eliminar {id_sel}")
                st.warning(f"¿Seguro que deseas eliminar la solicitud **{id_sel}** de **{fila['Cliente']}**? Esta acción no se puede deshacer.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🗑️ Sí, eliminar", type="primary", use_container_width=True):
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
    hoy_dash = datetime.now()
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

    # ── SECCIÓN 4: ALERTAS ───────────────────────────────────────────────────
    st.markdown('<p class="section-title">🚨 ALERTAS Y PENDIENTES</p>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**OTs que requieren atención**")
        if not ots.empty and "Fecha_Limite" in ots.columns:
            def est_lim(val):
                try:
                    diff = (datetime.strptime(val, "%Y-%m-%d %H:%M") - hoy_dash).total_seconds() / 3600
                    return "🔴 Vencida" if diff < 0 else ("🟡 Vence en <24h" if diff <= 24 else None)
                except Exception:
                    return None
            ots_a = ots[(ots["Estado"].isin(["Programada","En ejecución"])) &
                        (ots["Fecha_Limite"].apply(lambda x: est_lim(x) is not None))].copy()
            ots_a["⚠️"] = ots_a["Fecha_Limite"].apply(est_lim)
            if ots_a.empty:
                st.markdown('<div class="alert-box alert-green">✅ Sin OTs vencidas ni próximas a vencer</div>', unsafe_allow_html=True)
            else:
                for _, r in ots_a.head(5).iterrows():
                    cls = "alert-red" if "Vencida" in r["⚠️"] else "alert-yellow"
                    st.markdown(f'<div class="alert-box {cls}"><strong>{r["⚠️"]}</strong> — {r["ID"]} | {r["Cliente"]} | {r["Fecha_Limite"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-box alert-green">✅ Sin alertas</div>', unsafe_allow_html=True)

    with col_b:
        st.markdown("**Solicitudes pendientes más antiguas**")
        if not df.empty:
            pend_df = df[df["Estado"] == "Pendiente"].sort_values("Fecha").head(5)
            if pend_df.empty:
                st.markdown('<div class="alert-box alert-green">✅ Sin solicitudes pendientes</div>', unsafe_allow_html=True)
            else:
                for _, r in pend_df.iterrows():
                    st.markdown(f'<div class="alert-box alert-yellow"><strong>{r["ID"]}</strong> — {r["Cliente"]} | {r["Servicio"]} | {r["Fecha"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="alert-box alert-green">✅ Sin pendientes</div>', unsafe_allow_html=True)

    st.divider()

    # ── SECCIÓN 5: GRÁFICAS ───────────────────────────────────────────────────
    st.markdown('<p class="section-title">📈 ANÁLISIS</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if not df.empty:
            st.markdown("**Solicitudes por servicio**")
            st.bar_chart(df["Servicio"].value_counts())
        if not ots.empty:
            st.markdown("**OTs por estado**")
            st.bar_chart(ots["Estado"].value_counts())
    with c2:
        if not cv.empty:
            st.markdown("**Ventas vs Utilidad por servicio**")
            rsrv = cv.groupby("Servicio").apply(
                lambda g: pd.Series({"Ventas": g["Valor_Antes_IVA"].apply(to_num).sum(),
                                     "Utilidad": g["Utilidad"].apply(to_num).sum()})
            ).reset_index()
            st.bar_chart(rsrv.set_index("Servicio")[["Ventas","Utilidad"]])
        if not df.empty and "SLA" in df.columns:
            st.markdown("**Solicitudes por SLA**")
            st.bar_chart(df["SLA"].value_counts())

    st.divider()

    # ── SECCIÓN 6: ACTIVIDAD RECIENTE ─────────────────────────────────────────
    st.markdown('<p class="section-title">🕐 ACTIVIDAD RECIENTE</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Últimas 5 solicitudes**")
        if not df.empty:
            st.dataframe(df.sort_values("Fecha", ascending=False).head(5)
                         [["ID","Fecha","Cliente","Servicio","Estado"]],
                         use_container_width=True, hide_index=True)
        else:
            st.info("Sin solicitudes")
    with c2:
        st.markdown("**Últimas 5 OTs**")
        if not ots.empty:
            st.dataframe(ots.sort_values("Fecha_Creacion", ascending=False).head(5)
                         [["ID","Fecha_Creacion","Cliente","Servicio","Estado"]],
                         use_container_width=True, hide_index=True)
        else:
            st.info("Sin OTs")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: CLIENTES
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "clientes":
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

        buscar_cli = st.text_input("Buscar empresa", key="buscar_cli")
        vista_cli  = cli if not buscar_cli else cli[cli["Empresa"].str.contains(buscar_cli, case=False, na=False)]

        # Paginación de 5 registros
        POR_PAG = 5
        total_cli = len(vista_cli)
        total_pags = max(1, -(-total_cli // POR_PAG))  # ceil division
        pag_cli = st.session_state.get("pag_cli", 1)
        inicio = (pag_cli - 1) * POR_PAG
        fin    = inicio + POR_PAG
        tabla_html(vista_cli.iloc[inicio:fin].reset_index(drop=True))

        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("◀ Anterior", key="cli_prev", disabled=pag_cli <= 1):
                st.session_state["pag_cli"] = pag_cli - 1
                st.rerun()
        with c2:
            st.caption(f"Página {pag_cli} de {total_pags} — {total_cli} registro(s)")
        with c3:
            if st.button("Siguiente ▶", key="cli_next", disabled=pag_cli >= total_pags):
                st.session_state["pag_cli"] = pag_cli + 1
                st.rerun()

        st.divider()
        st.subheader("Eliminar una empresa / sede específica")
        opciones_eli = [
            f"{r['Empresa']} — {r['Sede']} (fila {i})"
            for i, r in cli.iterrows()
        ]
        sel_eli = st.selectbox("Selecciona la fila a eliminar", opciones_eli)
        if st.button("🗑️ Eliminar esta fila", type="secondary"):
            idx_eli = int(sel_eli.split("fila ")[-1].replace(")", ""))
            cli = cli.drop(index=idx_eli).reset_index(drop=True)
            save_cli(cli)
            st.success("Registro eliminado.")
            st.rerun()
    else:
        st.info("Aún no hay empresas registradas.")


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: ÓRDENES DE TRABAJO
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "ots":
    import io
    st.subheader("🛠️ Órdenes de Trabajo")

    accion_ot = st.radio("", ["➕ Nueva OT", "📋 Ver OTs"], horizontal=True, label_visibility="collapsed")
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

        with st.form("form_nueva_ot", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                ot_servicio  = st.selectbox("Servicio", SERVICIOS)
                ot_desc      = st.text_area("Descripción del trabajo")
                ot_tecnico   = st.text_input("Técnico asignado")
                ot_cel_tec   = st.text_input("📱 Celular del técnico", placeholder="Ej: 3001234567")
            with c2:
                ot_fecha      = st.date_input("Fecha de ejecución", value=datetime.today())
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
                        "SOL_Ref":         "",
                        "Fecha_Creacion":  datetime.now().strftime("%Y-%m-%d %H:%M"),
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
                        "Observaciones":   ot_obs.strip(),
                    }
                    ots = pd.concat([ots, pd.DataFrame([nueva_ot])], ignore_index=True)
                    save_ots(ots)
                    st.success(f"✅ OT **{nueva_ot['ID']}** guardada para {empresa_final_ot}.")

    # ── VER OTs ───────────────────────────────────────────────────────────────
    else:
        if ots.empty:
            st.info("Aún no hay órdenes de trabajo registradas.")
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

            COLS_TABLA_OT = ["ID", "Origen", "Fecha_Creacion", "Fecha_Limite", "Cliente", "Sede",
                             "Servicio", "SLA", "Zona", "Tecnico", "Fecha_Ejecucion", "Valor_COP", "Estado"]
            cols_vis_ot = [c for c in COLS_TABLA_OT if c in vista_ot_ord.columns]

            def color_limite(val):
                try:
                    limite = datetime.strptime(val, "%Y-%m-%d %H:%M")
                    diff   = (limite - datetime.now()).total_seconds() / 3600
                    if diff < 0:
                        return "background-color:#f8d7da; color:#000"  # vencida — rojo
                    elif diff <= 24:
                        return "background-color:#fff3cd; color:#000"  # próxima — amarillo
                    return "background-color:#d1e7dd; color:#000"       # ok — verde
                except Exception:
                    return ""

            COLORES_OT = {
                "Programada":   ("#e0e7ff", "#1e3a8a"),
                "En ejecución": ("#fef3c7", "#78350f"),
                "Finalizada":   ("#d1fae5", "#064e3b"),
                "Cancelada":    ("#fee2e2", "#7f1d1d"),
            }
            tabla_html(vista_ot_ord[cols_vis_ot].reset_index(drop=True),
                       color_col="Estado", colores_estado=COLORES_OT)

            c1, c2 = st.columns([3, 1])
            with c1:
                st.caption(f"Mostrando {len(vista_ot_ord)} de {len(ots)} órdenes.")
            with c2:
                buf_ot = io.BytesIO()
                with pd.ExcelWriter(buf_ot, engine="openpyxl") as w:
                    vista_ot_ord.to_excel(w, index=False, sheet_name="OTs")
                st.download_button(
                    "⬇️ Exportar Excel", data=buf_ot.getvalue(),
                    file_name=f"OTs_minzoe_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

            st.divider()
            ids_ot_lista = ots.sort_values("ID", ascending=False, key=lambda x: x.str.replace("OT-", ""))["ID"].tolist()
            id_ot_sel = st.selectbox("Selecciona una OT", ids_ot_lista, key="id_ot_sel")

            if id_ot_sel:
                fila_ot = ots[ots["ID"] == id_ot_sel].iloc[0]
                det, edi, eli = st.tabs(["🔍 Ver detalle", "✏️ Editar", "🗑️ Eliminar"])

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
                        f"Fecha ejecución: {fila_ot['Fecha_Ejecucion']} {fila_ot['Hora_Ejecucion']}\n\n"
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
                            ots.loc[idx_ot, "Estado"]         = ee_estado
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

                with eli:
                    st.warning(f"¿Eliminar la OT **{id_ot_sel}** de **{fila_ot['Cliente']}**? No se puede deshacer.")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("🗑️ Sí, eliminar", type="primary", use_container_width=True, key="eli_ot"):
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
    import io
    st.subheader("📄 Contratos de Mantenimiento")

    tab_con, tab_equ, tab_gen = st.tabs([
        "📋 Contratos", "🔧 Equipos / Ítems", "⚡ Generar OTs del Mes"
    ])

    # ── TAB 1: CONTRATOS ─────────────────────────────────────────────────────
    with tab_con:
        st.subheader("Registrar contrato de mantenimiento")
        with st.form("form_contrato", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                empresas_con = sorted(cli["Empresa"].unique().tolist()) if not cli.empty else []
                con_cliente  = st.selectbox("Empresa *", empresas_con + ["✏️ Ingresar manualmente"], key="con_cli")
                con_nit      = st.text_input("NIT")
                con_sede     = st.text_input("Sede / Sucursal")
                con_contacto = st.text_input("Nombre contacto")
                con_celular  = st.text_input("Celular contacto")
            with c2:
                con_servicio = st.selectbox("Servicio *", SERVICIOS)
                con_freq     = st.selectbox("Frecuencia", FRECUENCIAS)
                con_tecnico  = st.text_input("Técnico responsable")
                con_valor    = st.text_input("Valor del contrato (COP)", placeholder="Ej: 1200000")
                con_inicio   = st.date_input("Fecha inicio", value=datetime.today())
                con_fin      = st.date_input("Fecha fin")
                con_estado   = st.selectbox("Estado", ["Activo", "Inactivo"])

            if st.form_submit_button("💾 Guardar contrato", type="primary", use_container_width=True):
                if not con_cliente or con_cliente == "✏️ Ingresar manualmente":
                    st.error("Selecciona la empresa.")
                else:
                    nuevo_con = {
                        "ID_Contrato":      gen_contrato_id(contratos),
                        "Fecha_Inicio":     con_inicio.strftime("%Y-%m-%d"),
                        "Fecha_Fin":        con_fin.strftime("%Y-%m-%d"),
                        "Cliente":          con_cliente,
                        "NIT":              con_nit,
                        "Sede":             con_sede,
                        "Nombre_Contacto":  con_contacto,
                        "Celular_Contacto": con_celular,
                        "Servicio":         con_servicio,
                        "Frecuencia":       con_freq,
                        "Tecnico":          con_tecnico,
                        "Valor_Contrato":   con_valor,
                        "Estado_Contrato":  con_estado,
                    }
                    contratos = pd.concat([contratos, pd.DataFrame([nuevo_con])], ignore_index=True)
                    save_contratos(contratos)
                    requiere_items = con_servicio in SERVICIOS_CON_EQUIPOS
                    msg = f"✅ Contrato **{nuevo_con['ID_Contrato']}** registrado."
                    if requiere_items:
                        msg += " Registra los equipos en la pestaña 🔧 Equipos / Ítems."
                    st.success(msg)

        st.divider()
        if not contratos.empty:
            f_srv_con = st.multiselect("Filtrar por servicio", SERVICIOS, default=SERVICIOS, key="f_srv_con")
            vista_con = contratos[contratos["Servicio"].isin(f_srv_con)] if f_srv_con else contratos
            st.dataframe(vista_con, use_container_width=True, hide_index=True)
            st.caption(f"{len(contratos)} contrato(s) registrado(s).")
        else:
            st.info("No hay contratos registrados aún.")

    # ── TAB 2: EQUIPOS / ÍTEMS ───────────────────────────────────────────────
    with tab_equ:
        st.subheader("Registrar equipo o ítem por contrato")
        st.caption("Solo para servicios que requieren registro por equipo: Aires, UPS y Plantas, Cámaras de Seguridad.")

        contratos_eq = contratos[contratos["Servicio"].isin(SERVICIOS_CON_EQUIPOS)] if not contratos.empty else pd.DataFrame()

        if contratos_eq.empty:
            st.warning("No hay contratos de Aires, UPS o Cámaras registrados aún.")
        else:
            with st.form("form_item", clear_on_submit=True):
                opciones_con = contratos_eq.apply(
                    lambda r: f"{r['ID_Contrato']} — {r['Servicio']} | {r['Cliente']} / {r['Sede']}", axis=1
                ).tolist()
                item_con_sel = st.selectbox("Contrato *", opciones_con)
                c1, c2 = st.columns(2)
                with c1:
                    item_marca   = st.text_input("Marca")
                    item_modelo  = st.text_input("Modelo")
                    item_serial  = st.text_input("Número de serie")
                    item_specs   = st.text_input("Especificaciones", placeholder="Ej: 12000 BTU, R-410A / 5 KVA / 4MP")
                with c2:
                    item_ubic    = st.text_input("Ubicación dentro de la sede", placeholder="Ej: Oficina 301, Sala servidor")
                    item_primer  = st.date_input("Fecha primer mantenimiento", value=datetime.today())

                if st.form_submit_button("➕ Agregar ítem", type="primary", use_container_width=True):
                    id_con_sel = item_con_sel.split(" — ")[0]
                    fila_con   = contratos[contratos["ID_Contrato"] == id_con_sel].iloc[0]
                    primer_m   = item_primer.strftime("%Y-%m-%d")
                    nuevo_item = {
                        "ID_Item":              gen_item_id(equipos),
                        "ID_Contrato":          id_con_sel,
                        "Cliente":              fila_con["Cliente"],
                        "Sede":                 fila_con["Sede"],
                        "Servicio":             fila_con["Servicio"],
                        "Marca":                item_marca,
                        "Modelo":               item_modelo,
                        "Numero_Serie":         item_serial,
                        "Especificaciones":     item_specs,
                        "Ubicacion":            item_ubic,
                        "Ultimo_Mantenimiento":  "",
                        "Proximo_Mantenimiento": primer_m,
                    }
                    equipos = pd.concat([equipos, pd.DataFrame([nuevo_item])], ignore_index=True)
                    save_equipos(equipos)
                    st.success(f"✅ {nuevo_item['ID_Item']} registrado — próximo: {primer_m}")

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
        hoy        = datetime.today()
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
    import io
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
                v_fec_fac  = st.date_input("Fecha Facturación", value=datetime.today())
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
                       color_col="Estado_Pago", colores_estado=COLORES_PAGO)
            st.caption(f"{len(ventas)} factura(s) registrada(s).")

            buf_v = io.BytesIO()
            with pd.ExcelWriter(buf_v, engine="openpyxl") as w:
                vista_v.to_excel(w, index=False, sheet_name="Ventas")
            st.download_button("⬇️ Exportar Excel", data=buf_v.getvalue(),
                               file_name=f"ventas_{datetime.now().strftime('%Y%m%d')}.xlsx",
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
                    "Fecha":             datetime.now().strftime("%Y-%m-%d %H:%M"),
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
            tabla_html(costos.reset_index(drop=True))
            buf_c = io.BytesIO()
            with pd.ExcelWriter(buf_c, engine="openpyxl") as w:
                costos.to_excel(w, index=False, sheet_name="Costos")
            st.download_button("⬇️ Exportar Excel", data=buf_c.getvalue(),
                               file_name=f"costos_{datetime.now().strftime('%Y%m%d')}.xlsx",
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

    # ── TAB 1: REGISTRAR ─────────────────────────────────────────────────────
    with tab_reg:
        st.subheader("Nuevo registro de ingreso / costo")

        # Selector de OT para auto-llenar
        ots_fin = ots[ots["Estado"] == "Finalizada"] if not ots.empty else pd.DataFrame()
        opciones_ot = ["— Sin vincular a OT —"]
        if not ots_fin.empty:
            opciones_ot += ots_fin.apply(
                lambda r: f"{r['ID']} | {r['Cliente']} | {r['Servicio']}", axis=1
            ).tolist()

        ot_sel = st.selectbox("Vincular a OT finalizada (opcional)", opciones_ot, key="cv_ot_sel")

        # Auto-llenar desde OT
        cv_ot_ref = cv_sol_ref = cv_cliente = cv_servicio = cv_val_tec = ""
        if ot_sel != "— Sin vincular a OT —":
            ot_id   = ot_sel.split(" | ")[0]
            fila_ot_cv = ots[ots["ID"] == ot_id].iloc[0]
            cv_ot_ref   = ot_id
            cv_sol_ref  = fila_ot_cv.get("SOL_Ref", "")
            cv_cliente  = fila_ot_cv["Cliente"]
            cv_servicio = fila_ot_cv["Servicio"]
            cv_val_tec  = fila_ot_cv.get("Valor_COP", "")
            st.info(f"📋 Cliente: **{cv_cliente}** | Servicio: **{cv_servicio}**")

        with st.form("form_cv", clear_on_submit=True):
            st.markdown("**💵 VENTA — Lo que cobras al cliente**")
            c1, c2, c3 = st.columns(3)
            with c1:
                cv_cot    = st.text_input("N° Cotización Siigo", placeholder="Ej: COT-2026-001")
            with c2:
                cv_venta  = st.text_input("Valor antes de IVA (COP)", placeholder="Ej: 500000")
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                aplica_iva = st.checkbox("Aplica IVA 19%", value=True)

            # Mostrar cálculo de IVA
            venta_num = to_num(cv_venta)
            iva_num   = venta_num * 0.19 if aplica_iva else 0
            total_num = venta_num + iva_num
            if venta_num > 0:
                c1, c2, c3 = st.columns(3)
                c1.metric("Valor antes IVA", f"${venta_num:,.0f}")
                c2.metric("IVA 19%",         f"${iva_num:,.0f}")
                c3.metric("Total a cobrar",   f"${total_num:,.0f}")

            st.divider()
            st.markdown("**🔧 COSTOS — Lo que te cuesta el trabajo**")
            c1, c2, c3 = st.columns(3)
            with c1:
                cv_tec  = st.text_input("Valor asignado al técnico (COP)",
                                        value=cv_val_tec, placeholder="Ej: 150000")
            with c2:
                cv_mat  = st.text_input("Valor de materiales (COP)", placeholder="Ej: 80000")
            with c3:
                cv_fac  = st.text_input("N° Factura materiales", placeholder="Ej: FAC-001")

            # Cálculo de utilidad
            tec_num  = to_num(cv_tec)
            mat_num  = to_num(cv_mat)
            costo_total = tec_num + mat_num
            utilidad    = venta_num - costo_total
            margen      = (utilidad / venta_num * 100) if venta_num > 0 else 0

            if venta_num > 0 or costo_total > 0:
                st.divider()
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total costos",  f"${costo_total:,.0f}")
                c2.metric("Utilidad bruta", f"${utilidad:,.0f}",
                          delta=f"{margen:.1f}% margen",
                          delta_color="normal" if utilidad >= 0 else "inverse")

            if not cv_cliente:
                cv_cliente_manual = st.text_input("Cliente (si no vinculaste OT)", key="cv_cli_man")
                cv_servicio_manual = st.selectbox("Servicio", SERVICIOS, key="cv_ser_man")
            else:
                cv_cliente_manual = cv_cliente
                cv_servicio_manual = cv_servicio

            guardar_cv = st.form_submit_button("💾 Guardar registro", type="primary", use_container_width=True)

            if guardar_cv:
                venta_n = to_num(cv_venta)
                iva_n   = venta_n * 0.19 if aplica_iva else 0
                tec_n   = to_num(cv_tec)
                mat_n   = to_num(cv_mat)
                util_n  = venta_n - tec_n - mat_n
                mg_n    = (util_n / venta_n * 100) if venta_n > 0 else 0
                nuevo_cv = {
                    "ID_Registro":        gen_cv_id(cv),
                    "Fecha":              datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "OT_Ref":             cv_ot_ref,
                    "SOL_Ref":            cv_sol_ref,
                    "Cliente":            cv_cliente_manual,
                    "Servicio":           cv_servicio_manual,
                    "Cotizacion_Siigo":   cv_cot.strip(),
                    "Valor_Antes_IVA":    f"{venta_n:.0f}",
                    "IVA_19":             f"{iva_n:.0f}",
                    "Valor_Total_Cobrado": f"{venta_n + iva_n:.0f}",
                    "Valor_Tecnico":      f"{tec_n:.0f}",
                    "Valor_Materiales":   f"{mat_n:.0f}",
                    "Factura_Materiales": cv_fac.strip(),
                    "Utilidad":           f"{util_n:.0f}",
                    "Margen_Pct":         f"{mg_n:.1f}",
                }
                cv = pd.concat([cv, pd.DataFrame([nuevo_cv])], ignore_index=True)
                save_cv(cv)
                st.success(f"✅ Registro **{nuevo_cv['ID_Registro']}** guardado — Utilidad: **${util_n:,.0f}** ({mg_n:.1f}%)")

    # ── TAB 2: VER REGISTROS ─────────────────────────────────────────────────
    with tab_ver:
        st.subheader("Registros de compras y ventas")
        if cv.empty:
            st.info("Aún no hay registros.")
        else:
            buscar_cv = st.text_input("Buscar cliente", key="buscar_cv")
            vista_cv  = cv if not buscar_cv else cv[
                cv["Cliente"].str.contains(buscar_cv, case=False, na=False)
            ]
            st.dataframe(vista_cv, use_container_width=True, hide_index=True)
            st.caption(f"{len(cv)} registro(s).")

            buf_cv = io.BytesIO()
            with pd.ExcelWriter(buf_cv, engine="openpyxl") as w:
                vista_cv.to_excel(w, index=False, sheet_name="Compras y Ventas")
            st.download_button("⬇️ Exportar Excel", data=buf_cv.getvalue(),
                               file_name=f"compras_ventas_{datetime.now().strftime('%Y%m%d')}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ── TAB 3: RENTABILIDAD ───────────────────────────────────────────────────
    with tab_res:
        st.subheader("Resumen de rentabilidad")
        if cv.empty:
            st.info("Aún no hay datos para mostrar.")
        else:
            total_venta  = cv["Valor_Antes_IVA"].apply(to_num).sum()
            total_iva    = cv["IVA_19"].apply(to_num).sum()
            total_tec    = cv["Valor_Tecnico"].apply(to_num).sum()
            total_mat    = cv["Valor_Materiales"].apply(to_num).sum()
            total_util   = cv["Utilidad"].apply(to_num).sum()
            margen_gral  = (total_util / total_venta * 100) if total_venta > 0 else 0

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total vendido (sin IVA)", f"${total_venta:,.0f}")
            c2.metric("IVA recaudado",            f"${total_iva:,.0f}")
            c3.metric("Costo técnicos",           f"${total_tec:,.0f}")
            c4.metric("Costo materiales",         f"${total_mat:,.0f}")
            c5.metric("Utilidad total",           f"${total_util:,.0f}",
                      delta=f"{margen_gral:.1f}% margen")

            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Utilidad por servicio**")
                util_srv = cv.groupby("Servicio")["Utilidad"].apply(
                    lambda x: x.apply(to_num).sum()
                ).sort_values(ascending=False)
                st.bar_chart(util_srv)
            with c2:
                st.write("**Ventas por servicio**")
                vent_srv = cv.groupby("Servicio")["Valor_Antes_IVA"].apply(
                    lambda x: x.apply(to_num).sum()
                ).sort_values(ascending=False)
                st.bar_chart(vent_srv)


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA: GESTIÓN DE USUARIOS (solo admin)
# ══════════════════════════════════════════════════════════════════════════════
elif pagina == "usuarios":
    if st.session_state.get("user_rol") != "admin":
        st.error("Acceso restringido.")
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
            nu_rol    = st.selectbox("Rol", ["usuario", "admin"])
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
    if not usuarios.empty:
        vista_u = usuarios[["nombre", "correo", "rol"]].copy()
        tabla_html(vista_u.reset_index(drop=True))

        st.divider()
        st.subheader("Eliminar usuario")
        ops_eli = [f"{r['nombre']} ({r['correo']})" for _, r in usuarios.iterrows()
                   if r["correo"] != st.session_state.get("user_correo")]
        if ops_eli:
            sel_eli = st.selectbox("Selecciona el usuario a eliminar", ops_eli)
            if st.button("🗑️ Eliminar", type="secondary"):
                correo_eli = sel_eli.split("(")[-1].replace(")", "").strip()
                usuarios = usuarios[usuarios["correo"] != correo_eli].reset_index(drop=True)
                save_usuarios(usuarios)
                st.success("Usuario eliminado.")
                st.rerun()
        else:
            st.info("No hay otros usuarios para eliminar.")

        st.divider()
        st.subheader("Cambiar mi contraseña")
        with st.form("form_cambiar_pwd"):
            pwd_act  = st.text_input("Contraseña actual", type="password")
            pwd_new  = st.text_input("Nueva contraseña", type="password")
            pwd_new2 = st.text_input("Confirmar nueva contraseña", type="password")
            if st.form_submit_button("🔐 Cambiar contraseña", type="primary"):
                mi_correo = st.session_state.get("user_correo")
                u_row = usuarios[usuarios["correo"] == mi_correo]
                if u_row.iloc[0]["password_hash"] != hash_pwd(pwd_act):
                    st.error("La contraseña actual no es correcta.")
                elif pwd_new != pwd_new2:
                    st.error("Las contraseñas nuevas no coinciden.")
                elif len(pwd_new) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres.")
                else:
                    usuarios.loc[usuarios["correo"] == mi_correo, "password_hash"] = hash_pwd(pwd_new)
                    save_usuarios(usuarios)
                    st.success("✅ Contraseña actualizada correctamente.")
    else:
        st.info("No hay usuarios registrados.")
