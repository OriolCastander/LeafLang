from tokenizer import Token, Tokenizer
from sentencer import Sentence, Sentencer
from compiler import Compiler

def main()-> None:
    with open("test.lf", "r") as f:
        fileString = f.read()

    tokenizer = Tokenizer()
    tokens = tokenizer.tokenize(fileString)
    #print(tokens)

    sentencer = Sentencer()
    sentences = sentencer.parseSentences(tokens)
    for s in sentences:
        print(type(s), s)

    compiler = Compiler()
    compiler.compile(sentences)


if __name__ == "__main__":
    main()