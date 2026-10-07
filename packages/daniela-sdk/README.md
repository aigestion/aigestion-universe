# daniela-sdk

Official SDK for Daniela OS (aigestion.net).

## Python

```bash
pip install daniela-sdk
```

```python
from daniela_sdk import DanielaClient

with DanielaClient("http://localhost:9200") as daniela:
    print(daniela.greet())
    print(daniela.brain_stats())
    result = daniela.process("What is the weather?")
    daniela.memory_store("episodic", "User asked about weather")
    hits = daniela.memory_recall("weather")
    engines = daniela.engines()
```

## TypeScript

```bash
npm install @aigestion/daniela-sdk
```

```ts
import { DanielaClient } from "@aigestion/daniela-sdk"

const daniela = new DanielaClient("http://localhost:9200")
console.log(await daniela.greet())
```
