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

import os
import random

import pytest
from myhdl import (
    ResetSignal,
    Signal,
    StopSimulation,
    always,
    block,
    delay,
    instance,
    instances,
)

from veri_quickbench.tb_endpoints import (
    AXIBusWidthError,
    AXIMaster,
    AXIMemoryError,
    AXISlave,
    AXITransactionError,
    ElementSizeError,
    axi,
)

# def test_source_sink():
#     vcdtrace = True  # controls whether vcd files are created
#     tb(AXI_DATA_WIDTH=32, AXI_ADDR_WIDTH=32, simlen=1, repr_items=0, vcdtrace=vcdtrace)


def test_aximaster_init():
    """
    Testing that exceptions are raised for various invalid inputs
    """
    # data_width not assigned
    with pytest.raises(TypeError):
        AXIMaster(data_width=None)

    # addr_width not assigned
    with pytest.raises(TypeError):
        AXIMaster(data_width=None)

    # data_width not an integer
    with pytest.raises(TypeError):
        AXIMaster(data_width=1.1)

    # addr_width not an integer
    with pytest.raises(TypeError):
        AXIMaster(data_width=8, addr_width=1.1)

    # data_width not a multiple of 8
    with pytest.raises(ElementSizeError):
        AXIMaster(data_width=9)

    AXIMaster(data_width=32, addr_width=32)


def test_aximaster_issue_write():
    """
    Testing issue_write()
    """
    axi_m = AXIMaster(data_width=32, addr_width=32, allow_narrow=False, allow_unaligned=False)

    # data something other than int, bytearray, array of ints
    with pytest.raises(TypeError):
        axi_m.issue_write(addr=0, data=1.1, tid=0)

    # data is int, but too big
    with pytest.raises(ElementSizeError):
        axi_m.issue_write(addr=0, data=256, tid=0)

    # data is list of ints, but too big
    with pytest.raises(ElementSizeError):
        axi_m.issue_write(addr=0, data=[0, 1, 2, 300], tid=0)

    # data is list but not of ints
    with pytest.raises(TypeError):
        axi_m.issue_write(addr=0, data=[0.5, 1.1], tid=0)

    # unaligned address write with allow_unaligned=False, should fail
    with pytest.raises(AXITransactionError):
        axi_m.issue_write(addr=1, data=[1, 1], tid=0)

    # aligned address but narrow write with allow_narrow=False, should fail
    with pytest.raises(AXITransactionError):
        axi_m.issue_write(addr=0, data=[1], tid=0)
    with pytest.raises(AXITransactionError):
        axi_m.issue_write(addr=0, data=[1, 1], tid=0)
    with pytest.raises(AXITransactionError):
        axi_m.issue_write(addr=0, data=[1, 1, 1], tid=0)
    with pytest.raises(AXITransactionError):
        axi_m.issue_write(addr=0, data=[1, 1, 1, 1, 1], tid=0)

    # aligned 2 beats
    din = [0, 1, 2, 3, 4, 5, 6, 7]
    axi_m.issue_write(addr=0, data=din)
    (adr, d, wstrb, tid, awlen) = axi_m.wqueue.pop(0)
    assert adr == 0
    assert d == din
    assert wstrb == [1 for _ in din]
    assert tid == 0
    assert awlen == 1

    # aligned 1 beat
    din = [0, 1, 2, 3]
    axi_m.issue_write(addr=0, data=din)
    (adr, d, wstrb, tid, awlen) = axi_m.wqueue.pop(0)
    assert adr == 0
    assert d == din
    assert wstrb == [1 for _ in din]
    assert tid == 0
    assert awlen == 0

    # allow narrow bursts
    axi_m = AXIMaster(data_width=32, addr_width=32, allow_narrow=True, allow_unaligned=True)

    # aligned 1 + partial beat
    din = [0, 1, 2, 3, 4, 5]
    axi_m.issue_write(addr=0, data=din)
    (adr, d, wstrb, tid, awlen) = axi_m.wqueue.pop(0)
    assert adr == 0
    assert d == din
    assert wstrb == [1 for _ in din]
    assert tid == 0
    assert awlen == 1

    # unaligned 1 beat
    din = [0, 1, 2]
    axi_m.issue_write(addr=1, data=din, tid=2)
    (adr, d, wstrb, tid, awlen) = axi_m.wqueue.pop(0)
    assert adr == 0
    assert d == [0, *din]
    assert wstrb == [0] + [1 for _ in din]
    assert tid == 2  # noqa: PLR2004
    assert awlen == 0

    # unaligned 2 beats
    axi_m = AXIMaster(data_width=32, addr_width=32, allow_narrow=True, allow_unaligned=True)
    din = [0, 1, 2, 3]
    axi_m.issue_write(addr=1, data=din, tid=3)
    (adr, d, wstrb, tid, awlen) = axi_m.wqueue.pop(0)
    assert adr == 0
    assert d == [0, *din]
    assert wstrb == [0] + [1 for _ in din]
    assert tid == 3  # noqa: PLR2004
    assert awlen == 1

    # todo: add more tests here


