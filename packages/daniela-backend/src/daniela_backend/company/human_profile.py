#!/usr/bin/env python3
# human_profile.py - Perfiles humanos de la Dirección de AIGestion
# Source: indicaciones.txt conversacion 1
from __future__ import annotations

from typing import TypedDict


# Type hints para DG_PROFILE
class DgProfile(TypedDict):
    nombre: str
    rol: str
    imagen: str
    email: str
    departamento: str
    nivel: int
    facultad: str
    ano_ingreso: int
    genero: str

DG_PROFILE: DgProfile = {
    "nombre": "Daniela Ferrer Soler",
    "rol": "Directora General",
    "imagen": "daniela_avatar.jpg",
    "email": "daniela@aigestion.net",
    "departamento": "Ejecutiva",
    "nivel": 0,
    "facultad": "Universidad Complutense de Madrid",
    "ano_ingreso": 2018,
    "genero": "Femenino",
}

# Type hints para director individual
class DirectorProfile(TypedDict):
    nombre: str
    rol: str
    imagen: str
    email: str
    departamento: str
    nivel: int
    facultad: str
    ano_ingreso: int
    genero: str

# Type hints para configuración
class Configuracion(TypedDict):
    empresa: str
    dashboard_puerto: int
    hermes_puerto: int
    hermes_openclaw_puerto: int

CONFIGURACION: Configuracion = {
    "empresa": "AIGestion",
    "dashboard_puerto": 8082,
    "hermes_puerto": 9300,
    "hermes_openclaw_puerto": 9900,
}

# Type hints para lista de directores
class DirectorType(TypedDict):
    nombre: str
    rol: str
    imagen: str
    email: str
    departamento: str
    nivel: int
    facultad: str
    ano_ingreso: int
    genero: str

