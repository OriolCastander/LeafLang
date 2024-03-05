"""
The sentencer forms sentences from the tokens. In construction, sentences are made of words
"""

from enum import IntEnum
from tokenizer import Token, TokenKind
import words
import sentences
from sentences import Sentence



class SentencerState(IntEnum):
    NEUTRAL = 0
    EXPECTING_DESCRIPTOR_BEFORE_ASSIGNMENT = 1
    EXPECTING_ASSINGMENT = 2


class Sentencer:
    """Transforms the list of tokens to a list of sentences"""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.index: int = 0
        self.sentences: list[Sentence] = []
        self.tokens: list[Token] = []

        self.state: SentencerState = SentencerState.NEUTRAL

        self.nameTree: list[words.NameMention | words.FunctionCall] = []
        self.descriptor: words.VariableDescriptor = None

    def parseSentences(self, tokens: list[Token]) -> list[Sentence]:
        self.reset()
        self.tokens = tokens

        while self.index < len(tokens):
            self._consume()

        return self.sentences
    
    def _consume(self) -> None:
        if self.state == SentencerState.NEUTRAL: self._consumeNeutral()
        elif self.state == SentencerState.EXPECTING_DESCRIPTOR_BEFORE_ASSIGNMENT: self._consumeTypeBeforeExpression()
        elif self.state == SentencerState.EXPECTING_ASSINGMENT: self._consumeRightSideExpression()
        else:
            raise Exception(f"Unkonwn sentencer state {self.state}")
        

    def _consumeNeutral(self) -> None:
        token = self.tokens[self.index]
        
        if token.kind == TokenKind.STRING:
            if token.value == "def":
                self._consumeFunctionDeclaration()

            elif token.value == "class":
                self._consumeClassDeclaration()

            elif token.value == "return":
                self._consumeReturnDeclaration()

            else:
                initialLine = token.line
                crawlable = self._consumeCrawlable()

                token = self.tokens[self.index]
                if token.kind == TokenKind.SEMICOLON:
                    self.index += 1
                    self.sentences.append(sentences.NakedFunctionCall(initialLine, crawlable))

                elif token.kind == TokenKind.COLON:
                    self.index += 1
                    self.nameTree = crawlable
                    self.state = SentencerState.EXPECTING_DESCRIPTOR_BEFORE_ASSIGNMENT
                
                elif token.kind == TokenKind.EQUALS:
                    self.index += 1
                    self.nameTree = crawlable
                    self.state = SentencerState.EXPECTING_ASSINGMENT

                else:
                    raise Exception(f"Unknown token {token} in line {token.line}")
                
        elif token.kind == TokenKind.OPEN_CUR:
            self.index += 1
            self.sentences.append(sentences.ScopeOpener(token.line))

        elif token.kind == TokenKind.CLOSE_CUR:
            self.index += 1
            self.sentences.append(sentences.ScopeCloser(token.line))

        elif token.kind == TokenKind.SEMICOLON:
            self.index += 1

        else:
            raise Exception(f"Invalid token {token} in line {token.line}")

    def _consumeTypeBeforeExpression(self) -> None:
        initialLine = self.tokens[self.index].line

        self.descriptor = self._consumeDescription()

        token = self.tokens[self.index]
        if token.kind == TokenKind.EQUALS:
            self.index += 1
            self.state = SentencerState.EXPECTING_ASSINGMENT

        elif token.kind == TokenKind.SEMICOLON:
            self.index += 1
            self.sentences.append(sentences.VariableDeclaration(initialLine, self.nameTree[0].value, self.descriptor))
            self.state = SentencerState.NEUTRAL
            self.nameTree = []
            self.descriptor = None

    def _consumeRightSideExpression(self) -> None:
        """Consume an expression after an equals in the typical x: int = 3; """
        
        expression = self._consumeExpression()

        token = self.tokens[self.index]
        if token.kind != TokenKind.SEMICOLON:
            raise Exception(f"Expected semicolon at line {token.line} got {token}")
        
        self.index += 1

        self.sentences.append(sentences.VariableAssignment(token.line, self.nameTree, self.descriptor, expression))

        self.state = SentencerState.NEUTRAL
        self.nameTree = []
        self.descriptor = None

    
    def _consumeFunctionDeclaration(self) -> None:
        self.index += 1
        nameToken = self.tokens[self.index]

        initialLine = nameToken.line
        functionParams = None
        functionGenerics: list[words.Generic] = []

        if nameToken.kind != TokenKind.STRING:
            raise Exception(f"Expected function name at line {self.tokens[self.index].line}, found {self.tokens[self.index]}")
        
        self.index += 1
        

        while True:
            token = self.tokens[self.index]
            if token.kind == TokenKind.OPEN_PAR:
                self.index += 1
                functionParams = self._consumeParams()

            elif token.kind == TokenKind.COLON:
                self.index += 1
                break

            elif token.kind == TokenKind.OPEN_ANG:
                if functionParams is not None or len(functionGenerics) > 0:
                    raise Exception(f"Function params or generics of the function already declared, unexpected < in line {token.line}")
                self.index += 1
                functionGenerics = self._consumeGenerics()

            else:
                raise Exception(f"Unexpected token {token} in line {token.line}")

        if functionParams is None:
            raise Exception(f"Expected param declaration between parenthesis at line {initialLine}, got SEMICOLON instead")

        functionReturn = self._consumeDescription()

        token = self.tokens[self.index]
        if token.kind != TokenKind.OPEN_CUR:
            raise Exception(f"Expected {'{'} after function declaration at line {token.line}, got {token}")
        
        self.sentences.append(sentences.FunctionDeclaration(initialLine, nameToken.value, functionParams, functionGenerics, functionReturn))
        

    def _consumeClassDeclaration(self) -> None:
        """Missing extends and behaves"""
        self.index += 1
        nameToken = self.tokens[self.index]

        initialLine = nameToken.line
        classGenerics: list[words.Generic] = []
        classFeatures: list[str] = []

        genericsDeclared = False
        featuresDeclared = False

        if nameToken.kind != TokenKind.STRING:
            raise Exception(f"Expected class name at line {self.tokens[self.index].line}, got {self.tokens[self.index]}")
        
        self.index += 1

        while True:
            token = self.tokens[self.index]
            if token.kind == TokenKind.OPEN_BRA and not featuresDeclared:
                self.index += 1
                classFeatures = self._consumeFeatures()
                featuresDeclared = True
            elif token.kind == TokenKind.OPEN_ANG and not genericsDeclared:
                self.index += 1
                classGenerics = self._consumeGenerics()
                genericsDeclared = True
            elif token.kind == TokenKind.OPEN_CUR:
                break

        self.sentences.append(sentences.ClassDeclaration(initialLine, nameToken.value, classFeatures, classGenerics))

    def _consumeReturnDeclaration(self) -> None:
        """Consumes return + expression + ;"""
        self.index += 1
        line = self.tokens[self.index].line

        expression = self._consumeExpression()

        token = self.tokens[self.index]
        if token.kind != TokenKind.SEMICOLON:
            raise Exception(f"Expected semicolon at line {token.line} got {token}")
        
        self.index += 1

        self.sentences.append(sentences.ReturnExpression(token.line, expression))
        

    def _consumeGenerics(self) -> list[words.Generic]:
        """Consumes everything until the next closing > (included) and returns the generics Should not start on <
            Example of generics <T: A|B % C&D, U>
        """
        
        generics = []
        
        while True:
            #OUTER LOOP, ONLY BREAK WHEN > IS FOUND, VIA RETURNING

            analytinzg = None # None, "appertains", "behaves"
            typeTree = []
            appertains = []
            behaves = []

            while True:
                token = self.tokens[self.index]

                if analytinzg is None:
                    if token.kind == TokenKind.CLOSE_ANG:
                        self.index += 1
                        if len(typeTree) > 0:
                            generics.append(words.Generic(typeTree, appertains, behaves))
                        return generics
                    
                    elif token.kind == TokenKind.STRING:
                        self.index += 1
                        typeTree.append(words.NameMention(token.value))

                    elif token.kind == TokenKind.DOT: self.index += 1

                    elif token.kind == TokenKind.COMMA:
                        if len(typeTree) == 0: raise Exception(f"Expected a type in generics before comma in line {token.line}")
                        self.index += 1
                        generics.append(words.Generic(typeTree, appertains, behaves))
                        continue
                    
                    elif token.kind == TokenKind.COLON:
                        if len(typeTree) == 0: raise Exception(f"Expected a type in generics before colon in line {token.line}")
                        self.index += 1
                        analytinzg = "appertains"
                        appertains.append([])

                    else:
                        raise Exception(f"Unexpected {token} in line {token.line}")
                    
                elif analytinzg == "appertains":
                    if token.kind == TokenKind.CLOSE_ANG:
                        if len(appertains[-1]) == 0: raise Exception(f"Expected type before closing in line {token.line}")
                        self.index += 1
                        return generics
                    
                    elif token.kind == TokenKind.STRING:
                        self.index += 1
                        appertains[-1].append(words.NameMention(token.value))

                    elif token.kind == TokenKind.DOT: self.index += 1

                    elif token.kind == TokenKind.COMMA:
                        if len(appertains[-1]) == 0: raise Exception(f"Expected a type in generics before comma in line {token.line}")
                        self.index += 1
                        generics.append(words.Generic(typeTree, appertains, behaves))
                        continue
                    
                    elif token.kind == TokenKind.PIPE:
                        if len(appertains[-1]) == 0: raise Exception(f"Expected type before | in line {token.line}")
                        self.index += 1
                        appertains.append([])

                    elif token.kind == TokenKind.PERCENT:
                        if not ((len(appertains) == 1 and len(appertains[-1]) == 0) or len(appertains[-1]) > 0):
                            raise Exception(f"Expected a type before % in line {token.line}")
                        self.index += 1
                        analytinzg = "behaves"
                        behaves.append([])

                    else:
                        raise Exception(f"Unexpected {token} in line {token.line}")

                elif analytinzg == "behaves":
                    if token.kind == TokenKind.CLOSE_ANG:
                        if len(behaves[-1]) == 0: raise Exception(f"Expected type before closing in line {token.line}")
                        self.index += 1
                        return generics
                    
                    elif token.kind == TokenKind.STRING:
                        self.index += 1
                        behaves[-1].append(words.NameMention(token.value))

                    elif token.kind == TokenKind.DOT: self.index += 1

                    elif token.kind == TokenKind.COMMA:
                        if len(behaves[-1]) == 0: raise Exception(f"Expected a type in generics before comma in line {token.line}")
                        self.index += 1
                        generics.append(words.Generic(typeTree, appertains, behaves))
                        continue
                    
                    elif token.kind == TokenKind.AND:
                        if len(behaves[-1]) == 0: raise Exception(f"Expected type before & in line {token.line}")
                        self.index += 1
                        behaves.append([])

                    else:
                        raise Exception(f"Unexpected {token} in line {token.line}")
                    
                else:
                    raise Exception(f"Unkwown analyzing state {analytinzg}")
                


    def _consumeFeatures(self) -> list[str]:
        """Consumes all features, consumes until the closing ] (included)"""
        
        features = []
        while True:
            token = self.tokens[self.index]

            if token.kind == TokenKind.CLOSE_BRA:
                self.index += 1
                break

            if token.kind != TokenKind.STRING:
                raise Exception(f"Expected a feature in line {token.line}")
            
            self.index += 1
            commaToken = self.tokens[self.index]
            
            if commaToken.kind == TokenKind.COMMA:
                self.index += 1
                features.append(token.value)
            elif commaToken.kind == TokenKind.CLOSE_BRA:
                self.index += 1
                break
            else:
                raise Exception(f"Expecting a comma after feature {token} in line {token.line}")
            
            
        
        return features



    def _consumeParams(self) -> list[words.ParameterDescription]:
        """Returns the params of a function or method declaration. Consumes until the closing ) (included). Should not start on ("""
        
        params = []

        while True:
            token = self.tokens[self.index]

            if token.kind != TokenKind.STRING:
                raise Exception(f"Expected string in parameter declaration in line {token.line}")
            
            self.index += 1


            nextToken = self.tokens[self.index]

            if nextToken.kind == TokenKind.COLON:
                self.index += 1
                params.append(words.ParameterDescription(token.value, self._consumeDescription()))

            elif nextToken.kind != TokenKind.COMMA and nextToken.kind != TokenKind.CLOSE_PAR:
                raise Exception(f"Unexpecred token {nextToken} in line {nextToken.line}, expecting , ) or :")
            
            
            commaOrClosure = self.tokens[self.index]
            if commaOrClosure.kind == TokenKind.COMMA:
                self.index += 1
            elif commaOrClosure.kind == TokenKind.CLOSE_PAR:
                self.index += 1
                break
            else:
                raise Exception(f"Unexpecred token {nextToken} in line {nextToken.line}, expecting , ) or :")
        
        return params



    def _consumeDescription(self) -> words.VariableDescriptor:
        """Returns the descriptor of a variable/method
        Currently the descriptor type tree only accepts name mentions, might change
        """
        typeTree: list[words.NameMention] = []
        generics: list[words.Generic] = []
        features: list[str] = []

        while True:
            token = self.tokens[self.index]
            
            if token.kind == TokenKind.STRING:
                self.index += 1
                typeTree.append(words.NameMention(token.value))
            
            elif token.kind == TokenKind.DOT:
                self.index += 1

            elif token.kind == TokenKind.OPEN_ANG:
                #STARTS BEING THE GENERICS
                self.index += 1
                generics = self._consumeGenerics()

            elif token.kind == TokenKind.OPEN_BRA:
                #STARTS THE FEATURES
                self.index += 1
                features = self._consumeFeatures()

            else:
                break #WITHOUT CONSUMING

        return words.VariableDescriptor(typeTree, features, generics)
    

    def _consumeExpression(self) -> words.Expression:
        """Consumes an expression (a simple crawlable or operator and returns it)"""
        
        token = self.tokens[self.index]
        if token.kind in [TokenKind.STRING, TokenKind.NUMBER]:
            firstThing = self._consumeCrawlable()

        else:
            raise Exception(f"Expected string or number at line {token.line} got {token}")

        
        nextToken = self.tokens[self.index]
        potentialOperator = words.Operator.getOperator(nextToken.kind)
        
        if potentialOperator is not None:
            self.index += 1
            return words.Operator(potentialOperator, firstThing, self._consumeExpression())
        
        else:
            return firstThing
        

    def _consumeCrawlable(self) -> list[words.Crawlable]:
        """Consumes a crawlable example: car.getSpeed().max.inUnit("m") and stops (without consuming) at other token"""
        
        def getCorrectCrawlable(token: Token)-> words.Crawlable:
            if token.kind == TokenKind.STRING:
                return words.NameMention(token.value)
            elif token.kind == TokenKind.NUMBER:
                return words.NumberLiteral(token.value, "." in token.value)
            
            elif token.kind == TokenKind.QUOTES:
                return self._consumeStringLiteral()
            else:
                raise Exception("literals have to be string or number")
            
        nameTree = []

        shouldHaveDot = False
        alreadyHadDot = True

        while True:
            token = self.tokens[self.index]

            if shouldHaveDot:
                if token.kind == TokenKind.DOT:
                    self.index += 1
                    shouldHaveDot = False
                    alreadyHadDot = True
                
                elif token.kind == TokenKind.STRING or token.kind == TokenKind.QUOTES:
                    raise Exception(f"Unexpected token {token} in line {token.line}")
                
                else: #TODO: ELSE IF VALID BREAKABLE TOKENS
                    break

            elif alreadyHadDot:
                if token.kind in [TokenKind.STRING, TokenKind.NUMBER, TokenKind.QUOTES]:
                    self.index += 1
                    alreadyHadDot = False
                    nameTree.append(getCorrectCrawlable(token))
                
                else:
                    raise Exception(f"Expected name after string in line {token.line} got {token}")
                
            else:
                #not should have dot, not preceded by a dot, must be a dot or parenthesis for variable call or end of crawlable
                if token.kind == TokenKind.DOT:
                    alreadyHadDot = True
                    self.index += 1

                elif token.kind == TokenKind.OPEN_PAR:
                    if len(nameTree) == 0: raise Exception(f"Unexpected parenthesis opening in line {token.line}")
                    if type(nameTree[-1]) != words.NameMention: raise Exception(f"Unexpected parenthesis opening ater {type(nameTree[-1])} in line {token.line}")
                    self.index += 1
                    nameTree[-1] = words.FunctionCall(nameTree[-1].value, self._consumeFunctionCallParams(), [])
                    shouldHaveDot = True

                elif token.kind == TokenKind.OPEN_ANG:
                    self.index += 1
                    generics = self._consumeGenerics()
                    
                    nextToken = self.tokens[self.index]
                    if nextToken.kind != TokenKind.OPEN_PAR:
                        raise Exception(f"Expected ( in line {nextToken.line}")
                    
                    if len(nameTree) == 0: raise Exception(f"Unexpected parenthesis opening in line {token.line}")
                    if type(nameTree[-1]) != words.FunctionCall: raise Exception(f"Unexpected parenthesis opening ater {type(nameTree[-1])} in line {token.line}")
                    self.index += 1
                    nameTree[-1] = words.FunctionCall(nameTree[-1].value, self._consumeFunctionCallParams(), generics)

                elif token.kind in [TokenKind.STRING, TokenKind.NUMBER, TokenKind.QUOTES]:
                    raise Exception(f"Invalid token {token} in line {token.line}")
                
                else:
                    break
        
        return nameTree
                



    def _consumeStringLiteral(self) -> words.StringLiteral:
        alowedInString = [TokenKind.STRING, TokenKind.NUMBER]

        string = ""

        while True:
            token = self.tokens[self.index]
            
            if token.kind in alowedInString:
                self.index += 1
                string += token.value

            elif token.kind == TokenKind.QUOTES:
                self.index += 1
                break

            else:
                raise Exception(f"Token {token} not allowed in string in line {token.line}")

        return words.StringLiteral(string)
    

    def _consumeFunctionCallParams(self) -> list[words.Crawlable]:
        """Consumes all parameters passed to a function call (including the closing ) )"""

        args: list[words.Crawlable] = []

        while True:
            token = self.tokens[self.index]
            if token.kind == TokenKind.CLOSE_PAR:
                break

            args.append(self._consumeExpression())

            token = self.tokens[self.index]

            if token.kind == TokenKind.COMMA:
                self.index += 1

            elif token.kind == TokenKind.CLOSE_PAR:
                break
            else:
                raise Exception(f"Expected comma at function call at line {token.line}")
        
        self.index += 1 #consume closing par
        return args
