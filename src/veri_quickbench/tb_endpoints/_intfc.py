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


import inspect
import sys

from myhdl import Signal, _Signal, intbv


class axis:
    def __init__(  # noqa: PLR0912, PLR0913
        self,
        DATA_WIDTH=32,
        USER_WIDTH=1,
        DEST_WIDTH=1,
        ID_WIDTH=1,
        ELEMENT_SIZE_BITS=8,  # size of element within tdata vector, usually 8 for bytes
        clk=None,
        rst=None,
        tdata=None,
        tkeep=None,
        tuser=None,
        tdest=None,
        tid=None,
        tvalid=None,
        tready=None,
        tlast=None,
    ):
        # if isinstance(clk, (_Signal._Signal,)):
        #     self.aclk = clk
        # else:
        #     self.aclk = Signal(bool(0))

        # if isinstance(rst, (_Signal._Signal,)):
        #     self.aresetn = rst
        # else:
        #     self.aresetn = Signal(bool(0))

        if isinstance(tdata, (_Signal._Signal,)):
            self.tdata = tdata
        else:
            self.tdata = Signal(intbv(0)[DATA_WIDTH:])

        if isinstance(tkeep, (_Signal._Signal,)):
            self.tkeep = tkeep
        elif DATA_WIDTH < 8:  # noqa: PLR2004
            self.tkeep = Signal(intbv(1)[1:])
        else:
            self.tkeep = Signal(intbv(2 ** int(DATA_WIDTH / ELEMENT_SIZE_BITS) - 1)[(DATA_WIDTH / ELEMENT_SIZE_BITS) :])

        if isinstance(tuser, (_Signal._Signal,)):
            self.tuser = tuser
        else:
            self.tuser = Signal(intbv(0)[USER_WIDTH:])

        if isinstance(tdest, (_Signal._Signal,)):
            self.tdest = tdest
        else:
            self.tdest = Signal(intbv(0)[DEST_WIDTH:])

        if isinstance(tid, (_Signal._Signal,)):
            self.tid = tid
        else:
            self.tid = Signal(intbv(0)[ID_WIDTH:])

        if isinstance(tvalid, (_Signal._Signal,)):
            self.tvalid = tvalid
        else:
            self.tvalid = Signal(bool(0))

        if isinstance(tready, (_Signal._Signal,)):
            self.tready = tready
        else:
            self.tready = Signal(bool(0))

        if isinstance(tlast, (_Signal._Signal,)):
            self.tlast = tlast
        else:
            self.tlast = Signal(bool(0))


class axi_lite:
    def __init__(  # noqa: PLR0912, PLR0913, PLR0915
        self,
        AXI_ADDR_WIDTH=32,
        AXI_ID_WIDTH=1,
        AXI_DATA_WIDTH=32,
        awaddr=None,
        awvalid=None,
        awready=None,
        wdata=None,
        wstrb=None,
        wvalid=None,
        wready=None,
        bresp=None,
        bvalid=None,
        bready=None,
        araddr=None,
        arvalid=None,
        arready=None,
        rdata=None,
        rresp=None,
        rvalid=None,
        rready=None,
    ):
        if isinstance(awaddr, (_Signal._Signal,)):
            self.awaddr = awaddr
        else:
            self.awaddr = Signal(intbv(0)[AXI_ADDR_WIDTH:])

        if isinstance(awvalid, (_Signal._Signal,)):
            self.awvalid = awvalid
        else:
            self.awvalid = Signal(bool(0))

        if isinstance(awready, (_Signal._Signal,)):
            self.awready = awready
        else:
            self.awready = Signal(bool(0))

        if isinstance(wdata, (_Signal._Signal,)):
            self.wdata = wdata
        else:
            self.wdata = Signal(intbv(0)[AXI_DATA_WIDTH:])

        if isinstance(wstrb, (_Signal._Signal,)):
            self.wstrb = wstrb
        else:
            self.wstrb = Signal(intbv(0)[(AXI_DATA_WIDTH / 8) :])

        if isinstance(wvalid, (_Signal._Signal,)):
            self.wvalid = wvalid
        else:
            self.wvalid = Signal(bool(0))

        if isinstance(wready, (_Signal._Signal,)):
            self.wready = wready
        else:
            self.wready = Signal(bool(0))

        if isinstance(bresp, (_Signal._Signal,)):
            self.bresp = bresp
        else:
            self.bresp = Signal(intbv(0)[2:])

        if isinstance(bvalid, (_Signal._Signal,)):
            self.bvalid = bvalid
        else:
            self.bvalid = Signal(bool(0))

        if isinstance(bready, (_Signal._Signal,)):
            self.bready = bready
        else:
            self.bready = Signal(bool(0))

        if isinstance(araddr, (_Signal._Signal,)):
            self.araddr = araddr
        else:
            self.araddr = Signal(intbv(0)[AXI_ADDR_WIDTH:])

        if isinstance(arvalid, (_Signal._Signal,)):
            self.arvalid = arvalid
        else:
            self.arvalid = Signal(bool(0))

        if isinstance(arready, (_Signal._Signal,)):
            self.arready = arready
        else:
            self.arready = Signal(bool(0))

        if isinstance(rdata, (_Signal._Signal,)):
            self.rdata = rdata
        else:
            self.rdata = Signal(intbv(0)[AXI_DATA_WIDTH:])

        if isinstance(rresp, (_Signal._Signal,)):
            self.rresp = rresp
        else:
            self.rresp = Signal(intbv(0)[2:])

        if isinstance(rvalid, (_Signal._Signal,)):
            self.rvalid = rvalid
        else:
            self.rvalid = Signal(bool(0))

        if isinstance(rready, (_Signal._Signal,)):
            self.rready = rready
        else:
            self.rready = Signal(bool(0))


