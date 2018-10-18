import ast
import pprint

from llvmlite import ir


def ast2tree(node, include_attrs=True):
    def _transform(node):
        if isinstance(node, ast.AST):
            fields = ((a, _transform(b))
                      for a, b in ast.iter_fields(node))
            if include_attrs:
                attrs = ((a, _transform(getattr(node, a)))
                         for a in node._attributes
                         if hasattr(node, a))
                return (node.__class__.__name__, dict(fields), dict(attrs))
            return (node.__class__.__name__, dict(fields))
        elif isinstance(node, list):
            return [_transform(x) for x in node]
        elif isinstance(node, str):
            return repr(node)
        return node
    if not isinstance(node, ast.AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    return _transform(node)


def dump_ast(node):
    pprint.pprint(ast2tree(node))


def compile(src):
    node = ast.parse(src)
    #dump_ast(node)

    emitter = IREmitter()
    compiler = Compiler(emitter)
    compiler.visit(node)

    return emitter.module


Int32 = ir.IntType(32)
Void = ir.VoidType()

TYPES = {
    "int": Int32,
    "void": Void,
}


class IREmitter(object):
    def __init__(self):
        self.module = None
        self.function = None
        self.block = None
        self.builder = None
        self.locals = {}

    def add_module(self):
        self.module = ir.Module()

    def add_block(self, name):
        self.block = self.function.append_basic_block(name)
        self.builder = ir.IRBuilder(self.block)

    def add_function(self, func_type, name):
        self.function = ir.Function(self.module, func_type, name)
        self.add_block("entry")
        self.locals.clear()


class Compiler(ast.NodeVisitor):
    def __init__(self, emitter):
        self.emitter = emitter

    def map_annotation(self, annotation):
        return TYPES[annotation.id]

    def visit_Module(self, node):
        self.emitter.add_module()

        for chunk in node.body:
            self.visit(chunk)

    def visit_FunctionDef(self, node):
        return_type = self.map_annotation(node.returns) if node.returns else Void
        arg_types = tuple(self.map_annotation(arg.annotation) for arg in node.args.args)
        func_type = ir.FunctionType(return_type, arg_types)

        self.emitter.add_function(func_type, node.name)

        arg_names = tuple(arg.arg for arg in node.args.args)

        for arg_name, func_arg, arg_type in zip(arg_names, self.emitter.function.args, arg_types):
            self.emitter.locals[arg_name] = func_arg

        for body_node in node.body:
            self.visit(body_node)

    def visit_Name(self, node):
        return self.emitter.locals[node.id]

    def visit_Return(self, node):
        rv = self.visit(node.value) if node.value else None

        if rv and rv.type is not Void:
            self.emitter.builder.ret(rv)
        else:
            self.emitter.builder.ret_void()
