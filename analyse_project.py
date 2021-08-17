import subprocess
import os
import shutil

from os import listdir
from os.path import isfile, join

from pathlib import Path

from Automaton.DotReader import DotReader

from Reach.ReachManager import ReachManager

from Equations.EquationSolver import EquationSolver

root_directory = Path("xrdp-devel")

# make sure the directory is empty
path = os.path.abspath("c-dead-code-analyser/TreePlots")

if os.path.exists(path):
    shutil.rmtree(path)

with open('output.txt', 'w+') as output_stream:
    for file in root_directory.rglob('*.c'):
        print("\n\nanalysing: {}".format(file))

        # define the current working directory
        cwd = os.path.abspath("c-dead-code-analyser")

        # generate the automata
        command = ["python", "./Compiler.py",
                   "analysis", file.absolute(),
                   "true", "false"]

        with open('err.txt', 'w+') as error_stream:
            subprocess.call(command, env=os.environ, cwd=cwd,
                            stderr=error_stream, stdout=output_stream)

            error_stream.seek(0)

            errors = error_stream.read()

        errors = errors.split("\n")
        errors = [error for error in errors if "dot: " not in error]
        errors = "\n".join(errors)
        if errors != "":
            print("Something went wrong, carrying on")

# only_files = [join(path, f) for f in listdir(path) if isfile(join(path, f))]
# for file in only_files:
#     if "reachability_automaton" in file:
#         print(file)
#         reader = DotReader(file)
#
#         automaton = reader.create_automaton()
#
#         automaton.set_lower_bound(-float('inf'))
#         automaton.set_upper_bound(float('inf'))
#         automaton.set_initial_value(0)
#
#         manager = ReachManager(automaton)
#         manager.set_debug(False)
#
#         while not manager.is_finished():
#             manager.update_automaton()
#
#         for node in automaton.get_nodes():
#             if automaton.is_invisible(node):
#                 continue
#             if not manager.is_reachable(node):
#                 fully_reachable = False
#                 if node[0] == "Q":
#                     print('Line {} was found to be not '
#                           'reachable.'.format(node[1:]))
