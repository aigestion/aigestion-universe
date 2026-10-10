"""Unit tests for the canonical semantic vector layer (Slice 3).

Rule: tests NEVER touch the production database. Vector tests run on tmp_path
and SKIP honestly when sqlite-vec is not installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from daniela_core.memory_semantic import (
    DIM_HASHING,
    Embedder,
    MemorySemantic,
    _embed_hashing,
    _l2_a_coseno,
)
from daniela_core.memory_vault import MemoryVault

if TYPE_CHECKING:
    from pathlib import Path


def test_embedding_tiene_dimension_y_norma_unitaria():
    v = _embed_hashing("factura del proveedor Garcia")
    assert len(v) == DIM_HASHING
    norma = sum(x * x for x in v) ** 0.5
    assert norma == pytest.approx(1.0, abs=1e-9)


def test_embedding_es_determinista():
    a = _embed_hashing("proveedor Garcia marzo")
    b = _embed_hashing("proveedor Garcia marzo")
    assert a == b


def test_texto_vacio_no_revienta():
    v = _embed_hashing("")
    assert len(v) == DIM_HASHING
    assert sum(v) == 0.0


def test_textos_relacionados_puntuan_mas_que_no_relacionados():
    q = _embed_hashing("factura Garcia marzo")
    cerca = _embed_hashing("la factura del proveedor Garcia de marzo")
    lejos = _embed_hashing("el gato duerme en el sofa")
    cos_cerca = sum(x * y for x, y in zip(q, cerca, strict=False))
    cos_lejos = sum(x * y for x, y in zip(q, lejos, strict=False))
    assert cos_cerca > cos_lejos
    assert cos_cerca > 0.5
    assert cos_lejos < 0.2


def test_l2_a_coseno_identidad_con_vectores_unitarios():
    cos = 0.4472135954999579
    l2 = (2 - 2 * cos) ** 0.5
    assert _l2_a_coseno(l2) == pytest.approx(cos, abs=1e-9)


def test_l2_a_coseno_casos_limite():
    assert _l2_a_coseno(0.0) == pytest.approx(1.0)
    assert _l2_a_coseno(2.0) == pytest.approx(0.0)
    assert _l2_a_coseno(5.0) == 0.0


def test_embedder_hashing_por_defecto_y_describe():
    emb = Embedder(proveedor="hashing")
    d = emb.describe()
    assert d["proveedor"] == "hashing"
    assert d["dim"] == DIM_HASHING
    assert d["degradado_a_hashing"] is False


def test_embedder_ollama_cae_a_hashing_sin_servidor():
    emb = Embedder(proveedor="ollama")
    v = emb.embed("factura Garcia marzo")
    assert len(v) == DIM_HASHING  # degradado a hashing
    assert emb.degradado is True


def _vault_con_recuerdos(tmp_path: Path, recuerdos):
    db = tmp_path / "test_rag.db"
    v = MemoryVault(db)
    for src, txt in recuerdos:
        v.record(src, txt)
    return db


RECUERDOS = [
    ("facturas", "El proveedor Garcia emitio la factura 4471 en marzo por 1250 euros"),
    ("facturas", "La factura del proveedor Lopez de febrero ascendia a 890 euros"),
    ("agenda", "Reunion con el cliente Miguelito el martes a las 10 de la manana"),
]


def test_index_all_indexa_todos_los_docs(tmp_path: Path):
    db = _vault_con_recuerdos(tmp_path, RECUERDOS)
    sem = MemorySemantic(db, embedder=Embedder(proveedor="hashing"))
    res = sem.index_all()
    if not res.get("ok"):
        pytest.skip("sqlite-vec no disponible en este entorno")
    assert res["indexados"] == len(RECUERDOS)


def test_search_devuelve_vecinos_vectoriales(tmp_path: Path):
    db = _vault_con_recuerdos(tmp_path, RECUERDOS)
    sem = MemorySemantic(db, embedder=Embedder(proveedor="hashing"))
    idx = sem.index_all()
    if not idx.get("ok"):
        pytest.skip("sqlite-vec no disponible en este entorno")
    res = sem.search("factura Garcia", top_k=2)
    assert len(res) >= 1
    assert res[0]["via"] == "vectorial"
    assert "Garcia" in res[0]["content"]


def test_search_sin_indice_devuelve_vacio(tmp_path: Path):
    db = _vault_con_recuerdos(tmp_path, RECUERDOS)
    sem = MemorySemantic(db, embedder=Embedder(proveedor="hashing"))
    # Sin indexar: search no debe crear esquema ni fallar
    assert sem.search("factura", top_k=2) == []


def test_stats_no_miente(tmp_path: Path):
    db = _vault_con_recuerdos(tmp_path, RECUERDOS)
    sem = MemorySemantic(db, embedder=Embedder(proveedor="hashing"))
    s = sem.stats()
    assert s["docs_en_vault"] == len(RECUERDOS)
    assert "embedder" in s
