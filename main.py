import copy
import re
import parser

PATTERN_ARG = r'[,\(]([A-Za-z][A-Za-z0-9]*)'
PATTERN_PRED = r'^([!A-Z][A-Za-z]*)\('
PATTERN_VAR = r'[,\(]([A-Z][A-Za-z0-9]*)'
PATTERN_CONST = r'[,\(]([a-z][A-Za-z]*)'

std_index = 1000000

def get_input():
    with open('knowledge_base.txt', 'r') as kb_file:
        unparsed_sentences = kb_file.readlines()
    with open('queries.txt', 'r') as queries_file:
        queries = queries_file.readlines()
    return queries, unparsed_sentences

def print_sentence(sentence):
    print(' v '.join(sentence))

def print_kb(kb):
    for pred in sorted(kb.keys()):
        print(pred)
        for sentence in sorted(kb[pred]):
            print('  ' + ' v '.join(sentence))

def get_pred(literal):
    pred = re.findall(PATTERN_PRED, literal)
    return pred[0] if pred else None

def get_args(literal):
    return re.findall(PATTERN_ARG, literal)

def get_sent_args(s):
    constants = []
    variables = []
    for literal in s:
        constants.extend(re.findall(PATTERN_VAR, literal))
        variables.extend(re.findall(PATTERN_CONST, literal))
    return set(constants), set(variables)

def get_sent_vars(s):
    return get_args(s)[1]

def get_sent_consts(s):
    return get_args(s)[0]

def is_all_consts(literal):
    True if not re.findall('[,\(]([a-z][A-Za-z]*)', literal) else False

def is_variable(x):
    return isinstance(x, str) and x[0].islower()

def is_compound(x):
    if not isinstance(x, str):
        return False
    return re.findall(PATTERN_PRED, x)

def extend(sub, var, val):
    sub2 = sub.copy()
    sub2[var] = val
    return sub2

def unify_var(var, x, sub):
    if var in sub:
        return unify(sub[var], x, sub)
    else:
        return extend(sub, var, x)

def unify(x, y, sub):
    if sub == None:
        return None
    elif x == y:
        return sub
    elif is_variable(x):
        return unify_var(x, y, sub)
    elif is_variable(y):
        return unify_var(y, x, sub)
    elif is_compound(x) and is_compound(y):
        return unify(get_args(x), get_args(y),
                unify(get_pred(x), get_pred(y), sub))
    elif isinstance(x, list) and isinstance(y, list) and len(x) == len(y):
        return unify(x[1:], y[1:], unify(x[0], y[0], sub))
    else:
        return None

def standardize_apart_literal(s):
    s_args = get_args(s)
    for i in range(len(s_args)):
        if is_variable(s_args[i]) and not re.search(r'\d+$', s_args[i]):
            global std_index
            s_args[i] = s_args[i] + str(std_index)
    new_s = get_pred(s) + '(' + ','.join(s_args) + ')'
    return new_s

def standardize_apart_sentence(s):
    new_s = set()
    for literal in s:
        new_s.add(standardize_apart_literal(literal))
    global std_index
    std_index += 1
    return new_s

def index_kb(sentences, kb):
    for sentence in sentences:
        for literal in sentence:
            if get_pred(literal) not in kb:
                kb[get_pred(literal)] = set()
            kb[get_pred(literal)].add(sentence)

def parse_input_sentences(unparsed_sentences):
    to_return = set()
    for sentence in unparsed_sentences:
        parsed = parser.parse_to_cnf(sentence)
        for new_sentence in parsed:
            to_return.add(new_sentence)
    return to_return

def add_negated_query_to_kb(query, new_kb):
    query = '~(' + query + ')'
    parsed = parser.parse_to_cnf(query.strip().replace(' ', ''))
    for sentence in parsed:
        for literal in sentence:
            if get_pred(literal) not in new_kb:
                new_kb[get_pred(literal)] = set()
            new_kb[get_pred(literal)].add(sentence)
    return parsed

##############
# RESOLUTION #
##############

def negate(literal):
    return literal[1:] if literal.startswith('!') else '!' + literal

def substitute(sub, sent):
    new_sent = set()
    for literal in sent:
        new_literal = literal
        for key in sub:
            new_literal = re.sub(key, sub[key], new_literal)
        new_literal = re.sub('\d+', '', new_literal)
        new_sent.add(new_literal)
    return tuple(sorted(new_sent))

def resolve(x, y):
    'Takes two sets and returns the resolvent.'
    # check for the negated ones
    x = set(x)
    y = set(y)
    x = standardize_apart_sentence(set(x))
    y = standardize_apart_sentence(set(y))
    x_preds = set()
    y_preds = set()
    for literal in x:
        x_preds.add(get_pred(literal))
    for literal in y:
        y_preds.add(get_pred(literal))
    unioned = x | y
    for x_literal in x:
        for y_literal in y:
            if negate(get_pred(x_literal)) == get_pred(y_literal):
                sub = unify(x_literal.replace('!', ''),
                        y_literal.replace('!', ''),
                        {})
                if sub is None: # couldn't unify
                    continue
                else: # unified, apply substitution
                    unioned.remove(x_literal)
                    unioned.remove(y_literal)
                    return substitute(sub, unioned)
    return None

def check_terminate(set_of_support, depth):
    empty_clause = tuple([])
    if empty_clause in set_of_support:
        return 'contradiction'
    elif len(set_of_support) < 1:
        return 'empty set of support'
    elif depth > 50:
        return 'depth limit reached'
    elif len(set_of_support) > 100:
        return 'breadth limit reached'
    else:
        return None

def do_resolution(query, original_kb):
    kb = copy.deepcopy(original_kb)
    parsed_query = add_negated_query_to_kb(query, kb)
    set_of_support = {query for query in parsed_query}
    should_terminate = None
    depth = 0
    while should_terminate is None:
        next_set_of_support = set()
        for sentence in set_of_support:
            for literal in sentence:
                pred = negate(get_pred(literal))
                for candidate in kb[pred]:
                    next_set_of_support.add(resolve(sentence, candidate))
        should_terminate = check_terminate(next_set_of_support, depth)
        set_of_support = {s for s in next_set_of_support if s is not None}
        depth += 1
    return should_terminate

def output_results(results):
    with open('output.txt', 'w') as f:
        f.write('\n'.join(results))

def main():
    queries, unparsed_sentences = get_input()
    parsed_sentences = parse_input_sentences(unparsed_sentences)
    original_kb = {}
    index_kb(parsed_sentences, original_kb)
    results = []
    for query in queries:
        termination_reason = do_resolution(query, original_kb)
        if termination_reason == 'contradiction':
            results.append('TRUE')
        else:
            results.append('FALSE')
    output_results(results)

if __name__ == '__main__':
    main()
