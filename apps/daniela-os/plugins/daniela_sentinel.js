/**
 * DANIELA OS — Sentinel Automático de Facturas y Correos
 * AIGestion.net // Sostenibilidad y Soberanía Operativa
 */

const CONFIG = {
  SEARCH_QUERY: 'label:unread (subject:factura OR subject:invoice OR filename:pdf)',
  DRIVE_FOLDER_NAME: 'AIGestion_Facturas_Inbound',
  LABEL_NAME: 'AIGestion/Facturas'
};

function ejecutarDanielaSentinel() {
  console.log('🟢 [DANIELA OS]: Iniciando escaneo de bandeja de entrada...');
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
