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


def compile(node):
    compiler = Compiler()
    module = compiler.visit(node)
    return module.module


Int32 = ir.IntType(32)
Void = ir.VoidType()
Bool = ir.IntType(8)

TYPES = {
    "int": Int32,
    "void": Void,
}

# Desugared representation that maps to LLVM IR


class Module(object):
    def __init__(self):
        self.module = ir.Module()
        self.functions = []

    def add_function(self, func_type, name):
        ir_func = ir.Function(self.module, func_type, name)
        func = Function(ir_func)
        self.functions.append(func)
        return func


class Function(object):
    def __init__(self, func):
        self.func = func
        self.blocks = []
        self.scope = {}

    def add_local(self, name, ref):
        self.scope[name] = ref

    def add_block(self, name=""):
        ir_block = self.func.append_basic_block(name)
        block = Block(ir_block)
        self.blocks.append(block)
        return block


class Block(object):
    def __init__(self, block):
        self.block = block
        self.builder = ir.IRBuilder(self.block)


class Compiler(ast.NodeVisitor):
    def __init__(self):
        self.module = None
        self.function = None
        self.block = None

    def map_annotation(self, annotation):
        if isinstance(annotation, ast.NameConstant):
            if annotation.value is None:
                return Void
            elif isinstance(annotation.value, bool):
                return Bool

        if isinstance(annotation, ast.Name):
            return TYPES[annotation.id]

        raise ValueError("unhandled annotation type: " + annotation)

    def visit_Module(self, node):
        self.module = Module()

        for chunk in node.body:
            self.visit(chunk)

        return self.module

    def visit_FunctionDef(self, node):
        return_type = self.map_annotation(node.returns) if node.returns else Void
        arg_types = tuple(self.map_annotation(arg.annotation) for arg in node.args.args)
        func_type = ir.FunctionType(return_type, arg_types)
        func_name = node.name

        self.function = self.module.add_function(func_type, func_name)

        arg_names = tuple(arg.arg for arg in node.args.args)

        for arg_name, func_arg, arg_type in zip(arg_names, self.function.func.args, arg_types):
            self.function.add_local(arg_name, func_arg)

        self.block = self.function.add_block("entry")

        for body_node in node.body:
            self.visit(body_node)

    def visit_Num(self, node):
        return ir.Constant(Int32, node.n)

    def visit_Name(self, node):
        return self.function.scope[node.id]

    def visit_Return(self, node):
        rv = self.visit(node.value) if node.value else None

        if rv and rv.type is not Void:
            self.block.builder.ret(rv)
        else:
            self.block.builder.ret_void()

    def visit_If(self, node):
        pass
