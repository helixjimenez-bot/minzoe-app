"""Reemplaza datetime.now() con ahora_colombia() manteniendo UTF-8."""
import re

with open("solicitudes_minzoe.py", "r", encoding="utf-8") as f:
    txt = f.read()

# Agregar funcion ahora_colombia despues de los imports
FUNC = '''
def ahora_colombia():
    """Retorna datetime actual en hora Colombia (UTC-5)."""
    return datetime.utcnow() - timedelta(hours=5)

'''

# Insertar funcion antes de COLS_COUNTERS
txt = txt.replace("COLS_COUNTERS = ", FUNC + "COLS_COUNTERS = ", 1)

# Reemplazar datetime.now() en contextos de fecha/hora (no en comparaciones ni strptime)
txt = txt.replace("datetime.now().strftime(", "ahora_colombia().strftime(")
txt = txt.replace("datetime.now().hour", "ahora_colombia().hour")
txt = txt.replace("ahora = datetime.now()", "ahora = ahora_colombia()")
txt = txt.replace("desde = desde or datetime.now()", "desde = desde or ahora_colombia()")
txt = txt.replace("hoy_dash = datetime.now()", "hoy_dash = ahora_colombia()")
txt = txt.replace("hoy        = datetime.today()", "hoy        = ahora_colombia()")
txt = txt.replace("hoy       = datetime.today()", "hoy       = ahora_colombia()")
txt = txt.replace("value=datetime.today()", "value=ahora_colombia().date()")

with open("solicitudes_minzoe.py", "w", encoding="utf-8") as f:
    f.write(txt)

print("OK - reemplazos completados en UTF-8")
