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

for file in root_directory.rglob('*.c'):
    print("analysing: {}".format(file))

    # define the current working directory
    cwd = os.path.abspath("c-dead-code-analyser")

    # generate the automata
    command = ["python", "./Compiler.py",
               "analysis", file.absolute(),
               "true", "false"]

    with open('err.txt', 'w+') as error_stream:
        subprocess.call(command, env=os.environ, cwd=cwd, stderr=error_stream)

        error_stream.seek(0)

        errors = error_stream.read()

    if errors != "":
        print("Something went wrong, carrying on")
        print(errors)
        print()
        continue

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

    print(generated_files)
