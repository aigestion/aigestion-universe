/**
 * aigestion.net — Core Webhook Relay
 * Operaciones bajo la cuenta corporativa admin@aigestion.net
 */
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    return ContentService.createTextOutput(JSON.stringify({
      status: "success",
      message: "Conexión profesional aigestion.net verificada",
      received: data
    })).setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      status: "error",
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
