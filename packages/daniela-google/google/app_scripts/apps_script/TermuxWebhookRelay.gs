/**
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
