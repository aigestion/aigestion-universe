/**
 * DANIELA OS — Executive Report Generator
 */
function generarInformeSemanal() {
  const doc = DocumentApp.create(`Informe_Ejecutivo_AIGestion_${Utilities.formatDate(new Date(), "GMT+1", "yyyyMMdd")}`);
  const body = doc.getBody();

  body.appendParagraph("AIG.NET — REPORTE EJECUTIVO").setHeading(DocumentApp.ParagraphHeading.HEADING1);
  body.appendParagraph(`Fecha de emisión: ${new Date().toLocaleDateString()}`);
  body.appendHorizontalRule();

  body.appendParagraph("1. Resumen de Operaciones").setHeading(DocumentApp.ParagraphHeading.HEADING2);
  body.appendParagraph("Facturas e incidentes procesados por Daniela OS.");

  doc.saveAndClose();
  console.log(`📄 Documento generado: ${doc.getUrl()}`);
}