def test_aximaster_issue_read():
    """
    Testing issue_read()
    """
    axi_m = AXIMaster(data_width=32, addr_width=32, allow_narrow=False)
    # read address should be aligned to data_width
    with pytest.raises(AXITransactionError):
        axi_m.issue_read(addr=1, len_beats=1, arid=0)

    # read length in beats should be >= 1
    with pytest.raises(AXITransactionError):
        axi_m.issue_read(addr=0, len_beats=0, arid=0)


def test_aximaster_create_logic():
    """
    test create_logic()
    """

    # data mismatch between data_width and connected wd rd axi channels
    axi_m = AXIMaster(data_width=32, addr_width=32, allow_narrow=False)
    axi_sigs = axi(AXI_ADDR_WIDTH=32, AXI_DATA_WIDTH=16)
    with pytest.raises(AXIBusWidthError):
        axi_m_logic = axi_m.create_logic(
            clk=Signal(bool(0)),
            rst=Signal(bool(0)),
            axi=axi_sigs,
            pause_waddr=Signal(bool(0)),
            pause_wdata=Signal(bool(0)),
            pause_bresp=Signal(bool(0)),
            pause_araddr=Signal(bool(0)),
            pause_rdata=Signal(bool(0)),
            xname="axi master",
        )

    # address mismatch between addr_width and connected axi channels
    axi_m = AXIMaster(data_width=32, addr_width=32, allow_narrow=False)
    axi_sigs = axi(AXI_ADDR_WIDTH=16, AXI_DATA_WIDTH=32)
    with pytest.raises(AXIBusWidthError):
        axi_m_logic = axi_m.create_logic(  # noqa: F841
            clk=Signal(bool(0)),
            rst=Signal(bool(0)),
            axi=axi_sigs,
            pause_waddr=Signal(bool(0)),
            pause_wdata=Signal(bool(0)),
            pause_bresp=Signal(bool(0)),
            pause_araddr=Signal(bool(0)),
            pause_rdata=Signal(bool(0)),
            xname="axi master",
        )


def test_axislave_init():
    """
    Testing that exceptions are raised for various invalid inputs
    """
    # data_width not assigned
    with pytest.raises(TypeError):
        AXISlave(data_width=None)

    # addr_width not assigned
    with pytest.raises(TypeError):
        AXISlave(data_width=None)

    # data_width not an integer
    with pytest.raises(TypeError):
        AXISlave(data_width=1.1)

    # addr_width not an integer
    with pytest.raises(TypeError):
        AXISlave(data_width=8, addr_width=1.1)

    # data_width not a multiple of 8
    with pytest.raises(ElementSizeError):
        AXISlave(data_width=9)

    AXISlave(data_width=32, addr_width=32)


