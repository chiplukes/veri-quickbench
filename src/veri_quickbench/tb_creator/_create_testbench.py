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


"""Testbench Generator

Generates a MyHDL testbench for testing verilog or MyHDL modules
"""

import datetime
import os
import sys
from pathlib import Path

import questionary

from ._verilog_iface import verilog_iface
from ._verilog_module import verilog_module
from ._verilog_reset import verilog_reset
from .templates._template_header import mit_header, work_header
from .templates._template_tf_config import write_tf_config
from .templates._template_tf_sigs import write_tf_sigs
from .templates._template_tf_uut import write_tf_uut
from .templates._template_verilog_tb import write_verilog_tb


def create_testbench(debug=False):  # noqa: PLR0912, PLR0915
    """
    creates a myhdl cosimulation for a verilog file
    """
    caller_folder = Path.cwd()

    if caller_folder.name != "testbench":
        # change directory to testbench folder if it exists
        if Path("testbench").is_dir():
            caller_folder = Path("testbench").absolute()
            print(f"Changing directory to {caller_folder}")
            os.chdir(caller_folder)
        else:
            print("Please run this script from the testbench folder, exiting now")
            sys.exit(1)

    # query for type of testbench to create
    print("\nInstructions:\n - Navigate to folder containing <uut_name>.v")
    print(" - up/down selects current file/folder, enter selects file\n")
    cdir = Path(caller_folder).absolute()
    basedir = Path(caller_folder).absolute()
    updirs = 0
    while 1:
        # get list of files/folders in current directory
        cdir_files = cdir.iterdir()
        cdir_files_filt = []
        for f in cdir_files:
            if (not f.is_file()) or (".v" in f.name) or (".py" in f.name):
                cdir_files_filt.append(f)
        flst = [".. <up a directory>"]  # add option for up a directory
        flst.extend([f"{f}" for f in cdir_files_filt])
        choice = questionary.select(
            "Navigate to and select file <uut_top.v>", choices=flst
        ).ask()  # returns value of selection
        if choice == flst[0]:
            cdir = cdir.parent
            if basedir > cdir:
                basedir = cdir
                updirs = updirs + 1
        else:
            choice_index = flst.index(choice)
            choice_path = cdir_files_filt[choice_index - 1]
            if choice_path.is_file():
                uut_path = choice_path
                break
            else:
                cdir = choice_path

    # format needed for path location of source in myhdl python testbench
    rel_pth = (uut_path.parent).relative_to(basedir)
    rel_pth_str = f"{rel_pth}"
    # fixme, there must be a better way to do this
    if "\\" in rel_pth_str:
        rel_pth_lst = rel_pth_str.split("\\")
    else:
        rel_pth_lst = rel_pth_str.split("/")
    rel_folders_str = "'" + "' / '".join(rel_pth_lst) + "'"
    primary_src_dir = f"parents[{updirs}] / {rel_folders_str}"

    # query for type of header to add to testbench files
    tb_lst = ["NONE", "MIT", "WORK"]
    header_type = questionary.select(
        "Select type of header for created files:", choices=tb_lst
    ).ask()  # returns value of selection
    currentDateTime = datetime.datetime.now()
    date = currentDateTime.date()
    if header_type == "NONE":
        header = ""
    elif header_type == "MIT":
        author = questionary.text("Please enter name:").ask()
        header = mit_header(author=author, date=date.year)
    elif header_type == "WORK":
        author = questionary.text("Please enter name:").ask()
        company = questionary.text("Please enter company:").ask()
        header = work_header(author=author, company=company, date=date.year)
    if debug:
        print(f"{header}")

    uut = uut_path.name.replace(".v", "")
    uut = uut.replace(".py", "")

    # add all files from src folder
    tb_lst = ["Yes", "No"]
    add_all = questionary.select(
        "Add all Verilog files from source folder:", choices=tb_lst
    ).ask()  # returns value of selection
    if add_all == "Yes":
        # make list of file names only
        cdir_file_names = []
        for f in cdir_files_filt:
            if (not f.is_file()) or (".v" in f.name) or (".py" in f.name):
                cdir_file_names.append(f.name)
        primary_src_files = cdir_file_names[:]
    else:
        primary_src_files = [choice_path.name]
    print("\n**************************")
    print("Source files found:")
    for psf in primary_src_files:
        print(f"* {psf}")
    print("**************************")

    # add additional verilog files?
    tb_lst = ["Yes", "No"]
    add_all = questionary.select(
        "Add additional Verilog files from testbench root folder (typically xilinx primitives or testbench helper files):",
        choices=tb_lst,
    ).ask()  # returns value of selection
    additional_src_dir = "Path(__file__).parent"
    if add_all == "Yes":
        cdir_files = caller_folder.iterdir()
        cdir_files_filt = []
        for f in cdir_files:
            if not f.is_file() or ".v" in f.name:
                cdir_files_filt.append(f)
        # make list of file names only
        cdir_file_names = []
        for f in cdir_files_filt:
            if (not f.is_file()) or (".v" in f.name) or (".py" in f.name):
                cdir_file_names.append(f.name)
        additional_src_files = cdir_file_names[:]
    else:
        additional_src_files = []
    print("\n**************************")
    print("Additional files found:")
    for asf in additional_src_files:
        print(f"* {asf}")
    print("**************************")

    print(f"Attempting to parse {uut}.v")
    mod = verilog_module(ifile=uut_path, debug=debug)

    # TODO: query for signals identified as axis, axi in them
    print("\n**************************")
    print("type,size,name")
    print(mod.debug_print_ports())
    print("**************************")

    ports_ok = questionary.select("Do these ports look correct?", choices=["Yes", "No"]).ask()
    if ports_ok == "No":
        print(
            "Ok, need to improve port parser, exiting now to avoid potential crash.  Calling create_testbench(debug=True) may help debug what is breaking."
        )
        sys.exit(1)

    # create tf_config.py
    overwrite = "Yes"
    if Path("tf_config.py").is_file():
        overwrite = questionary.select("tf_config.py already exists, overwrite?", choices=["Yes", "No"]).ask()
    if overwrite == "Yes":
        # discover any parameters
        params = mod.get_params(value_format="python")

        # determine type and value of params
        params_iface_lst = []  # parameters related to uut interface (width of ports etc.)
        params_core_lst = []  # parameters related to core function (timeouts,etc)
        for param in params:
            c = questionary.select(
                f"Is parameter {param[0]} used for uut interface (width of ports, etc)?", choices=["Yes", "No"]
            ).ask()
            param_val = questionary.select(
                f"Please enter default value for {param[0]}:", choices=[f"{param[1]}", "Custom"]
            ).ask()
            if param_val == "Custom":
                param_val = questionary.text(
                    f"Please enter default value for {param[0]} (note: needs to be a hex (0x prefix) or integer value):"
                ).ask()
            if c == "Yes":
                params_iface_lst.append((param[0], param_val))
            else:
                params_core_lst.append((param[0], param_val))

        with open("tf_config.py", "w") as f:
            f.writelines(header)
            write_tf_config(
                f,
                uut_name=uut,
                primary_src_dir=primary_src_dir,
                primary_src_files=primary_src_files,
                additional_src_dir=additional_src_dir,
                additional_src_files=additional_src_files,
                params_iface=params_iface_lst,
                params_core=params_core_lst,
            )

        # create tf_sigs.py
        def connect_fn(iface_sigs_str=None, iface_nm_str=None):
            """
            function passed into write_tf_sigs that attempts to connect any parameters
            not the cleanest way of doing this...
            iface_sig_str - strings of comma seperated interface signal/parameter name
            """
            nonlocal params_iface_lst

            print("\n**************************")
            print(f"Connecting parameters to {iface_nm_str} interface")
            params_lst = [p[0] for p in params_iface_lst]
            connected_iface_sig_lst = []
            for sig in iface_sigs_str.split(","):
                if sig.isupper():
                    # probably a parameter
                    choices = ["Custom"]
                    choices.extend(params_lst)
                    param_val = questionary.select(f"Connect {sig}?", choices=choices).ask()
                    if param_val == "Custom":
                        param_val = questionary.text(
                            f"Please enter default value for {sig} (note: needs to be a hex (0x prefix) or integer value):"
                        ).ask()
                    connected_iface_sig_lst.append(f"{sig}={param_val}")
            # Fixme: attempt to hook up signal defaults?  ie tkeep tready if axis()?
            return ",".join(connected_iface_sig_lst)

        overwrite = "Yes"
        if Path("tf_sigs.py").is_file():
            overwrite = questionary.select("tf_sigs.py already exists, overwrite?", choices=["Yes", "No"]).ask()
        if overwrite == "Yes":
            with open("tf_sigs.py", "w") as f:
                f.writelines(header)
                write_tf_sigs(f, module=mod, connect_fn=connect_fn)

        # discover any clocks
        clocks = mod.get_clocks()
        clocks_lst = []
        for clk in clocks:
            is_clk = questionary.select(f"Is {clk} a clock?", choices=["Yes", "No"]).ask()
            if is_clk == "Yes":
                clocks_lst.append(clk)

        # discover any resets
        resets = mod.get_resets()  # gets any pors with "rst" or "reset" in the name
        resets_lst = []
        for reset in resets:
            is_reset = questionary.select(f"Is {reset} a reset?", choices=["Yes", "No"]).ask()
            if is_reset == "Yes":
                reset_active_high = questionary.select(f"Is {reset} a active high?", choices=["Yes", "No"]).ask()
                if reset_active_high == "Yes":
                    reset_active_high = True
                else:
                    reset_active_high = False
                associated_clock = questionary.select(f"Choose clock associated to {reset}?", choices=clocks_lst).ask()
                resets_lst.append(
                    verilog_reset(name=reset, polarity_is_positive=reset_active_high, associated_clock=associated_clock)
                )

        # discover any interfaces
        iface_lst = []
        iface_name_lst, iface_type_lst = mod.get_ifaces()
        for iface_i, iface_name in enumerate(iface_name_lst):
            associated_clock = questionary.select(f"Choose clock associated to {iface_name}?", choices=clocks).ask()
            associated_reset = None
            for reset in resets_lst:
                if reset.associated_clock == associated_clock:
                    associated_reset = reset.name
            # add any pause logic for interfaces (axi ready pushback,etc.)
            add_pause_logic = questionary.select(f"Add pause logic for {iface_name}?", choices=["Yes", "No"]).ask()
            if add_pause_logic == "Yes":
                pause = True
            else:
                pause = False
            # add any example logic for interfaces
            add_example_code = questionary.select(f"Add example logic for {iface_name}?", choices=["Yes", "No"]).ask()
            if add_example_code == "Yes":
                example = True
            else:
                example = False
            iface_lst.append(
                verilog_iface(
                    iface_type=iface_type_lst[iface_i],
                    name=iface_name,
                    associated_clock=associated_clock,
                    associated_reset=associated_reset,
                    pause=pause,
                    example=example,
                )
            )

        print("todo: connect any iface params to axi/axis instances in tf_sigs.py")

        print(
            "todo: ask if tready used, if not tie high in tf_sigs.py, same for tkeep (which needs to match element_size)"
        )

        # create tf_uut.py
        overwrite = "Yes"
        if Path(f"test_{uut}.py").is_file():
            overwrite = questionary.select(f"test_{uut}.py already exists, overwrite?", choices=["Yes", "No"]).ask()
        if overwrite == "Yes":
            with open(f"test_{uut}.py", "w") as f:
                f.writelines(header)
                write_tf_uut(f, uut_name=uut, clocks=clocks_lst, resets=resets_lst, iface_lst=iface_lst)


def mk_verilog_tb_wrap(uut, ofile=None, params=None):
    """
    creates the verilog testbench file for use in a MyHDL cosimulation
    uut - pathlib object input verilog uut
    ofile - pathlib object output testbench, if None then {uut}_tb.v is created in same
          - folder as {uut}
    """
    print(f"Parsing {uut!s}")
    mod = verilog_module(ifile=uut, debug=True)

    if ofile is None:
        ofile = uut.parent / uut.name + "_tb.v"
    print(f"Generating testbench {ofile}")
    with open(ofile, "w") as f:
        write_verilog_tb(f, mod, params)
