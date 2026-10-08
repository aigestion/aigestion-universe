import os

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.modify",
]

creds_path = os.path.expanduser("~/daniela-os/credentials.json")
token_path = os.path.expanduser("~/daniela-os/token.json")

flow = InstalledAppFlow.from_client_secrets_file(
    creds_path, scopes=SCOPES, redirect_uri="http://localhost:8080/"
)

auth_url, _ = flow.authorization_url(prompt="consent")

print("\n" + "=" * 70)
print("🔗 1. COPIA Y ABRE ESTA URL EN EL NAVEGADOR:")
print("=" * 70 + "\n")
print(auth_url)
print("\n" + "=" * 70)
print("⚠️  2. PEGA LA URL DE REDIRECCIÓN (LOCALHOST:8080/...) ABAJO:")
print("=" * 70 + "\n")

auth_response = input("📥 URL de redirección: ").strip()

flow.fetch_token(authorization_response=auth_response)
creds = flow.credentials

with open(token_path, "w") as token:
    token.write(creds.to_json())

print("\n✅ ¡Token de Workspace + Gmail actualizado exitosamente en ~/daniela-os/token.json!")
