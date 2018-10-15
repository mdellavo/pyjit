from jit import compiler

NOOP = """
def noop(): pass 
"""

CONST = """
def const() -> int:
    return 42 
"""

PASSTHRU = """
def passthu(x: int) -> int:
    return x 
"""


FACTORIAL = """
def fact(x: int) -> int:
    if x < 1:
        return 1
    y = foo(x-1)
    return x * y
"""

ALL = [
    NOOP,
    CONST,
    PASSTHRU,
    FACTORIAL,
]


class TestJIT(object):
    def test_simple(self):
        compiler.compile(PASSTHRU)
        assert False
