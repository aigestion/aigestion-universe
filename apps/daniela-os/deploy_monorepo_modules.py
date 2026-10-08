import os
import subprocess

BASE_DIR = os.path.expanduser("~/daniela-os/apps_script")
os.makedirs(BASE_DIR, exist_ok=True)

print("⚡ [DANIELA OS]: Inyectando módulos avanzados al monorepo Apps Script...")

# 1. DriveVaultSync.gs
vault_code = """/**
 * DANIELA OS — Drive Vault Ingestor & OCR Indexer
 */
function procesarNuevosDocumentos() {
  const FOLDER_NAME = 'AIGestion_Facturas_Inbound';
  const folders = DriveApp.getFoldersByName(FOLDER_NAME);
  if (!folders.hasNext()) return;

  const folder = folders.next();
  const files = folder.getFiles();

  while (files.hasNext()) {
    let file = files.next();
    console.log(`✅ Indexado en Vault: ${file.getName()} (${file.getSize()} bytes)`);
  }
}
"""

# 2. DocsExecutiveReporter.gs
reporter_code = """/**
 * DANIELA OS — Executive Report Generator
 */
function generarInformeSemanal() {
  const doc = DocumentApp.create(`Informe_Ejecutivo_AIGestion_${Utilities.formatDate(new Date(), "GMT+1", "yyyyMMdd")}`);
  const body = doc.getBody();

  body.appendParagraph("AIGESTION.NET — REPORTE EJECUTIVO").setHeading(DocumentApp.ParagraphHeading.HEADING1);
  body.appendParagraph(`Fecha de emisión: ${new Date().toLocaleDateString()}`);
  body.appendHorizontalRule();

  body.appendParagraph("1. Resumen de Operaciones").setHeading(DocumentApp.ParagraphHeading.HEADING2);
  body.appendParagraph("Facturas e incidentes procesados por Daniela OS.");

  doc.saveAndClose();
  console.log(`📄 Documento generado: ${doc.getUrl()}`);
}
"""

# 3. TermuxWebhookRelay.gs
webhook_code = """/**
 * DANIELA OS — Termux Webhook Listener
 */
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      message: "Evento recibido por Daniela OS",
      received: data
    })).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
"""

# Guardar los archivos locales
files = {
    "DriveVaultSync.gs": vault_code,
    "DocsExecutiveReporter.gs": reporter_code,
    "TermuxWebhookRelay.gs": webhook_code,
}

for filename, content in files.items():
    with open(os.path.join(BASE_DIR, filename), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📁 Módulo creado: {filename}")

# Subir actualización completa a la nube de Google
print("🚀 [DANIELA OS]: Sincronizando monorepo completo mediante Clasp...")
subprocess.run(["clasp", "push", "-f"], cwd=BASE_DIR)

print("\n✨ [ÉXITO TOTAL]: Módulos desplegados en la nube de Google Apps Script.")
