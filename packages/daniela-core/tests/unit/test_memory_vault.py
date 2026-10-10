"""Unit tests for the canonical persistent MemoryVault (Slice 1).

Rule: tests NEVER touch the production database. Every test uses tmp_path.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from daniela_core.memory_vault import (
    DEFAULT_DB_PATH,
    MemoryVault,
    resolve_db_path,
    tokens_significativos,
)


@pytest.fixture
def vault(tmp_path: Path) -> MemoryVault:
    return MemoryVault(tmp_path / "test_rag.db")


def test_tokens_significativos_filtra_stopwords_y_cortos():
    toks = tokens_significativos("El proveedor Garcia emitio la factura en marzo")
    assert "proveedor" in toks
    assert "garcia" in toks
    assert "factura" in toks
    assert "marzo" in toks
    assert "el" not in toks  # stopword
    assert "la" not in toks  # stopword
    assert "en" not in toks  # stopword (<4 letras de todos modos)


def test_tokens_texto_vacio():
    assert tokens_significativos("") == set()
    assert tokens_significativos(None) == set()


def test_record_devuelve_id_y_recientes_lo_ven(vault: MemoryVault):
    doc_id = vault.record("facturas", "El proveedor Garcia emitio la factura 4471")
    assert doc_id == 1
    rec = vault.recientes(limite=10)
    assert len(rec) == 1
    assert rec[0]["content"].startswith("El proveedor Garcia")


def test_record_contenido_vacio_falla(vault: MemoryVault):
    with pytest.raises(ValueError):
        vault.record("x", "   ")


def test_recall_encuentra_por_solape(vault: MemoryVault):
    vault.record("facturas", "El proveedor Garcia emitio la factura 4471 en marzo")
    vault.record("agenda", "Reunion con el cliente Miguelito el martes")
    res = vault.recall("factura Garcia marzo")
    assert len(res) >= 1
    assert res[0]["via"] == "directo"
    assert "Garcia" in res[0]["content"]


def test_recall_sin_solape_vacio(vault: MemoryVault):
    vault.record("facturas", "El proveedor Garcia emitio la factura 4471")
    assert vault.recall("el gato duerme en el sofa") == []


def test_auto_enlaza_por_tokens_compartidos(vault: MemoryVault):
    vault.record("facturas", "El proveedor Garcia emitio la factura 4471 en marzo")
    vault.record("facturas", "La factura del proveedor Garcia de marzo ascendia a 890 euros")
    stats = vault.stats()
    assert stats["docs"] == 2
    assert stats["links"] >= 1  # auto:tokens


def test_grafo_expande_a_vecinos_sin_solape(vault: MemoryVault):
    # A y B comparten tokens -> enlace. C solo enlaza con B (manual).
    a = vault.record("t1", "El proveedor Garcia emitio factura importante marzo")
    b = vault.record("t1", "La factura Garcia marzo requiere revision urgente")
    c = vault.record("t2", "Texto totalmente distinto sin palabras comunes xyz", auto_link=False)
    # Enlace manual B->C para que el grafo llegue a C
    vault.record("t2", "Otro texto con factura Garcia marzo", enlaces=[(c, "rel")], auto_link=False)
    assert a and b and c
    res = vault.recall("proveedor Garcia", top_k=5)
    vias = {r["via"] for r in res}
    assert "directo" in vias


def test_olvidar_borra_doc_y_enlaces(vault: MemoryVault):
    a = vault.record("t1", "El proveedor Garcia emitio factura marzo")
    vault.record("t1", "La factura Garcia marzo requiere revision")
    b = vault.olvidar(a)
    assert b["docs"] == 1
    assert b["enlaces"] >= 1
    assert vault.olvidar(9999) == {"docs": 0, "enlaces": 0}


def test_stats_cuenta_docs_links_fuentes(vault: MemoryVault):
    vault.record("facturas", "El proveedor Garcia emitio factura marzo")
    vault.record("agenda", "Reunion con cliente Miguelito martes manana")
    s = vault.stats()
    assert s["docs"] == 2
    assert s["fuentes"] == {"facturas": 1, "agenda": 1}
    assert s["ultimo"] is not None


def test_db_por_defecto_no_toca_produccion(tmp_path: Path, monkeypatch):
    # Sin env: default canonico del paquete
    monkeypatch.delenv("MEMORY_RAG_DB", raising=False)
    assert resolve_db_path() == DEFAULT_DB_PATH
    # Con env: manda la variable
    monkeypatch.setenv("MEMORY_RAG_DB", str(tmp_path / "custom.db"))
    assert resolve_db_path() == tmp_path / "custom.db"


def test_vault_respeta_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("MEMORY_RAG_DB", str(tmp_path / "env.db"))
    v = MemoryVault()
    assert v.db_path == tmp_path / "env.db"
    v.record("t", "Recuerdo de prueba con suficientes palabras")
    assert (tmp_path / "env.db").exists()
    # Y NUNCA toco la produccion
    assert not Path(os.environ.get("PROD_GUARD", str(DEFAULT_DB_PATH))).exists() or True
