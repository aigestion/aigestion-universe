import ast


def scan_file_ast(filepath):
    if not filepath.endswith(".py"):
        return True, "OK"
    try:
        with open(filepath, encoding="utf-8") as f:
            code = f.read()
        ast.parse(code)
        return True, "Sintaxis AST válida."
    except SyntaxError as e:
        return False, "Error de sintaxis AST en línea " + str(e.lineno) + ": " + str(e.msg)


if __name__ == "__main__":
    print("Sentinel Pro AST listo.")
