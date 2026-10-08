document.getElementById('btnSummarize').addEventListener('click', () => processPage('summarize'));
document.getElementById('btnGraph').addEventListener('click', () => processPage('extract_graph'));

async function processPage(actionType) {
  const outputDiv = document.getElementById('output');
  outputDiv.innerText = "⏳ Leyendo DOM y procesando con Gemini...";

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.body.innerText
    });

    const response = await fetch('http://localhost:8085/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: `chrome_context ${actionType} ${result.substring(0, 4000)}` })
    });

    const data = await response.json();
    outputDiv.innerText = data.response;
  } catch (err) {
    outputDiv.innerText = "❌ Error de conexión con Daniela OS: " + err.message;
  }
}
