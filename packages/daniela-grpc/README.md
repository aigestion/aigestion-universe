# daniela-grpc

gRPC contracts for Daniela OS, defined in `proto/daniela/v1/`.

## Generate

```bash
buf generate        # produces daniela_grpc/ python stubs
buf lint            # lint protos
buf breaking        # breaking-change detection vs main
```

## Services

- `BrainService` — cognitive processing + streaming
- `OrchestratorService` — swarm delegation, Raft consensus, engine registry
- `MemoryService` — three-tier memory vault

## Layout

```
proto/daniela/v1/*.proto   # source of truth
daniela_grpc/              # generated python stubs (committed)
buf.yaml                   # lint/breaking config
buf.gen.yaml               # codegen config
```
