
from leaf.leafClass import LeafClass, BASE_CLASSES
from leaf.leafFunction import LeafFunction
from leaf.leafVariable import LeafVariable

class ScopeManager:
    """Contains all classes, functions and variables that are defined in this scope"""

    def __init__(self) -> None:
        self.classesInScope: list[LeafClass] = [b for b in BASE_CLASSES.values()]
        self.functionsInScope: list[LeafFunction] = []
        self.variablesInScope: list[LeafVariable] = []

        self.nLayers: int = 1


    def _getAllNames(self) -> list[str]:
        return [c.scopedName[-1] for c in self.classesInScope + self.functionsInScope + self.variablesInScope]

    def isNameInValid(self, name: str) -> bool:
        """Returns if the name conflicts with something in scope"""
        return name in self._getAllNames()