DIRECTORES_PROFILE: list[DirectorProfile] = [
    {
        "nombre": "Elena Vidal",
        "rol": "Directora Ejecutiva Operaciones",
        "imagen": "elena_vidal.jpg",
        "email": "elena.vidal@aigestion.net",
        "departamento": "Operaciones",
        "nivel": 1,
        "facultad": "IE Business School",
        "ano_ingreso": 2019,
        "genero": "Femenino",
    },
    {
        "nombre": "Amara Diallo",
        "rol": "Directora de Diversidad e Inclusión",
        "imagen": "amara_diallo.jpg",
        "email": "amara.diallo@aigestion.net",
        "departamento": "RRHH",
        "nivel": 1,
        "facultad": "Universidad de Barcelona",
        "ano_ingreso": 2020,
        "genero": "Femenino",
    },
    {
        "nombre": "Priya Sharma",
        "rol": "Directora de Tecnología",
        "imagen": "priya_sharma.jpg",
        "email": "priya.sharma@aigestion.net",
        "departamento": "TI",
        "nivel": 1,
        "facultad": "Stanford University",
        "ano_ingreso": 2018,
        "genero": "Femenino",
    },
    {
        "nombre": "Kenji Tanaka",
        "rol": "Director de Desarrollo Internacional",
        "imagen": "kenji_tanaka.jpg",
        "email": "kenji.tanaka@aigestion.net",
        "departamento": "Expansión",
        "nivel": 1,
        "facultad": "Waseda University",
        "ano_ingreso": 2019,
        "genero": "Masculino",
    },
    {
        "nombre": "Sofia Petrova",
        "rol": "Directora de Finanzas",
        "imagen": "sofia_petrova.jpg",
        "email": "sofia.petrova@aigestion.net",
        "departamento": "Finanzas",
        "nivel": 1,
        "facultad": "Universidad Complutense de Madrid",
        "ano_ingreso": 2021,
        "genero": "Femenino",
    },
    {
        "nombre": "Liam O'Connor",
        "rol": "Director de Marketing",
        "imagen": "liam_oconnor.jpg",
        "email": "liam.oconnor@aigestion.net",
        "departamento": "Marketing",
        "nivel": 1,
        "facultad": "University College Dublin",
        "ano_ingreso": 2018,
        "genero": "Masculino",
    },
    {
        "nombre": "Valentina Ríos",
        "rol": "Directora de Innovación",
        "imagen": "valentina_rios.jpg",
        "email": "valentina.rios@aigestion.net",
        "departamento": "I+D+i",
        "nivel": 1,
        "facultad": "Pontifical Catholic University",
        "ano_ingreso": 2020,
        "genero": "Femenino",
    },
    {
        "nombre": "Alex Rivera",
        "rol": "Director de Datos y AI",
        "imagen": "alex_rivera.jpg",
        "email": "alex.rivera@aigestion.net",
        "departamento": "Data Science",
        "nivel": 1,
        "facultad": "MIT",
        "ano_ingreso": 2020,
        "genero": "Masculino",
    },
    {
        "nombre": "Yuki Nakamura",
        "rol": "Directora de Expansión Asiática",
        "imagen": "yuki_nakamura.jpg",
        "email": "yuki.nakamura@aigestion.net",
        "departamento": "Internacionalización",
        "nivel": 1,
        "facultad": "University of Tokyo",
        "ano_ingreso": 2021,
        "genero": "Femenino",
    },
    {
        "nombre": "Marco Ruiz",
        "rol": "Director de Relaciones Institucionales",
        "imagen": "marco_ruiz.jpg",
        "email": "marco.ruiz@aigestion.net",
        "departamento": "Relaciones Institucionales",
        "nivel": 1,
        "facultad": "Universidad Autónoma de Madrid",
        "ano_ingreso": 2019,
        "genero": "Masculino",
    },
    {
        "nombre": "Kwame Mensah",
        "rol": "Director de Sostenibilidad",
        "imagen": "kwame_mensah.jpg",
        "email": "kwame.mensah@aigestion.net",
        "departamento": "Sostenibilidad",
        "nivel": 1,
        "facultad": "University of Cambridge",
        "ano_ingreso": 2020,
        "genero": "Masculino",
    },
    {
        "nombre": "Ingrid Larsen",
        "rol": "Directora de Atención al Cliente",
        "imagen": "ingrid_larsen.jpg",
        "email": "ingrid.larsen@aigestion.net",
        "departamento": "Servicio al Cliente",
        "nivel": 1,
        "facultad": "Aarhus University",
        "ano_ingreso": 2018,
        "genero": "Femenino",
    },
    {
        "nombre": "Diego Fernández",
        "rol": "Director de Cumplimiento Normativo",
        "imagen": "diego_fernandez.jpg",
        "email": "diego.fernandez@aigestion.net",
        "departamento": "Legal",
        "nivel": 1,
        "facultad": "Universidad de Deusto",
        "ano_ingreso": 2021,
        "genero": "Masculino",
    },
    {
        "nombre": "Camille Dubois",
        "rol": "Directora de Cadena de Suministro",
        "imagen": "camille_dubois.jpg",
        "email": "camille.dubois@aigestion.net",
        "departamento": "Operaciones",
        "nivel": 1,
        "facultad": "Sorbonne University",
        "ano_ingreso": 2019,
        "genero": "Femenino",
    },
    {
        "nombre": "Mei Chen",
        "rol": "Directora de Desarrollo de Producto",
        "imagen": "mei_chen.jpg",
        "email": "mei.chen@aigestion.net",
        "departamento": "Producto",
        "nivel": 1,
        "facultad": "National University of Singapore",
        "ano_ingreso": 2020,
        "genero": "Femenino",
    },
    {
        "nombre": "Jordan Blake",
        "rol": "Director de Ciberseguridad",
        "imagen": "jordan_blake.jpg",
        "email": "jordan.blake@aigestion.net",
        "departamento": "TI Seguridad",
        "nivel": 1,
        "facultad": "University of Southern California",
        "ano_ingreso": 2021,
        "genero": "Masculino",
    },
    {
        "nombre": "Fatima Al-Hassan",
        "rol": "Directora de Responsabilidad Social",
        "imagen": "fatima_al-hassan.jpg",
        "email": "fatima.al-hassan@aigestion.net",
        "departamento": "CSR",
        "nivel": 1,
        "facultad": "Sciences Po",
        "ano_ingreso": 2019,
        "genero": "Femenino",
    },
    {
        "nombre": "Noah Kim",
        "rol": "Director de Expansión Coreana",
        "imagen": "noah_kim.jpg",
        "email": "noah.kim@aigestion.net",
        "departamento": "Internacionalización",
        "nivel": 1,
        "facultad": "Yonsei University",
        "ano_ingreso": 2021,
        "genero": "Masculino",
    },
    {
        "nombre": "Lucía Gómez",
        "rol": "Directora de Experiencia de Usuario",
        "imagen": "lucia_gomez.jpg",
        "email": "lucia.gomez@aigestion.net",
        "departamento": "UX",
        "nivel": 1,
        "facultad": "Politecnico di Milano",
        "ano_ingreso": 2018,
        "genero": "Femenino",
    },
    {
        "nombre": "David Steiner",
        "rol": "Director de Auditoría Interna",
        "imagen": "david_steiner.jpg",
        "email": "david.steiner@aigestion.net",
        "departamento": "Auditoría",
        "nivel": 1,
        "facultad": "University of Oxford",
        "ano_ingreso": 2021,
        "genero": "Masculino",
    },
]

SUBAGENTES_TOTAL = 88
