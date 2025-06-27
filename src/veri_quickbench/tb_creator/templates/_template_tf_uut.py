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


def write_tf_uut(  # noqa: PLR0913
    f, uut_name=None, src_dir=None, clocks=None, resets=None, iface_lst=None
):
    """
    Writes the tf_<uut_name> testbench file
    uut_name -
    src_dir -
    clocks -
    resets - list of verilog_reset objects
    """
    # add special import for files located in folders above testfixture folder
    import_str = ""

    # create code for clock generation
    clk_sources = ""
    for clk in clocks:
        clk_sources += f"""
    @always(delay(4))
    def {clk}_gen():
        tf.{clk}.next = not tf.{clk}
"""

    # create code for asserting reset at start of testbench
    reset_assertions = ""
    for reset in resets:
        reset_assertions += f"      {reset.create_reset_template_myhdl()}"

    # TBD: create random pauses
    pause_logic = ""
    for iface in iface_lst:
        if iface.pause is True:
            pause_logic += f"      {iface.create_iface_pause_template_myhdl()}"

    # create code for asserting reset at start of testbench
    endpoint_instances = ""
    for iface in iface_lst:
        endpoint_instances += f"      {iface.create_iface_endpoint_template_myhdl()}"

    # create example code using endpoints
    examples = ""
    for iface in iface_lst:
        examples += f"      {iface.create_iface_example_template_myhdl()}"

    pytest_mark_param = """
@pytest.mark.parametrize("params_iface, params_core", [(tf_config.PARAMS_IFACE,tf_config.PARAMS_CORE)])"""

    cosim_test = ""
    cosim_call = ""
    cosim_test = f'''# test function for cosimulation{pytest_mark_param}
def test_main_cosim(params_iface,params_core):
    """
    Test function running a Verilog cosimulation
    This function starts with test_ and will be called automatically with pytest
    """
    # make temporary test folder, unique name with any params changed from default
    mtf = mk_test_folder(folder=tf_config.TB_DIR / f"{{get_fname()}}_{{print_param_changes(params_iface,tf_config.PARAMS_IFACE)}}_{{print_param_changes(params_core,tf_config.PARAMS_CORE)}}") # make unique named test folder

    # creates a dict of signals to/from uut
    sigs = tf_sigs.tf_sigs(**params_iface,**params_core)'''

    cosim_test = (
        cosim_test
        + """
    # Testing plain ol' Verilog
    uut_top = tf_config.SRC_DIR / f"{tf_config.UUT_NAME}.v"
    mk_verilog_tb_wrap(uut=uut_top, ofile=mtf / f"tb_{tf_config.UUT_NAME}.v", params={**params_iface, **params_core})"""
    )

    cosim_test = (
        cosim_test
        + """
    tb_file = str(mtf / f"tb_{tf_config.UUT_NAME}.v")
    if os.system(
        f"iverilog -W all -o test_{tf_config.UUT_NAME}.vvp {tf_config.VERILOG_SRC_FILES} {tb_file}"
    ):
        raise Exception("Error running build command")
    sim = Simulation( tb(uut_inst=Cosimulation,
                      sigs=sigs,
                      sigs_dict = sigs.get_sigs_dict_cosim(),
                      sim_cmd={"exe":f"vvp -v -m myhdl test_{tf_config.UUT_NAME}.vvp -lxt2"},
                      params_iface=params_iface,
                      params_core=params_core))
    sim.run()
        """
    )
    cosim_call = """test_main_cosim(params_iface=tf_config.PARAMS_IFACE, params_core=tf_config.PARAMS_CORE)"""

    f.writelines(f'''
import os
import random

import pytest
import tf_config
import tf_sigs
from myhdl import (
    Cosimulation,
    Signal,
    Simulation,
    StopSimulation,
    always,
    block,
    delay,
    instance,
    instances,
)

from veri_quickbench.tb_creator import (
    get_fname,
    mk_test_folder,
    mk_verilog_tb_wrap,
    print_param_changes,
)
from veri_quickbench.tb_endpoints import (
    AXIMaster,
    AXISlave,
    AXIStreamFrame,
    AXIStreamSink,
    AXIStreamSource,
    send_axis,
    wait_axis,
)


{import_str}

PAUSE_FACTOR = 1000 # will pause 1/PAUSE_FACTOR

@block
def tb(
    uut_inst=None,
    sigs=None,
    sigs_dict=None,
    sim_cmd=None,
    params_iface=None,
    params_core=None,
):
    """
    The actual testbench
    uut_inst - myhdl instance or Cosimulation obect
    sigs - object containing MyHDL Signals for the uut_inst
    sigs_dict - dictionary of names as keys and signals as values
    params_iface - parameters that affect size of uut ports
    params_core - all other parameters for uut
    """
    if sim_cmd is None:
        sim_cmd={{}}
    if params_iface is None:
        params_iface={{}}
    if params_core is None:
        params_core={{}}



    print("Simulation Started")
    tf = sigs

    #######################
    # Clocks
    #######################
    # Note: may want to change the period here
{clk_sources}

    #######################
    # Pause Logic
    #######################{pause_logic}

    #######################
    # Endpoint Instances
    #######################{endpoint_instances}

    uut_i = uut_inst(**sigs_dict, **sim_cmd, **params_iface, **params_core)

    @instance
    def check():

        global PAUSE_FACTOR # noqa: PLW0603
        PAUSE_FACTOR = 4

        #######################
        # Resets
        #######################{reset_assertions}

        #######################
        # Example Code
        #######################
        # Notes:
        #  - see test_axi_ep.py and test_axis_ep.py for more use cases
        #######################{examples}

        yield delay(10000)
        print("Simulation finished, disaster averted!")
        raise StopSimulation

    return instances()

{cosim_test}

if __name__ == "__main__":
    {cosim_call}
''')
