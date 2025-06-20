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


import math

from myhdl import Signal, block, instance, instances

from ._axis_ep import (
    AXIStreamFrame,
    AXIStreamSink,
    AXIStreamSource,
    ElementSizeError,
)
from ._intfc import axis

# todo: create an issue_write_as_beats()


class AXITransactionError(Exception):
    pass


class AXIBusWidthError(Exception):
    pass


class AXIMemoryError(Exception):
    pass


class AXIMaster(object):
    def __init__(  # noqa: PLR0913
        self,
        data_width=None,
        addr_width=None,
        allow_narrow=False,
        allow_unaligned=False,
        endian="little",
        repr_items=-1,
        aw_first=False,
        check_bresp=True,
        store_as_beats=False,
    ):
        """
        Takes the following and converts to axi beats:
        data_width - width of wdata, rdata in bits
        addr_width - width of waddr, araddr in bits
        allow_narrow - when True uses WSTRB bits to allow writes to individual bytes
                           - within a beat
        allow_unaligned - first beat can have address unaligned to beat size
        endian - controls placement of bytes within wdata,rdata
                    - 'little' - first byte stored in lower bits of wdata,rdata beat
                    - 'big' - first byte stored in upper bits of wdata,rdata beat
        repr_items - number of items to print in data, keep, etc. arrays when printing an AXIStreamFrame, -1=full, 0=none
        aw_first- if True, forces aw channel to happen before wd channel
        check_bresp - if True, bresp channel is checked on a transaction
        """
        if data_width is None or not isinstance(data_width, (int,)):
            raise TypeError("data_width must be a integer multiple of 8")
        elif data_width % 8 != 0:
            raise ElementSizeError(f"data_width={data_width}, which is not a multiple of 8")
        else:
            self.data_width = data_width
        self.bytes_per_beat = data_width // 8
        self.adr_lbits_mask = self.bytes_per_beat - 1  # mask to get lower address bits

        if addr_width is None or not isinstance(addr_width, (int,)):
            raise TypeError("addr_width must be an integer")
        else:
            self.addr_width = addr_width
        self.adr_ubits_mask = 2**addr_width - 1 - self.adr_lbits_mask  # mask to get lower address bits

        self.allow_narrow = allow_narrow
        self.allow_unaligned = allow_unaligned
        self.endian = endian
        self.repr_items = repr_items
        self.aw_first = aw_first  # sends awvalid stream before wvalid
        self.check_bresp = check_bresp  # waits for bresp before transaction finished
        self.store_as_beats = store_as_beats

        self.has_logic = False
        self.wqueue = []  # pending write transactions
        self.rqueue = []  # pending read transactions
        self.a = []  # addresses of read bytes
        self.d = []  # read bytes
        self.tid = []

    def issue_write(self, addr, data, tid=0):
        """
        AXI Write
        addr - address to write to
               - if not aligned to self.addr_width and self.allow_narrow = True then
                 additional bytes will be included in transaction with corresponding wstrb bit cleared
               - if not aligned to self.addr_width and self.allow_narrow = False then
                 raises AXITransactionError
        data - can be one of the following:
                - bytearray
                - array of integers 0-255
                - single int 0-255
        tid - transaction id
        """
        # check data
        d_lst = []
        if isinstance(data, (bytes, bytearray)):
            d_lst = [d for d in data]
        elif isinstance(data, (list,)):
            for i, d in enumerate(data):
                if not isinstance(d, (int,)):
                    raise TypeError(f"data[{i}]={d} passed into issue_write should be an integer 0-255")
                if d < 0 or d > 256:  # noqa: PLR2004
                    raise ElementSizeError(f"data[{i}]={d} passed into issue_write should be integer 0-255,")
                d_lst.append(d)
        elif isinstance(data, (int,)):
            if data >= 0 and data <= 255:  # noqa: PLR2004
                d_lst.append(data)
            else:
                raise ElementSizeError(f"data={data} passed into issue_write should be integer 0-255,")
        else:
            raise TypeError(f"data={data} passed into issue_write should be bytearray, list of ints, int 0-255,")

        # check addr
        address_lbits = addr & self.adr_lbits_mask
        if self.allow_unaligned is False and address_lbits != 0:
            raise AXITransactionError(
                f"when allow_unaligned = False, transaction address {addr} must be aligned to axi beat width {self.bytes_per_beat}"
            )
        if self.allow_narrow is False and len(d_lst) % self.bytes_per_beat != 0:
            raise AXITransactionError(
                f"when allow_narrow = False, # bytes {len(d_lst)} must be a multiple of beat size {self.bytes_per_beat}"
            )

        address_ubits = self.adr_ubits_mask & addr
        wstrb = [1 for _ in d_lst]
        # for unaligned transfer pad w/ unused bytes at the start and set wstrb bits to 0
        for _ in range(address_lbits):
            wstrb.insert(0, 0)
            d_lst.insert(0, 0)
        # awlen
        awlen = math.ceil(len(d_lst) / self.bytes_per_beat) - 1
        self.wqueue.append((address_ubits, d_lst, wstrb, tid, awlen))

    def issue_write_beats(self, adr, data, tid=0, len_bytes=None):
        """
        converts data to beats
        """
        ...

    def write_empty(self):
        """AXI Write Queue Empty"""
        return len(self.wqueue) == 0

    def issue_read(self, addr, len_beats, arid=0):
        """AXI Read"""
        address_lbits = addr & self.adr_lbits_mask
        if self.allow_unaligned is False and address_lbits != 0:
            raise AXITransactionError(
                f"issue_read() - transaction address {addr} must be aligned to axi beat width {self.bytes_per_beat}"
            )
        if len_beats < 1:
            raise AXITransactionError(f"issue_read() - len_beats({len_beats}) should be >= 1")
        self.rqueue.append((addr, len_beats, arid))

    def read_empty(self):
        """AXI Read Queue Empty"""
        return len(self.rqueue) == 0

    def get_read_log(self):
        """returns address and read data lists"""
        return self.a, self.d, self.tid

    def clear(self):
        """clears address and write data lists"""
        self.a = []
        self.d = []
        self.tid = []

    def send(self, adr, data, tid=0, len_bytes=None):
        """Legacy function"""
        self.issue_write(adr, data, tid, len_bytes)

    def empty(self):
        """Legacy function"""
        return len(self.wqueue) == 0

    @block
    def create_logic(  # noqa: PLR0913, PLR0915
        self,
        clk,
        rst,
        axi=None,
        pause_waddr=0,
        pause_wdata=0,
        pause_bresp=0,
        pause_araddr=0,
        pause_rdata=0,
        xname=None,
    ):
        if self.has_logic:
            raise RuntimeError("create_logic() has already been called on this instance.")
        self.has_logic = True
        aw_size = len(axi.awaddr)
        wd_size = len(axi.wdata)
        ar_size = len(axi.araddr)
        rd_size = len(axi.rdata)

        if self.data_width != wd_size:
            raise AXIBusWidthError(
                f"AXIMaster configured with data_width{self.data_width} but not the same as connected WD bus width {wd_size}"
            )
        if self.data_width != rd_size:
            raise AXIBusWidthError(
                f"AXIMaster configured with data_width{self.data_width} but not the same as connected RD bus width {wd_size}"
            )
        if self.addr_width != aw_size:
            raise AXIBusWidthError(
                f"AXIMaster configured with addr_width{self.addr_width} but not the same as connected AW bus width {aw_size}"
            )
        if self.addr_width != ar_size:
            raise AXIBusWidthError(
                f"AXIMaster configured with addr_width{self.addr_width} but not the same as connected AR bus width {ar_size}"
            )

        # axi4 write address channel
        axis_wa_intfc = axis(
            DATA_WIDTH=aw_size,
            ID_WIDTH=len(axi.awid),
            DEST_WIDTH=len(axi.awlen),
            ELEMENT_SIZE_BITS=aw_size,
            tdata=axi.awaddr,
            tvalid=axi.awvalid,
            tready=axi.awready,
            tlast=Signal(bool(1)),
            tdest=axi.awlen,
            tid=axi.awid,
        )
        axis_waddr = AXIStreamSource(repr_items=self.repr_items)
        axis_waddr_logic = axis_waddr.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axis=axis_wa_intfc,
            pause=pause_waddr,
            xname="m_axi4 waddr",
        )

        # axi4 write data channel
        axis_wd_intfc = axis(
            DATA_WIDTH=wd_size,
            tdata=axi.wdata,
            tvalid=axi.wvalid,
            tkeep=axi.wstrb,
            tready=axi.wready,
            tlast=axi.wlast,
        )
        axis_wdata = AXIStreamSource(repr_items=self.repr_items)
        axis_wdata_logic = axis_wdata.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axis=axis_wd_intfc,
            pause=pause_wdata,
            xname="m_axi4 wdata",
        )

        # axi4 response channel
        axis_resp_intfc = axis(
            DATA_WIDTH=2,
            ID_WIDTH=len(axi.awid),
            tdata=axi.bresp,
            tvalid=axi.bvalid,
            tready=axi.bready,
            tlast=Signal(bool(1)),
            tid=axi.bid,
        )
        axis_resp = AXIStreamSink(repr_items=self.repr_items)
        axis_resp_logic = axis_resp.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axis=axis_resp_intfc,
            pause=pause_bresp,
            xname="m_axi4 bresp",
        )

        # axi4 read address channel
        axis_ar_intfc = axis(
            DATA_WIDTH=ar_size,
            ID_WIDTH=len(axi.awid),
            DEST_WIDTH=len(axi.arlen),
            ELEMENT_SIZE_BITS=ar_size,
            tdata=axi.araddr,
            tvalid=axi.arvalid,
            tready=axi.arready,
            tlast=Signal(bool(1)),
            tdest=axi.arlen,
            tid=axi.arid,
        )
        axis_araddr = AXIStreamSource(repr_items=self.repr_items)
        axis_araddr_logic = axis_araddr.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axis=axis_ar_intfc,
            pause=pause_araddr,
            xname="m_axi4 araddr",
        )

        # axi4 read data channel
        axis_rd_intfc = axis(
            DATA_WIDTH=rd_size,
            ID_WIDTH=len(axi.awid),
            tdata=axi.rdata,
            tvalid=axi.rvalid,
            tready=axi.rready,
            tlast=axi.rlast,
            tid=axi.rid,
        )
        axis_rdata = AXIStreamSink(repr_items=self.repr_items)
        axis_rdata_logic = axis_rdata.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axis=axis_rd_intfc,
            pause=pause_rdata,
            xname="m_axi4 rdata",
        )

        @instance
        def logic():
            while True:
                yield clk.posedge, rst.posedge

                if self.wqueue:
                    (adr, data, wstrb, awid, awlen) = self.wqueue.pop(0)

                    # AW Channel
                    axi.awburst.next = 1
                    axis_frame = AXIStreamFrame(
                        data=[adr],
                        tid=awid,
                        dest=awlen,
                        element_size_bits=aw_size,
                        elements_per_beat=1,
                        repr_items=self.repr_items,
                    )
                    axis_waddr.send(axis_frame)
                    if self.aw_first:  # sometimes AW transaction needed first
                        while not (axi.awvalid and axi.awready):
                            yield clk.posedge

                    # WD Channel
                    axis_frame = AXIStreamFrame(
                        data=data,
                        keep=wstrb,
                        elements_per_beat=wd_size // 8,
                        element_size_bits=8,
                        endian=self.endian,
                        repr_items=self.repr_items,
                    )
                    axis_wdata.send(axis_frame)

                    if self.check_bresp:
                        while axis_resp.empty():
                            yield clk.posedge
                        axis_resp.recv()

                if self.rqueue:
                    #  TODO: for now just issue one read at a time, change later!
                    (adr, len_beats, arid) = self.rqueue.pop(0)
                    axi.arburst.next = 1
                    axis_frame = AXIStreamFrame(
                        data=[adr],
                        tid=arid,
                        dest=len_beats - 1,
                        element_size_bits=ar_size,
                        elements_per_beat=1,
                        repr_items=self.repr_items,
                    )
                    axis_araddr.send(axis_frame)

                    while axis_rdata.empty():
                        yield clk.posedge
                    d = axis_rdata.recv()

                    if self.store_as_beats:
                        raise NotImplementedError("Not implemented yet!")
                        # self.a.append(adr)
                        # d_beats = d.to_beats(endian=self.endian)
                        # for x in d_beats:
                        #    self.d.append(x)
                        # for x in d.tid:
                        #    self.tid.append(x)
                    else:
                        araddr_aligned = adr & (~self.adr_lbits_mask)
                        d.elements_per_beat = rd_size // 8
                        d.element_size_bits = 8
                        d_lst = d.to_elements(endian=self.endian)
                        rid = d.tid[0]
                        for i, x in enumerate(d_lst):
                            self.a.append(araddr_aligned + i)
                            self.d.append(x)
                            self.tid.append(rid)

        return instances()
        # return axis_waddr_logic, axis_wdata_logic, axis_resp_logic, axis_araddr_logic, axis_rdata_logic, logic