class axi:
    def __init__(  # noqa: PLR0912, PLR0913, PLR0915
        self,
        AXI_ADDR_WIDTH=32,
        AXI_ID_WIDTH=1,
        AXI_DATA_WIDTH=32,
        aclk=None,
        aresetn=None,
        awaddr=None,
        awlen=None,
        awid=None,
        awsize=None,
        awburst=None,
        awlock=None,
        awcache=None,
        awprot=None,
        awqos=None,
        awregion=None,
        awvalid=None,
        awready=None,
        wdata=None,
        wid=None,
        wstrb=None,
        wlast=None,
        wvalid=None,
        wready=None,
        bid=None,
        bresp=None,
        bvalid=None,
        bready=None,
        araddr=None,
        arlen=None,
        arid=None,
        arsize=None,
        arburst=None,
        arlock=None,
        arcache=None,
        arprot=None,
        arvalid=None,
        arready=None,
        rdata=None,
        rid=None,
        rresp=None,
        rlast=None,
        rvalid=None,
        rready=None,
    ):
        if isinstance(aclk, (_Signal._Signal,)):
            self.aclk = aclk
        else:
            self.aclk = Signal(bool(0))

        if isinstance(aresetn, (_Signal._Signal,)):
            self.aresetn = aresetn
        else:
            self.aresetn = Signal(bool(0))

        if isinstance(awaddr, (_Signal._Signal,)):
            self.awaddr = awaddr
        else:
            self.awaddr = Signal(intbv(0)[AXI_ADDR_WIDTH:])

        if isinstance(awlen, (_Signal._Signal,)):
            self.awlen = awlen
        else:
            self.awlen = Signal(intbv(0)[8:])

        if isinstance(awid, (_Signal._Signal,)):
            self.awid = awid
        else:
            self.awid = Signal(intbv(0)[AXI_ID_WIDTH:])

        if isinstance(awsize, (_Signal._Signal,)):
            self.awsize = awsize
        else:
            self.awsize = Signal(intbv(0)[3:])

        if isinstance(awburst, (_Signal._Signal,)):
            self.awburst = awburst
        else:
            self.awburst = Signal(intbv(0)[2:])

        if isinstance(awlock, (_Signal._Signal,)):
            self.awlock = awlock
        else:
            self.awlock = Signal(bool(0))

        if isinstance(awcache, (_Signal._Signal,)):
            self.awcache = awcache
        else:
            self.awcache = Signal(intbv(0)[4:])

        if isinstance(awprot, (_Signal._Signal,)):
            self.awprot = awprot
        else:
            self.awprot = Signal(intbv(0)[3:])

        if isinstance(awqos, (_Signal._Signal,)):
            self.awqos = awqos
        else:
            self.awqos = Signal(intbv(0)[4:])

        if isinstance(awregion, (_Signal._Signal,)):
            self.awregion = awregion
        else:
            self.awregion = Signal(intbv(0)[4:])

        if isinstance(awvalid, (_Signal._Signal,)):
            self.awvalid = awvalid
        else:
            self.awvalid = Signal(bool(0))

        if isinstance(awready, (_Signal._Signal,)):
            self.awready = awready
        else:
            self.awready = Signal(bool(0))

        if isinstance(wdata, (_Signal._Signal,)):
            self.wdata = wdata
        else:
            self.wdata = Signal(intbv(0)[AXI_DATA_WIDTH:])

        if isinstance(wid, (_Signal._Signal,)):
            self.wid = wid
        else:
            self.wid = Signal(intbv(0)[AXI_ID_WIDTH:])

        if isinstance(wstrb, (_Signal._Signal,)):
            self.wstrb = wstrb
        else:
            self.wstrb = Signal(intbv(2 ** (AXI_DATA_WIDTH // 8) - 1)[(AXI_DATA_WIDTH // 8) :])

        if isinstance(wlast, (_Signal._Signal,)):
            self.wlast = wlast
        else:
            self.wlast = Signal(bool(0))

        if isinstance(wvalid, (_Signal._Signal,)):
            self.wvalid = wvalid
        else:
            self.wvalid = Signal(bool(0))

        if isinstance(wready, (_Signal._Signal,)):
            self.wready = wready
        else:
            self.wready = Signal(bool(0))

        if isinstance(bid, (_Signal._Signal,)):
            self.bid = bid
        else:
            self.bid = Signal(intbv(0)[AXI_ID_WIDTH:])

        if isinstance(bresp, (_Signal._Signal,)):
            self.bresp = bresp
        else:
            self.bresp = Signal(intbv(0)[2:])

        if isinstance(bvalid, (_Signal._Signal,)):
            self.bvalid = bvalid
        else:
            self.bvalid = Signal(bool(0))

        if isinstance(bready, (_Signal._Signal,)):
            self.bready = bready
        else:
            self.bready = Signal(bool(1))

        if isinstance(araddr, (_Signal._Signal,)):
            self.araddr = araddr
        else:
            self.araddr = Signal(intbv(0)[AXI_ADDR_WIDTH:])

        if isinstance(arlen, (_Signal._Signal,)):
            self.arlen = arlen
        else:
            self.arlen = Signal(intbv(0)[8:])

        if isinstance(arid, (_Signal._Signal,)):
            self.arid = arid
        else:
            self.arid = Signal(intbv(0)[AXI_ID_WIDTH:])

        if isinstance(arsize, (_Signal._Signal,)):
            self.arsize = arsize
        else:
            self.arsize = Signal(intbv(0)[3:])

        if isinstance(arburst, (_Signal._Signal,)):
            self.arburst = arburst
        else:
            self.arburst = Signal(intbv(0)[2:])

        if isinstance(arlock, (_Signal._Signal,)):
            self.arlock = arlock
        else:
            self.arlock = Signal(bool(0))

        if isinstance(arcache, (_Signal._Signal,)):
            self.arcache = arcache
        else:
            self.arcache = Signal(intbv(0)[4:])

        if isinstance(arprot, (_Signal._Signal,)):
            self.arprot = arprot
        else:
            self.arprot = Signal(intbv(0)[3:])

        if isinstance(arvalid, (_Signal._Signal,)):
            self.arvalid = arvalid
        else:
            self.arvalid = Signal(bool(0))

        if isinstance(arready, (_Signal._Signal,)):
            self.arready = arready
        else:
            self.arready = Signal(bool(0))

        if isinstance(rdata, (_Signal._Signal,)):
            self.rdata = rdata
        else:
            self.rdata = Signal(intbv(0)[AXI_DATA_WIDTH:])

        if isinstance(rid, (_Signal._Signal,)):
            self.rid = rid
        else:
            self.rid = Signal(intbv(0)[AXI_ID_WIDTH:])

        if isinstance(rresp, (_Signal._Signal,)):
            self.rresp = rresp
        else:
            self.rresp = Signal(intbv(0)[2:])

        if isinstance(rlast, (_Signal._Signal,)):
            self.rlast = rlast
        else:
            self.rlast = Signal(bool(0))

        if isinstance(rvalid, (_Signal._Signal,)):
            self.rvalid = rvalid
        else:
            self.rvalid = Signal(bool(0))

        if isinstance(rready, (_Signal._Signal,)):
            self.rready = rready
        else:
            self.rready = Signal(bool(0))


def get_intfc_lst(debug=False):
    """
    returns a list of interfaces in this module
    """
    # get names of all interfaces that are in this module
    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    if debug:
        print(clsmembers)
    intfc_lst = [f"{x[0]}_" for x in clsmembers if "intfc" in f"{x[1]}"]
    return intfc_lst


def get_intfc_inits(iface_nm):
    """
    returns a list of init parameters for iface_nm

    Ie. AXI_ADDR_WIDTH, AXI_ID_WIDTH, AXI_DATA_WIDTH
    """
    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    for x in clsmembers:
        if x[0] == iface_nm:
            return ", ".join(inspect.getfullargspec(x[1].__init__).args[1:])


if __name__ == "__main__":
    # tests
    print(get_intfc_lst())

    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    intfc_lst = [f"{x[0]}_" for x in clsmembers if "intfc" in f"{x[1]}"]
