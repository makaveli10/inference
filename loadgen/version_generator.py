# Copyright 2019 The MLPerf Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================

## \file
#  \brief A script run by the build to generate the version definitions
#  expected at link time.

import datetime
import errno
import hashlib
import os
import sys


# Creates a C++ raw string literal using a delimiter that is very
# unlikely to show up in a git stats.
def make_raw_string(str) :
    delimeter = "LGVG_RSLD"
    return "R\"" + delimeter + "(" + str + ")" + delimeter + "\""

def func_def(name, string):
    return ("const std::string& Loadgen" + name + "() {\n" +
            "  static const std::string str = " + string + ";\n" +
            "  return str;\n" +
            "}\n\n")


# For clients that build the loadgen from the git respository without
# any modifications.
def generate_loadgen_version_definitions_git(ofile, git_command):
    git_rev = os.popen(git_command + "rev-parse --short=10 HEAD").read()
    git_commit_date = os.popen(git_command + "log --format=\"%cI\" -n 1").read()
    git_status = os.popen(git_command + "status -s -uno").read()
    git_log = os.popen(
        git_command + "log --pretty=oneline -n 16 --no-decorate").read()
    ofile.write(func_def("GitRevision", "\"" + git_rev[0:-1] + "\""))
    ofile.write(func_def("GitCommitDate", "\"" + git_commit_date[0:-1] + "\""))
    ofile.write(func_def("GitStatus", make_raw_string(git_status[0:-1])))
    ofile.write(func_def("GitLog", make_raw_string(git_log[0:-1])))


# For clients that might not import the loadgen code as the original git
# repository.
def generate_loadgen_verstion_definitions_git_stubs(ofile):
    na = "\"NA\""
    ofile.write(func_def("GitRevision", na))
    ofile.write(func_def("GitCommitDate", na))
    ofile.write(func_def("GitStatus", na))
    ofile.write(func_def("GitLog", na))


# Always log the sha1 of the loadgen files, regardless of whether we are
# in the original git repository or not.
def generate_loadgen_version_definitions_sha1(ofile, loadgen_root):
    """Writes definition for Sha1OfFiles."""
    sha1s = ""
    loadgen_files = (
        ["/bindings/" + s for s in os.listdir(loadgen_root + "/bindings")] +
        ["/demos/" + s for s in os.listdir(loadgen_root + "/demos")] +
        ["/" + s for s in os.listdir(loadgen_root)])
    for fn in sorted(loadgen_files):
        full_fn = loadgen_root + fn
        if not os.path.isfile(full_fn):
            continue
        file_data = open(full_fn, "rb").read()
        sha1s += hashlib.sha1(file_data).hexdigest() + " " + fn + "\n"

    ofile.write(func_def("Sha1OfFiles", make_raw_string(sha1s[0:-1])))


# Outputs version function definitions to cc_filename.
# Includes SHA1's of the relevant dirs in the loadgen_root directory.
def generate_loadgen_version_definitions(cc_filename, loadgen_root):
    """Generates the C++ source file with the loadgen version info."""
    try:
        os.makedirs(os.path.dirname(cc_filename))
    except OSError as exc:
        if exc.errno != errno.EEXIST:
            raise
    ofile = open(cc_filename, "w")
    ofile.write("// DO NOT EDIT: Autogenerated by version_generator.py.\n\n")
    ofile.write("#include <string>\n\n")
    ofile.write("namespace mlperf {\n\n")
    ofile.write(func_def("Version", "\"2.0\""))

    date_time_now_local = datetime.datetime.now().isoformat()
    date_time_now_utc = datetime.datetime.utcnow().isoformat()
    ofile.write(func_def("BuildDateLocal", "\"" + date_time_now_local + "\""))
    ofile.write(func_def("BuildDateUtc", "\"" + date_time_now_utc + "\""))

    git_dir = "--git-dir=\"" + loadgen_root + "/../.git\" "
    git_work_tree = "--work-tree=\"" + loadgen_root + "/..\" "
    git_command = "git " + git_dir + git_work_tree
    git_status = os.popen(git_command + "status")
    git_status.read()
    is_git_repo = git_status.close() is None
    if is_git_repo:
        generate_loadgen_version_definitions_git(ofile, git_command)
    else:
        generate_loadgen_verstion_definitions_git_stubs(ofile)
    generate_loadgen_version_definitions_sha1(ofile, loadgen_root)

    ofile.write("}  // namespace mlperf\n")
    ofile.close()


def main():
    if len(sys.argv) != 3:
        raise ValueError("Incorrect command-line arguments.")
    generate_loadgen_version_definitions(sys.argv[1], sys.argv[2])


if __name__ == "__main__":
    main()
