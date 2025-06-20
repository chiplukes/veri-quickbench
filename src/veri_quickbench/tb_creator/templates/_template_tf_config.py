# MIT License
#
# Copyright (c) 2022 Chip Lukes
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


def write_tf_config(  # noqa: PLR0913
    f,
    uut_name=None,
    primary_src_dir=None,
    primary_src_files=None,
    additional_src_dir=None,
    additional_src_files=None,
    params_iface=None,
    params_core=None,
):
    """
    creates the tf_config.py file for this testbench
    primary_src_dir - relative path for source directory (from testbench root folder)
                    - Ie. typically something like: Path(__file__).parents[2]/'src'
    primary_src_files - list of files (including uut) from primary source folder
                      - Ie. ['uut.v', 'submodule1.v', 'submodule2.v']
    additional_src_dir - relative path for additional source directory (from testbench root folder)
                       - used for xilinx primitives such as glbl.v typically placed into testbench directory
                       - Ie. typically something like: str(Path(__file__).parent
    additional_src_files - list of files (including uut) from primary source folder
                      Ie. ['glbl.v', 'FIFO36E2.v', ... ]
    params_iface - parameters related to uut interface (list of tuples of type (parameter_name,parameter_value))
    params_core - parameters related to uut function (parameter_name,parameter_value)
    """

    if primary_src_dir is None:
        primary_src_dir = "Path(__file__).parents[2]/'src'"
    if primary_src_files is None:
        primary_src_files = []

    if additional_src_dir is None:
        additional_src_dir = "Path(__file__).parent"
    if additional_src_files is None:
        additional_src_files = []

    # add any additional verilog files
    src_files = []
    src_files.append("#Verilog source files\n")
    src_files.append("srcs = []\n")
    for src in primary_src_files:
        src_files.append(f'srcs.append(str(SRC_DIR / "{src}"))\n')
    for src in additional_src_files:
        src_files.append(f'srcs.append(str({additional_src_dir} / "{src}"))\n')
    src_files.append('VERILOG_SRC_FILES = " ".join(srcs)')
    verilog_src = "".join(src_files)

    # parse interface parameters
    params_iface_str = """
# Parameters used for uut interface"""
    if params_iface is None:
        params_iface_str += """
# TODO: needs to be manually created for UUT, example below
PARAMS_IFACE = {{
    #'DATA_WIDTH' : 32,
    #'USER_WIDTH' : 1,
    #'DEST_WIDTH' : 1,
    #'ID_WIDTH' : 1,
    #'ELEMENT_SIZE_BITS' : 32
}}
"""
    else:
        params_iface_str += """
PARAMS_IFACE = {
"""
        for param in params_iface:
            params_iface_str += f"  '{param[0]}' : {param[1]},\n"
        params_iface_str += """}
"""

    # parse core parameters
    params_core_str = """
# Parameters for uut core functionality (timeouts, etc.)"""
    if params_core is None:
        params_core_str += """
# TODO: needs to be manually created for UUT, example below
PARAMS_CORE = {
    #'DEPTH' : 4096,
    #'KEEP_ENABLE' : None,
    #'LAST_ENABLE' : 1,
    #'ID_ENABLE' : 0,
    #'DEST_ENABLE' : 0,
    #'USER_ENABLE' : 1,
    #'PIPELINE_OUTPUT' : 2,
    #'FRAME_FIFO' : 0,
    #'USER_BAD_FRAME_VALUE' : 1,
    #'USER_BAD_FRAME_MASK' : 1,
    #'DROP_BAD_FRAME' : 0,
    #'DROP_WHEN_FULL' : 0
}
"""
    else:
        params_core_str += """
PARAMS_CORE = {
"""
        for param in params_core:
            params_core_str += f"  '{param[0]}' : {param[1]},\n"
        params_core_str += """}
"""

    f.writelines(
        f"""
# Configuration file for the testbench

from pathlib import Path

# Name of Verilog or MyHDL module being simulated (must match file name)
UUT_NAME = "{uut_name}"

# Paths Setup

# Testbench Temporary Folder
TB_DIR = Path(__file__)
TB_DIR = TB_DIR.parent / ".tmptst"

# Path to Source code
SRC_DIR = Path(__file__).{primary_src_dir}

{verilog_src}

{params_iface_str}

{params_core_str}

# Save VCD (True, False)
TRACE = True

"""
    )
