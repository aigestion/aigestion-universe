import os
import subprocess

BASE_DIR = os.path.expanduser("~/daniela-os/apps_script")
os.makedirs(BASE_DIR, exist_ok=True)

print("⚡ [DANIELA OS]: Creando proyecto de Google Apps Script automáticamente...")

# 1. Crear el proyecto en los servidores de Google mediante Clasp
subprocess.run(["clasp", "create", "--type", "standalone", "--title", "Daniela_Sentinel_aig"], cwd=BASE_DIR)

# 2. Inyectar el código de Apps Script
gs_code = """/**
 * DANIELA OS — Sentinel Automático de Facturas y Correos
 * aigestion.net // Sostenibilidad y Soberanía Operativa
 */

const CONFIG = {
  SEARCH_QUERY: 'label:unread (subject:factura OR subject:invoice OR filename:pdf)',
  DRIVE_FOLDER_NAME: 'AIGestion_Facturas_Inbound',
  LABEL_NAME: 'aig/Facturas'
};

function ejecutarDanielaSentinel() {
  console.log('🟢 [DANIELA OS]: Escaneando correo entrante...');
  let folder = obtenerOCrearCarpeta(CONFIG.DRIVE_FOLDER_NAME);
  let label = obtenerOCrearEtiqueta(CONFIG.LABEL_NAME);
  let threads = GmailApp.search(CONFIG.SEARCH_QUERY);

  threads.forEach(thread => {
    let messages = thread.getMessages();
    messages.forEach(message => {
      if (message.isUnread()) {
        let attachments = message.getAttachments();
        attachments.forEach(attachment => {
          let mimeType = attachment.getContentType();
          if (mimeType === 'application/pdf' || mimeType.includes('image/')) {
            let fileName = `${Utilities.formatDate(new Date(), "GMT+1", "yyyyMMdd")}_${attachment.getName()}`;
            folder.createFile(attachment.copyBlob().setName(fileName));
            console.log(`📁 Ingesta en Google Drive: ${fileName}`);
          }
        });
        message.markRead();
      }
    });
    thread.addLabel(label);
  });
}

function obtenerOCrearCarpeta(nombreCarpeta) {
  let folders = DriveApp.getFoldersByName(nombreCarpeta);
  return folders.hasNext() ? folders.next() : DriveApp.createFolder(nombreCarpeta);
}

function obtenerOCrearEtiqueta(nombreEtiqueta) {
  let label = GmailApp.getUserLabelByName(nombreEtiqueta);
  return label ? label : GmailApp.createLabel(nombreEtiqueta);
}
"""

with open(os.path.join(BASE_DIR, "Code.gs"), "w", encoding="utf-8") as f:
    f.write(gs_code)

# 3. Subir el código automáticamente a la nube de Google
print("🚀 [DANIELA OS]: Desplegando el código en los servidores de Google...")
subprocess.run(["clasp", "push", "-f"], cwd=BASE_DIR)

print("\n✨ [ÉXITO TOTAL]: El Apps Script fue creado y desplegado automáticamente en admin@aigestion.net.")
