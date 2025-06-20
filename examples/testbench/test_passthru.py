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
    AXIStreamSink,
    AXIStreamSource,
    send_axis,
    wait_axis,
)

PAUSE_FACTOR = 1000  # will pause 1/PAUSE_FACTOR


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
        sim_cmd = {{}}
    if params_iface is None:
        params_iface = {{}}
    if params_core is None:
        params_core = {{}}

    print("Simulation Started")
    tf = sigs

    #######################
    # Clocks
    #######################
    # Note: may want to change the period here

    @always(delay(4))
    def clk_gen():
        tf.clk.next = not tf.clk

    #######################
    # Pause Logic
    #######################
    s_axis_pause = Signal(bool(0))

    @instance
    def s_axis_randPause():
        while 1:
            s_axis_pause.next = random.randint(1, PAUSE_FACTOR) == 1
            yield tf.clk.posedge

    m_axis_pause = Signal(bool(0))

    @instance
    def m_axis_randPause():
        while 1:
            m_axis_pause.next = random.randint(1, PAUSE_FACTOR) == 1
            yield tf.clk.posedge

    s_axi_pause_araddr = Signal(bool(0))
    s_axi_pause_rdata = Signal(bool(0))
    s_axi_pause_awaddr = Signal(bool(0))
    s_axi_pause_wdata = Signal(bool(0))
    s_axi_pause_bresp = Signal(bool(0))

    @instance
    def s_axi_randPause():
        while 1:
            s_axi_pause_araddr.next = random.randint(1, PAUSE_FACTOR) == 1
            s_axi_pause_rdata.next = random.randint(1, PAUSE_FACTOR) == 1
            s_axi_pause_awaddr.next = random.randint(1, PAUSE_FACTOR) == 1
            s_axi_pause_wdata.next = random.randint(1, PAUSE_FACTOR) == 1
            s_axi_pause_bresp.next = random.randint(1, PAUSE_FACTOR) == 1
            yield tf.clk.posedge

    m_axi_pause_araddr = Signal(bool(0))
    m_axi_pause_rdata = Signal(bool(0))
    m_axi_pause_awaddr = Signal(bool(0))
    m_axi_pause_wdata = Signal(bool(0))
    m_axi_pause_bresp = Signal(bool(0))

    @instance
    def m_axi_randPause():
        while 1:
            m_axi_pause_araddr.next = random.randint(1, PAUSE_FACTOR) == 1
            m_axi_pause_rdata.next = random.randint(1, PAUSE_FACTOR) == 1
            m_axi_pause_awaddr.next = random.randint(1, PAUSE_FACTOR) == 1
            m_axi_pause_wdata.next = random.randint(1, PAUSE_FACTOR) == 1
            m_axi_pause_bresp.next = random.randint(1, PAUSE_FACTOR) == 1
            yield tf.clk.posedge

    #######################
    # Endpoint Instances
    #######################
    source_s_axis = AXIStreamSource(repr_items=0)
    source_logic_s_axis = source_s_axis.create_logic(
        clk=tf.clk,
        rst=tf.rst,
        axis=tf.s_axis,
        pause=s_axis_pause,
        xname="s_axis",
    )
    sink_m_axis = AXIStreamSink(repr_items=0)
    sink_logic_m_axis = sink_m_axis.create_logic(
        clk=tf.clk,
        rst=tf.rst,
        axis=tf.m_axis,
        pause=m_axis_pause,
        xname="m_axis",
    )
    source_s_axi = AXIMaster(
        data_width=params_iface["AXI_DATA_WIDTH"],
        addr_width=params_iface["AXI_ADDR_WIDTH"],
        allow_narrow=True,
        allow_unaligned=True,
        repr_items=0,
        store_as_beats=False,
        aw_first=False,
        check_bresp=True,
    )
    source_s_axi_logic = source_s_axi.create_logic(
        clk=tf.clk,
        rst=tf.rst,
        axi=tf.s_axi,
        pause_waddr=s_axi_pause_awaddr,
        pause_wdata=s_axi_pause_wdata,
        pause_bresp=s_axi_pause_bresp,
        pause_araddr=s_axi_pause_araddr,
        pause_rdata=s_axi_pause_rdata,
        xname="axi_s_axi",
    )
    sink_m_axi = AXISlave(
        data_width=params_iface["AXI_DATA_WIDTH"],
        addr_width=params_iface["AXI_ADDR_WIDTH"],
        allow_narrow=True,
        allow_unaligned=True,
        repr_items=0,
        store_as_beats=False,
        rd_storage_fn=None,
        fill=0xDC,
    )
    sink_m_axi_logic = sink_m_axi.create_logic(
        clk=tf.clk,
        rst=tf.rst,
        axi=tf.m_axi,
        pause_waddr=m_axi_pause_awaddr,
        pause_wdata=m_axi_pause_wdata,
        pause_bresp=m_axi_pause_bresp,
        pause_araddr=m_axi_pause_araddr,
        pause_rdata=m_axi_pause_rdata,
        xname="m_axi",
    )

    uut_i = uut_inst(**sigs_dict, **sim_cmd, **params_iface, **params_core)

    @instance
    def check():
        global PAUSE_FACTOR  # noqa: PLW0603
        PAUSE_FACTOR = 4

        #######################
        # Resets
        #######################
        yield tf.clk.posedge
        tf.rst.next = 1
        yield tf.clk.posedge
        tf.rst.next = 0
        for _ in range(10):
            yield tf.clk.posedge

        #######################
        # Example Code
        #######################
        # Notes:
        #  - see test_axi_ep.py and test_axis_ep.py for more use cases
        #######################
        snd_frm = send_axis(
            source=source_s_axis,
            data=[i for i in range(10)],
            list_is_beats=True,
            tid=0,
            tdest=0,
            tuser=0,
            debug=True,
            endian="little",
        )
        # can also pass array of elements into here and set list_is_beats = False
        # snd_frm = send_axis(source=source_s_axis, data=[i for i in range(10)], list_is_beats=False, tid=0, tdest=0, tuser=0, debug=True, endian="little")
        #
        yield wait_axis(sink=sink_m_axis, clk=tf.clk, timeout=2000, msg="waiting m_axis")
        rcv_frm = sink_m_axis.recv()
        assert rcv_frm.data == snd_frm.data  # Note: likely need more stuff here!
        #
        # Issue write into s_axi
        din = [d % 256 for d in range(256)]  # 256 bytes
        source_s_axi.issue_write(addr=0, data=din, tid=0)

        # delay for write to complete
        for _ in range(100):
            yield tf.clk.posedge

        # checking writes on m_axi
        wr_a_actual, wr_d_actual, wr_tid_actual = sink_m_axi.get_write_log()
        print(wr_a_actual)
        print(wr_d_actual)
        print(wr_tid_actual)
        assert wr_d_actual == din

        # Read on s_axi
        # can pre-fill the memory like this
        sink_m_axi.clear()
        sink_m_axi.a = [a for a in range(256)]
        sink_m_axi.d = [d % 256 for d in range(256)]
        sink_m_axi.tid = [0 for _ in range(256)]

        source_s_axi.issue_read(addr=0, len_beats=1, arid=0)

        source_s_axi.clear()
        source_s_axi.a = [a for a in range(256)]
        source_s_axi.d = [d % 256 for d in range(256)]
        source_s_axi.tid = [0 for _ in range(256)]

        yield delay(10000)
        print("Simulation finished, disaster averted!")
        raise StopSimulation

    return instances()


