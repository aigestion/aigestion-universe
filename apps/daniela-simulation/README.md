# daniela-simulation

Simulation worlds for Daniela OS — engine-agnostic descriptions
that run on MuJoCo, Isaac Lab, or Genesis.

```python
from daniela_simulation import WorldRegistry

registry = WorldRegistry()
print(registry.list())        # empty-room, kitchen, warehouse, humanoid-arena

world = registry.create("kitchen")
world.reset()
state = world.step({"robot": "move_forward"})
print(world.observation)
```

## Layout

```
daniela_simulation/   # World, WorldConfig, WorldRegistry
worlds/               # per-world assets (URDF/MJCF/USD)
configs/              # world manifests
```

## Backends

Install the backend you need:

```bash
pip install daniela-simulation[mujoco]   # MuJoCo + MJX
pip install daniela-simulation[isaac]    # Isaac Sim
```
