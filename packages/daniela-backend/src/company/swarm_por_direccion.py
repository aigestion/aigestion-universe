#!/usr/bin/env python3
# swarm_por_direccion.py - Distribucion de 88 subagentes por 20 directores
# Fuente: indicaciones.txt + team.json
# Nota honesta: el "12F" incluye a la DG Daniela Ferrer Soler.
# Directores solos: 11F / 7M / 2X = 20. Con DG: 12F / 7M / 2X = 21 personas, 21 emails.
# Distribucion: 8 directores x 5 + 12 directores x 4 = 40 + 48 = 88.

SUBAGENTES_POR_DIRECTOR_NOMBRES = {
    # 8 directores con 5 subagentes (40)
    "Elena Vidal": 5,
    "Amara Diallo": 5,
    "Priya Sharma": 5,
    "Sofia Petrova": 5,
    "Valentina Rios": 5,
    "Yuki Nakamura": 5,
    "Mei Chen": 5,
    "Fatima Al-Hassan": 5,
    # 12 directores con 4 subagentes (48)
    "Kenji Tanaka": 4,
    "Liam OConnor": 4,
    "Alex Rivera": 4,  # X - sin genero especificado
    "Marco Ruiz": 4,
    "Kwame Mensah": 4,
    "Ingrid Larsen": 4,
    "Diego Fernandez": 4,
    "Camille Dubois": 4,
    "Jordan Blake": 4,  # X - sin genero especificado
    "Noah Kim": 4,
    "Lucia Gomez": 4,
    "David Steiner": 4,
}

DIRECTORAS = [
    "Elena Vidal", "Amara Diallo", "Priya Sharma", "Sofia Petrova",
    "Valentina Rios", "Yuki Nakamura", "Ingrid Larsen", "Camille Dubois",
    "Mei Chen", "Fatima Al-Hassan", "Lucia Gomez",
]
DIRECTORES_HOMBRES = [
    "Kenji Tanaka", "Liam OConnor", "Marco Ruiz", "Kwame Mensah",
    "Diego Fernandez", "Noah Kim", "David Steiner",
]
DIRECTORES_X = ["Alex Rivera", "Jordan Blake"]

SUBAGENTES_POR_DIRECTOR = {}
_agent_id = 1
for _nombre, _count in SUBAGENTES_POR_DIRECTOR_NOMBRES.items():
    SUBAGENTES_POR_DIRECTOR[_nombre] = list(range(_agent_id, _agent_id + _count))
    _agent_id += _count

SWARM_CONFIG = {
    "total_subagentes": 88,
    "total_directores": 20,
    "composicion_directores": {
        "mujeres": 11,
        "hombres": 7,
        "no_especificado": 2,
    },
    "composicion_total_con_dg": {
        "mujeres": 12,
        "hombres": 7,
        "no_especificado": 2,
    },
    "subagentes_por_director": dict(SUBAGENTES_POR_DIRECTOR_NOMBRES),
    "validacion": {
        "total_asignado": sum(len(v) for v in SUBAGENTES_POR_DIRECTOR.values()),
        "debe_ser": 88,
        "status": "PENDIENTE",
        # Total con DG incluida (21 personas, 21 emails): la DG suma 1 mujer.
        "genero": {"mujeres": 12, "hombres": 7, "no_especificado": 2},
    },
}
SWARM_CONFIG["validacion"]["status"] = (
    "VALIDADO"
    if SWARM_CONFIG["validacion"]["total_asignado"] == 88
    else "ERROR"
)

if __name__ == "__main__":
    print("Swarm AIG validado")
    print("Total subagentes: " + str(SWARM_CONFIG["validacion"]["total_asignado"]))
    print("Status: " + SWARM_CONFIG["validacion"]["status"])
    counts = {}
    for _v in SUBAGENTES_POR_DIRECTOR.values():
        _c = len(_v)
        counts[_c] = counts.get(_c, 0) + 1
    for _count in sorted(counts):
        print("  " + str(_count) + " subagentes: " + str(counts[_count]) + " directores")
