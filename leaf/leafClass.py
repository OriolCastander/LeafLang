



class LeafClass:
    """A leaf class"""
    def __init__(self, scopedName: list[str]) -> None:
        self.scopedName: list[str] = scopedName




intClass = LeafClass(["int"])




BASE_CLASSES = {"int": intClass}