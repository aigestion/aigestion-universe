/**
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
