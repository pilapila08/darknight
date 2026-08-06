"""静态检查：找出各模块引用了但未定义/未导入的名字（漏 import 扫描）。

用法：python tools/check_undefined.py [file_or_dir ...]
不递归目录的话自行传所有目标文件。
"""
import ast
import sys
import builtins

BUILTINS = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__package__", "__builtins__"}


def defined_names(tree):
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for a in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
                    if a.arg:
                        names.add(a.arg)
                if node.args.vararg:
                    names.add(node.args.vararg.arg)
                if node.args.kwarg:
                    names.add(node.args.kwarg.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.Lambda):
            for a in node.args.args + node.args.kwonlyargs + node.args.posonlyargs:
                if a.arg:
                    names.add(a.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.Import):
            for a in node.names:
                names.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                names.add(a.asname or a.name)
        elif isinstance(node, (ast.comprehension,)):
            names.add(node.target.id) if isinstance(node.target, ast.Name) else None
    return names


def used_names(tree):
    return {n.id for n in ast.walk(tree)
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def check(path):
    try:
        with open(path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), path)
    except SyntaxError as e:
        print(f"{path}: SYNTAX ERROR {e}")
        return
    defined = defined_names(tree)
    used = used_names(tree)
    missing = sorted(used - defined - BUILTINS - {"self", "cls", "super"})
    if missing:
        print(f"{path}: MISSING -> {missing}")


if __name__ == "__main__":
    import glob
    targets = sys.argv[1:] or glob.glob("**/*.py", recursive=True)
    for t in targets:
        if t.startswith("venv"):
            continue
        check(t)
    print("SCAN_DONE")
