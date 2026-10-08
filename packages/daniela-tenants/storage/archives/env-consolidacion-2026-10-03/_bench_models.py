from dotenv import dotenv_values
import urllib.request, json, time

tok = (dotenv_values('.env').get('GEMINI_API_KEY') or '').strip()
candidatos = [
    'gemini-flash-latest',
    'gemini-3.8-flash',
    'gemini-3.7-flash',
    'gemini-3.6-flash',
    'gemini-3.5-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.1-flash-lite',
    'gemini-2.5-flash',
]
prompt = 'Responde exactamente: hola'
for m in candidatos:
    body = json.dumps({
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': 300},
    }).encode()
    req = urllib.request.Request(
        f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={tok}',
        data=body, headers={'Content-Type': 'application/json'})
    t0 = time.time()
    try:
        r = json.load(urllib.request.urlopen(req, timeout=60))
        dt = time.time() - t0
        u = r.get('usageMetadata', {})
        parts = r['candidates'][0].get('content', {}).get('parts', [])
        txt = ''.join(p.get('text', '') for p in parts).strip()
        print(f"{m:26} OK  ver={r.get('modelVersion','?'):20} "
              f"pensamiento={u.get('thoughtsTokenCount',0):>3} "
              f"salida={u.get('candidatesTokenCount',0):>3} "
              f"total={u.get('totalTokenCount',0):>3} "
              f"{dt:4.1f}s finish={r['candidates'][0].get('finishReason','?'):10} "
              f"txt={txt[:20]!r}")
    except Exception as ex:
        code = getattr(ex, 'code', '')
        err = (ex.read().decode('utf-8', 'replace')[:120] if hasattr(ex, 'read') else str(ex)).replace('\n', ' ')
        print(f"{m:26} FAIL {code} {err}")
