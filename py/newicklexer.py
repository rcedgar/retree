"""Lexer for Newick-formatted tree data"""

import sys
from enum import Enum
from dataclasses import dataclass
from newickstrings import newick_strs

class NewickTokenType(Enum):
    '''Enum for token types occurring in Newick lexical analysis.'''
    INVALID = 0
    EOF = 1
    LPAREN = 2
    RPAREN = 3
    COLON = 4
    COMMA = 5
    SEMICOLON = 6
    STRING = 7
    FLOAT = 8
    COMMENT = 9
    LABEL = 10
    ERROR = 11

@dataclass
class NewickToken():
    """Token object for Newick lexical analysis"""
    toktype: NewickTokenType
    tokstr: str

    def __init__(self):
        self.toktype = NewickTokenType.INVALID
        self.tokstr = ""

class NewickLexer():
    """Lexical analyser for Newick tree data.

    Typical usage:
      str = "(A,(B,C));"
      lexer = NewickLexer(str)
      tokens = lexer.get_tokens()
    """
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.size = len(data)

        # 1-based line, col for diagnostics
        # subscript is zero-based index into array-like data
        self.src_linenrs = []
        self.src_colnrs = []
        src_linenr = 1
        src_colnr = 1
        for i in range(self.size):
            c = data[i]
            if c == '\n':
                src_linenr += 1
                src_colnr = 1
            else:
                src_colnr += 1
            self.src_linenrs.append(src_linenr)
            self.src_colnrs.append(src_colnr)

    def lexer_error(self, msg_str):
        sys.stderr.write("\n")
        if linenr < len(self.src_linenrs):
            linenr = self.src_linenrs[self.pos]
            colnr = self.src_colnrs[self.pos]
        else:
            linenr = -1
            colnr = -1
        
        # TODO: improve error-handling, decide on return code/exception throwing
        sys.stderr.write(f"newick lexer error line {linenr}, col {colnr}: ")
        sys.stderr.write(msg_str)
        sys.stderr.write("\n")
        sys.exit(1)

    def getc(self, end_of_file_ok):
        if self.pos == self.size:
            if not end_of_file_ok:
                # TODO: improve error-handling, decide on return code/exception throwing
                self.lexer_error("unexpected end-of-file")
            return None
        assert self.pos >= 0 and self.pos < self.size
        c = self.data[self.pos]
        self.pos += 1
        return c

    def ungetc(self):
        assert self.pos >= 0
        self.pos -= 1

    def getc_skip_white_space(self, *, end_of_file_ok):
        while True:
            c = self.getc(end_of_file_ok)
            if c is None:
                return c
            if not c.isspace():
                return c

    def get_token(self):
        token = NewickToken()
        c = self.getc_skip_white_space(end_of_file_ok=True)
        token.tokstr = c

        if c is None:
            token.toktype = NewickTokenType.EOF

        elif c == '(':
            token.toktype = NewickTokenType.LPAREN

        elif c == ')':
            token.toktype = NewickTokenType.RPAREN

        elif c == ':':
            token.toktype = NewickTokenType.COLON

        elif c == ';':
            token.toktype = NewickTokenType.SEMICOLON

        elif c == ',':
            token.toktype = NewickTokenType.COMMA

        elif c == '"':
            token.toktype = NewickTokenType.STRING
            while (c := self.getc(end_of_file_ok=False)) != '"':
                token.tokstr += c

        elif c == "'":
            token.toktype = NewickTokenType.STRING
            while (c := self.getc(end_of_file_ok=False)) != "'":
                token.tokstr += c

        elif c in "0123456789.":  # float can't start with e
            token.toktype = NewickTokenType.FLOAT

            # disagree with pylint here
            # pylint: disable=superfluous-parens
            while (c := self.getc(end_of_file_ok=True)) in "0123456789e.":
                token.tokstr += c

            # test if valid float by converting
            try:
                value = float(token.tokstr)
            except ValueError:
                value = None
            if value is None:
                # TODO: improve error-handling, decide on return code/exception throwing
                self.lexer_error(f"Invalid float '{token.tokstr}'")
                token.toktype = NewickTokenType.ERROR
            self.ungetc()  # push back the first non-float character

        elif c == "[":
            token.toktype = NewickTokenType.COMMENT
            while (c := self.getc(end_of_file_ok=False)) != "]":
                token.tokstr += c

        elif c.isalpha():
            token.toktype = NewickTokenType.LABEL
            while True:
                c = self.getc(end_of_file_ok=True)
                if c is None:
                    break
                if not c.isalnum() and not c in "._":
                    self.ungetc()
                    break
                token.tokstr += c

        else:
            self.lexer_error(f"Unexpected character '{c}'")
            token.toktype = NewickTokenType.ERROR

        return token

    def get_tokens(self):
        tokens = []
        while True:
            token = self.get_token()
            if token.toktype == NewickTokenType.EOF:
                return tokens
            if (token.toktype == NewickTokenType.ERROR or
                    token.toktype == NewickTokenType.INVALID):
                assert False
            tokens.append(token)
        return tokens

if __name__ == '__main__':
    for newick_str in newick_strs:
        newick_lexer = NewickLexer(newick_str)
        test_tokens = []
        while True:
            next_token = newick_lexer.get_token()
            test_tokens.append(next_token)
            if (next_token.toktype == NewickTokenType.EOF or
                    next_token.toktype == NewickTokenType.INVALID or
                    next_token.toktype == NewickTokenType.ERROR):
                break
        if (test_tokens and
                test_tokens[-1].toktype == NewickTokenType.EOF and
                test_tokens[-2].toktype == NewickTokenType.SEMICOLON):
            print(f"Lexer ok {len(test_tokens):5} tokens  '{newick_str}'")
        else:
            print(f"Lexer failed newick_str='{newick_str}'")
