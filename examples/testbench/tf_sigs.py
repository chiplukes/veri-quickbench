from myhdl import Signal

from veri_quickbench.tb_endpoints import axi, axis


class tf_sigs:
    """
    wrap signals for uut into class
    """

    def __init__(self, DATA_WIDTH, USER_WIDTH, DEST_WIDTH, ID_WIDTH, AXI_ADDR_WIDTH, AXI_ID_WIDTH, AXI_DATA_WIDTH):
        # Signal Declarations
        self.clk = Signal(bool(0))
        self.rst = Signal(bool(0))
        self.s_axis = axis(
            DATA_WIDTH=DATA_WIDTH, USER_WIDTH=USER_WIDTH, DEST_WIDTH=DEST_WIDTH, ID_WIDTH=ID_WIDTH, ELEMENT_SIZE_BITS=8
        )
        self.m_axis = axis(
            DATA_WIDTH=DATA_WIDTH, USER_WIDTH=USER_WIDTH, DEST_WIDTH=DEST_WIDTH, ID_WIDTH=ID_WIDTH, ELEMENT_SIZE_BITS=8
        )
        self.s_axi = axi(AXI_ADDR_WIDTH=AXI_ADDR_WIDTH, AXI_ID_WIDTH=AXI_ID_WIDTH, AXI_DATA_WIDTH=AXI_DATA_WIDTH)
        self.m_axi = axi(AXI_ADDR_WIDTH=AXI_ADDR_WIDTH, AXI_ID_WIDTH=AXI_ID_WIDTH, AXI_DATA_WIDTH=AXI_DATA_WIDTH)

    def get_sigs_dict_myhdl(self):
        """
        returns a dictionary of signals for this uut when testng a MyHDL uut
        """
        return vars(self)

    def get_sigs_dict_cosim(self):
        """
        returns a dictionary of signals for this uut when testng a Verilog uut
        """
        return {
            "clk": self.clk,
            "rst": self.rst,
            "s_axis_tdata": self.s_axis.tdata,
            "s_axis_tuser": self.s_axis.tuser,
            "s_axis_tdest": self.s_axis.tdest,
            "s_axis_tid": self.s_axis.tid,
            "s_axis_tkeep": self.s_axis.tkeep,
            "s_axis_tlast": self.s_axis.tlast,
            "s_axis_tvalid": self.s_axis.tvalid,
            "s_axis_tready": self.s_axis.tready,
            "m_axis_tdata": self.m_axis.tdata,
            "m_axis_tuser": self.m_axis.tuser,
            "m_axis_tdest": self.m_axis.tdest,
            "m_axis_tid": self.m_axis.tid,
            "m_axis_tkeep": self.m_axis.tkeep,
            "m_axis_tlast": self.m_axis.tlast,
            "m_axis_tvalid": self.m_axis.tvalid,
            "m_axis_tready": self.m_axis.tready,
            "s_axi_awid": self.s_axi.awid,
            "s_axi_awaddr": self.s_axi.awaddr,
            "s_axi_awlen": self.s_axi.awlen,
            "s_axi_awprot": self.s_axi.awprot,
            "s_axi_awvalid": self.s_axi.awvalid,
            "s_axi_awready": self.s_axi.awready,
            "s_axi_wdata": self.s_axi.wdata,
            "s_axi_wstrb": self.s_axi.wstrb,
            "s_axi_wvalid": self.s_axi.wvalid,
            "s_axi_wlast": self.s_axi.wlast,
            "s_axi_wready": self.s_axi.wready,
            "s_axi_bid": self.s_axi.bid,
            "s_axi_bresp": self.s_axi.bresp,
            "s_axi_bvalid": self.s_axi.bvalid,
            "s_axi_bready": self.s_axi.bready,
            "s_axi_arid": self.s_axi.arid,
            "s_axi_araddr": self.s_axi.araddr,
            "s_axi_arprot": self.s_axi.arprot,
            "s_axi_arvalid": self.s_axi.arvalid,
            "s_axi_arready": self.s_axi.arready,
            "s_axi_rid": self.s_axi.rid,
            "s_axi_rdata": self.s_axi.rdata,
            "s_axi_rresp": self.s_axi.rresp,
            "s_axi_rvalid": self.s_axi.rvalid,
            "s_axi_rlast": self.s_axi.rlast,
            "s_axi_rready": self.s_axi.rready,
            "m_axi_awid": self.m_axi.awid,
            "m_axi_awaddr": self.m_axi.awaddr,
            "m_axi_awlen": self.m_axi.awlen,
            "m_axi_awprot": self.m_axi.awprot,
            "m_axi_awvalid": self.m_axi.awvalid,
            "m_axi_awready": self.m_axi.awready,
            "m_axi_wdata": self.m_axi.wdata,
            "m_axi_wstrb": self.m_axi.wstrb,
            "m_axi_wvalid": self.m_axi.wvalid,
            "m_axi_wlast": self.m_axi.wlast,
            "m_axi_wready": self.m_axi.wready,
            "m_axi_bid": self.m_axi.bid,
            "m_axi_bresp": self.m_axi.bresp,
            "m_axi_bvalid": self.m_axi.bvalid,
            "m_axi_bready": self.m_axi.bready,
            "m_axi_arid": self.m_axi.arid,
            "m_axi_araddr": self.m_axi.araddr,
            "m_axi_arprot": self.m_axi.arprot,
            "m_axi_arvalid": self.m_axi.arvalid,
            "m_axi_arready": self.m_axi.arready,
            "m_axi_rid": self.m_axi.rid,
            "m_axi_rdata": self.m_axi.rdata,
            "m_axi_rresp": self.m_axi.rresp,
            "m_axi_rvalid": self.m_axi.rvalid,
            "m_axi_rlast": self.m_axi.rlast,
            "m_axi_rready": self.m_axi.rready,
        }
