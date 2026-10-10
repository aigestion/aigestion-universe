# ADR-023: Estructura Empresarial AIGestion con Daniela como Directora General

## Contexto
Sistema ECC para gestión empresarial con arquitectura Hermes → Daniela → Agentes.
Daniela Ferrer Soler nombrada Directora General de AIGestion.

## Decisión
Establecer Daniela Ferrer Soler como Directora General (DG) con estructura jerárquica:
- 20 directores (12F/7M/2X) con carteras sectoriales
- 88 subagentes distribuidos por dirección
- Plataforma Hermes como SO/infraestructura subyacente
- Dominio aigestion.net, namespace aig

## Consecuencias
- Positivo: Jerarquía clara, escalabilidad por cliente ({empresa}-daniela)
- Negativo: Sobrecarga inicial de configuración 20 directores + 88 subagentes
- Estado: Implementado y testeado (80 tests verdes, ruff=0)

## Related
- Heracles: Hermes → Daniela → Agentes
- Arquitectura: ADR-022 (decisión anterior de fallback)
- Documentos relacionados: ATRIBUCION-FOTOS.md, team.json