# daniela-research

Research environments for Daniela OS.

- **`EvalHarness`** — run eval cases against any callable
  (model, tool, or pipeline) with a pluggable scorer.
- Experiment tracking configs in `configs/`.
- Jupyter notebooks in `notebooks/`.

```python
from daniela_research import EvalHarness

h = EvalHarness("brain-v0")
h.add("What is 2+2?", "4")
h.add("Capital of France?", "Paris")

report = await h.run(my_model_fn)
print(report)  # pass_rate, avg_score, avg_latency_ms
```

## Layout

```
daniela_research/eval_harness.py   # core harness
environments/                       # env configs
notebooks/                          # experiments
configs/                            # experiment manifests
```
