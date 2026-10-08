/**
 * AIG_CORE — Monorepo Centralizado
 * Gestión de: Sentinel, VaultSync, Reporter y Webhook.
 */

// 1. WEBHOOK RELAY (Punto de entrada único)
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    return ContentService.createTextOutput(JSON.stringify({ status: "success", received: data })).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ status: "error", error: error.toString() })).setMimeType(ContentService.MimeType.JSON);
  }
}

// 2. SENTINEL (Facturas/Gmail)
function ejecutarSentinel() {
  const threads = GmailApp.search('label:unread (subject:factura OR subject:invoice OR filename:pdf)');
  threads.forEach(t => t.getMessages().forEach(m => {
    if(m.isUnread()) { /* lógica de guardado */ m.markRead(); }
  }));
}

// 3. VAULT SYNC (Drive)
function procesarVault() {
  const folder = DriveApp.getFoldersByName('AIGestion_Facturas_Inbound').next();
  const files = folder.getFiles();
  while(files.hasNext()) { console.log('Indexado: ' + files.next().getName()); }
}

// 4. REPORTER (Docs)
function generarInformeSemanal() {
  const doc = DocumentApp.create('Informe_Ejecutivo_' + new Date().toDateString());
  doc.getBody().appendParagraph('AIG.NET — REPORTE CORE');
}
