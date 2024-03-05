"""
The meat of the action. The compiler revises the sentences and detects mistakes
"""

import sentences
from sentences import Sentence
from scopeManager import ScopeManager

class Compiler:

    def __init__(self) -> None:
        self.reset([])

    def reset(self, sentences: list[Sentence]) -> None:
        self.index = 0
        self.sentences: list[Sentence] = sentences
        self.scopeManager: ScopeManager = ScopeManager()

    
    def compile(self, sentences: list[Sentence]) -> None:
        self.reset(sentences)
        self._firstPass()


    def _firstPass(self) -> None:
        ##CATCH VARIABLES FUNCTIONS AND CLASSES WITH INVALID NAMES
        
        while self.index < len(self.sentences):
            sentence = self.sentences[self.index]

            if type(sentence) in [sentences.ClassDeclaration, sentences.FunctionDeclaration, sentences.VariableDeclaration, sentences.VariableAssignment]:
                if self.scopeManager.isNameInValid(sentence.name):
                    raise Exception(f"Error: cannot name class /function/variable {sentence.name}, name already in use")
                

            self.index += 1
