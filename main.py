import argparse

from Automaton.DotReader import DotReader

from Reach.ReachManager import ReachManager

parser = argparse.ArgumentParser(description='Process to analyze reachability of '
                                             'specific nodes in a continuous one '
                                             'counter automaton.')
parser.add_argument('input', type=str, help='path for the .dot file that contains the '
                                            'automaton under analysis')
parser.add_argument('--node', type=str, help='node under test, defaults to all nodes if '
                                             'no node is given')
parser.add_argument('--start', type=int, default=0, help='The initial value for the '
                                                         'counter (default 0)')
parser.add_argument('--low', type=int, default=-float('inf'), help='The lower bound for the'
                                                                   'counter (default -inf)')
parser.add_argument('--high', type=int, default=float('inf'), help='The upper bound for the'
                                                                   'counter (default inf)')
parser.add_argument('--debug', type=bool, default=False, help='The debug mode adds additional '
                                                              'output when running the tool '
                                                              '(default False)')
args = vars(parser.parse_args())

reader = DotReader(args['input'])

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

if args['node'] is not None:
    if manager.is_reachable(args['node']):
        print('The node {} was found to be reachable '
              'with the following reaches:'.format(args['node']))
        print(manager.get_reach(args['node']))
    else:
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
            print('The node {} was found to be not '
                  'reachable'.format(node))
        print()
