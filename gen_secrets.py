import json

with open(r"D:\Descargas\minzoe-app-cff3a6612103.json", "r") as f:
    c = json.load(f)

pk = c["private_key"].replace("\n", "\\n")

toml = f"""spreadsheet_id = "1EzOOo8606udpHwjoYOS4u08tSWqz4UHAaMDlurrhoR4"

[gcp_service_account]
type = "service_account"
project_id = "{c['project_id']}"
private_key_id = "{c['private_key_id']}"
private_key = "{pk}"
client_email = "{c['client_email']}"
client_id = "{c['client_id']}"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "{c['client_x509_cert_url']}"

spreadsheet_id = "1EzOOo8606udpHwjoYOS4u08tSWqz4UHAaMDlurrhoR4"
"""

with open(r"D:\Escritorio\LA ASISTENTE MINZOE\.streamlit\secrets.toml", "w", encoding="utf-8") as f:
    f.write(toml)

print("secrets.toml generado correctamente")
