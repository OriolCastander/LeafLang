"""
Sentences types
"""
import words

class Sentence:
     def __init__(self, line: int) -> None:
          self.line: int = line


class ScopeOpener(Sentence):
    """Opens a scope with a {"""
    def __init__(self, line: int) -> None:
         super().__init__(line)

class ScopeCloser(Sentence):
    """Closes a scope with a }"""
    def __init__(self, line: int) -> None:
         super().__init__(line)


class FunctionDeclaration(Sentence):
    """Function declaration. Name (only one word), generics and params"""
    def __init__(self, line: int, name: str, parameters: list[words.ParameterDescription], generics: list[words.Generic], returnDescriptor: words.VariableDescriptor) -> None:
        
        super().__init__(line)
        self.name: str = name
        self.parameters: list[words.ParameterDescription] = parameters
        self.generics: list[words.Generic] = generics
        self.returnDescriptor: words.VariableDescriptor = returnDescriptor

    def __repr__(self) -> str:
        return f"Declaring {self.name} with generics {self.generics} params {self.parameters} returning {self.returnDescriptor}"


class ClassDeclaration(Sentence):
    """Declaration of a class. Currently missing extends and behaves"""
    def __init__(self, line: int, name: str, features: list[str], generics: list[words.Generic]) -> None:
        
        super().__init__(line)
        self.name: str = name
        self.features: list[str] = features
        self.generics: list[words.Generic] = generics

class ReturnExpression(Sentence):
    def __init__(self, line: int, expression: words.Expression) -> None:
        
        super().__init__(line)
        self.expression: words.Expression = expression


class NakedFunctionCall(Sentence):
    """Function call without a return car.setPosition(3);"""
    def __init__(self, line: int, tree: list[words.Crawlable]) -> None:
        super().__init__(line)
        self.tree: list[words.Crawlable] = tree


class VariableDeclaration(Sentence):
    """Variable declaration without initialization"""
    def __init__(self, line: int, variableName: str, descriptor: words.VariableDescriptor) -> None:
        super().__init__(line)

        self.variableName: str = variableName
        self.descriptor: words.VariableDescriptor = descriptor


class VariableAssignment(Sentence):
    """The typical car.speed = 10 + 3; """
    def __init__(self, line: int, nameTree: list[words.Crawlable], descriptor: words.VariableDescriptor | None, expression: words.Expression) -> None:
        super().__init__(line)
        self.nameTree: list[words.Crawlable] = nameTree
        self.descriptor: words.VariableDescriptor | None = descriptor
        self.expression: words.Expression = expression

