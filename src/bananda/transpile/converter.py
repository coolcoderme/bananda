"""Convert a BanANDa Python app into Kotlin sources."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from bananda.exceptions import BanandaTranspileError
from bananda.transpile.names import (
    BANANDA_MODULES,
    OVERRIDE_METHODS,
    WIDGET_TYPES,
    to_camel,
)


@dataclass
class TranspileResult:
    """Kotlin files produced from one Python module."""

    files: dict[str, str]
    app_class: str
    package: str
    title: str = "BanANDa"
    warnings: list[str] = field(default_factory=list)

    @property
    def kotlin(self) -> str:
        if not self.files:
            return ""
        return next(iter(self.files.values()))


def transpile_file(
    path: str | Path,
    *,
    package: str | None = None,
) -> TranspileResult:
    source_path = Path(path)
    return transpile_source(
        source_path.read_text(encoding="utf-8"),
        filename=str(source_path),
        package=package,
    )


def transpile_source(
    source: str,
    *,
    filename: str = "<app>",
    package: str | None = None,
) -> TranspileResult:
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        raise BanandaTranspileError(exc.msg, filename=filename, lineno=exc.lineno) from exc
    emitter = _KotlinEmitter(filename=filename, package=package or "com.bananda.app")
    try:
        emitter.visit(tree)
    except BanandaTranspileError:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise BanandaTranspileError(str(exc), filename=filename) from exc
    return emitter.result()


class _KotlinEmitter(ast.NodeVisitor):
    def __init__(self, filename: str, package: str) -> None:
        self.filename = filename
        self.package = package
        self.indent = 0
        self.lines: list[str] = []
        self.app_class = ""
        self.title = "BanANDa"
        self.warnings: list[str] = []
        self.imports: set[str] = {
            "com.bananda.app.App",
            "com.bananda.uix.Widget",
        }
        self._class_fields: dict[str, str] = {}
        self._declared_fields: set[str] = set()
        self._local_names: list[set[str]] = [set()]
        self._in_class: str | None = None
        self._current_method: str | None = None

    def result(self) -> TranspileResult:
        header = [f"package {self.package}", ""]
        for item in sorted(self.imports):
            header.append(f"import {item}")
        header.append("")
        body = "\n".join(header + self.lines).rstrip() + "\n"
        app_name = self.app_class or "BanandaApp"
        rel = f"{self.package.replace('.', '/')}/{app_name}.kt"
        files = {rel: body}
        if self.app_class:
            files[f"{self.package.replace('.', '/')}/MainActivity.kt"] = self._main_activity()
        return TranspileResult(
            files=files,
            app_class=self.app_class,
            package=self.package,
            title=self.title,
            warnings=self.warnings,
        )

    def _main_activity(self) -> str:
        return (
            f"package {self.package}\n\n"
            "import android.os.Bundle\n"
            "import androidx.appcompat.app.AppCompatActivity\n\n"
            "class MainActivity : AppCompatActivity() {\n"
            "    override fun onCreate(savedInstanceState: Bundle?) {\n"
            "        super.onCreate(savedInstanceState)\n"
            f"        val application = {self.app_class}()\n"
            "        application.attach(this)\n"
            "        setContentView(application.createContentView())\n"
            "    }\n"
            "}\n"
        )

    # --- helpers -----------------------------------------------------

    def emit(self, text: str = "") -> None:
        if text:
            self.lines.append(("    " * self.indent) + text)
        else:
            self.lines.append("")

    def error(self, node: ast.AST, message: str) -> None:
        lineno = getattr(node, "lineno", None)
        raise BanandaTranspileError(message, filename=self.filename, lineno=lineno)

    def unsupported(self, node: ast.AST) -> None:
        self.error(node, f"unsupported Python syntax: {type(node).__name__}")

    def push_scope(self) -> None:
        self._local_names.append(set())

    def pop_scope(self) -> None:
        self._local_names.pop()

    def declare_local(self, name: str) -> None:
        self._local_names[-1].add(name)

    def is_local(self, name: str) -> bool:
        return any(name in scope for scope in self._local_names)

    def expr(self, node: ast.AST) -> str:
        method = getattr(self, f"expr_{type(node).__name__}", None)
        if method is None:
            self.unsupported(node)
        return method(node)

    # --- module / statements ----------------------------------------

    def visit_Module(self, node: ast.Module) -> None:
        for stmt in node.body:
            if self._is_main_guard(stmt):
                continue
            self.visit(stmt)

    def _is_main_guard(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.If):
            return False
        test = node.test
        if not isinstance(test, ast.Compare) or len(test.ops) != 1:
            return False
        if not isinstance(test.ops[0], ast.Eq):
            return False
        left, right = test.left, test.comparators[0]
        names = {self._const_or_name(left), self._const_or_name(right)}
        return names == {"__name__", "__main__"}

    def _const_or_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name.split(".")[0] == "bananda":
                continue
            self.warnings.append(f"ignored import {alias.name}")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        if module in BANANDA_MODULES or module.startswith("bananda"):
            for alias in node.names:
                name = alias.name
                if name in WIDGET_TYPES:
                    self.imports.add(f"com.bananda.uix.{name}")
                elif name == "App":
                    self.imports.add("com.bananda.app.App")
            return
        self.warnings.append(f"ignored import from {module}")

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._in_class and self._current_method is None:
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                if name == "title" and isinstance(node.value, ast.Constant):
                    self.title = str(node.value.value)
                kotlin_type = self._infer_type(node.value)
                value = self.expr(node.value)
                prefix = "override " if name == "title" else ""
                self._class_fields[name] = f"{prefix}var {to_camel(name)}: {kotlin_type} = {value}"
                self._declared_fields.add(name)
                return
        prefix = ""
        if (
            self._current_method
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            local_name = node.targets[0].id
            if not self.is_local(local_name) and local_name not in self._declared_fields:
                prefix = "var "
                self.declare_local(local_name)
        targets = " = ".join(self.expr(t) for t in node.targets)
        self.emit(f"{prefix}{targets} = {self.expr(node.value)}")

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target = self.expr(node.target)
        value = self.expr(node.value) if node.value is not None else self._default_for_ann(node.annotation)
        self.emit(f"{target} = {value}")

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        op = self._aug_op(node.op)
        self.emit(f"{self.expr(node.target)} {op} {self.expr(node.value)}")

    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return
        self.emit(self.expr(node.value))

    def visit_Pass(self, node: ast.Pass) -> None:
        self.emit("// pass")

    def visit_Return(self, node: ast.Return) -> None:
        if node.value is None:
            self.emit("return")
        else:
            self.emit(f"return {self.expr(node.value)}")

    def visit_Break(self, node: ast.Break) -> None:
        self.emit("break")

    def visit_Continue(self, node: ast.Continue) -> None:
        self.emit("continue")

    def visit_If(self, node: ast.If) -> None:
        self.emit(f"if ({self.expr(node.test)}) {{")
        self.indent += 1
        self._body(node.body)
        self.indent -= 1
        current = node
        while current.orelse and len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
            current = current.orelse[0]
            self.emit(f"}} else if ({self.expr(current.test)}) {{")
            self.indent += 1
            self._body(current.body)
            self.indent -= 1
        if current.orelse:
            self.emit("} else {")
            self.indent += 1
            self._body(current.orelse)
            self.indent -= 1
        self.emit("}")

    def visit_While(self, node: ast.While) -> None:
        self.emit(f"while ({self.expr(node.test)}) {{")
        self.indent += 1
        self._body(node.body)
        self.indent -= 1
        self.emit("}")

    def visit_For(self, node: ast.For) -> None:
        target = self.expr(node.target)
        if (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
        ):
            self.emit(f"for ({target} in {self._range_iter(node.iter)}) {{")
        else:
            self.emit(f"for ({target} in {self.expr(node.iter)}) {{")
        self.indent += 1
        self._body(node.body)
        self.indent -= 1
        self.emit("}")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self._in_class is None:
            self._emit_function(node, top_level=True)
            return
        self._emit_method(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = [self._base_name(base) for base in node.bases]
        kotlin_base = bases[0] if bases else "Any"
        if kotlin_base == "App":
            self.app_class = node.name
            self.imports.add("com.bananda.app.App")
        self._in_class = node.name
        self._class_fields = {}
        self._declared_fields = set()
        methods = [stmt for stmt in node.body if isinstance(stmt, ast.FunctionDef)]
        others = [stmt for stmt in node.body if not isinstance(stmt, ast.FunctionDef)]
        for stmt in others:
            self.visit(stmt)
        self._collect_instance_fields(methods)
        suffix = f" : {kotlin_base}()" if kotlin_base != "Any" else ""
        self.emit(f"class {node.name}{suffix} {{")
        self.indent += 1
        for field in self._class_fields.values():
            self.emit(field)
        if self._class_fields:
            self.emit()
        for method in methods:
            self.visit(method)
            self.emit()
        self.indent -= 1
        self.emit("}")
        self._in_class = None

    def generic_visit(self, node: ast.AST) -> None:
        if isinstance(node, ast.stmt):
            self.unsupported(node)
        super().generic_visit(node)

    def _body(self, statements: Iterable[ast.stmt]) -> None:
        stmts = list(statements)
        if not stmts:
            self.emit("// pass")
            return
        for stmt in stmts:
            self.visit(stmt)

    def _base_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        self.error(node, "unsupported base class")
        return "Any"

    def _emit_function(self, node: ast.FunctionDef, top_level: bool) -> None:
        params = self._params(node, skip_self=False)
        ret = self._return_type(node)
        prefix = "fun"
        self.emit(f"{prefix} {to_camel(node.name)}({params}){ret} {{")
        self.indent += 1
        self.push_scope()
        for arg in node.args.args:
            self.declare_local(arg.arg)
        self._current_method = node.name
        self._body(node.body)
        self._current_method = None
        self.pop_scope()
        self.indent -= 1
        self.emit("}")

    def _emit_method(self, node: ast.FunctionDef) -> None:
        if node.name == "__init__":
            self.emit("init {")
            self.indent += 1
            self.push_scope()
            self._current_method = node.name
            self._body([s for s in node.body if not self._is_super_call(s)])
            self._current_method = None
            self.pop_scope()
            self.indent -= 1
            self.emit("}")
            return
        params = self._params(node, skip_self=True)
        ret = self._return_type(node)
        override = "override " if node.name in OVERRIDE_METHODS else ""
        self.emit(f"{override}fun {to_camel(node.name)}({params}){ret} {{")
        self.indent += 1
        self.push_scope()
        for arg in node.args.args:
            if arg.arg != "self":
                self.declare_local(arg.arg)
        self._current_method = node.name
        self._body(node.body)
        self._current_method = None
        self.pop_scope()
        self.indent -= 1
        self.emit("}")

    def _is_super_call(self, node: ast.stmt) -> bool:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            return False
        func = node.value.func
        return isinstance(func, ast.Attribute) and isinstance(func.value, ast.Call) and (
            isinstance(func.value.func, ast.Name) and func.value.func.id == "super"
        )

    def _params(self, node: ast.FunctionDef, skip_self: bool) -> str:
        parts: list[str] = []
        args = list(node.args.args)
        if skip_self and args and args[0].arg == "self":
            args = args[1:]
        for arg in args:
            name = to_camel(arg.arg) if arg.arg != "self" else "self"
            annotation = self._ann_type(arg.annotation) if arg.annotation else self._param_type(arg.arg)
            parts.append(f"{name}: {annotation}")
        return ", ".join(parts)

    def _param_type(self, name: str) -> str:
        if name == "instance":
            return "Widget"
        if name in {"value", "text"}:
            return "String"
        if name in {"active"}:
            return "Boolean"
        return "Any?"

    def _ann_type(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            mapping = {"str": "String", "int": "Int", "float": "Double", "bool": "Boolean"}
            return mapping.get(node.id, node.id)
        if isinstance(node, ast.Constant) and node.value is None:
            return "Unit"
        return "Any?"

    def _return_type(self, node: ast.FunctionDef) -> str:
        if node.name == "build":
            return ": Widget"
        if node.returns is not None:
            mapped = self._ann_type(node.returns)
            if mapped == "Unit":
                return ""
            return f": {mapped}"
        returns = [s.value for s in ast.walk(node) if isinstance(s, ast.Return)]
        if not returns or all(r is None for r in returns):
            return ""
        types = {self._infer_type(r) for r in returns if r is not None}
        if len(types) == 1:
            return f": {next(iter(types))}"
        return ": Any?"

    def _default_for_ann(self, annotation: ast.AST) -> str:
        mapped = self._ann_type(annotation)
        return {
            "String": '""',
            "Int": "0",
            "Double": "0.0",
            "Boolean": "false",
        }.get(mapped, "null")

    def _collect_instance_fields(self, methods: list[ast.FunctionDef]) -> None:
        for method in methods:
            for stmt in ast.walk(method):
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        self._maybe_field(target, stmt.value)
                elif isinstance(stmt, ast.AnnAssign) and stmt.value is not None:
                    self._maybe_field(stmt.target, stmt.value)
                elif isinstance(stmt, ast.AugAssign):
                    self._maybe_field(stmt.target, stmt.value)

    def _maybe_field(self, target: ast.AST, value: ast.AST) -> None:
        if not isinstance(target, ast.Attribute):
            return
        if not isinstance(target.value, ast.Name) or target.value.id != "self":
            return
        name = target.attr
        if name in self._declared_fields:
            return
        kotlin_type = self._infer_type(value)
        camel = to_camel(name)
        if kotlin_type in WIDGET_TYPES:
            self._class_fields[name] = f"lateinit var {camel}: {kotlin_type}"
            self.imports.add(f"com.bananda.uix.{kotlin_type}")
        else:
            default = self._default_value(kotlin_type, value)
            self._class_fields[name] = f"var {camel}: {kotlin_type} = {default}"
        self._declared_fields.add(name)

    def _infer_type(self, node: ast.AST | None) -> str:
        if node is None:
            return "Any?"
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "Boolean"
            if isinstance(node.value, int):
                return "Int"
            if isinstance(node.value, float):
                return "Double"
            if isinstance(node.value, str):
                return "String"
            if node.value is None:
                return "Any?"
        if isinstance(node, ast.List):
            return "MutableList<Any?>"
        if isinstance(node, ast.Dict):
            return "MutableMap<Any?, Any?>"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in WIDGET_TYPES:
                return node.func.id
            if node.func.id == "int":
                return "Int"
            if node.func.id == "float":
                return "Double"
            if node.func.id == "str":
                return "String"
            if node.func.id == "bool":
                return "Boolean"
        if isinstance(node, ast.JoinedStr):
            return "String"
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return self._infer_type(node.operand)
        if isinstance(node, ast.BinOp):
            left = self._infer_type(node.left)
            right = self._infer_type(node.right)
            if "Double" in {left, right}:
                return "Double"
            if left == "Int" and right == "Int":
                return "Int"
            if left == "String" or right == "String":
                return "String"
        return "Any?"

    def _default_value(self, kotlin_type: str, node: ast.AST) -> str:
        if kotlin_type == "Int":
            return self.expr(node) if isinstance(node, (ast.Constant, ast.UnaryOp)) else "0"
        if kotlin_type == "Double":
            return self.expr(node) if isinstance(node, ast.Constant) else "0.0"
        if kotlin_type == "Boolean":
            return self.expr(node) if isinstance(node, ast.Constant) else "false"
        if kotlin_type == "String":
            return self.expr(node) if isinstance(node, (ast.Constant, ast.JoinedStr)) else '""'
        if kotlin_type == "MutableList<Any?>":
            return "mutableListOf()"
        if kotlin_type == "MutableMap<Any?, Any?>":
            return "mutableMapOf()"
        return "null"

    def _range_iter(self, node: ast.Call) -> str:
        args = [self.expr(arg) for arg in node.args]
        if len(args) == 1:
            return f"0 until {args[0]}"
        if len(args) == 2:
            return f"{args[0]} until {args[1]}"
        if len(args) == 3:
            return f"{args[0]} until {args[1]} step {args[2]}"
        self.error(node, "range() expects 1-3 arguments")
        return "0 until 0"

    def _aug_op(self, op: ast.operator) -> str:
        return {
            ast.Add: "+=",
            ast.Sub: "-=",
            ast.Mult: "*=",
            ast.Div: "/=",
            ast.FloorDiv: "/=",
            ast.Mod: "%=",
        }.get(type(op), "+=")

    # --- expressions ------------------------------------------------

    def expr_Name(self, node: ast.Name) -> str:
        if node.id == "self":
            return "this"
        if node.id == "True":
            return "true"
        if node.id == "False":
            return "false"
        if node.id == "None":
            return "null"
        if self._in_class and node.id in self._declared_fields and not self.is_local(node.id):
            return to_camel(node.id)
        return to_camel(node.id)

    def expr_Constant(self, node: ast.Constant) -> str:
        value = node.value
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "null"
        if isinstance(value, str):
            return self._string(value)
        if isinstance(value, float):
            return repr(value)
        if isinstance(value, int):
            return str(value)
        self.error(node, f"unsupported constant {value!r}")
        return "null"

    def expr_Attribute(self, node: ast.Attribute) -> str:
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            return f"this.{to_camel(node.attr)}"
        return f"{self.expr(node.value)}.{to_camel(node.attr)}"

    def expr_Call(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            builtin = self._builtin_call(node)
            if builtin is not None:
                return builtin
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "bind"
        ):
            return self._bind_call(node)
        func = self.expr(node.func)
        args: list[str] = []
        for arg in node.args:
            args.append(self.expr(arg))
        for kw in node.keywords:
            if kw.arg is None:
                self.error(node, "splatted kwargs are not supported")
            name = to_camel(kw.arg)
            if name == "sizeHint":
                args.append(f"{name} = {self._size_hint(kw.value)}")
            elif name in {"onPress", "onText", "onActive", "onValue"}:
                args.append(f"{name} = {self._handler(kw.value)}")
            else:
                args.append(f"{name} = {self.expr(kw.value)}")
        if isinstance(node.func, ast.Name) and node.func.id in WIDGET_TYPES:
            self.imports.add(f"com.bananda.uix.{node.func.id}")
        return f"{func}({', '.join(args)})"

    def _handler(self, node: ast.AST) -> str:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            return f"this::{to_camel(node.attr)}"
        if isinstance(node, ast.Name):
            return to_camel(node.id)
        return self.expr(node)

    def _bind_call(self, node: ast.Call) -> str:
        owner = self.expr(node.func.value)  # type: ignore[attr-defined]
        parts = []
        for kw in node.keywords:
            event = to_camel(kw.arg or "")
            parts.append(f'{owner}.bind("{event}", {self._handler(kw.value)})')
        return "; ".join(parts) if parts else f"{owner}.bind()"

    def _size_hint(self, node: ast.AST) -> str:
        self.imports.add("com.bananda.uix.SizeHint")
        if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) == 2:
            x, y = node.elts
            return f"SizeHint({self._hint_axis(x)}, {self._hint_axis(y)})"
        return self.expr(node)

    def _hint_axis(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and node.value is None:
            return "null"
        text = self.expr(node)
        if text.isdigit():
            return f"{text}.0"
        return text

    def _builtin_call(self, node: ast.Call) -> str | None:
        name = node.func.id  # type: ignore[union-attr]
        args = [self.expr(arg) for arg in node.args]
        if name == "print":
            message = " + \" \" + ".join(args) if args else '""'
            return f'android.util.Log.d("Bananda", {message}.toString())'
        if name == "str":
            return f"{args[0]}.toString()" if args else '""'
        if name == "int":
            return f"{args[0]}.toString().toInt()" if args else "0"
        if name == "float":
            return f"{args[0]}.toString().toDouble()" if args else "0.0"
        if name == "bool":
            return f"({args[0]} == true)" if args else "false"
        if name == "len":
            return f"{args[0]}.size"
        if name == "abs":
            return f"kotlin.math.abs({args[0]})"
        if name in {"min", "max"}:
            return f"kotlin.math.{name}({', '.join(args)})"
        if name == "range":
            return self._range_iter(node)
        return None

    def expr_BinOp(self, node: ast.BinOp) -> str:
        if isinstance(node.op, ast.FloorDiv):
            return f"({self.expr(node.left)} / {self.expr(node.right)})"
        op = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
            ast.Pow: " toDouble() pow ",
        }.get(type(node.op))
        if op is None:
            self.unsupported(node.op)
        if isinstance(node.op, ast.Pow):
            return f"Math.pow({self.expr(node.left)}.toDouble(), {self.expr(node.right)}.toDouble())"
        return f"({self.expr(node.left)} {op} {self.expr(node.right)})"

    def expr_UnaryOp(self, node: ast.UnaryOp) -> str:
        value = self.expr(node.operand)
        if isinstance(node.op, ast.Not):
            if self._infer_type(node.operand) == "String" or self._looks_like_string(node.operand):
                return f"{value}.isNullOrBlank()"
            return f"!({value})"
        if isinstance(node.op, ast.USub):
            return f"-({value})"
        if isinstance(node.op, ast.UAdd):
            return value
        return f"!({value})"

    def _looks_like_string(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name) and node.id in {"name", "text", "who", "value"}:
            return True
        if isinstance(node, ast.Attribute) and node.attr in {"name", "text", "hint_text"}:
            return True
        return False

    def expr_BoolOp(self, node: ast.BoolOp) -> str:
        op = " && " if isinstance(node.op, ast.And) else " || "
        return "(" + op.join(self.expr(v) for v in node.values) + ")"

    def expr_Compare(self, node: ast.Compare) -> str:
        left = self.expr(node.left)
        parts: list[str] = []
        current = left
        for op, comparator in zip(node.ops, node.comparators):
            right = self.expr(comparator)
            if isinstance(op, ast.In):
                parts.append(f"{right}.contains({current})")
            elif isinstance(op, ast.NotIn):
                parts.append(f"!{right}.contains({current})")
            elif isinstance(op, ast.Is):
                parts.append(f"{current} === {right}" if right != "null" else f"{current} == null")
            elif isinstance(op, ast.IsNot):
                parts.append(f"{current} !== {right}" if right != "null" else f"{current} != null")
            else:
                symbol = {
                    ast.Eq: "==",
                    ast.NotEq: "!=",
                    ast.Lt: "<",
                    ast.LtE: "<=",
                    ast.Gt: ">",
                    ast.GtE: ">=",
                }[type(op)]
                parts.append(f"{current} {symbol} {right}")
            current = right
        return parts[0] if len(parts) == 1 else "(" + " && ".join(parts) + ")"

    def expr_List(self, node: ast.List) -> str:
        inner = ", ".join(self.expr(elt) for elt in node.elts)
        return f"mutableListOf({inner})"

    def expr_Tuple(self, node: ast.Tuple) -> str:
        inner = ", ".join(self.expr(elt) for elt in node.elts)
        if len(node.elts) == 2:
            return f"Pair({inner})"
        if len(node.elts) == 3:
            return f"Triple({inner})"
        return f"arrayOf({inner})"

    def expr_Dict(self, node: ast.Dict) -> str:
        pairs = []
        for key, value in zip(node.keys, node.values):
            if key is None:
                self.error(node, "dict unpacking is not supported")
            pairs.append(f"{self.expr(key)} to {self.expr(value)}")
        return f"mutableMapOf({', '.join(pairs)})"

    def expr_Subscript(self, node: ast.Subscript) -> str:
        return f"{self.expr(node.value)}[{self.expr(node.slice)}]"

    def expr_Slice(self, node: ast.Slice) -> str:  # pragma: no cover
        lower = self.expr(node.lower) if node.lower else "0"
        upper = self.expr(node.upper) if node.upper else "null"
        return f"{lower}..{upper}"

    def expr_JoinedStr(self, node: ast.JoinedStr) -> str:
        parts: list[str] = ['"']
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(self._escape_template(value.value))
            elif isinstance(value, ast.FormattedValue):
                inner = self.expr(value.value)
                parts.append(f"${{{inner}}}")
            else:
                parts.append(f"${{{self.expr(value)}}}")
        parts.append('"')
        return "".join(parts)

    def expr_IfExp(self, node: ast.IfExp) -> str:
        return f"(if ({self.expr(node.test)}) {self.expr(node.body)} else {self.expr(node.orelse)})"

    def expr_ListComp(self, node: ast.ListComp) -> str:
        if len(node.generators) != 1:
            self.error(node, "only single-iterator list comprehensions are supported")
        gen = node.generators[0]
        target = self.expr(gen.target)
        source = self.expr(gen.iter)
        mapped = self.expr(node.elt)
        chain = f"{source}.map {{ {target} -> {mapped} }}"
        for iff in gen.ifs:
            chain = f"{source}.filter {{ {target} -> {self.expr(iff)} }}.map {{ {target} -> {mapped} }}"
            break
        return f"{chain}.toMutableList()"

    def expr_Lambda(self, node: ast.Lambda) -> str:
        params = ", ".join(arg.arg for arg in node.args.args)
        return f"{{ {params} -> {self.expr(node.body)} }}"

    def expr_Starred(self, node: ast.Starred) -> str:
        return f"*{self.expr(node.value)}"

    def _string(self, value: str) -> str:
        escaped = (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )
        return f'"{escaped}"'

    def _escape_template(self, value: str) -> str:
        return (
            value.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("$", "\\$")
            .replace("\n", "\\n")
        )
