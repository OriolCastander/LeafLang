"""
Words are small structures within sentences sentences
"""
from enum import IntEnum

from tokenizer import TokenKind

class NumberLiteral:
    """A number literal, such as 5 or 3.2"""
    
    def __init__(self, value: str, isFloat: bool) -> None:
        self.value: str = value
        self.isFloat: bool = isFloat


class StringLiteral:
    """A string literal, between brackets, such as "John" """
    def __init__(self, value: str) -> None:
        self.value: str = value

class NameMention:
    """String of the name of a variable or class. Can be chained (car.windshield) (would get the last) but not functions/methods"""
    def __init__(self, value) -> None:
        self.value: str = value

    def __repr__(self) -> str:
        return f"{self.value}"

class Generic:
    """Descriptor of a generic
        Example of a generic <T: A|B % C&D> Any type T that is either class A or B and implements behavior C and D
    """

    def __init__(self, typeTree: list[NameMention], appertains: list[list[NameMention]], behaves: list[list[NameMention]]) -> None:
        self.typeTree: list[NameMention] = typeTree
        self.appertains: list[list[NameMention]] = appertains
        self.behaves: list[list[NameMention]] = behaves

    def __repr__(self) -> str:
        return f"Generic {self.typeTree} appertains {self.appertains} behaves {self.behaves}"

class FunctionCall:
    """Call of a function (or method) includes the name of the function (car.speed() is only speed) and the params and generics"""
    def __init__(self, functionName: str, parameters: list[list["Crawlable"]], generics: list["Generic"]) -> None:
        self.functionName: str = functionName
        self.parameters: list[ParameterDescription] = parameters
        self.generics: list[Generic] = generics

class VariableDescriptor:
    """Description of a variable/parameter. Example :Array[Stack, Value]<int, Array<int, Array<int>(2,3)> 
        In the future typeTree might accept function calls, not currently
    """
    def __init__(self, typeTree: list[NameMention], features: list[str], generics: list["Generic"]) -> None:

        self.typeTree: list[NameMention] = typeTree
        self.features: list[str] = features #[Stack, Value] in the example
        self.generics: list[Generic] = generics

    def __repr__(self) -> str:
        return f"type {self.typeTree} features {self.features} generics {self.generics}"

class ParameterDescription:
    """Name and descriptor of a parameter in a function declaration"""
    def __init__(self, name: str, descriptor: VariableDescriptor) -> None:
        self.name: str = name
        self.descriptor: VariableDescriptor = descriptor

    def __repr__(self) -> str:
        return f"Name {self.name} descriptor: {self.descriptor}"

type Crawlable = NameMention | FunctionCall | NumberLiteral | StringLiteral





class OperatorKind(IntEnum):
    SUM = 0


class Operator:
    def __init__(self, kind: OperatorKind, leftHand: list[Crawlable], rightHand: list[Crawlable]) -> None:
        self.kind: OperatorKind = kind
        self.leftHand: list[Crawlable] = leftHand
        self.rightHand: list[Crawlable] = rightHand


    @staticmethod
    def getOperator(tokenKind: TokenKind) -> None | OperatorKind:
        if tokenKind == TokenKind.PLUS: return OperatorKind.SUM

        return None
    

type Expression = list[Crawlable] | Operator