import sys
import os
import re
import ast


def get_files():
    paths = sys.argv[1]
    if paths.endswith(".py"):
        return [paths]
    else:
        files = []
        for (dirpath, dirnames, filenames) in os.walk(paths):
            for f in filenames:
                if f.endswith(".py"):
                    files.append(os.path.join(dirpath, f))
        files.sort()
        return files


def check_s001(filename, checking_line, counter):
    line_length = 79
    if len(checking_line) > line_length:
        print("{0}: Line {1}: S001 Too long".format(filename, counter))


def check_s002(filename, checking_line, counter):
    indent = 4
    if len(checking_line.strip()) != 0 and\
            (len(checking_line) - len(checking_line.lstrip())) % indent != 0:
        print("{0}: Line {1}: S002 Indentation is not a multiple of four".format(filename, counter))


def check_s003(filename, checking_line, counter):
    normalized_line = checking_line.split('#')[0].strip()
    if normalized_line.endswith(';'):
        print("{0}: Line {1}: S003 Unnecessary semicolon".format(filename, counter))


def check_s004(filename, checking_line, counter):
    spaces = 2
    line_parts = checking_line.split('#')
    if len(line_parts) > 1 and len(line_parts[0].strip()) != 0:
        normalized_line = line_parts[0]
        if len(normalized_line) - len(normalized_line.rstrip()) < spaces:
            print("{0}: Line {1}: S004 At least two spaces required before inline comments".format(filename, counter))


def check_s005(filename, checking_line, counter):
    line_parts = checking_line.split('#')
    if len(line_parts) > 1:
        comments = line_parts[1]
        if comments.upper().find("TODO") != -1:
            print("{0}: Line {1}: S005 TODO found".format(filename, counter))


def check_s006(filename, checking_line, line_counter, empty_count):
    empty_lines_number = 2
    if len(checking_line.strip()) == 0:
        return empty_count + 1
    elif empty_count > empty_lines_number:
        print("{0}: Line {1}: S006 More than two blank lines used before this line".format(filename, line_counter))
        return 0
    else:
        return 0


def check_s007(filename, checking_line, counter):
    class_temp = 'class\s{2,}'
    def_temp = '\s*def\s{2,}'
    if re.match(class_temp, checking_line) or re.match(def_temp, checking_line):
        print("{0}: Line {1}: S007 Too many spaces after".format(filename, counter))


def check_s008(filename, checking_line, counter):
    class_temp = 'class\s+[a-z]'
    if re.match(class_temp, checking_line):
        print("{0}: Line {1}: S008 Class name should use CamelCase".format(filename, counter))


def check_s009(filename, checking_line, counter):
    def_temp = '\s*def\s+[A-Z]\w*_?\w*'
    if re.match(def_temp, checking_line):
        print("{0}: Line {1}: S009 Function name should use snake_case".format(filename, counter))


def check_s010(filename, vals, counter):
    name_temp = '[A-Z]\w*'
    val = vals.get(counter)
    if val:
        args = val.get('args')
        for arg in args:
            if re.match(name_temp, arg):
                print("{0}: Line {1}: S010 Argument name should be snake_case".format(filename, counter))


def check_s011(filename, checking_line, vals, counter, variables):
    new_vars = variables.copy()
    name_temp = '[A-Z]\w*'
    val = vals.get(counter)
    if val:
        vars = val.get('vars')
        if vars:
            if variables == set():
                return set(vars)
            else:
                return variables.update(vars)
    else:
        if variables:
            for v in variables:
                if checking_line.count(v) > 0:
                    if re.match(name_temp, v):
                        new_vars.discard(v)
                        print("{0}: Line {1}: S011 Variable in function should be snake_case".format(filename, counter))
    return new_vars


def check_s012(filename, vals, counter):
    val = vals.get(counter)
    if val:
        is_mutable = val.get('defaults')
        if is_mutable:
            print("{0}: Line {1}: S012 Default argument value is mutable".format(filename, counter))


def get_ast_values(filepath):
    ast_result = {}
    content_file = open(filepath)
    content = content_file.read()
    tree = ast.parse(content)
    nodes = tree.body
    node_number = 0
    for t in nodes:
        if str(t).startswith('<ast.ClassDef'):
            node_number = 0
            for f in t.body:
                if str(f).startswith('<ast.FunctionDef'):
                    ast_result[f.lineno] = get_func_data(f, t.body, node_number)
                node_number += 1
        elif str(t).startswith('<ast.FunctionDef'):
            ast_result[t.lineno] = get_func_data(t, nodes, node_number)
        node_number += 1
    content_file.close()
    return ast_result


def get_func_data(t, nodes, node_number):
    function = nodes[node_number]
    args = [a.arg for a in function.args.args]
    variables = []
    for body_part in t.body:
        if str(body_part).startswith('<ast.Assign'):
            for name in body_part.targets:
                if str(name).startswith('<ast.Name '):
                    variables.append(name.id)
    defaults = [a for a in function.args.defaults]
    mutable = False
    for i in defaults:
        if ast.dump(i).startswith('List'):
            mutable = True
    return {'args': args, 'defaults': mutable, 'vars': variables}


def check_files(files):
    for filepath in files:
        ast_vals = get_ast_values(filepath)
        file = open(filepath, 'r')
        line_counter = 0
        empty_lines = 0
        variables = set()
        for line in file:
            line_counter += 1
            check_s001(filepath, line, line_counter)
            check_s002(filepath, line, line_counter)
            check_s003(filepath, line, line_counter)
            check_s004(filepath, line, line_counter)
            check_s005(filepath, line, line_counter)
            empty_lines = check_s006(filepath, line, line_counter, empty_lines)
            check_s007(filepath, line, line_counter)
            check_s008(filepath, line, line_counter)
            check_s009(filepath, line, line_counter)
            check_s010(filepath, ast_vals, line_counter)
            variables = check_s011(filepath, line, ast_vals, line_counter, variables)
            check_s012(filepath, ast_vals, line_counter)
        file.close()


check_files(get_files())