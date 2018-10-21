import ast

from jit import compiler

NOOP = """
def noop() -> None:
    return 
"""
NOOP_IR = """
; ModuleID = ""
target triple = "unknown-unknown-unknown"
target datalayout = ""

define void @"noop"()
{
entry:
  ret void
}
"""

CONST = """
def const() -> int:
    return 42 
"""
CONST_IR = """
; ModuleID = ""
target triple = "unknown-unknown-unknown"
target datalayout = ""

define i32 @"const"()
{
entry:
  ret i32 42
}
"""

PASSTHRU = """
def passthru(x: int) -> int:
    return x 
"""
PASSTHRU_IR = """
; ModuleID = ""
target triple = "unknown-unknown-unknown"
target datalayout = ""

define i32 @"passthru"(i32 %".1")
{
entry:
  ret i32 %".1"
}
"""

FACTORIAL = """
def fact(x: int) -> int:
    if x < 1:
        return 1
    y = foo(x-1)
    return x * y
"""
FACTORIAL_IR = """"""

TESTS = [
    ("noop", NOOP, NOOP_IR),
    ("const", CONST, CONST_IR),
    ("passthru", PASSTHRU, PASSTHRU_IR),
    ("factorial", FACTORIAL, FACTORIAL_IR),
]


class TestJIT(object):

    def assertLines(self, a, b, prefix):

        def clean(s):
            lines = s.split()
            return [line for line in lines if line]

        lines_a, lines_b = (clean(x) for x in (a, b))

        num_a, num_b = (len(lines) for lines in (lines_a, lines_b))
        assert len(lines_a) == len(lines_b), prefix + ": number of lines does not match ({} != {})".format(num_a, num_b)

        for i, pair in enumerate(zip(lines_a, lines_b)):
            line_a, line_b = (line.strip() for line in pair)
            assert line_a == line_b, prefix + ": line {} does not match ('{}' != '{}')".format(i, line_a, line_b)

    def test_simple(self):

        for name, test, expected in TESTS:
            print("----", name)

            print("  AST:")
            node = ast.parse(test)
            compiler.dump_ast(node)

            print()
            print("  IR:")
            ir = str(compiler.compile(node))
            print(ir)

            self.assertLines(ir, expected, name)
