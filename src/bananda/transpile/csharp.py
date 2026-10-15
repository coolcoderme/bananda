"""Convert a BanANDa Python app into C# for Windows."""

from __future__ import annotations

import ast
from typing import Iterable

from bananda.exceptions import BanandaTranspileError
from bananda.targets import Target
from bananda.transpile.converter import TranspileResult
from bananda.transpile.names import OVERRIDE_METHODS, WIDGET_TYPES, to_pascal


def transpile_csharp(
    source: str,
    *,
    filename: str = "<app>",
    package: str = "com.bananda.app",
) -> TranspileResult:
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        raise BanandaTranspileError(exc.msg, filename=filename, lineno=exc.lineno) from exc
    emitter = _CSharpEmitter(filename=filename, package=package)
    emitter.visit(tree)
    return emitter.result()


def csharp_namespace(package: str) -> str:
    parts = [to_pascal(part) for part in package.replace("-", "_").split(".") if part]
    return ".".join(parts) if parts else "Bananda.Generated"


class _CSharpEmitter(ast.NodeVisitor):
    def __init__(self, filename: str, package: str) -> None:
        self.filename = filename
        self.package = package
        self.ns = csharp_namespace(package)
        self.indent = 0
        self.lines: list[str] = []
        self.app_class = ""
        self.title = "BanANDa"
        self.warnings: list[str] = []
        self._class_fields: dict[str, str] = {}
        self._declared_fields: set[str] = set()
        self._local_names: list[set[str]] = [set()]
        self._in_class: str | None = None
        self._current_method: str | None = None

    def result(self) -> TranspileResult:
        app_name = self.app_class or "BanandaApp"
        header = [
            "using System;",
            "using System.Collections.Generic;",
            "using Bananda;",
            "",
            f"namespace {self.ns}",
            "{",
        ]
        body_lines = header + [("    " + line if line else line) for line in self.lines] + ["}", ""]
        body = "\n".join(body_lines)
        program = (
            "using Bananda;\n"
            f"using {self.ns};\n\n"
            "internal static class Program\n"
            "{\n"
            "    private static void Main()\n"
            "    {\n"
            f"        new {app_name}().Start();\n"
            "    }\n"
            "}\n"
        )
        return TranspileResult(
            files={f"{app_name}.cs": body, "Program.cs": program},
            app_class=self.app_class,
            package=self.package,
            title=self.title,
            warnings=self.warnings,
            target=Target.WINDOWS,
        )

    def emit(self, text: str = "") -> None:
        self.lines.append(("    " * self.indent) + text if text else "")

    def error(self, node: ast.AST, message: str) -> None:
        raise BanandaTranspileError(message, filename=self.filename, lineno=getattr(node, "lineno", None))

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

    def visit_Module(self, node: ast.Module) -> None:
        for stmt in node.body:
            if self._is_main_guard(stmt):
                continue
            self.visit(stmt)

    def _is_main_guard(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.If):
            return False
        test = node.test
        if not isinstance(test, ast.Compare) or len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
            return False
        names = {self._const_or_name(test.left), self._const_or_name(test.comparators[0])}
        return names == {"__name__", "__main__"}

    def _const_or_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return ""

    def visit_Import(self, node: ast.Import) -> None:
        return None

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        return None

    def visit_Assign(self, node: ast.Assign) -> None:
        if self._in_class and self._current_method is None:
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                if name == "title" and isinstance(node.value, ast.Constant):
                    self.title = str(node.value.value)
                    self._class_fields[name] = f'public override string Title {{ get; set; }} = "{self._escape(self.title)}";'
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
        self.emit(f"{prefix}{self.expr(node.targets[0])} = {self.expr(node.value)};")

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target = self.expr(node.target)
        value = self.expr(node.value) if node.value is not None else "null"
        self.emit(f"{target} = {value};")

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        op = {ast.Add: "+=", ast.Sub: "-=", ast.Mult: "*=", ast.Div: "/=", ast.Mod: "%="}.get(type(node.op), "+=")
        self.emit(f"{self.expr(node.target)} {op} {self.expr(node.value)};")

    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return
        self.emit(f"{self.expr(node.value)};")

    def visit_Pass(self, node: ast.Pass) -> None:
        self.emit("// pass")

    def visit_Return(self, node: ast.Return) -> None:
        self.emit("return;" if node.value is None else f"return {self.expr(node.value)};")

    def visit_Break(self, node: ast.Break) -> None:
        self.emit("break;")

    def visit_Continue(self, node: ast.Continue) -> None:
        self.emit("continue;")

    def visit_If(self, node: ast.If) -> None:
        self.emit(f"if ({self.expr(node.test)})")
        self.emit("{")
        self.indent += 1
        self._body(node.body)
        self.indent -= 1
        current = node
        while current.orelse and len(current.orelse) == 1 and isinstance(current.orelse[0], ast.If):
            current = current.orelse[0]
            self.emit(f"}} else if ({self.expr(current.test)})")
            self.emit("{")
            self.indent += 1
            self._body(current.body)
            self.indent -= 1
        if current.orelse:
            self.emit("} else")
            self.emit("{")
            self.indent += 1
            self._body(current.orelse)
            self.indent -= 1
        self.emit("}")

    def visit_While(self, node: ast.While) -> None:
        self.emit(f"while ({self.expr(node.test)})")
        self.emit("{")
        self.indent += 1
        self._body(node.body)
        self.indent -= 1
        self.emit("}")

    def visit_For(self, node: ast.For) -> None:
        target = self.expr(node.target)
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
            args = [self.expr(arg) for arg in node.iter.args]
            if len(args) == 1:
                self.emit(f"for (int {target} = 0; {target} < {args[0]}; {target}++)")
            elif len(args) == 2:
                self.emit(f"for (int {target} = {args[0]}; {target} < {args[1]}; {target}++)")
            else:
                self.emit(f"for (int {target} = {args[0]}; {target} < {args[1]}; {target} += {args[2]})")
        else:
            self.emit(f"foreach (var {target} in {self.expr(node.iter)})")
        self.emit("{")
        self.indent += 1
        self._body(node.body)
        self.indent -= 1
        self.emit("}")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self._in_class is None:
            self.emit(f"static void {to_pascal(node.name)}({self._params(node, False)})")
            self.emit("{")
            self._method_body(node)
            return
        self._emit_method(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        bases = [self._base_name(base) for base in node.bases]
        base = bases[0] if bases else ""
        if base == "App":
            self.app_class = node.name
        self._in_class = node.name
        self._class_fields = {}
        self._declared_fields = set()
        methods = [stmt for stmt in node.body if isinstance(stmt, ast.FunctionDef)]
        others = [stmt for stmt in node.body if not isinstance(stmt, ast.FunctionDef)]
        for stmt in others:
            self.visit(stmt)
        self._collect_instance_fields(methods)
        suffix = " : App" if base == "App" else (f" : {base}" if base else "")
        self.emit(f"public class {node.name}{suffix}")
        self.emit("{")
        self.indent += 1
        for field in self._class_fields.values():
            self.emit(field)
        if self._class_fields:
            self.emit()
        for method in methods:
            if method.name == "__init__":
                continue
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

    def _method_body(self, node: ast.FunctionDef) -> None:
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

    def _emit_method(self, node: ast.FunctionDef) -> None:
        params = self._params(node, skip_self=True)
        override = "override " if node.name in OVERRIDE_METHODS else ""
        ret = self._return_type(node)
        self.emit(f"public {override}{ret} {to_pascal(node.name)}({params})")
        self.emit("{")
        self._method_body(node)

    def _params(self, node: ast.FunctionDef, skip_self: bool) -> str:
        args = list(node.args.args)
        if skip_self and args and args[0].arg == "self":
            args = args[1:]
        parts = []
        for arg in args:
            name = to_pascal(arg.arg) if arg.arg == "instance" else (arg.arg if arg.arg != "self" else "self")
            if arg.arg == "instance":
                parts.append("Widget instance")
            elif arg.arg in {"value", "text"}:
                parts.append(f"string {arg.arg}")
            elif arg.arg == "active":
                parts.append("bool active")
            else:
                parts.append(f"object {name}")
        return ", ".join(parts)

    def _return_type(self, node: ast.FunctionDef) -> str:
        if node.name == "build":
            return "Widget"
        returns = [s.value for s in ast.walk(node) if isinstance(s, ast.Return)]
        if not returns or all(r is None for r in returns):
            return "void"
        types = {self._infer_type(r) for r in returns if r is not None}
        if len(types) == 1:
            return next(iter(types))
        return "object"

    def _infer_type(self, node: ast.AST | None) -> str:
        if node is None:
            return "object"
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "bool"
            if isinstance(node.value, int):
                return "int"
            if isinstance(node.value, float):
                return "double"
            if isinstance(node.value, str):
                return "string"
        if isinstance(node, ast.JoinedStr):
            return "string"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in WIDGET_TYPES:
            return node.func.id
        return "object"

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
        inferred = self._infer_type(value)
        pascal = to_pascal(name)
        if inferred in WIDGET_TYPES:
            self._class_fields[name] = f"public {inferred} {pascal};"
        elif inferred == "string":
            default = self.expr(value) if isinstance(value, (ast.Constant, ast.JoinedStr)) else '""'
            self._class_fields[name] = f"public string {pascal} = {default};"
        elif inferred == "int":
            default = self.expr(value) if isinstance(value, (ast.Constant, ast.UnaryOp)) else "0"
            self._class_fields[name] = f"public int {pascal} = {default};"
        elif inferred == "bool":
            self._class_fields[name] = f"public bool {pascal} = false;"
        elif inferred == "double":
            self._class_fields[name] = f"public double {pascal} = 0;"
        else:
            self._class_fields[name] = f"public object {pascal};"
        self._declared_fields.add(name)

    def _base_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""

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
            return to_pascal(node.id)
        return node.id

    def expr_Constant(self, node: ast.Constant) -> str:
        value = node.value
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "null"
        if isinstance(value, str):
            return f'"{self._escape(value)}"'
        if isinstance(value, float):
            return repr(value)
        if isinstance(value, int):
            return str(value)
        self.error(node, f"unsupported constant {value!r}")
        return "null"

    def expr_Attribute(self, node: ast.Attribute) -> str:
        attr = to_pascal(node.attr)
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            return f"this.{attr}"
        return f"{self.expr(node.value)}.{attr}"

    def expr_Call(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            builtin = self._builtin(node)
            if builtin is not None:
                return builtin
            if node.func.id in WIDGET_TYPES:
                return self._widget_ctor(node)
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"strip", "trim"}:
            return f"{self.expr(node.func.value)}.Trim()"
        if isinstance(node.func, ast.Attribute) and node.func.attr == "upper":
            return f"{self.expr(node.func.value)}.ToUpperInvariant()"
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"lower", "lowercase"}:
            return f"{self.expr(node.func.value)}.ToLowerInvariant()"
        if isinstance(node.func, ast.Attribute) and node.func.attr == "bind":
            return self._bind_call(node)
        func = self.expr(node.func)
        args = ", ".join(self.expr(arg) for arg in node.args)
        return f"{func}({args})"

    def _widget_ctor(self, node: ast.Call) -> str:
        cls = node.func.id
        parts: list[str] = []
        positional = {"Label": ["Text"], "Button": ["Text"], "TextInput": ["Text"]}
        for index, arg in enumerate(node.args):
            names = positional.get(cls, [])
            if index < len(names):
                parts.append(f"{names[index]} = {self.expr(arg)}")
        for kw in node.keywords:
            name = to_pascal(kw.arg or "")
            if name in {"OnPress", "OnActive", "OnValue", "OnText"}:
                parts.append(f"{name} = {self._handler(kw.value)}")
            elif name == "SizeHint":
                parts.append(f"{name} = {self._size_hint(kw.value)}")
            else:
                parts.append(f"{name} = {self.expr(kw.value)}")
        inner = ", ".join(parts)
        return f"new {cls} {{ {inner} }}" if inner else f"new {cls}()"

    def _handler(self, node: ast.AST) -> str:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            return to_pascal(node.attr)
        if isinstance(node, ast.Name):
            return to_pascal(node.id)
        return self.expr(node)

    def _bind_call(self, node: ast.Call) -> str:
        owner = self.expr(node.func.value)  # type: ignore[attr-defined]
        parts = []
        for kw in node.keywords:
            event = to_pascal(kw.arg or "")
            parts.append(f"{owner}.{event} = {self._handler(kw.value)}")
        return "; ".join(parts)

    def _size_hint(self, node: ast.AST) -> str:
        if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) == 2:
            return f"new SizeHint({self._hint_axis(node.elts[0])}, {self._hint_axis(node.elts[1])})"
        return self.expr(node)

    def _hint_axis(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and node.value is None:
            return "null"
        text = self.expr(node)
        return f"{text}d" if text.isdigit() else text

    def _builtin(self, node: ast.Call) -> str | None:
        name = node.func.id  # type: ignore[union-attr]
        args = [self.expr(arg) for arg in node.args]
        if name == "print":
            return f'Console.WriteLine(string.Join(" ", new object[] {{ {", ".join(args)} }}))' if args else "Console.WriteLine()"
        if name == "str":
            return f"{args[0]}.ToString()" if args else '""'
        if name == "int":
            return f"Convert.ToInt32({args[0]})" if args else "0"
        if name == "float":
            return f"Convert.ToDouble({args[0]})" if args else "0d"
        if name == "len":
            return f"{args[0]}.Count"
        if name == "abs":
            return f"Math.Abs({args[0]})"
        return None

    def expr_BinOp(self, node: ast.BinOp) -> str:
        op = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "/", ast.Mod: "%"}.get(type(node.op))
        if op is None:
            self.unsupported(node.op)
        return f"({self.expr(node.left)} {op} {self.expr(node.right)})"

    def expr_UnaryOp(self, node: ast.UnaryOp) -> str:
        value = self.expr(node.operand)
        if isinstance(node.op, ast.Not):
            if self._looks_like_string(node.operand):
                return f"string.IsNullOrWhiteSpace({value})"
            return f"!({value})"
        if isinstance(node.op, ast.USub):
            return f"-({value})"
        return value

    def _looks_like_string(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Name) and node.id in {"name", "text", "who", "value"}:
            return True
        if isinstance(node, ast.Attribute) and node.attr in {"name", "text", "hint_text", "Name", "Text"}:
            return True
        return False

    def expr_BoolOp(self, node: ast.BoolOp) -> str:
        op = " && " if isinstance(node.op, ast.And) else " || "
        return "(" + op.join(self.expr(v) for v in node.values) + ")"

    def expr_Compare(self, node: ast.Compare) -> str:
        left = self.expr(node.left)
        parts = []
        current = left
        for op, comparator in zip(node.ops, node.comparators):
            right = self.expr(comparator)
            if isinstance(op, ast.In):
                parts.append(f"{right}.Contains({current})")
            elif isinstance(op, ast.Eq):
                parts.append(f"{current} == {right}")
            elif isinstance(op, ast.NotEq):
                parts.append(f"{current} != {right}")
            elif isinstance(op, ast.Lt):
                parts.append(f"{current} < {right}")
            elif isinstance(op, ast.LtE):
                parts.append(f"{current} <= {right}")
            elif isinstance(op, ast.Gt):
                parts.append(f"{current} > {right}")
            elif isinstance(op, ast.GtE):
                parts.append(f"{current} >= {right}")
            elif isinstance(op, ast.Is):
                parts.append(f"object.ReferenceEquals({current}, {right})")
            elif isinstance(op, ast.IsNot):
                parts.append(f"!object.ReferenceEquals({current}, {right})")
            current = right
        return parts[0] if len(parts) == 1 else "(" + " && ".join(parts) + ")"

    def expr_List(self, node: ast.List) -> str:
        return "new List<object> { " + ", ".join(self.expr(elt) for elt in node.elts) + " }"

    def expr_Tuple(self, node: ast.Tuple) -> str:
        return self.expr_List(node)  # type: ignore[arg-type]

    def expr_Dict(self, node: ast.Dict) -> str:
        pairs = []
        for key, value in zip(node.keys, node.values):
            if key is None:
                self.error(node, "dict unpacking is not supported")
            pairs.append(f"[{self.expr(key)}] = {self.expr(value)}")
        return "new Dictionary<object, object> { " + ", ".join(pairs) + " }"

    def expr_Subscript(self, node: ast.Subscript) -> str:
        return f"{self.expr(node.value)}[{self.expr(node.slice)}]"

    def expr_JoinedStr(self, node: ast.JoinedStr) -> str:
        parts = ['$"']
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value.replace('"', '\\"').replace("{", "{{").replace("}", "}}"))
            elif isinstance(value, ast.FormattedValue):
                parts.append("{" + self.expr(value.value) + "}")
            else:
                parts.append("{" + self.expr(value) + "}")
        parts.append('"')
        return "".join(parts)

    def expr_IfExp(self, node: ast.IfExp) -> str:
        return f"(({self.expr(node.test)}) ? ({self.expr(node.body)}) : ({self.expr(node.orelse)}))"

    def expr_Lambda(self, node: ast.Lambda) -> str:
        params = ", ".join(arg.arg for arg in node.args.args)
        return f"({params}) => {self.expr(node.body)}"

    def _escape(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