# test function for cosimulation
@pytest.mark.parametrize(
    "params_iface, params_core",
    [(tf_config.PARAMS_IFACE, tf_config.PARAMS_CORE)],
)
def test_main_cosim(params_iface, params_core):
    """
    Test function running a Verilog cosimulation
    This function starts with test_ and will be called automatically with pytest
    """
    # make temporary test folder, unique name with any params changed from default
    mtf = mk_test_folder(
        folder=tf_config.TB_DIR
        / f"{get_fname()}_{print_param_changes(params_iface, tf_config.PARAMS_IFACE)}_{print_param_changes(params_core, tf_config.PARAMS_CORE)}"
    )  # make unique named test folder

    # creates a dict of signals to/from uut
    sigs = tf_sigs.tf_sigs(**params_iface, **params_core)
    # Testing plain ol' Verilog
    uut_top = tf_config.SRC_DIR / f"{tf_config.UUT_NAME}.v"
    mk_verilog_tb_wrap(
        uut=uut_top,
        ofile=mtf / f"tb_{tf_config.UUT_NAME}.v",
        params={**params_iface, **params_core},
    )
    tb_file = str(mtf / f"tb_{tf_config.UUT_NAME}.v")
    if os.system(f"iverilog -W all -o test_{tf_config.UUT_NAME}.vvp {tf_config.VERILOG_SRC_FILES} {tb_file}"):
        raise Exception("Error running build command")
    sim = Simulation(
        tb(
            uut_inst=Cosimulation,
            sigs=sigs,
            sigs_dict=sigs.get_sigs_dict_cosim(),
            sim_cmd={"exe": f"vvp -v -m myhdl test_{tf_config.UUT_NAME}.vvp -lxt2"},
            params_iface=params_iface,
            params_core=params_core,
        )
    )
    sim.run()


if __name__ == "__main__":
    print("here")
    test_main_cosim(params_iface=tf_config.PARAMS_IFACE, params_core=tf_config.PARAMS_CORE)