def test_axislave_load():
    """
    Testing load()
    """
    axi_s = AXISlave(data_width=32, addr_width=32)

    # data something other than int, bytearray, array of ints
    with pytest.raises(TypeError):
        axi_s.load(addr=0, data=1.1, tid=0)

    # data is int, but too big
    with pytest.raises(ElementSizeError):
        axi_s.load(addr=0, data=256, tid=0)

    # data is list of ints, but too big
    with pytest.raises(ElementSizeError):
        axi_s.load(addr=0, data=[0, 1, 2, 300], tid=0)

    # data is list but not of ints
    with pytest.raises(TypeError):
        axi_s.load(addr=0, data=[0.5, 1.1], tid=0)

    # addr is list but does not match data length
    with pytest.raises(AXIMemoryError):
        axi_s.load(addr=[0, 1, 2], data=[0, 1, 2, 3], tid=0)

    # addr is list but has non integer element
    with pytest.raises(TypeError):
        axi_s.load(addr=[0, 1, 2, 3.1], data=[0, 1, 2, 3], tid=0)

    # addr is not a list, but also non-integer
    with pytest.raises(TypeError):
        axi_s.load(addr=3.1, data=[0, 1, 2, 3], tid=0)

    # tid is list but does not match data length
    with pytest.raises(AXIMemoryError):
        axi_s.load(addr=0, data=[0, 1, 2, 3], tid=[0, 1, 2])

    # tid is list but has non integer element
    with pytest.raises(TypeError):
        axi_s.load(addr=0, data=[0, 1, 2, 3], tid=[0, 1, 2, 3.1])

    # tid is not a list, but also non-integer
    with pytest.raises(TypeError):
        axi_s.load(addr=0, data=[0, 1, 2, 3], tid=0.5)

    # wsrtb is list but does not match data length
    with pytest.raises(AXIMemoryError):
        axi_s.load(addr=0, data=[0, 1, 2, 3], tid=0, wstrb=[1, 0, 1])

    # tid is not a list, but also non-integer
    with pytest.raises(TypeError):
        axi_s.load(addr=0, data=[0, 1, 2, 3], tid=0, wstrb=0.4)

    # load bytearray to address
    din = [0, 1, 2, 3]
    axi_s = AXISlave(data_width=32, addr_width=32)
    axi_s.load(addr=0, data=bytearray(din), tid=1)
    assert axi_s.a == din
    assert axi_s.d == din
    assert axi_s.tid == [1 for _ in din]

    # load data list to address
    din = [4, 5, 6, 7]
    axi_s = AXISlave(data_width=32, addr_width=32)
    axi_s.load(addr=4, data=din, tid=2)
    assert axi_s.a == din
    assert axi_s.d == din
    assert axi_s.tid == [2 for _ in din]

    # load data list to address
    axi_s = AXISlave(data_width=32, addr_width=32)
    axi_s.load(addr=[0, 1, 2, 3], data=[4, 5, 6, 7], tid=[8, 9, 10, 11])
    assert axi_s.a == [0, 1, 2, 3]
    assert axi_s.d == [4, 5, 6, 7]
    assert axi_s.tid == [8, 9, 10, 11]

    # load data list to address, but not last element
    axi_s = AXISlave(data_width=32, addr_width=32)
    axi_s.load(
        addr=[0, 1, 2, 3],
        data=[4, 5, 6, 7],
        tid=[8, 9, 10, 11],
        wstrb=[1, 1, 1, 0],
    )
    assert axi_s.a == [0, 1, 2]
    assert axi_s.d == [4, 5, 6]
    assert axi_s.tid == [8, 9, 10]

    # load data list to address, but only last byte
    axi_s = AXISlave(data_width=32, addr_width=32)
    axi_s.load(
        addr=[0, 1, 2, 3],
        data=[4, 5, 6, 7],
        tid=[8, 9, 10, 11],
        wstrb=[0, 0, 0, 1],
    )
    assert axi_s.a == [3]
    assert axi_s.d == [7]
    assert axi_s.tid == [11]


def test_axislave_create_logic():
    """
    Testing create_logic()
    """

    # data mismatch between data_width and connected wd rd axi channels
    axi_s = AXISlave(data_width=32, addr_width=32)
    axi_sigs = axi(AXI_ADDR_WIDTH=32, AXI_DATA_WIDTH=16)
    with pytest.raises(AXIBusWidthError):
        axi_s_logic = axi_s.create_logic(
            clk=Signal(bool(0)),
            rst=Signal(bool(0)),
            axi=axi_sigs,
            pause_waddr=Signal(bool(0)),
            pause_wdata=Signal(bool(0)),
            pause_bresp=Signal(bool(0)),
            pause_araddr=Signal(bool(0)),
            pause_rdata=Signal(bool(0)),
            xname="axi slave",
        )

    # address mismatch between addr_width and connected axi channels
    axi_s = AXISlave(data_width=32, addr_width=32)
    axi_sigs = axi(AXI_ADDR_WIDTH=16, AXI_DATA_WIDTH=32)
    with pytest.raises(AXIBusWidthError):
        axi_s_logic = axi_s.create_logic(  # noqa: F841
            clk=Signal(bool(0)),
            rst=Signal(bool(0)),
            axi=axi_sigs,
            pause_waddr=Signal(bool(0)),
            pause_wdata=Signal(bool(0)),
            pause_bresp=Signal(bool(0)),
            pause_araddr=Signal(bool(0)),
            pause_rdata=Signal(bool(0)),
            xname="axi slave",
        )


