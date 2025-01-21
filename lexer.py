from enum import Enum, auto
import sys


class State(Enum):
    ''' States Enums '''
    START = auto()
    IDENTIFIER = auto()
    INTEGER = auto()
    FLOAT = auto()
    BINARY_OP = auto()
    REL_OP = auto()
    UNARY_OP = auto()
    ASSIGN_OP = auto()
    PAR_OP = auto()
    ADD_OP = auto()
    MUL_OP = auto()
    PUNCTUATION = auto()
    ERROR = auto()


KEYWORDS = {'else', 'if', 'for', 'var', 'print'}


class TokenType(Enum):
    ''' Token Type Enums (Final States) '''
    NEWLINE = auto()
    IDENTIFIER = auto()
    INT_LITERAL = auto()
    FLOAT_LITERAL = auto()
    BINARY_OP = auto()
    REL_OP = auto()
    UNARY_OP = auto()
    ASSIGN_OP = auto()
    PAR_OP = auto()
    ADD_OP = auto()
    MUL_OP = auto()
    PUNCTUATION = auto()
    KEYWORD = auto()
    ERROR = auto()


class Lexer:
    ''' Lexer main class'''

    def __init__(self, file_path):
        self.file_path = file_path
        self.position = 0
        self.text = ''
        self.current_char = None
        self.var_table = {}
        self.const_table = {}
        self.sym_table = {}
        self.tokens_list = []

    def read_line(self, text):
        ''' WIP '''
        self.position = 0
        self.text = text
        self.current_char = self.text[self.position] if self.text else None
        return self

    def advance(self):
        """Змістити позицію на один символ вперед."""
        self.position += 1
        self.current_char = self.text[self.position] if self.position < len(self.text) else None


    def tokenize(self):
        ''' WIP '''
        tokens = []
        state = State.START

        identifier = ''
        integer = ''

        while self.current_char is not None:
            if state == State.START:
                if self.current_char.isalpha() or self.current_char == '_':
                    identifier = ''
                    state = State.IDENTIFIER
                elif self.current_char.isdigit():
                    integer = ''
                    state = State.INTEGER
                elif self.current_char in ',;:{}"':
                    tokens.append((TokenType.PUNCTUATION, self.current_char, ''))
                    self.advance()
                elif self.current_char in '()':
                    tokens.append((TokenType.PAR_OP, self.current_char, ''))
                    self.advance()

                elif self.current_char in '><=!':
                    next_char = self.text[self.position + 1] if self.position + 1 < len(self.text) else None
                    if self.current_char == '=' and next_char != '=':
                        tokens.append((TokenType.ASSIGN_OP, '=', ''))
                        self.advance()
                    elif self.current_char == '=' and next_char == '=':
                        tokens.append((TokenType.REL_OP, '==', ''))
                        self.advance()
                        self.advance()
                    elif self.current_char == '!' and next_char == '=':
                        tokens.append((TokenType.REL_OP, '!=', ''))
                        self.advance()
                        self.advance()
                    elif self.current_char == '<' and next_char == '=':
                        tokens.append((TokenType.REL_OP, '<=', ''))
                        self.advance()
                        self.advance()
                    elif self.current_char == '>' and next_char == '=':
                        tokens.append((TokenType.REL_OP, '>=', ''))
                        self.advance()
                        self.advance()
                    else:
                        tokens.append((TokenType.REL_OP, self.current_char, ''))
                        self.advance()

                elif self.current_char in '+-':
                    next_char = self.text[self.position + 1] if self.position + 1 < len(self.text) else None
                    if self.current_char == '+' and next_char == '+':
                        tokens.append((TokenType.UNARY_OP, '++', ''))
                        self.advance()
                        self.advance()
                    elif self.current_char == '-' and next_char == '-':
                        tokens.append((TokenType.UNARY_OP, '--', ''))
                        self.advance()
                        self.advance()
                    else:
                        tokens.append((TokenType.ADD_OP, self.current_char, ''))
                        self.advance()
                        print(self.current_char)

                elif self.current_char in '*/^':
                    tokens.append((TokenType.MUL_OP, self.current_char, ''))
                    self.advance()
                elif self.current_char == '\n' or self.current_char.isspace():
                    self.advance()

                else:
                    state = State.ERROR

            elif state == State.IDENTIFIER:
                if self.current_char.isalnum() or self.current_char == '_':
                    # initialized in START block
                    identifier += self.current_char
                    self.advance()
                else:
                    if identifier in KEYWORDS:
                        tokens.append((TokenType.KEYWORD, identifier, ''))
                    else:
                        identifier_id = self.index_var_const(state, identifier)
                        tokens.append((TokenType.IDENTIFIER, identifier, identifier_id))
                    state = State.START

            elif state == State.INTEGER:
                if self.current_char.isdigit():
                    # initialized in START block
                    integer += self.current_char
                    self.advance()
                elif self.current_char == '.':
                    float_num = integer + self.current_char
                    self.advance()
                    state = State.FLOAT
                else:
                    integer_id = self.index_var_const(state, integer)
                    tokens.append((TokenType.INT_LITERAL, integer, integer_id))
                    state = State.START

            elif state == State.FLOAT:
                if self.current_char.isdigit():
                    float_num += self.current_char
                    self.advance()
                elif self.current_char.isalpha():
                    state = State.ERROR
                else:
                    float_id = self.index_var_const(state, float_num)
                    tokens.append((TokenType.FLOAT_LITERAL, float_num, float_id))
                    state = State.START

            elif state == State.ERROR:
                print(f"Error: unexpected character '{self.current_char}'")
                self.advance()
                state = State.START

        return tokens

    def index_var_const(self, state, lexeme):
        ''' WIP '''
        idx = 0
        if state == State.IDENTIFIER:
            idx = self.var_table.get(lexeme)
            if idx is None:
                idx = len(self.var_table) + 1
                self.var_table[lexeme] = idx
        if state in (State.FLOAT, State.INTEGER):
            idx = self.const_table.get(lexeme)
            if idx is None:
                idx = len(self.const_table) + 1
                self.const_table[lexeme] = idx
        return idx

    def read_source_file(self):
        ''' WIP '''
        with open(self.file_path, encoding='utf-8') as f:
            line_num = 0
            for l in f.readlines():
                line_num += 1
                new_tokens = self.read_line(l).tokenize()
                new_tokens = [{"line": line_num, "tkn": tkn} for tkn in new_tokens]
                self.tokens_list = [*self.tokens_list, *new_tokens]

        return self

    def create_sym_table(self):
        ''' WIP '''
        print('\n', '=' * 40, ' LEXER ', '=' * 40)

        for i, t in enumerate(self.tokens_list):
            line, lexem, token, index = t["line"], t["tkn"][1], t["tkn"][0].name, t["tkn"][2]
            print(f"Line {line}: {lexem}  {token} {index}")

            self.sym_table[i + 1] = (line, lexem, token, index)

        print('\nTable of Symbols:\n', self.sym_table, '\n')

        return self.sym_table


if __name__ == '__main__':

    lex = Lexer(sys.argv[1])
    tokens_list = lex.read_source_file()
    sym_table = lex.create_sym_table()

    print(lex.const_table)
    print(lex.var_table)

# Add comments to table, in diagram and in code
# Add ==, >=, <= to code
# Stop execution after errors
# Add stdin
