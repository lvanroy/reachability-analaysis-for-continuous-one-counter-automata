import subprocess
import os
import shutil

import pandas as pd

from pathlib import Path

column_names = ["file", "function", "is representable", "has dead code"]
df = pd.DataFrame(columns=column_names)

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
            subprocess.call(command, env=os.environ, cwd=cwd, stderr=error_stream, stdout=output_stream)

            error_stream.seek(0)

            errors = error_stream.read()

        errors = errors.split("\n")
        errors = [error for error in errors if "dot: " not in error]
        errors = "\n".join(errors)
        if errors != "":
            print("Something went wrong, carrying on")
            # print(errors)
            # print()
            # exit(-1)
