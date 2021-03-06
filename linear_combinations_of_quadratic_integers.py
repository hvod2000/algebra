import math
from functools import reduce

from frozendict import frozendict

from mynumbers import Rational


def normalize_root(root):
    x = root
    if isinstance(x, (set, frozenset)):
        return frozenset(x)
    if isinstance(x, tuple) and x[0] == "+√":
        return frozenset({x})
    factors, r = [], x
    for p in range(2, math.isqrt(x) + 1):
        if x % p == 0:
            x //= p
            factors.append(p)
            if x % p == 0:
                raise ValueError(f"{x} has factor {p}^2")
    if x != 1:
        factors.append(x)
    return frozenset(factors)


def root_to_str(roots):
    result, number = [], 1
    for root in roots:
        match root:
            case int(x):
                number *= x
            case "+√", int(x):
                result.append(f"√({x}+√{x})")
    if number != 1:
        result.append(f"√{number}")
    return "".join(result) if result else ""


def root_to_latex(roots):
    result, number = [], 1
    for root in roots:
        match root:
            case int(x):
                number *= x
            case "+√", int(x):
                result.append("\sqrt{" + str(x) + "+\sqrt{" + str(x) + "}}")
    if number != 1:
        result.append("\sqrt{" + str(number) + "}")
    return "".join(result) if result else ""


class LCoQI:
    def __init__(self, coeffs):
        coeffs = {frozenset(normalize_root(r)): Rational(c) for r, c in coeffs.items()}
        self.coeffs = frozendict(coeffs)

    def inverse(self):
        if len(self.coeffs) == 1 and frozenset({}) in self.coeffs:
            return LCoQI({1: Rational(1) / self.coeffs[frozenset({})]})
        numerator, denominator = LCoQI({1: 1}), self
        for root in reduce(lambda x, y: x | y, denominator.coeffs):
            complement = LCoQI(
                {
                    roots: (-coef if root in roots else coef)
                    for roots, coef in denominator.coeffs.items()
                }
            )
            denominator *= complement
            numerator *= complement
        return numerator / denominator

    def __str__(self):
        terms = []
        for root, coef in self.coeffs.items():
            root = root_to_str(root)
            terms.append(str(coef) + root if coef != 1 else root or "1")
        return " + ".join(terms) if terms else "0"

    def __repr__(self):
        return __class__.__name__ + f"({self.coeffs})"

    def __add__(self, other):
        result = dict(self.coeffs)
        for root, coef in other.coeffs.items():
            result[root] = result.get(root, 0) + coef
        return LCoQI({root: coef for root, coef in result.items() if coef})

    def __sub__(self, other):
        result = dict(self.coeffs)
        for root, coef in other.coeffs.items():
            result[root] = result.get(root, 0) - coef
        return LCoQI({root: coef for root, coef in result.items() if coef})

    def __mul__(self, other):
        if not len(self.coeffs) == len(other.coeffs) == 1:
            result = LCoQI({})
            for root1, coef1 in self.coeffs.items():
                for root2, coef2 in other.coeffs.items():
                    result += LCoQI({root1: coef1}) * LCoQI({root2: coef2})
            return result
        root1, coef1 = next(iter(self.coeffs.items()))
        root2, coef2 = next(iter(other.coeffs.items()))
        additional_factors = []
        coef, root = coef1 * coef2, root1.symmetric_difference(root2)
        for r in root1.intersection(root2):
            match r:
                case int(natural):
                    coef *= natural
                case "+√", int(x):
                    additional_factors.append(LCoQI({1: x, x: 1}))
        result = LCoQI({root: coef})
        for factor in additional_factors:
            result *= factor
        return result

    def __truediv__(self, other):
        return self * other.inverse()

    def __pow__(self, power: int):
        n = abs(power)
        result, factor = LCoQI({1: 1}), self
        while n:
            if n % 2 == 1:
                result *= factor
            n //= 2
            factor *= factor
        return result if power >= 0 else result.inverse()

    def __float__(self):
        result = float(0)
        for roots, coef in self.coeffs.items():
            term = float(coef)
            for x in roots:
                term *= x**0.5 if isinstance(x, int) else (x[1] + x[1]**0.5)**0.5
            result += term
        return result

    def to_tex(self):
        terms = []
        for root, coef in self.coeffs.items():
            root = root_to_latex(root)
            terms.append(coef.to_tex() + root if coef != 1 else root or "1")
        return ("+".join(terms) if terms else "0")

    def _repr_latex_(self):
        return "$$ " + self.to_tex() + " $$"


if __name__ == "__main__":
    x = LCoQI({("+√", 2): 1})
    print(f"x = {x}")
    for n in range(-16, 16 + 1):
        print(f"x^{n} = {x**n}")
