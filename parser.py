import lex
import yacc

#########
# LEXER #
#########

tokens = ['LITERAL', 'NOT', 'OR', 'AND', 'IMPLIES', 'LPAREN', 'RPAREN']
t_ignore = ' \t'
t_NOT = r'~'
t_AND = r'&'
t_OR = r'\|'
t_IMPLIES = r'=>'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LITERAL = r'[A-Z][A-Za-z]*\([A-Za-z,]*\)'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print("Illegal character '{}'".format(t.value[0]))
    t.lexer.skip(1)

lexer = lex.lex()

##########
# PARSER #
##########

precedence = (
        ('right', 'IMPLIES'),
        ('left', 'OR'),
        ('left', 'AND'),
        ('right', 'NOT')
        )

def p_not_clause(p):
    'clause : NOT clause'
    p[0] = ('NOT', p[2])

def p_and(p):
    'clause : clause AND clause'
    p[0] = ('AND', p[1], p[3])

def p_or(p):
    'clause : clause OR clause'
    p[0] = ('OR', p[1], p[3])

def p_implies(p):
    'clause : clause IMPLIES clause'
    p[0] = ('OR', ('NOT', p[1]), p[3])

def p_clause_group(p):
    'clause : LPAREN clause RPAREN'
    p[0] = p[2]

def p_clause_literal(p):
    'clause : LITERAL'
    p[0] = p[1]

def p_error(t):
    print("Syntax error at '{}'".format(t.value))

parser = yacc.yacc()

#################
# CNF CONVERTER #
#################

def to_nnf(s):
    # terminate if LITERAL or ['NOT', LITERAL]
    if isinstance(s, str):
        return s
    elif s[0] == 'NOT':
        if isinstance(s[1], str):
            return '!' + s[1]
        elif s[1][0] == 'NOT':
            return to_nnf(s[1][1])
        elif s[1][0] == 'AND':
            return to_nnf(('OR', ('NOT', s[1][1]), ('NOT', s[1][2])))
        elif s[1][0] == 'OR':
            return to_nnf(('AND', ('NOT', s[1][1]), ('NOT', s[1][2])))
    else:
        return (s[0], to_nnf(s[1]), to_nnf(s[2]))

def to_cnf(s):
    if isinstance(s, str):
        return s
    elif isinstance(s[1], str) and isinstance(s[2], str):
        return s
    elif s[0] == 'OR':
        if isinstance(s[1], tuple) and s[1][0] == 'AND':
            return ('AND',
                    to_cnf(('OR', s[1][1], s[2])),
                    to_cnf(('OR', s[1][2], s[2])))
        elif isinstance(s[2], tuple) and s[2][0] == 'AND':
            return ('AND',
                    to_cnf(('OR', s[2][1], s[1])),
                    to_cnf(('OR', s[2][2], s[1])))
        else:
            return ('OR', to_cnf(s[1]), to_cnf(s[2]))
    elif s[0] == 'AND':
        return (s[0], to_cnf(s[1]), to_cnf(s[2]))

def combine_ors(s):
    if isinstance(s, str):
        return frozenset([s])
    elif isinstance(s[1], str) and isinstance(s[2], str):
        return frozenset([s[1], s[2]])
    elif isinstance(s[1], str) and isinstance(s[2], tuple):
        return frozenset(set([s[1]]) | combine_ors(s[2]))
    elif isinstance(s[1], tuple) and isinstance(s[2], str):
        return frozenset(combine_ors(s[1]) | set([s[2]]))
    else:
        return frozenset(combine_ors(s[1]) | combine_ors(s[2]))

def split_ands(s, ns):
    if isinstance(s, str):
        ns.add(frozenset([s]))
        return
    elif s[0] == 'OR':
        ns.add(frozenset(combine_ors(s)))
        return
    else:
        split_ands(s[1], ns)
        split_ands(s[2], ns)
        return

#############
# INTERFACE #
#############

def parse_to_cnf(sentence):
    'Returns set of frozensets.'
    sentence = parser.parse(sentence.strip().replace(' ', ''))
    sentence = to_cnf(to_nnf(sentence))
    split_sentences = set()
    split_ands(sentence, split_sentences)
    parsed_sentences = set()
    for s in split_sentences:
        parsed_sentences.add(tuple(sorted(s)))
    return parsed_sentences
