from dotenv import dotenv_values
import urllib.request, json

tok = (dotenv_values('.env').get('GEMINI_API_KEY') or '').strip()
for m in ['gemini-flash-latest', 'gemini-3.8-flash']:
    for label, gcfg in [
        ('budget0', {'maxOutputTokens': 300, 'thinkingConfig': {'thinkingBudget': 0}}),
        ('sin tocar', {'maxOutputTokens': 300}),
    ]:
        body = json.dumps({'contents': [{'parts': [{'text': 'Responde exactamente: hola'}]}],
                           'generationConfig': gcfg}).encode()
        req = urllib.request.Request(
            f'https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={tok}',
            data=body, headers={'Content-Type': 'application/json'})
        try:
            r = json.load(urllib.request.urlopen(req, timeout=60))
            u = r.get('usageMetadata', {})
            parts = r['candidates'][0].get('content', {}).get('parts', [])
            txt = ''.join(p.get('text', '') for p in parts).strip()
            print(f"{m:24} {label:10} pensamiento={u.get('thoughtsTokenCount',0):>3} "
                  f"total={u.get('totalTokenCount',0):>3} txt={txt[:15]!r}")
        except Exception as ex:
            err = (ex.read().decode('utf-8', 'replace')[:150] if hasattr(ex, 'read') else str(ex)).replace('\n', ' ')
            print(f"{m:24} {label:10} FAIL {getattr(ex, 'code', '')} {err}")
