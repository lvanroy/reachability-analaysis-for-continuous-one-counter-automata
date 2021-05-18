import argparse
import subprocess
import os
import shutil

from typing import Dict

from Automaton.DotReader import DotReader

from Reach.ReachManager import ReachManager

from Equations.EquationSolver import EquationSolver


def grammar():
    cwd = os.path.abspath("c-dead-code-analyser")
    grammar_file = find_correct_path(args["input"])

    command = ["python", "./Compiler.py",
               "grammar", grammar_file]
    subprocess.call(command, env=os.environ, cwd=cwd)


def find_correct_path(path):
    if path[0] == ".":
        while path[0] in {".", "/", "\\"}:
            path = path[1:]

    path = os.path.join(path)
    file1 = os.path.join(os.getcwd(), path)
    file1 = os.path.normpath(file1)
    file2 = os.path.join(os.getcwd(), "c-dead-code-analyser", path)
    file2 = os.path.normpath(file2)

    if os.path.exists(file1):
        path = file1
    elif os.path.exists(file2):
        path = file2
    elif not os.path.exists(path):
        print("Error: failed to find or open automaton-input file. "
              "Make sure it is relative to the current "
              "directories or absolute.")
        exit(-1)

    return path


def analyze_code():
    cwd = os.path.abspath("c-dead-code-analyser")
    code_file = find_correct_path(args["input"])

    # make sure the directory is empty
    path = os.path.abspath("c-dead-code-analyser/TreePlots")
    if os.path.exists(path):
        shutil.rmtree(path)

    # generate the automata
    command = ["python", "./Compiler.py",
               "analysis", code_file,
               bool2str(args["trace"]), bool2str(args["image"])]
    subprocess.call(command, env=os.environ, cwd=cwd)

    # copy the generated file to the reachability input dir
    # track the copied files as those are relevant
    # in case we do a full analysis
    generated_files = list()
    for generated_file in os.listdir(path):
        if "reachability_automaton" in generated_file:
            if generated_file.endswith(".dot"):
                original_path = os.path.join(path, generated_file)
                new_path = os.path.join(os.getcwd(), "automaton-input", generated_file)
                shutil.copy(original_path, new_path)
                generated_files.append(new_path)

    return generated_files


def analyze_reachability_with_interval(dot_file):
    reader = DotReader(dot_file)

    automaton = reader.create_automaton()

    if args['debug']:
        print(automaton)

    automaton.set_lower_bound(args['low'])
    automaton.set_upper_bound(args['high'])
    automaton.set_initial_value(args['start'])

    manager = ReachManager(automaton)
    manager.set_debug(args['debug'])

    while not manager.is_finished():
        manager.update_automaton()

    fully_reachable = True

    if args['node'] is not None:
        if manager.is_reachable(args['node']):
            print('The node {} was found to be reachable '
                  'with the following reaches:'.format(args['node']))
            print(manager.get_reach(args['node']))
        else:
            fully_reachable = False
            print('The node {} was found to be not '
                  'reachable'.format(args['node']))
    else:
        for node in automaton.get_nodes():
            if automaton.is_invisible(node):
                continue
            if manager.is_reachable(node):
                print('The node {} was found to be reachable '
                      'with the following reaches:'.format(node))
                reach = manager.get_reach(node)
                for preceding in reach.get_preceding_nodes():
                    print('{}: {}'.format(preceding, reach.get_reachable_set(preceding)))
            else:
                fully_reachable = False
                print('The node {} was found to be not '
                      'reachable'.format(node))
            print()

    return fully_reachable


def analyze_reachability_with_formula(dot_file):
    reader = DotReader(dot_file)

    automaton = reader.create_automaton()

    if args['debug']:
        print(automaton)

    automaton.set_lower_bound(args['low'])
    automaton.set_upper_bound(args['high'])
    automaton.set_initial_value(args['start'])

    solver = EquationSolver(automaton)
    solver.analyse()


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def bool2str(b):
    if b:
        return 'true'
    else:
        return 'false'


parser = argparse.ArgumentParser(description='Process to analyze reachability of '
                                             'lines of c code.')
parser.add_argument('input', type=str, help='.dot file in case reach is the desired op, '
                                            'c file in case c code or full is the desired op, '
                                            'g4 file in case grammar is the desired op')
parser.add_argument('op', default='c-code', help="select the desired operation out of "
                                                 "{'reachability', 'c-code', 'full', 'grammar'}")
parser.add_argument('--node', type=str, help='Node under test, defaults to all nodes if '
                                             'no node is given')
parser.add_argument('--start', type=int, default=0, help='The initial value for the '
                                                         'counter (default 0)')
parser.add_argument('--low', type=int, default=-float('inf'), help='The lower bound for the '
                                                                   'counter (default -inf)')
parser.add_argument('--high', type=int, default=float('inf'), help='The upper bound for the '
                                                                   'counter (default inf)')
parser.add_argument('--debug', type=str2bool, default=False, help='The debug mode adds additional '
                                                                  'output when running the tool '
                                                                  '(default False)')
parser.add_argument('--trace', type=str2bool, default=False, help='Enable debug for the c code to automaton '
                                                                  'implementation')
parser.add_argument('--image', type=str2bool, default=False, help='Output all images representing the '
                                                                  'generated automata (default false)')
parser.add_argument('--method', type=str, default='interval', help='Select the method desired to analyse ' \
                                                                   'reachability. Method must be either ' \
                                                                   'interval or formula (default interval)')
args = vars(parser.parse_args())

if args['op'] not in ['reachability', 'c-code', 'full', 'grammar']:
    print("Error: op must be in ['reachability', 'c-code', "
          "'full', 'grammar'] but is {}".format(args['op']))
    exit(-1)

if 'method' in args and args['method'] not in ['interval', 'formula']:
    print("Error: method must be in ['interval', 'formula'] but is {}"
          .format(args['method']))
    exit(-1)

if args['op'] == "grammar":
    grammar()

if args['op'] == "reachability":
    if args['method'] == 'interval':
        analyze_reachability_with_interval(args["input"])
    if args['method'] == 'formula':
        analyze_reachability_with_formula(args["input"])

if args['op'] == "c-code":
    analyze_code()

if args['op'] == "full":
    files = analyze_code()

    reachabilities: Dict[str, bool] = dict()

    print()
    for file in files:
        print("Starting to analyze: {}".format(file))
        result = analyze_reachability_with_interval(file)
        reachabilities[file] = result

    for file_name in reachabilities:
        tokens = file_name.split("_")
        reachable = reachabilities[file_name]
        function = ""
        code_file = ""
        # retrieve the code file name
        while tokens[0] != "reachability":
            code_file += "{}_".format(tokens.pop(0))
        if "/" in code_file:
            sep = "/"
        else:
            sep = "\\"
        code_file = code_file.split("automaton-input" + sep)[-1]
        code_file = code_file[:-1]

        # pop the tokens 'reachability' and 'automaton'
        tokens.pop(0)
        tokens.pop(0)

        # retrieve the function name
        function = "_".join(tokens).split(".dot")[0]

        print("Reachability was found to be {} for the function {} in the file {}"
              .format(reachable, function, code_file))