class AXISlave(object):
    def __init__(  # noqa: PLR0913
        self,
        data_width=None,
        addr_width=None,
        allow_narrow=False,
        allow_unaligned=False,
        endian="little",
        repr_items=-1,
        aw_first=False,
        send_bresp=True,
        store_as_beats=False,
        rd_storage_fn=None,
        fill=None,
    ):
        """
        Takes the following and converts to axi beats:
        data_width - width of wdata, rdata in bits
        addr_width - width of waddr, araddr in bits
        allow_unaligned - first beat can have address unaligned to beat size
        allow_narrow - when True uses WSTRB bits to allow writes to individual bytes
                           - within a beat
        endian - controls placement of bytes within wdata,rdata
                    - 'little' - first byte stored in lower bits of wdata,rdata beat
                    - 'big' - first byte stored in upper bits of wdata,rdata beat
        repr_items - number of items to print in data, keep, etc. arrays when printing an AXIStreamFrame, -1=full, 0=none
        aw_first- if True, forces aw channel to happen before wd channel
        send_bresp - if True, slave sends bresp
        rd_storage_fn - when not None, this is a function that returns a storage byte for a given address or list of addresses
        fill - data value used as filler when memory access is not found in self.a, self.d
        """
        if data_width is None or not isinstance(data_width, (int,)):
            raise TypeError("data_width must be a integer multiple of 8")
        elif data_width % 8 != 0:
            raise ElementSizeError("data_width={data_width}, which is not a multiple of 8")
        else:
            self.data_width = data_width
        self.bytes_per_beat = data_width // 8
        self.adr_lbits_mask = self.bytes_per_beat - 1  # mask to get lower address bits

        if addr_width is None or not isinstance(addr_width, (int,)):
            raise TypeError("addr_width must be an integer")
        else:
            self.addr_width = addr_width
        self.adr_ubits_mask = 2**addr_width - 1 - self.adr_lbits_mask  # mask to get lower address bits

        self.allow_narrow = allow_narrow
        self.allow_unaligned = allow_unaligned
        self.endian = endian
        self.aw_first = aw_first  # sends awvalid stream before wvalid
        self.send_bresp = send_bresp  # waits for bresp before transaction finished
        self.store_as_beats = store_as_beats
        self.repr_items = repr_items
        self.rd_storage_fn = rd_storage_fn
        self.fill = fill
        self.has_logic = False

        # lists of address and data written to this slave, also used for reads
        # FIXME: byte addressing only or allow these to be axi beats of variable size?
        self.a = []  # list of byte addresses that have been written
        self.d = []  # list of bytes that have been written
        self.tid = []  # tid for each byte

    def get_write_log(self):
        """returns address and write data lists"""
        return self.a, self.d, self.tid

    def clear(self):
        """clears address and write data lists"""
        # fixme: instead of assigning to empty list, just clear these, that way multiple multiple instances of this could be used in a way that shares the same arrays
        # ie:
        # top level
        # d = [0,1,2]
        # axi4_0.d = d
        # axi4_1.d = d
        self.a = []
        self.d = []
        self.tid = []

    def load(self, addr, data, tid=0, wstrb=None):  # noqa: PLR0912, PLR0915
        """
        takes item data and loads it into a and d arrays as ints
        addr - can be one of the following:
               - 1 to 1 array of addresses for each data list item
               - integer starting address for array of data
        data - can be one of the following:
                - bytearray
                - array of integers 0-255
                - single int 0-255
        tid - can be one of the following:
               - 1 to 1 array of tids for each data list item
               - integer tid used for all items in data
        wstrb - can be one of the following:
                - None, init will create wstrb array based on length of data
                - array of 1,0,bool of same length as data
        """
        # check data
        d_lst = []
        if isinstance(data, (bytes, bytearray)):
            d_lst = [d for d in data]
        elif isinstance(data, (list,)):
            for i, d in enumerate(data):
                if not isinstance(d, (int,)):
                    raise TypeError(f"data[{i}]={d} passed into load should be an integer 0-255")
                if d < 0 or d > 256:  # noqa: PLR2004
                    raise ElementSizeError(f"data[{i}]={d} passed into load should be integer 0-255,")
                d_lst.append(d)
        elif isinstance(data, (int,)):
            if data >= 0 and data <= 255:  # noqa: PLR2004
                d_lst.append(data)
            else:
                raise ElementSizeError(f"data={data} passed into load should be integer 0-255,")
        else:
            raise TypeError(f"data={data} passed into load should be bytearray, list of ints, int 0-255,")

        # check adr
        a_lst = []
        if isinstance(addr, (list,)):
            if len(addr) != len(data):
                raise AXIMemoryError(
                    "When loading AXI memory addr must either be a single integer (starting address to write data) or a 1-1 list of addresses to match each byte in data list."
                )
            for i, a in enumerate(addr):
                if not isinstance(a, (int,)):
                    raise TypeError(f"address[{i}]={a} passed into load should be an integer")
                a_lst.append(a)
        elif isinstance(addr, (int,)):
            for i, _ in enumerate(d_lst):
                a_lst.append(addr + i)
        else:
            raise TypeError(f"addr={addr} passed into load should be list of ints, int")

        # check tid
        t_lst = []
        if isinstance(tid, (list,)):
            if len(tid) != len(data):
                raise AXIMemoryError(
                    "When loading AXI memory tid must either be a single integer (starting address to write data) or a 1-1 list of addresses to match each byte in data list."
                )
            for i, t in enumerate(tid):
                if not isinstance(t, (int,)):
                    raise TypeError(f"tid[{i}]={t} passed into load should be an integer")
                t_lst.append(t)
        elif isinstance(tid, (int,)):
            for _ in d_lst:
                t_lst.append(tid)
        else:
            raise TypeError(f"tid={tid} passed into load should be list of ints, int")

        # check wstrb
        if wstrb is None:
            wstrb = [1 for _ in d_lst]
        elif isinstance(wstrb, (list,)):
            if len(wstrb) != len(data):
                raise AXIMemoryError(
                    "When loading AXI memory wstrb must either be 1 or a 1-1 list of (int,bool) to flag whether each data list item is valid."
                )
            for i, w in enumerate(wstrb):
                if not isinstance(w, (int,)):
                    raise TypeError(f"tid[{i}]={w} passed into load should be an integer")
        else:
            raise TypeError(f"wstrb={wstrb} passed into load should be list of ints,bools")

        # deternime if need to check for pre-existing items as they are added
        if len(self.d) != 0 or len(self.a) != 0:
            for i, d in enumerate(d_lst):
                if wstrb[i]:
                    try:
                        indx = self.a.index(a_lst[i])
                        self.a[indx] = d
                        self.tid[indx] = t_lst[i]
                    except ValueError:
                        self.a.append(a_lst[i])
                        self.d.append(d)
                        self.tid.append(t_lst[i])
        else:
            for i, d in enumerate(d_lst):
                if wstrb[i]:
                    self.a.append(a_lst[i])
                    self.d.append(d)
                    self.tid.append(t_lst[i])

    @block
    def create_logic(  # noqa: PLR0913, PLR0915
        self,
        clk,
        rst,
        axi=None,
        pause_waddr=0,
        pause_wdata=0,
        pause_bresp=0,
        pause_araddr=0,
        pause_rdata=0,
        xname=None,
    ):
        if self.has_logic:
            raise RuntimeError("create_logic() has already been called on this instance.")
        self.has_logic = True
        aw_size = len(axi.awaddr)
        wd_size = len(axi.wdata)
        ar_size = len(axi.araddr)
        rd_size = len(axi.rdata)
        if self.data_width != wd_size:
            raise AXIBusWidthError(
                f"AXIMaster configured with data_width{self.data_width} but not the same as connected WD bus width {wd_size}"
            )
        if self.data_width != rd_size:
            raise AXIBusWidthError(
                f"AXIMaster configured with data_width{self.data_width} but not the same as connected RD bus width {wd_size}"
            )
        if self.addr_width != aw_size:
            raise AXIBusWidthError(
                f"AXIMaster configured with addr_width{self.addr_width} but not the same as connected AW bus width {aw_size}"
            )
        if self.addr_width != ar_size:
            raise AXIBusWidthError(
                f"AXIMaster configured with addr_width{self.addr_width} but not the same as connected AR bus width {ar_size}"
            )

        # axi4 write address channel
        axis_wa_intfc = axis(
            DATA_WIDTH=aw_size,
            DEST_WIDTH=len(axi.awlen),
            ID_WIDTH=len(axi.awid),
            ELEMENT_SIZE_BITS=aw_size,
            tdata=axi.awaddr,
            tvalid=axi.awvalid,
            tready=axi.awready,
            tdest=axi.awlen,
            tid=axi.awid,
            tlast=Signal(bool(1)),
        )
        axis_waddr = AXIStreamSink(repr_items=self.repr_items)
        axis_waddr_logic = axis_waddr.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axis=axis_wa_intfc,
            pause=pause_waddr,
            xname="s_axi4 waddr",
        )

        # axi4 write data channel
        axis_wd_intfc = axis(
            DATA_WIDTH=wd_size,
            tdata=axi.wdata,
            tvalid=axi.wvalid,
            tready=axi.wready,
            tlast=axi.wlast,
            tkeep=axi.wstrb,
        )
        axis_wdata = AXIStreamSink(
            repr_items=self.repr_items, skip_asserts=True, capture_leading=True
        )  # skip assertions on KEEP since wstrb can be anything
        axis_wdata_logic = axis_wdata.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axis=axis_wd_intfc,
            pause=pause_wdata,
            xname="s_axi4 wdata",
        )

        # axi4 response channel
        axis_resp_intfc = axis(
            DATA_WIDTH=2,
            ID_WIDTH=len(axi.bid),
            tdata=axi.bresp,
            tvalid=axi.bvalid,
            tready=axi.bready,
            tid=axi.bid,
        )
        axis_resp = AXIStreamSource(repr_items=self.repr_items)
        axis_resp_logic = axis_resp.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axis=axis_resp_intfc,
            pause=pause_bresp,
            xname="s_axi4 bresp",
        )

        # axi4 read address channel
        axis_ar_intfc = axis(
            DATA_WIDTH=ar_size,
            DEST_WIDTH=len(axi.arlen),
            ID_WIDTH=len(axi.arid),
            ELEMENT_SIZE_BITS=ar_size,
            tdata=axi.araddr,
            tvalid=axi.arvalid,
            tready=axi.arready,
            tdest=axi.arlen,
            tid=axi.arid,
            tlast=Signal(bool(1)),
        )
        axis_araddr = AXIStreamSink(repr_items=self.repr_items)
        axis_araddr_logic = axis_araddr.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axis=axis_ar_intfc,
            pause=pause_araddr,
            xname="s_axi4 araddr",
        )

        # axi4 read data channel
        axis_rd_intfc = axis(
            DATA_WIDTH=rd_size,
            ID_WIDTH=len(axi.rid),
            tdata=axi.rdata,
            tvalid=axi.rvalid,
            tready=axi.rready,
            tlast=axi.rlast,
            tid=axi.rid,
        )
        axis_rdata = AXIStreamSource(repr_items=self.repr_items)
        axis_rdata_logic = axis_rdata.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axis=axis_rd_intfc,
            pause=pause_rdata,
            xname="s_axi4 rdata",
        )

        @instance
        def logic():  # noqa: PLR0912, PLR0915
            while True:
                yield clk.posedge, rst.posedge

                if rst:
                    self.a = []
                    self.d = []
                elif not axis_waddr.empty() and not axis_wdata.empty():
                    a_stream = axis_waddr.recv()
                    d_stream = axis_wdata.recv()
                    # address and length of this burst
                    a_awaddr = a_stream.data[0]
                    a_awlen = a_stream.dest[0]
                    awid = a_stream.tid[0]

                    if self.store_as_beats:
                        raise NotImplementedError("Not implemented yet!")
                    else:
                        # store data as individual bytes paired with addresses
                        # check awlen
                        if a_awlen != math.ceil(len(d_stream.data) / self.bytes_per_beat) - 1:
                            raise AXITransactionError(
                                f"a_awlen ({a_awlen}) does not match expected value ({math.ceil(len(d_stream.data) / self.bytes_per_beat) - 1})"
                            )

                        # fixme: maybe add check for narrow burst into load?
                        self.load(
                            addr=a_awaddr,
                            data=d_stream.data,
                            tid=awid,
                            wstrb=d_stream.keep,
                        )

                    # create response
                    axis_frame = AXIStreamFrame(data=[0], tid=awid, repr_items=self.repr_items)
                    axis_resp.send(axis_frame)

                elif not axis_araddr.empty():
                    a_stream = axis_araddr.recv()

                    # address and length of this burst
                    araddr = a_stream.data[0]
                    len_beats = a_stream.dest[0] + 1
                    arid = a_stream.tid[0]
                    beat_bytes = int(len(axi.rdata) / 8)

                    # check if address is aligned to beat size, if not will need to either fill in beats with data from self.d, or if non-existant fill with zeros?
                    # added fill bytes parameter, if None raise error if access asks for memory

                    if (araddr & self.adr_lbits_mask) != 0:
                        if not self.allow_unaligned:
                            print("unaligned address detected")
                            raise AXITransactionError(
                                "Unaligned transaction not allowed for AXISlave with allow_unaliged=False."
                            )
                    araddr_aligned = araddr & (~self.adr_lbits_mask)

                    if self.rd_storage_fn is None:
                        # request expected to be in self.a and self.d
                        if not self.fill:
                            msg = "\nOOPS!\n{} not found in array {}".format(
                                hex(araddr_aligned), [hex(x) for x in self.a]
                            )
                            if araddr not in self.a:
                                raise AXIMemoryError(msg)

                        # FIXME: this section needs work
                        len_bytes = len_beats * beat_bytes

                        if self.fill:
                            # requested data may not be in self.a, self.d
                            # if so, return fill value
                            a_new = [araddr_aligned + x for x in range(len_bytes)]
                            d_new = [self.fill for x in range(len_bytes)]
                            # araddr expected to be in self.a
                            id_new = [self.tid[self.a.index(araddr)] for x in range(len_bytes)]
                            for i, a in enumerate(a_new):
                                try:
                                    index_a = self.a.index(a)
                                    d_new[i] = self.d[index_a]
                                except ValueError:
                                    pass

                        else:
                            # data expected to be in self.a,self.d
                            index_a = self.a.index(araddr_aligned)
                            a_new = self.a[index_a : index_a + len_bytes]
                            d_new = self.d[index_a : index_a + len_bytes]
                            id_new = self.tid[index_a : index_a + len_bytes]

                        if id_new[0] != arid:
                            print("Warning: ARID mismatch.")
                        # a_reverse = a_new
                        d_reverse = d_new
                        # d_reverse.reverse()
                    else:
                        # todo: should add id to rd_storage_fn
                        d_reverse = self.rd_storage_fn(araddr_aligned, len_beats)
                        id_new = [arid for _ in d_reverse]

                    axis_frame = AXIStreamFrame(
                        data=d_reverse,
                        tid=id_new,
                        elements_per_beat=beat_bytes,
                        repr_items=self.repr_items,
                    )
                    axis_rdata.send(axis_frame)

        return instances()
