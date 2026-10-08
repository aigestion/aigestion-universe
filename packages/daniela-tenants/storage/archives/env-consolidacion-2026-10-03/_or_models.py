import urllib.request, json

req = urllib.request.Request('https://openrouter.ai/api/v1/models', headers={'User-Agent': 'aig'})
d = json.load(urllib.request.urlopen(req, timeout=30))
free = [m for m in d['data'] if m['id'].endswith(':free')]
print('modelos free:', len(free))
reason = [m for m in free if 'reasoning' in (m.get('supported_parameters') or [])]
print('free con reasoning:', len(reason))
for m in sorted(reason, key=lambda x: x.get('created', ''), reverse=True):
    ctx = m.get('context_length', 0)
    created = str(m.get('created', ''))[:10]
    print(f"  {m['id']:58} ctx={ctx:>7} created={created}")
