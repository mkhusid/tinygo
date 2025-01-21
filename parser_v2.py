# pylint: disable=C0114, C0115, C0103, C0116, C0201
import sys
from lexer import Lexer


class Parser(Lexer):
    def __init__(self, file_path):
        super().__init__(file_path)
        self.symbol_table = self.read_source_file().create_sym_table()

        # Row number of first token in symbols table
        self.current_token_index = min(self.symbol_table.keys()) if self.symbol_table else None

        # Initialize first token (row number can be 0 or 1)
        self.current_token = self.symbol_table[self.current_token_index]\
            if self.current_token_index is not None else None

        self.expression_tokens = []
        self.declared_vars = {}

        self.token_types = {'INT_LITERAL': 'int', 'FLOAT_LITERAL': 'float'}

        self.labels = set()
        self.nestLevel = 0

    def isDeclared(self):
        """Перевірка, чи змінна була оголошена."""
        numLine, lex, tkn, _ = self.current_token
        if tkn == "IDENTIFIER" and self.declared_vars.get(lex) is None:
            self.failParse(
                f'Undeclared identifier: "{lex}".\n' +
                f'Declared variables are: {list(self.declared_vars.keys())}.')
        elif tkn == "IDENTIFIER" and self.declared_vars.get(lex).get('type') is None:
            self.failParse(f'Variable "{lex}" is declared, but not intialized at line {numLine}.\n')

    def wasDeclared(self, is_iterable=False):
        if self.declared_vars.get(self.current_token[1]) and not is_iterable:
            self.failParse(
                f'Variable {self.current_token[1]} is already ' +
                f'intialized at line: {self.declared_vars[self.current_token[1]]["num_line"]}.')

    def checkExpressionTypes(self, left_op, operator, right_op):
        """Перевіряє типи у виразах."""
        try:
            left_type = self.declared_vars[left_op[1]]["type"]\
                if left_op[2] == 'IDENTIFIER' else self.token_types[left_op[2]]

            right_type = self.declared_vars[right_op[1]]["type"]\
                if right_op[2] == 'IDENTIFIER' else self.token_types[right_op[2]]
            if left_type != right_type:
                self.failParse(f'Wrong types: {left_type} {operator} {right_type}')
        except KeyError as e:
            self.failParse(f'Unitialized variable: {e}.')

    def nextToken(self):
        """Переміщуємо вказівник на наступний токен та повертаємо його."""
        if self.current_token_index is not None:
            next_index = self.current_token_index + 1
            self.current_token = self.symbol_table.get(next_index, None)
            self.current_token_index = next_index if self.current_token else None
            return self.current_token
        else:
            return False

    def parseToken(self, expected_token_type, expected_lexeme):
        """
        Перевіряє, чи поточний токен відповідає очікуваному типу.
        Переміщає парсер на наступний токен. 
        """
        num_line, lex, token, _ = self.current_token
        if token == expected_token_type and expected_lexeme == lex:
            self.printTree(f"Token at line {num_line}: {token} {lex}", log_level='INFO')
            self.nextToken()
            return True
        else:
            self.failParse(f"Очікував {expected_token_type}, але отримав {self.current_token}")
            return False

    def parseAssign(self, var_name):
        """ WIP """
        self.printTree(f"parseAssign: {self.current_token[2]} {self.current_token[1]}")
        self.nextToken()

        try:
            c_tkn = self.current_token
            self.declared_vars[var_name]["type"] = self.declared_vars[c_tkn[1]]["type"]\
                if c_tkn[2] == 'IDENTIFIER' else self.token_types[c_tkn[2]]
        except KeyError as e:
            print(e)

        if not self.parseExpression():
            return False

        return self.parseToken('PUNCTUATION', ';')

    def parseBoolExpr(self):
        self.printTree('parseBoolExpr:')
        self.parseExpression(save_tokens=False)

        numLine, lex, tok, _ = self.current_token

        if tok == 'REL_OP':
            self.nextToken()
            self.printTree(f'Token at line {numLine}: {lex} {tok}', log_level='INFO')
        else:
            self.failParse(f"Mismatch in BoolExpr: {(numLine, lex, tok)}, expected REL_OP.")

        self.parseExpression()

    def parseUnaryExpr(self):
        self.printTree('parseUnaryExpr:')
        start_index = self.current_token_index

        is_ready = False
        if self.current_token[2] == 'IDENTIFIER':
            self.parseFactor()
            numLine, lex, tok, _ = self.current_token

            if tok == 'UNARY_OP':
                self.printTree(f'Token at line {numLine}: {lex} {tok}', log_level='INFO')
                self.nextToken()
                is_ready = True
            else:
                self.failParse(f"Mismatch in BoolExpr: {(numLine, lex, tok)}, expected UNARY_OP.")
        # self.savePostfixTokens(start_index)
        return is_ready

    def parseIdentifier(self):
        ''' Обробка присвоювання '''
        numLine, lex, tok, _ = self.current_token
        self.printTree(f'parseIdentifier: {tok}, {lex}')

        self.nextToken()
        if self.current_token[2] == ('ASSIGN_OP'):
            return self.parseAssign(lex)
        else:
            self.failParse("Очікував '=' після ідентифікатора")
            return False

    def parseVar(self, is_iterable=False):
        ''' Заглушка для інших операторів '''
        if self.current_token[1] != 'var':
            self.failParse('Expected var KEYWORD')

        self.printTree(f'parseVar: {self.current_token[2]}, {self.current_token[1]}')
        self.nextToken()
        if self.current_token[2] == 'IDENTIFIER':
            self.wasDeclared(is_iterable)
            self.declared_vars[self.current_token[1]] = {
                "id": self.current_token[3],
                "num_line": self.current_token[0]
            }
            return self.parseIdentifier()
        else:
            self.failParse('Expected IDENTIFIER')

    def parseStatement(self):
        """Розбір окремого оператора."""
        self.printTree("parseStatement:")

        if self.current_token[2] == 'IDENTIFIER':
            return self.parseIdentifier()

        elif self.current_token[2] == 'KEYWORD' and self.current_token[1] == 'print':
            return self.parsePrint()

        elif self.current_token[2] == 'KEYWORD' and self.current_token[1] == 'if':
            # Заглушка для інших операторів
            return self.parseIf()

        elif self.current_token[2] == 'KEYWORD' and self.current_token[1] == 'for':
            return self.parseFor()

        elif self.current_token[2] == 'KEYWORD' and self.current_token[1] == 'var':
            return self.parseVar()
        else:
            return self.parseExpression()

    def savePostfixTokens(self, start_index, statement_close_token=None, end_index=None):
        end_index_ = self.current_token_index if end_index is None else end_index
        exp_tokens = [
            (self.symbol_table[i][1], self.symbol_table[i][2])
            for i in range(start_index, end_index_)
        ]

        # Add closing token to identify that 'for' or 'if statement is closed
        if statement_close_token:
            exp_tokens.append(statement_close_token)

        # Remove '(' symbol from print operation
        if self.symbol_table[start_index][1] == 'print':
            del exp_tokens[1]

        print('\033[93m\t\t\t\tADD POSTFIX TOKENS:\n\t\t\t', exp_tokens, '\n\033[0m')
        self.expression_tokens.append(exp_tokens)

        return self.expression_tokens

    def parseExpression(self, save_tokens=True):
        """Розбір виразу без лівої рекурсії: Expression = Term {(+|-) Term} """
        start_index = self.current_token_index
        numLine, lex, tok, _ = self.current_token
        l_op = self.current_token

        self.printTree("\tparseExpression:")
        self.parseTerm()

        while self.current_token[2] == 'ADD_OP':
            numLine, lex, tok, _ = self.current_token

            self.printTree(f'Token at line {numLine}: {lex} {tok}', log_level='INFO')
            self.nextToken()
            self.isDeclared()
            self.checkExpressionTypes(l_op, lex, self.current_token)
            self.parseTerm()

        if save_tokens:
            self.savePostfixTokens(start_index - 2)

        return True

    def parseTerm(self):
        """Розбір термів: Term = Factor {(*|/) Factor} """
        self.printTree("\t\tparseTerm:")

        if self.current_token is None:
            self.failParse('Unexpected end of file.')

        l_op = self.current_token
        self.parseFactor()
        while self.current_token[2] == 'MUL_OP':
            numLine, lex, tok, _ = self.current_token
            self.printTree(f'Token at line {numLine}: {lex} {tok}', log_level='INFO')
            self.nextToken()
            self.checkExpressionTypes(l_op, lex, self.current_token)
            self.parseFactor()

        return True

    def parseFactor(self):
        """Розбір факторів. Factor = Id | Const | ( Expression ) """
        self.printTree("\t\t\tparseFactor:")

        numLine, lex, tok, _ = self.current_token
        if self.current_token[2] in ('INT_LITERAL', 'FLOAT_LITERAL', 'IDENTIFIER'):
            self.isDeclared()
            self.nextToken()
            self.printTree(f'Token at line {numLine}: {lex} {tok}', log_level='INFO')
            return self.current_token[2]
        elif self.parseToken('PAR_OP', '('):
            self.parseExpression()
            self.parseToken('PAR_OP', ')')
        else:
            self.parseToken('PUNCTUATION', ';')

        return True

    def parseFor(self):
        '''WIP'''
        self.printTree(f'parseFor: {self.current_token[2]}, {self.current_token[1]}')

        # Save the starting label for the loop
        loop_start_label = f'm{len(self.labels)+1}'

        # POSTFIX STEP 1: add label and colon
        self.labels.add(loop_start_label)
        self.savePostfixTokens(self.current_token_index, (loop_start_label, 'label'))
        self.savePostfixTokens(self.current_token_index, (':', 'colon'))

        # self.savePostfixTokens(self.current_token_index, end_index=self.current_token_index+1)

        self.nextToken()
        self.parseToken('PAR_OP', '(')

        # POSTFIX STEP 2: add assignment (k := a)
        self.parseVar(is_iterable=True)

        # POSTFIX STEP 3: add condition (bool expression)
        self.parseBoolExpr()

        # POSTFIX STEP 4: Save the jump to the end if the condition is false
        loop_end_label = f'm{len(self.labels)+1}'
        self.labels.add(loop_end_label)
        self.savePostfixTokens(self.current_token_index, (loop_end_label, 'label'))

        # POSTFIX STEP 5: add JF (УПХ)
        self.savePostfixTokens(self.current_token_index, ('JF', 'jf'))

        self.parseToken('PUNCTUATION', ';')

        self.parseUnaryExpr()
        self.parseToken('PAR_OP', ')')

        # POSTFIX STEP 6: add block statement (A)
        self.parseBlock()

        # POSTFIX STEP 7: Add a JMP jump back to the loop start to repeat the iteration
        self.savePostfixTokens(self.current_token_index, (loop_start_label, 'label'))
        self.savePostfixTokens(self.current_token_index, ('JMP', 'jump'))

        # POSTFIX STEP 8: Save the ending label for the loop
        self.savePostfixTokens(self.current_token_index, (loop_end_label, 'label'))
        self.savePostfixTokens(self.current_token_index, (':', 'colon'))

        self.parseToken('PUNCTUATION', ';')

    def parseBlock(self):
        self.parseToken('PUNCTUATION', '{')
        self.nestLevel += 1
        while self.current_token[1] != '}':
            self.parseStatement()
        self.parseToken('PUNCTUATION', '}')
        self.nestLevel -= 1
        return True

    def parseIf(self):
        '''WIP'''
        self.printTree(f'parseIf: {self.current_token[2]}, {self.current_token[1]}')
        self.nextToken()

        self.parseToken("PAR_OP", '(')
        self.parseBoolExpr()
        self.labels.add('m1')
        self.savePostfixTokens(self.current_token_index, ('m1', 'label'))
        self.parseToken('PAR_OP', ')')

        # JF - УПХ, умовний перехід
        self.savePostfixTokens(self.current_token_index, ('JF', 'jf'))

        self.parseBlock()

        if_closed = False
        if self.current_token[1] == ';':
            self.nextToken()
            if_closed = True
        elif self.parseToken('KEYWORD', 'else'):

            self.labels.add('m2')
            self.savePostfixTokens(self.current_token_index, ('m2', 'label'))

            # JMP - БП, безумовний перехід
            self.savePostfixTokens(self.current_token_index, ('JMP', 'jump'))
            self.savePostfixTokens(self.current_token_index, ('m1', 'label'))
            self.savePostfixTokens(self.current_token_index, (':', 'colon'))

            self.parseBlock()
            self.savePostfixTokens(self.current_token_index, ('m2', 'label'))
            self.savePostfixTokens(self.current_token_index, (':', 'colon'))

            self.parseToken('PUNCTUATION', ';')

            if_closed = True

        # self.savePostfixTokens(self.current_token_index + 1, ('endif', 'KEYWORD'))
        return if_closed

    def parsePrint(self):
        self.printTree(f'parsePrint: {self.current_token[2]}, {self.current_token[1]}')
        self.nextToken()

        self.parseToken("PAR_OP", '(')
        self.parseExpression()
        self.parseToken("PAR_OP", ')')
        self.parseToken('PUNCTUATION', ';')
        return True

    def printTree(self, message, log_level='STACKTRACE'):
        if log_level == 'INFO':
            message = f'\t\t\t\t\033[92m{message}\033[0m'

        print('\t' * self.nestLevel, message)

    def failParse(self, message):
        """Обробка помилок парсера."""
        if self.current_token:
            raise SyntaxError(f"\033[91mSyntaxError at line {self.current_token[0]}: {message} \033[0m")
        else:
            raise SyntaxError(f"\033[92mSyntaxError: {message}\033[0m")

    def parseStatementList(self):
        """Розбір списку операторів."""
        while self.current_token is not None:
            if not self.parseStatement():
                return True
        return True

    def parseProgram(self):
        """Головна функція для розбору програми."""
        print('=' * 40, ' PARSER ', '=' * 40)
        print("Розбір програми...\n")
        self.parseStatementList()
        print('\nDeclared Vars:', self.declared_vars, '\n')
        return True


if __name__ == '__main__':

    parser = Parser(sys.argv[1])

    try:
        if parser.parseProgram():
            print("Програма успішно розібрана!")
        else:
            print("Не вдалося розібрати програму.")
    except SyntaxError as e:
        print(e)
