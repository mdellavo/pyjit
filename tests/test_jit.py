from jit import compiler

NOOP = """
def noop():
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
CONST_IR = """"""

PASSTHRU = """
def passthru(x: int) -> int:
    return x 
"""
PASSTHRU_IR = """"""

FACTORIAL = """
def fact(x: int) -> int:
    if x < 1:
        return 1
    y = foo(x-1)
    return x * y
"""
FACTORIAL_IR = """"""

TESTS = [
    (NOOP, NOOP_IR),
    (CONST, CONST_IR),
    (PASSTHRU, PASSTHRU_IR),
    (FACTORIAL, FACTORIAL_IR),
]


class TestJIT(object):
    def test_simple(self):
        for test, expected in TESTS:
            module = compiler.compile(test)
            print(module)
            assert str(module) == expected