def tb(
    AXI_ADDR_WIDTH=32,
    AXI_DATA_WIDTH=32,
    AXI_ID_WIDTH=8,
    repr_items=-1,
    simlen=10,
    vcdtrace=False,
):
    """
    Testbench for AXIMaster and AXISlave
    """

    @block
    def test():
        print("** Simulation Started **")
        print(
            f"AXI_ADDR_WIDTH={AXI_ADDR_WIDTH}, AXI_DATA_WIDTH={AXI_DATA_WIDTH}, simlen={simlen}, repr_items={repr_items}"
        )
        clk = Signal(bool(1))
        rst = ResetSignal(0, active=1, isasync=True)
        axi_sigs = axi(
            AXI_ADDR_WIDTH=AXI_ADDR_WIDTH,
            AXI_DATA_WIDTH=AXI_DATA_WIDTH,
            AXI_ID_WIDTH=AXI_ID_WIDTH,
        )

        PAUSE_FACTOR = 4  # will pause 1/PAUSE_FACTOR
        pause_araddr = Signal(bool(0))
        pause_rdata = Signal(bool(0))
        pause_awaddr = Signal(bool(0))
        pause_wdata = Signal(bool(0))
        pause_bresp = Signal(bool(0))

        @instance
        def randPause():
            while 1:
                pause_araddr.next = random.randint(1, PAUSE_FACTOR) == 1
                pause_rdata.next = random.randint(1, PAUSE_FACTOR) == 1
                pause_awaddr.next = random.randint(1, PAUSE_FACTOR) == 1
                pause_wdata.next = random.randint(1, PAUSE_FACTOR) == 1
                pause_bresp.next = random.randint(1, PAUSE_FACTOR) == 1
                yield clk.posedge

        axi_m = AXIMaster(
            data_width=AXI_DATA_WIDTH,
            addr_width=AXI_ADDR_WIDTH,
            allow_narrow=True,
            allow_unaligned=True,
            repr_items=repr_items,
        )
        axi_m_logic = axi_m.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axi=axi_sigs,
            pause_waddr=pause_awaddr,
            pause_wdata=pause_wdata,
            pause_bresp=pause_bresp,
            pause_araddr=pause_araddr,
            pause_rdata=pause_rdata,
            xname="axi master",
        )

        axi_s = AXISlave(
            data_width=AXI_DATA_WIDTH,
            addr_width=AXI_ADDR_WIDTH,
            allow_narrow=True,
            repr_items=repr_items,
        )
        axi_s_logic = axi_s.create_logic(  # noqa: F841
            clk=clk,
            rst=rst,
            axi=axi_sigs,
            pause_waddr=pause_awaddr,
            pause_wdata=pause_wdata,
            pause_bresp=pause_bresp,
            pause_araddr=pause_araddr,
            pause_rdata=pause_rdata,
            xname="axi slave",
        )

        @always(delay(3))
        def tbclk():
            clk.next = not clk

        @instance
        def tbstim():  # noqa: PLR0912
            # testbench stimulus
            rst.next = rst.active
            yield clk.posedge
            yield clk.posedge
            rst.next = not rst.active
            yield clk.posedge
            yield clk.posedge

            # test read_storage_fn

            # test narrow writes master to slave
            for i in range(1, simlen, 1):
                din = list(range(0, i, 1))
                tid = random.randint(0, 2**AXI_ID_WIDTH - 1)
                axi_m.issue_write(addr=i, data=din, tid=tid)
                while not axi_m.write_empty():
                    yield clk.posedge
                for _ in range(100):
                    yield clk.posedge  # wait a few more cycles for transaction to finish

                for _ in range(20):
                    yield clk.posedge  # wait a few more cycles for transaction to finish
                # get log of data expected
                wr_a_actual, wr_d_actual, wr_tid_actual = axi_s.get_write_log()
                assert wr_a_actual == [d + i for d in din]
                assert wr_d_actual == din
                assert wr_tid_actual == [tid for _ in din]
                axi_s.clear()

            # test m_axi read from s_axi (loaded manually)
            axi_s.clear()
            axi_s.load(
                addr=[i for i in range(256)],
                data=[i for i in range(256)],
                tid=0xA,
            )
            for i in range(1, 10, 1):
                axi_m.clear()
                axi_m.issue_read(addr=0, len_beats=i, arid=0xA)

                while 1:
                    if axi_sigs.rvalid and axi_sigs.rready and axi_sigs.rlast:
                        break
                    yield clk.posedge
                yield clk.posedge
                yield clk.posedge
                rd_a_actual, rd_d_actual, rd_tid_actual = axi_m.get_read_log()
                print(i, rd_a_actual, rd_d_actual, rd_tid_actual)
                assert rd_a_actual == [d for d in range(4 * i)]
                assert rd_d_actual == [d for d in range(4 * i)]
                assert rd_tid_actual == [0xA for _ in range(4 * i)]
            axi_m.clear()

            # test m_axi read from s_axi (using rd_storage_fn)
            print("here")

            def rd_storage_fn(adr, num_beats):
                """
                function to return data from fake sdram
                returns array of rdata beats
                """
                data_beats = [adr + d for d in range(4 * num_beats)]
                return data_beats

            axi_s.rd_storage_fn = rd_storage_fn
            axi_s.clear()
            for i in range(1, 10, 1):
                axi_m.clear()
                axi_m.issue_read(addr=0, len_beats=i, arid=0xA)
                while 1:
                    if axi_sigs.rvalid and axi_sigs.rready and axi_sigs.rlast:
                        break
                    yield clk.posedge
                yield clk.posedge
                yield clk.posedge
                rd_a_actual, rd_d_actual, rd_tid_actual = axi_m.get_read_log()
                print(i, rd_a_actual, rd_d_actual, rd_tid_actual)
                assert rd_a_actual == [d for d in range(4 * i)]
                assert rd_d_actual == [d for d in range(4 * i)]
                assert rd_tid_actual == [0xA for _ in range(4 * i)]

            # test unaligned reads work
            axi_s.rd_storage_fn = None
            axi_m.allow_unaligned = True
            axi_s.allow_unaligned = True
            axi_s.clear()
            axi_s.load(
                addr=[i for i in range(256)],
                data=[i for i in range(256)],
                tid=0xA,
            )
            axi_m.clear()
            axi_m.clear()
            axi_m.issue_read(addr=1, len_beats=1, arid=0xA)
            while 1:
                if axi_sigs.rvalid and axi_sigs.rready and axi_sigs.rlast:
                    break
                yield clk.posedge
            yield clk.posedge
            axi_m.clear()

            # test that fill works for reads of data not contained in self.a self.d
            axi_s.fill = 0xDC
            axi_s.clear()
            axi_s.load(addr=[1, 2, 3], data=[1, 2, 3], tid=0xA)
            axi_m.clear()
            axi_m.issue_read(addr=1, len_beats=1, arid=0xA)
            while 1:
                if axi_sigs.rvalid and axi_sigs.rready and axi_sigs.rlast:
                    break
                yield clk.posedge
            yield clk.posedge
            yield clk.posedge
            rd_a_actual, rd_d_actual, rd_tid_actual = axi_m.get_read_log()
            print(f"{rd_a_actual=}, {rd_d_actual=}, {rd_tid_actual=}")
            assert rd_a_actual == [0, 1, 2, 3]
            assert rd_d_actual == [0xDC, 1, 2, 3]
            assert rd_tid_actual == [0xA, 0xA, 0xA, 0xA]

            # test unaligned reads fail
            axi_m.allow_unaligned = True
            axi_s.allow_unaligned = True
            print("pre exception")
            # with pytest.raises(AXITransactionError):
            axi_s.clear()
            axi_s.load(
                addr=[i for i in range(256)],
                data=[i for i in range(256)],
                tid=0xA,
            )
            axi_m.clear()
            axi_m.issue_read(addr=1, len_beats=i, arid=0xA)
            yield clk.posedge
            yield clk.posedge
            yield clk.posedge
            axi_m.clear()

            # # beat align address and disallow overlaps
            yield delay(1000)
            raise StopSimulation

        return instances()

    tb = test()
    tb.config_sim(backend="myhdl", trace=vcdtrace)
    tb.run_sim()
    tb.quit_sim()
    # delete old vcd files if present, then rename current sim file
    if vcdtrace:
        ifile = "test.vcd"
        ofile = f"AXI_ADDR_WIDTH_{AXI_DATA_WIDTH}_AXI_ADDR_WIDTH_{AXI_ADDR_WIDTH}_simlen_{simlen}.vcd"
        exists = os.path.isfile(ofile)
        if exists:
            os.remove(ofile)
        os.rename(ifile, ofile)
    print("** Simulation Successful **")


# test that axi transactions work from master to slave
def test_aximaster_to_axislave():
    tb(
        AXI_DATA_WIDTH=32,
        AXI_ADDR_WIDTH=32,
        simlen=10,
        repr_items=-1,
        vcdtrace=True,
    )


if __name__ == "__main__":
    # simulation setup
    repr_items = 0
    simlen = 10  # number axi packets sent in simulation
    vcdtrace = True  # controls whether vcd files are created
    tb(
        AXI_DATA_WIDTH=32,
        AXI_ADDR_WIDTH=32,
        simlen=10,
        repr_items=0,
        vcdtrace=vcdtrace,
    )
