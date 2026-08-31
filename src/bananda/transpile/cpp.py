"""Convert a BanANDa Python app into C++ for Linux."""

from __future__ import annotations

import ast
from typing import Iterable

from bananda.exceptions import BanandaTranspileError
from bananda.targets import Target
from bananda.transpile.converter import TranspileResult
from bananda.transpile.names import OVERRIDE_METHODS, WIDGET_TYPES, to_camel


def transpile_cpp(
    source: str,
    *,
    filename: str = "<app>",
    package: str = "com.bananda.app",
) -> TranspileResult:
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        raise BanandaTranspileError(exc.msg, filename=filename, lineno=exc.lineno) from exc
    emitter = _CppEmitter(filename=filename, package=package)
    emitter.visit(tree)
    return emitter.result()


class _CppEmitter(ast.NodeVisitor):
    def __init__(self, filename: str, package: str) -> None:
        self.filename = filename
        self.package = package
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
            "#include <format>",
            "#include <iostream>",
            "#include <string>",
            "#include <vector>",
            '#include "bananda/runtime.hpp"',
            "",
        ]
        body = "\n".join(header + self.lines).rstrip() + "\n"
        if self.app_class:
            body += (
                "\nint main() {\n"
                f"    {self.app_class} application;\n"
                "    application.start();\n"
                "    return 0;\n"
                "}\n"
            )
        return TranspileResult(
            files={f"{app_name}.cpp": body},
            app_class=self.app_class,
            package=self.package,
            title=self.title,
            warnings=self.warnings,
            target=Target.LINUX,
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
                return
        prefix = ""
        if (
            self._current_method
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            local_name = node.targets[0].id
            if not self.is_local(local_name) and local_name not in self._declared_fields:
                prefix = "auto "
                self.declare_local(local_name)
        target = self.expr(node.targets[0])
        self.emit(f"{prefix}{target} = {self.expr(node.value)};")

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        target = self.expr(node.target)
        value = self.expr(node.value) if node.value is not None else "0"
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
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
            args = [self.expr(arg) for arg in node.iter.args]
            if len(args) == 1:
                self.emit(f"for (int {target} = 0; {target} < {args[0]}; ++{target}) {{")
            elif len(args) == 2:
                self.emit(f"for (int {target} = {args[0]}; {target} < {args[1]}; ++{target}) {{")
            else:
                self.emit(f"for (int {target} = {args[0]}; {target} < {args[1]}; {target} += {args[2]}) {{")
        else:
            self.emit(f"for (auto {target} : {self.expr(node.iter)}) {{")
        self.indent += 1
        self._body(node.body)
        self.indent -= 1
        self.emit("}")

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self._in_class is None:
            params = self._params(node, skip_self=False)
            self.emit(f"auto {to_camel(node.name)}({params}) {{")
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
        suffix = " : public bananda::App" if base == "App" else (f" : public {base}" if base else "")
        self.emit(f"class {node.name}{suffix} {{")
        self.emit("public:")
        self.indent += 1
        if self.title and base == "App":
            self.emit(f'{node.name}() {{ title = "{self._escape(self.title)}"; }}')
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
        self.emit("};")
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
        override = " override" if node.name in OVERRIDE_METHODS else ""
        ret = self._return_type(node)
        self.emit(f"{ret} {to_camel(node.name)}({params}){override} {{")
        self._method_body(node)

    def _params(self, node: ast.FunctionDef, skip_self: bool) -> str:
        args = list(node.args.args)
        if skip_self and args and args[0].arg == "self":
            args = args[1:]
        parts = []
        for arg in args:
            name = to_camel(arg.arg)
            if arg.arg == "instance":
                parts.append(f"bananda::Widget* {name}")
            elif arg.arg in {"value", "text"}:
                parts.append(f"const std::string& {name}")
            elif arg.arg == "active":
                parts.append(f"bool {name}")
            else:
                parts.append(f"auto {name}")
        return ", ".join(parts)

    def _return_type(self, node: ast.FunctionDef) -> str:
        if node.name == "build":
            return "bananda::Widget*"
        returns = [s.value for s in ast.walk(node) if isinstance(s, ast.Return)]
        if not returns or all(r is None for r in returns):
            return "void"
        types = {self._infer_type(r) for r in returns if r is not None}
        if types == {"std::string"}:
            return "std::string"
        if types == {"int"}:
            return "int"
        if types == {"double"}:
            return "double"
        if types == {"bool"}:
            return "bool"
        return "auto"

    def _infer_type(self, node: ast.AST | None) -> str:
        if node is None:
            return "auto"
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                return "bool"
            if isinstance(node.value, int):
                return "int"
            if isinstance(node.value, float):
                return "double"
            if isinstance(node.value, str):
                return "std::string"
        if isinstance(node, ast.JoinedStr):
            return "std::string"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in WIDGET_TYPES:
            return f"bananda::{node.func.id}*"
        return "auto"

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
        camel = to_camel(name)
        if inferred.endswith("*"):
            self._class_fields[name] = f"{inferred} {camel} = nullptr;"
        elif inferred == "std::string":
            default = self.expr(value) if isinstance(value, (ast.Constant, ast.JoinedStr)) else '""'
            self._class_fields[name] = f"std::string {camel} = {default};"
        elif inferred == "int":
            default = self.expr(value) if isinstance(value, (ast.Constant, ast.UnaryOp)) else "0"
            self._class_fields[name] = f"int {camel} = {default};"
        elif inferred == "double":
            self._class_fields[name] = f"double {camel} = 0.0;"
        elif inferred == "bool":
            self._class_fields[name] = "bool " + camel + " = false;"
        else:
            self._class_fields[name] = f"auto {camel} = {self.expr(value)};"
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
            return "nullptr"
        return to_camel(node.id)

    def expr_Constant(self, node: ast.Constant) -> str:
        value = node.value
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "nullptr"
        if isinstance(value, str):
            return f'"{self._escape(value)}"'
        if isinstance(value, float):
            return repr(value)
        if isinstance(value, int):
            return str(value)
        self.error(node, f"unsupported constant {value!r}")
        return "0"

    def expr_Attribute(self, node: ast.Attribute) -> str:
        attr = to_camel(node.attr)
        if attr == "trim":
            return "trim"
        if isinstance(node.value, ast.Name) and node.value.id == "self":
            return f"this->{attr}"
        return f"{self.expr(node.value)}.{attr}"

    def expr_Call(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            builtin = self._builtin(node)
            if builtin is not None:
                return builtin
            if node.func.id in WIDGET_TYPES:
                return self._widget_ctor(node)
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"strip", "trim"}:
            return f"bananda::trim({self.expr(node.func.value)})"
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"upper", "lowercase"}:
            return f"bananda::uppercase({self.expr(node.func.value)})" if node.func.attr == "upper" else f"bananda::lowercase({self.expr(node.func.value)})"
        if isinstance(node.func, ast.Attribute) and node.func.attr == "bind":
            return self._bind_call(node)
        func = self.expr(node.func)
        args = ", ".join(self.expr(arg) for arg in node.args)
        if func.startswith("this->"):
            return f"{func}({args})"
        return f"{func}({args})"

    def _widget_ctor(self, node: ast.Call) -> str:
        cls = node.func.id
        assignments: list[str] = []
        positional = {"Label": ["text"], "Button": ["text"], "TextInput": ["text"]}
        for index, arg in enumerate(node.args):
            names = positional.get(cls, [])
            if index < len(names):
                assignments.append(f"_w->{names[index]} = {self.expr(arg)};")
        for kw in node.keywords:
            name = to_camel(kw.arg or "")
            if name in {"onPress", "onActive", "onValue"}:
                assignments.append(f"_w->{name} = {self._handler(kw.value, 'press')};")
            elif name == "onText":
                assignments.append(f"_w->{name} = {self._handler(kw.value, 'text')};")
            elif name == "sizeHint":
                assignments.append(f"_w->{name} = {self._size_hint(kw.value)};")
            else:
                assignments.append(f"_w->{name} = {self.expr(kw.value)};")
        body = " ".join(assignments)
        return f"([&]() {{ auto* _w = new bananda::{cls}(); {body} return _w; }})()"

    def _handler(self, node: ast.AST, kind: str) -> str:
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "self":
            method = to_camel(node.attr)
            if kind == "text":
                return f"[this](bananda::Widget* instance, const std::string& value) {{ this->{method}(instance, value); }}"
            return f"[this](bananda::Widget* instance) {{ this->{method}(instance); }}"
        return self.expr(node)

    def _bind_call(self, node: ast.Call) -> str:
        owner = self.expr(node.func.value)  # type: ignore[attr-defined]
        parts = []
        for kw in node.keywords:
            event = to_camel(kw.arg or "")
            kind = "text" if event == "onText" else "press"
            parts.append(f"{owner}->{event} = {self._handler(kw.value, kind)}")
        return ", ".join(parts) if parts else f"{owner}"

    def _size_hint(self, node: ast.AST) -> str:
        if isinstance(node, (ast.Tuple, ast.List)) and len(node.elts) == 2:
            return f"bananda::SizeHint{{{self._hint_axis(node.elts[0])}, {self._hint_axis(node.elts[1])}}}"
        return self.expr(node)

    def _hint_axis(self, node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and node.value is None:
            return "std::nullopt"
        text = self.expr(node)
        return f"{text}.0" if text.isdigit() else text

    def _builtin(self, node: ast.Call) -> str | None:
        name = node.func.id  # type: ignore[union-attr]
        args = [self.expr(arg) for arg in node.args]
        if name == "print":
            message = ' << " " << '.join(args) if args else '""'
            return f"(std::cout << {message} << std::endl)"
        if name == "str":
            return f"std::format(\"{{}}\", {args[0]})" if args else '""'
        if name == "int":
            return f"std::stoi(std::format(\"{{}}\", {args[0]}))" if args else "0"
        if name == "float":
            return f"std::stod(std::format(\"{{}}\", {args[0]}))" if args else "0.0"
        if name == "len":
            return f"static_cast<int>({args[0]}.size())"
        if name == "abs":
            return f"std::abs({args[0]})"
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
                return f"bananda::isBlank({value})"
            return f"!({value})"
        if isinstance(node.op, ast.USub):
            return f"-({value})"
        return value

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
        parts = []
        current = left
        for op, comparator in zip(node.ops, node.comparators):
            right = self.expr(comparator)
            if isinstance(op, ast.In):
                parts.append(f"(std::find({right}.begin(), {right}.end(), {current}) != {right}.end())")
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
                parts.append(f"{current} == {right}")
            elif isinstance(op, ast.IsNot):
                parts.append(f"{current} != {right}")
            current = right
        return parts[0] if len(parts) == 1 else "(" + " && ".join(parts) + ")"

    def expr_List(self, node: ast.List) -> str:
        return "std::vector{" + ", ".join(self.expr(elt) for elt in node.elts) + "}"

    def expr_Tuple(self, node: ast.Tuple) -> str:
        return self.expr_List(node)  # type: ignore[arg-type]

    def expr_Dict(self, node: ast.Dict) -> str:
        pairs = []
        for key, value in zip(node.keys, node.values):
            if key is None:
                self.error(node, "dict unpacking is not supported")
            pairs.append(f"{{{self.expr(key)}, {self.expr(value)}}}")
        return "std::vector<std::pair<std::string, std::string>>{" + ", ".join(pairs) + "}"

    def expr_Subscript(self, node: ast.Subscript) -> str:
        return f"{self.expr(node.value)}[{self.expr(node.slice)}]"

    def expr_JoinedStr(self, node: ast.JoinedStr) -> str:
        fmt: list[str] = []
        args: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                fmt.append(value.value.replace("{", "{{").replace("}", "}}"))
            elif isinstance(value, ast.FormattedValue):
                fmt.append("{}")
                args.append(self.expr(value.value))
            else:
                fmt.append("{}")
                args.append(self.expr(value))
        template = "".join(fmt)
        if not args:
            return f'"{self._escape(template)}"'
        return f'std::format("{self._escape(template)}", {", ".join(args)})'

    def expr_IfExp(self, node: ast.IfExp) -> str:
        return f"(({self.expr(node.test)}) ? ({self.expr(node.body)}) : ({self.expr(node.orelse)}))"

    def expr_Lambda(self, node: ast.Lambda) -> str:
        params = ", ".join(f"auto {arg.arg}" for arg in node.args.args)
        return f"[=]({params}) {{ return {self.expr(node.body)}; }}"

    def _escape(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
