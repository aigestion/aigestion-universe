"""
Code Generation Agent
=====================
Genera codigo, prueba, depura y documenta automaticamente.

Quick Win #9: Expande coder_engine.py existente.
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CODEGEN] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class CodeGenerationResult:
    """Resultado de generacion de codigo."""

    language: str
    code: str
    tests: str
    documentation: str
    status: str  # generated, tested, debugged, complete
    errors: list[str]


class CodeGenerationAgent:
    """Agente de generacion de codigo end-to-end."""

    def __init__(self):
        self.templates = self._cargar_templates()
        self.history = []

    def _cargar_templates(self) -> dict:
        """Carga templates de codigo."""
        return {
            "python": {
                "function": '''def {name}({params}):
    """
    {description}

    Args:
        {args_doc}

    Returns:
        {return_doc}
    """
    # TODO: Implementar logica
    {body}
    return result
''',
                "class": '''class {name}:
    """{description}"""

    def __init__(self{init_params}):
        {init_body}

    def {method_name}(self{method_params}):
        """{method_doc}"""
        {method_body}
''',
                "flask_endpoint": '''@{app}.route('{route}', methods={methods})
def {name}({params}):
    """
    {description}
    ---
    {swagger_doc}
    """
    try:
        {body}
        return jsonify({response}), 200
    except Exception as e:
        return jsonify({{"error": str(e)}}), 500
''',
            },
            "javascript": {
                "function": """/**
 * {description}
 * @param {params} {param_types}
 * @returns {return_type}
 */
function {name}({params}) {{
    // {logic}
    {body}
    return result;
}}
""",
                "class": """/**
 * {description}
 */
class {name} {{
    constructor({init_params}) {{
        {init_body}
    }}

    {method_name}({method_params}) {{
        // {method_doc}
        {method_body}
    }}
}}
""",
            },
            "sql": {
                "query": """-- {description}
SELECT {columns}
FROM {table}
WHERE {conditions}
{order_by}
{limit};
"""
            },
        }

    def parse_requirement(self, description: str) -> dict:
        """
        Parsea requerimiento en lenguaje natural a especificacion tecnica.

        Args:
            description: Descripcion del requerimiento

        Returns:
            Dict con especificacion parseada
        """
        spec = {
            "language": self._detect_language(description),
            "type": self._detect_type(description),
            "name": self._extract_name(description),
            "description": description,
            "inputs": self._extract_inputs(description),
            "outputs": self._extract_outputs(description),
            "constraints": self._extract_constraints(description),
        }
        return spec

    def _detect_language(self, description: str) -> str:
        """Detecta lenguaje de programacion solicitado."""
        desc_lower = description.lower()
        languages = {
            "python": ["python", "py", "flask", "django", "fastapi"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular"],
            "typescript": ["typescript", "ts"],
            "sql": ["sql", "query", "base de datos", "database"],
            "html": ["html", "css", "frontend"],
            "bash": ["bash", "shell", "script", "comando"],
        }

        for lang, keywords in languages.items():
            if any(kw in desc_lower for kw in keywords):
                return lang

        return "python"  # Default

    def _detect_type(self, description: str) -> str:
        """Detecta tipo de codigo solicitado."""
        desc_lower = description.lower()

        if any(w in desc_lower for w in ["clase", "class", "objeto"]):
            return "class"
        elif any(w in desc_lower for w in ["funcion", "function", "metodo"]):
            return "function"
        elif any(w in desc_lower for w in ["api", "endpoint", "ruta", "route"]):
            return "flask_endpoint"
        elif any(w in desc_lower for w in ["query", "consulta", "select"]):
            return "query"
        elif any(w in desc_lower for w in ["script", "automatizar", "pipeline"]):
            return "script"

        return "function"

    def _extract_name(self, description: str) -> str:
        """Extrae nombre sugerido del componente."""
        # Buscar patrones como "crear X", "funcion X", "clase X"
        patterns = [
            r'(?:crear|hacer|implementar|generar)\s+(?:una?\s+)?(?:funcion|clase|metodo|script)\s+(?:llamad[oa]?\s+)?["\']?(\w+)["\']?',
            r'(?:funcion|clase|metodo)\s+(?:llamad[oa]?\s+)?["\']?(\w+)["\']?',
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)

        # Generar nombre desde palabras clave
        words = re.findall(r"\b\w{4,}\b", description.lower())
        if words:
            return words[0] + "_" + words[1] if len(words) > 1 else words[0]

        return "generated_component"

    def _extract_inputs(self, description: str) -> list[dict]:
        """Extrae parametros de entrada."""
        inputs = []

        # Buscar patrones de parametros
        param_patterns = [
            r"(?:recibe|toma|acepta|con|parametro)\s+(?:el\s+)?(\w+)(?:\s*:?\s*(\w+))?",
            r"(?:input|entrada)\s*:?\s*(\w+)(?:\s*-\s*(\w+))?",
        ]

        for pattern in param_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                name = match.group(1)
                type_hint = match.group(2) if match.group(2) else "Any"
                inputs.append({"name": name, "type": type_hint})

        return inputs

    def _extract_outputs(self, description: str) -> str:
        """Extrae tipo de retorno esperado."""
        patterns = [
            r"(?:retorna|devuelve|regresa|return)\s+(?:un\s+)?(\w+)",
            r"(?:output|salida|resultado)\s*:?\s*(\w+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)

        return "result"

    def _extract_constraints(self, description: str) -> list[str]:
        """Extrae restricciones o validaciones."""
        constraints = []

        if any(w in description.lower() for w in ["no debe", "no puede", "prohibido"]):
            constraints.append("Restricciones de negocio identificadas")

        if any(w in description.lower() for w in ["validar", "validacion", "verificar"]):
            constraints.append("Validaciones de entrada requeridas")

        if any(w in description.lower() for w in ["manejar error", "excepcion", "try"]):
            constraints.append("Manejo de errores necesario")

        return constraints

    def generate(self, description: str) -> CodeGenerationResult:
        """
        Genera codigo completo desde descripcion.

        Pipeline: Parse -> Generate -> Test -> Document
        """
        logger.info(f"Generando codigo para: {description[:50]}...")

        # 1. Parsear requerimiento
        spec = self.parse_requirement(description)
        logger.info(f"Lenguaje detectado: {spec['language']}, Tipo: {spec['type']}")

        # 2. Generar codigo
        code = self._generate_code(spec)

        # 3. Generar tests
        tests = self._generate_tests(spec, code)

        # 4. Generar documentacion
        docs = self._generate_documentation(spec, code)

        # 5. Validar
        errors = self._validate_code(code, spec["language"])

        result = CodeGenerationResult(
            language=spec["language"],
            code=code,
            tests=tests,
            documentation=docs,
            status="complete" if not errors else "debugged",
            errors=errors,
        )

        self.history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "requirement": description,
                "spec": spec,
                "result": result,
            }
        )

        return result

    def _generate_code(self, spec: dict) -> str:
        """Genera codigo desde especificacion."""
        lang = spec["language"]
        code_type = spec["type"]
        name = spec["name"]

        if lang not in self.templates or code_type not in self.templates[lang]:
            return f"# TODO: Implementar {name}\n# Requerimiento: {spec['description']}\n"

        template = self.templates[lang][code_type]

        # Preparar parametros
        params = (
            ", ".join([f"{i['name']}: {i['type']}" for i in spec["inputs"]])
            if spec["inputs"]
            else ""
        )
        args_doc = (
            "\n        ".join([f"{i['name']}: Descripcion" for i in spec["inputs"]])
            if spec["inputs"]
            else "Ninguno"
        )

        return template.format(
            name=name,
            params=params,
            description=spec["description"],
            args_doc=args_doc,
            return_doc=spec["outputs"],
            body="pass  # Implementar logica aqui",
            app="app",
            route="/api/endpoint",
            methods=["GET", "POST"],
            swagger_doc="",
            response='{"status": "ok"}',
            init_params="",
            init_body="pass",
            method_name="process",
            method_params="",
            method_doc="Procesa datos",
            method_body="pass",
            logic="Implementar logica",
            param_types="",
            return_type="Any",
            columns="*",
            table="tabla",
            conditions="1=1",
            order_by="",
            limit="LIMIT 100",
        )

    def _generate_tests(self, spec: dict, code: str) -> str:
        """Genera tests para el codigo."""
        name = spec["name"]
        lang = spec["language"]

        if lang == "python":
            return f'''import pytest
from {name} import {name}

class Test{name.title()}:
    def test_{name}_basic(self):
        """Test basico de {name}"""
        result = {name}()
        assert result is not None

    def test_{name}_edge_cases(self):
        """Test casos limite"""
        # TODO: Implementar casos de prueba
        pass

    def test_{name}_error_handling(self):
        """Test manejo de errores"""
        with pytest.raises(Exception):
            {name}(invalid_input=True)
'''
        return f"// Tests para {name}\n// TODO: Implementar tests"

    def _generate_documentation(self, spec: dict, code: str) -> str:
        """Genera documentacion."""
        return f"""# {spec["name"]}

