import importlib
import os
import sys

TOOLS_REGISTRY = {}


def daniela_tool(keywords, description=""):
    def decorator(func):
        TOOLS_REGISTRY[func.__name__] = {
            "func": func,
            "keywords": [k.lower() for k in keywords],
            "description": description,
        }
        return func

    return decorator


def load_tools():
    tools_dir = os.path.expanduser("~/core/tools")
    if not os.path.exists(tools_dir):
        os.makedirs(tools_dir)
    sys.path.append(tools_dir)

    for file in os.listdir(tools_dir):
        if file.endswith(".py") and not file.startswith("__"):
            module_name = file[:-3]
            importlib.import_module(module_name)


def execute_matching_tool(user_prompt):
    load_tools()
    prompt_lower = user_prompt.lower()

    for _tool_name, meta in TOOLS_REGISTRY.items():
        if any(kw in prompt_lower for kw in meta["keywords"]):
            return True, meta["func"](user_prompt)
    return False, None
