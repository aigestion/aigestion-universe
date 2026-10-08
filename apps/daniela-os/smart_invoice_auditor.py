"""
Smart Invoice Auditor
=====================
OCR + clasificacion + deteccion de duplicados y fraude.

Quick Win #4: Expande daniela_invoice_auditor.py existente.
"""

import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [INVOICE] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class InvoiceAnalysis:
    """Resultado del analisis de una factura."""

    filename: str
    provider: str
    invoice_number: str
    date: str
    amount: float
    category: str
    status: str  # valid, duplicate, suspicious, expired
    warnings: list[str]


class SmartInvoiceAuditor:
    """Auditor inteligente de facturas."""

    def __init__(self):
        self.database_file = "invoice_database.json"
        self.providers_file = "invoice_providers.json"
        self.database = self._cargar_database()
        self.providers = self._cargar_providers()

    def _cargar_database(self) -> list[dict]:
        """Carga base de datos de facturas procesadas."""
        if os.path.exists(self.database_file):
            with open(self.database_file, encoding="utf-8") as f:
                return json.load(f)
        return []

    def _cargar_providers(self) -> dict:
        """Carga proveedores conocidos."""
        if os.path.exists(self.providers_file):
            with open(self.providers_file, encoding="utf-8") as f:
                return json.load(f)
        return {
            "proveedores_conocidos": [
                "amazon",
                "google",
                "microsoft",
                "apple",
                "telefonica",
                "vodafone",
                "orange",
                "endesa",
                "iberdrola",
                "renta",
            ],
            "categorias": {
                "software": ["saas", "licencia", "suscripcion", "cloud"],
                "servicios": ["consultoria", "mantenimiento", "soporte"],
                "infraestructura": ["hosting", "dominio", "servidor"],
                "oficina": ["luz", "agua", "internet", "telefono", "alquiler"],
                "marketing": ["publicidad", "seo", "ads", "campana"],
            },
        }

    def extraer_datos_texto(self, text: str) -> dict:
        """
        Extrae datos de factura desde texto (simulando OCR).

        Args:
            text: Texto extraido de la factura
        """
        datos = {
            "proveedor": self._extraer_proveedor(text),
            "numero": self._extraer_numero(text),
            "fecha": self._extraer_fecha(text),
            "total": self._extraer_total(text),
            "concepto": self._extraer_concepto(text),
        }
        return datos

    def _extraer_proveedor(self, text: str) -> str:
        """Extrae nombre del proveedor."""
        # Buscar proveedores conocidos
        for prov in self.providers.get("proveedores_conocidos", []):
            if prov.lower() in text.lower():
                return prov.title()

        # Intentar extraer de lineas comunes
        lines = text.split("\n")
        for line in lines[:10]:  # Proveedor suele estar al inicio
            if any(word in line.lower() for word in ["s.l.", "s.a.", "sl", "sa", "gmbh", "inc"]):
                return line.strip()

        return "Proveedor desconocido"

    def _extraer_numero(self, text: str) -> str:
        """Extrae numero de factura."""
        patterns = [
            r"factura[\s#]*[Nn]?[Oo]?[\s:]*([A-Z0-9\-]+)",
            r"invoice[\s#]*[Nn]?[Oo]?[\s:]*([A-Z0-9\-]+)",
            r"n[\u00ba°][\s:]*([A-Z0-9\-]+)",
            r"#[\s:]*([A-Z0-9\-]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return "SIN_NUMERO"

    def _extraer_fecha(self, text: str) -> str:
        """Extrae fecha de factura."""
        patterns = [
            r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",  # DD/MM/YYYY
            r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})",  # YYYY/MM/DD
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        return datetime.now().strftime("%Y-%m-%d")

    def _extraer_total(self, text: str) -> float:
        """Extrae importe total."""
        # Buscar cantidades con moneda
        pattern = r"(total|importe|amount)[\s:]*[\u20ac$]?[\s:]*(\d+[.,]\d{2})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(2).replace(",", "."))

        # Buscar cualquier cantidad grande
        amounts = re.findall(r"[\u20ac$]?\s*(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})", text)
        if amounts:
            return max(float(a.replace(",", "").replace(".", ".")) for a in amounts)

        return 0.0

    def _extraer_concepto(self, text: str) -> str:
        """Extrae concepto/descripcion."""
        lines = text.split("\n")
        for line in lines:
            if any(
                word in line.lower() for word in ["concepto", "descripcion", "servicio", "producto"]
            ):
                return line.strip()
        return "Concepto no especificado"

    def clasificar_categoria(self, text: str) -> str:
        """Clasifica factura por categoria."""
        text_lower = text.lower()
        categorias = self.providers.get("categorias", {})

        for categoria, keywords in categorias.items():
            if any(kw in text_lower for kw in keywords):
                return categoria

        return "otros"

    def verificar_factura(self, datos: dict) -> InvoiceAnalysis:
        """
        Verifica factura contra base de datos.

        Detecta: duplicados, montos anomalos, proveedores desconocidos.
        """
        warnings = []
        status = "valid"

        # 1. Verificar duplicado
        factura_id = hashlib.md5(
            f"{datos['proveedor']}_{datos['numero']}_{datos['total']}".encode()
        ).hexdigest()

        existente = next((f for f in self.database if f.get("hash") == factura_id), None)
        if existente:
            warnings.append(f"DUPLICADO: Factura ya procesada el {existente['fecha_procesado']}")
            status = "duplicate"

        # 2. Verificar monto anomalo
        proveedor = datos["proveedor"].lower()
        facturas_proveedor = [
            f for f in self.database if f.get("proveedor", "").lower() == proveedor
        ]

        if facturas_proveedor:
            promedio = sum(f["total"] for f in facturas_proveedor) / len(facturas_proveedor)
            if datos["total"] > promedio * 2:
                warnings.append(f"MONTO ANOMALO: {datos['total']} vs promedio {promedio:.2f}")
                if status == "valid":
                    status = "suspicious"

        # 3. Verificar proveedor desconocido
        if datos["proveedor"] == "Proveedor desconocido":
            warnings.append("PROVEEDOR DESCONOCIDO: Verificar legitimidad")
            if status == "valid":
                status = "suspicious"

        # 4. Verificar fecha futura
        try:
            fecha_factura = datetime.strptime(datos["fecha"], "%Y-%m-%d")
            if fecha_factura > datetime.now() + timedelta(days=1):
                warnings.append("FECHA FUTURA: Verificar fecha de factura")
                if status == "valid":
                    status = "suspicious"
        except Exception:
            pass

        # Guardar en base de datos
        self.database.append(
            {
                "hash": factura_id,
                "proveedor": datos["proveedor"],
                "numero": datos["numero"],
                "fecha": datos["fecha"],
                "total": datos["total"],
                "categoria": self.clasificar_categoria(datos["concepto"]),
                "status": status,
                "fecha_procesado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        self._guardar_database()

        return InvoiceAnalysis(
            filename="factura.pdf",
            provider=datos["proveedor"],
            invoice_number=datos["numero"],
            date=datos["fecha"],
            amount=datos["total"],
            category=self.clasificar_categoria(datos["concepto"]),
            status=status,
            warnings=warnings,
        )

    def _guardar_database(self):
        """Guarda base de datos actualizada."""
        with open(self.database_file, "w", encoding="utf-8") as f:
            json.dump(self.database, f, indent=2, ensure_ascii=False)

    def generar_reporte(self, periodo: str = "mensual") -> dict:
        """Genera reporte de facturas."""
        total = len(self.database)
        if total == 0:
            return {"mensaje": "Sin facturas en base de datos"}

        por_categoria = {}
        por_proveedor = {}
        total_monto = 0
        duplicados = 0
        sospechosas = 0

        for factura in self.database:
            cat = factura["categoria"]
            prov = factura["proveedor"]
            monto = factura["total"]

            por_categoria[cat] = por_categoria.get(cat, 0) + monto
            por_proveedor[prov] = por_proveedor.get(prov, 0) + monto
            total_monto += monto

            if factura["status"] == "duplicate":
                duplicados += 1
            elif factura["status"] == "suspicious":
                sospechosas += 1

        return {
            "periodo": periodo,
            "total_facturas": total,
            "monto_total": round(total_monto, 2),
            "por_categoria": por_categoria,
            "top_proveedores": dict(
                sorted(por_proveedor.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
            "alertas": {"duplicados": duplicados, "sospechosas": sospechosas},
        }

    def demo(self):
        """Demostracion del auditor de facturas."""
        print("=" * 60)
        print("SMART INVOICE AUDITOR - DEMO")
        print("=" * 60)
        print()

        facturas_demo = [
            "Factura N 00123\nProveedor: Amazon Web Services\nFecha: 05/09/2026\nTotal: 150.00\nConcepto: Servicios cloud",
            "Factura N 00123\nProveedor: Amazon Web Services\nFecha: 05/09/2026\nTotal: 150.00\nConcepto: Servicios cloud",  # Duplicado
            "Factura N 99999\nProveedor: Desconocido SL\nFecha: 05/09/2026\nTotal: 5000.00\nConcepto: Consultoria",
            "Factura N 00456\nProveedor: Endesa\nFecha: 05/09/2026\nTotal: 85.50\nConcepto: Suministro electrico",
        ]

        for i, texto in enumerate(facturas_demo, 1):
            print(f"[Factura {i}]")
            datos = self.extraer_datos_texto(texto)
            resultado = self.verificar_factura(datos)

            print(f"  Proveedor: {resultado.provider}")
            print(f"  Numero: {resultado.invoice_number}")
            print(f"  Fecha: {resultado.date}")
            print(f"  Total: {resultado.amount}")
            print(f"  Categoria: {resultado.category}")
            print(f"  Estado: {resultado.status.upper()}")
            if resultado.warnings:
                for w in resultado.warnings:
                    print(f"  ⚠️ {w}")
            print()

        print("[Reporte Mensual]")
        reporte = self.generar_reporte()
        print(f"  Total facturas: {reporte['total_facturas']}")
        print(f"  Monto total: {reporte['monto_total']}")
        print(f"  Duplicados: {reporte['alertas']['duplicados']}")
        print(f"  Sospechosas: {reporte['alertas']['sospechosas']}")
        print()
        print("=" * 60)


if __name__ == "__main__":
    auditor = SmartInvoiceAuditor()
    auditor.demo()