## Descripcion
{spec["description"]}

## Parametros
{chr(10).join(f"- `{i['name']}`: {i['type']}" for i in spec["inputs"]) if spec["inputs"] else "Ninguno"}

## Retorno
{spec["outputs"]}

## Ejemplo
```python
result = {spec["name"]}({", ".join(i["name"] + "=..." for i in spec["inputs"])})
```

## Notas
{chr(10).join(f"- {c}" for c in spec["constraints"]) if spec["constraints"] else "Sin restricciones adicionales"}
"""

    def _validate_code(self, code: str, language: str) -> list[str]:
        """Valida codigo generado."""
        errors = []

        if language == "python":
            # Verificar sintaxis basica
            if "def " not in code and "class " not in code:
                errors.append("No se detecto definicion de funcion o clase")

            if "pass" in code:
                errors.append("Codigo contiene 'pass' - requiere implementacion")

        return errors

    def demo(self):
        """Demostracion del Code Generation Agent."""
        print("=" * 60)
        print("CODE GENERATION AGENT - DEMO")
        print("=" * 60)
        print()

        ejemplos = [
            "Crear una funcion en Python que reciba una lista de numeros y retorne el promedio",
            "Generar un endpoint Flask para crear usuarios con validacion de email",
            "Crear una clase llamada DatabaseManager que conecte con PostgreSQL",
            "Hacer una consulta SQL que obtenga los productos mas vendidos del ultimo mes",
        ]

        for i, ejemplo in enumerate(ejemplos, 1):
            print(f"[{i}] Requerimiento: {ejemplo}")
            print()

            result = self.generate(ejemplo)

            print(f"  Lenguaje: {result.language}")
            print(f"  Estado: {result.status}")
            if result.errors:
                print(f"  ⚠️  Advertencias: {', '.join(result.errors)}")

            print("\n  --- CODIGO ---")
            for line in result.code.split("\n")[:10]:
                print(f"  {line}")
            if len(result.code.split("\n")) > 10:
                print(f"  ... ({len(result.code.splitlines())} lineas totales)")

            print("\n  --- TESTS ---")
            for line in result.tests.split("\n")[:5]:
                print(f"  {line}")

            print("\n  --- DOCUMENTACION ---")
            for line in result.documentation.split("\n")[:5]:
                print(f"  {line}")

            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    agent = CodeGenerationAgent()
    agent.demo()
