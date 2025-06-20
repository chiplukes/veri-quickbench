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
    AXIStreamFrame,
    AXIStreamSink,
    AXIStreamSource,
    BeatSizeError,
    ElementSizeError,
    axis,
)


def tb_main(
    DATA_WIDTH=32,
    USER_WIDTH=1,
    DEST_WIDTH=1,
    ID_WIDTH=1,
    ELEMENT_SIZE_BITS=8,
    repr_items=-1,
    simlen=10,
    vcdtrace=False,
    stim_fn=None,
):
    """
    Testbench for AXIStreamSource and AXIStreamSink
    """

    @block
    def test():
        print("** Simulation Started **")
        print(
            f"DATA_WIDTH={DATA_WIDTH}, USER_WIDTH={USER_WIDTH}, DEST_WIDTH={DEST_WIDTH}, ID_WIDTH={ID_WIDTH}, ELEMENT_SIZE_BITS={ELEMENT_SIZE_BITS}"
        )
        clk = Signal(bool(1))
        rst = ResetSignal(0, active=1, isasync=True)
        axis_sigs = axis(
            DATA_WIDTH=DATA_WIDTH,
            USER_WIDTH=USER_WIDTH,
            DEST_WIDTH=DEST_WIDTH,
            ID_WIDTH=ID_WIDTH,
            ELEMENT_SIZE_BITS=ELEMENT_SIZE_BITS,
        )

        snd_pause = Signal(bool(0))
        rcv_pause = Signal(bool(0))

        # instantiate the design under test
        m_axis = AXIStreamSource(repr_items=repr_items)
        m_axis_logic = m_axis.create_logic(  # noqa: F841
            clk=clk, rst=rst, axis=axis_sigs, pause=snd_pause, xname="m_axis"
        )

        s_axis = AXIStreamSink(repr_items=repr_items)
        s_axis_logic = s_axis.create_logic(  # noqa: F841
            clk=clk, rst=rst, axis=axis_sigs, pause=rcv_pause, xname="s_axis"
        )

        @always(delay(3))
        def tbclk():
            clk.next = not clk

        @always(clk.posedge)
        def pause_rand():
            snd_pause.next = random.randint(0, 1)
            rcv_pause.next = random.randint(0, 1)

        @instance
        def tbstim():
            yield stim_fn(
                clk=clk,
                m_axis=m_axis,
                s_axis=s_axis,
                simlen=simlen,
                DATA_WIDTH=DATA_WIDTH,
                USER_WIDTH=USER_WIDTH,
                DEST_WIDTH=DEST_WIDTH,
                ID_WIDTH=ID_WIDTH,
                ELEMENT_SIZE_BITS=ELEMENT_SIZE_BITS,
            )
            raise StopSimulation

        return instances()

    tb = test()
    tb.config_sim(backend="myhdl", trace=vcdtrace)
    tb.run_sim()
    tb.quit_sim()
    # delete old vcd files if present, then rename current sim file
    if vcdtrace:
        ifile = "test.vcd"
        ofile = f"DATA_WIDTH_{DATA_WIDTH}_USER_WIDTH_{USER_WIDTH}_DEST_WIDTH_{DEST_WIDTH}_ID_WIDTH_{ID_WIDTH}_ELEMENT_WIDTH_BITS_{ELEMENT_SIZE_BITS}"
        exists = os.path.isfile(ofile)
        if exists:
            os.remove(ofile)
        os.rename(ifile, ofile)

    print("** Simulation Successful **")


def test_frame_init():
    # Testing empty initializer
    frm = AXIStreamFrame()

    # test init from other AXIStreamFrame
    frm1 = AXIStreamFrame(data=[15, 15], element_size_bits=4)
    frm2 = AXIStreamFrame(data=frm1)
    assert frm1 == frm2  # also tests __eq__

    # Testing bytes input, element_size_bits = 8
    d = bytearray([random.randint(0, 255) for _ in range(100)])
    frm = AXIStreamFrame(data=d, element_size_bits=8)
    assert len(frm.data) == len(frm.keep) == len(frm.dest) == len(frm.tid) == len(frm.user) == len(frm.last)
    for i, dexp in enumerate(d):
        assert frm.data[i] == dexp
    assert frm.keep == [1] * len(frm.data)
    assert frm.dest == [0] * len(frm.data)
    assert frm.tid == [0] * len(frm.data)
    assert frm.user == [0] * len(frm.data)
    assert frm.last == [0] * (len(frm.data) - 1) + [1]

    # Testing bytes input, element_size_bits = 16, non default dest, tid, user
    d = bytearray([random.randint(0, 255) for i in range(100)])
    frm = AXIStreamFrame(data=d, dest=1, tid=2, user=3, element_size_bits=16)
    for i in range(0, len(d), 2):
        assert frm.data[i // 2] == int.from_bytes(d[i : i + 2], byteorder="little", signed=False)
    assert len(frm.data) == len(frm.keep) == len(frm.dest) == len(frm.tid) == len(frm.user) == len(frm.last)
    assert frm.keep == [1] * len(frm.data)
    assert frm.dest == [1] * len(frm.data)
    assert frm.tid == [2] * len(frm.data)
    assert frm.user == [3] * len(frm.data)
    assert frm.last == [0] * (len(frm.data) - 1) + [1]

    # Testing bytes input, element_size_bits = 9
    d = [random.randint(0, 2**9 - 1) for i in range(100)]
    frm = AXIStreamFrame(data=d, element_size_bits=9)
    assert len(frm.data) == len(frm.keep) == len(frm.dest) == len(frm.tid) == len(frm.user) == len(frm.last)
    for i, dexp in enumerate(d):
        assert frm.data[i] == dexp
    assert frm.keep == [1] * len(frm.data)
    assert frm.dest == [0] * len(frm.data)
    assert frm.tid == [0] * len(frm.data)
    assert frm.user == [0] * len(frm.data)
    assert frm.last == [0] * (len(frm.data) - 1) + [1]

    # Testing bytes input, element_size_bits = 9, elements_per_beat = 2
    d = [random.randint(0, 2**9 - 1) for i in range(100)]
    frm = AXIStreamFrame(data=d, element_size_bits=9)
    assert len(frm.data) == len(frm.keep) == len(frm.dest) == len(frm.tid) == len(frm.user) == len(frm.last)
    for i, dexp in enumerate(d):
        assert frm.data[i] == dexp


def test_frame_init_exceptions():
    """
    Testing that exceptions are raised for various invalid inputs
    """

    d = bytearray([random.randint(0, 255) for i in range(100)])
    with pytest.raises(ElementSizeError):
        AXIStreamFrame(data=d, element_size_bits=9)
    with pytest.raises(ValueError):
        AXIStreamFrame(data=0, element_size_bits=9)

    with pytest.raises(AssertionError):
        AXIStreamFrame(data=d, keep=[1] * (len(d) + 1), element_size_bits=8)
    with pytest.raises(AssertionError):
        AXIStreamFrame(data=d, dest=[1] * (len(d) + 1), element_size_bits=8)
    with pytest.raises(AssertionError):
        AXIStreamFrame(data=d, tid=[1] * (len(d) + 1), element_size_bits=8)
    with pytest.raises(AssertionError):
        AXIStreamFrame(data=d, user=[1] * (len(d) + 1), element_size_bits=8)
    with pytest.raises(AssertionError):
        AXIStreamFrame(data=d, last=[1] * (len(d) + 1), element_size_bits=8)

    with pytest.raises(ValueError):
        AXIStreamFrame(data=d, keep=[1.1] * (len(d)), element_size_bits=8)
    with pytest.raises(ValueError):
        AXIStreamFrame(data=d, last=[None] * (len(d)), element_size_bits=8)

    with pytest.raises(ValueError):
        AXIStreamFrame(data=d, keep=5, element_size_bits=8)
    with pytest.raises(ValueError):
        AXIStreamFrame(data=d, dest=None, element_size_bits=8)
    with pytest.raises(ValueError):
        AXIStreamFrame(data=d, tid=2.0, element_size_bits=8)
    with pytest.raises(ValueError):
        AXIStreamFrame(data=d, user=1.1, element_size_bits=8)
    with pytest.raises(ValueError):
        AXIStreamFrame(data=d, last=5, element_size_bits=8)


def test_frame_to_beats():
    """
    Testing that to_beats works properly
    """
    d = [i for i in range(4)]
    frm = AXIStreamFrame(data=d, dest=1, user=2, tid=3, element_size_bits=8)
    tdata, tkeep, tdest, tuser, tid, tlast = frm.to_beats()
    assert tdata == [0, 1, 2, 3]
    assert tkeep == [1, 1, 1, 1]
    assert tdest == [1, 1, 1, 1]
    assert tuser == [2, 2, 2, 2]
    assert tid == [3, 3, 3, 3]
    assert tlast == [0, 0, 0, 1]
    frm = AXIStreamFrame(data=d, dest=1, user=2, tid=3, element_size_bits=8, elements_per_beat=2)
    tdata, tkeep, tdest, tuser, tid, tlast = frm.to_beats()
    assert tdata == [0x0100, 0x0302]
    assert tkeep == [3, 3]
    assert tdest == [1, 1]
    assert tuser == [2, 2]
    assert tid == [3, 3]
    assert tlast == [0, 1]
    frm = AXIStreamFrame(
        data=d,
        dest=1,
        user=2,
        tid=3,
        element_size_bits=8,
        elements_per_beat=2,
        endian="big",
    )
    tdata, tkeep, tdest, tuser, tid, tlast = frm.to_beats()
    assert tdata == [0x0001, 0x0203]
    assert tkeep == [3, 3]
    assert tdest == [1, 1]
    assert tuser == [2, 2]
    assert tid == [3, 3]
    assert tlast == [0, 1]

    d = [i for i in range(3)]
    frm = AXIStreamFrame(data=d, dest=1, user=2, tid=3, element_size_bits=8, elements_per_beat=2)
    tdata, tkeep, tdest, tuser, tid, tlast = frm.to_beats()
    assert tdata == [0x0100, 0x0002]
    assert tkeep == [3, 1]
    assert tdest == [1, 1]
    assert tuser == [2, 2]
    assert tid == [3, 3]
    assert tlast == [0, 1]
    frm = AXIStreamFrame(
        data=d,
        dest=1,
        user=2,
        tid=3,
        element_size_bits=8,
        elements_per_beat=2,
        endian="big",
    )
    tdata, tkeep, tdest, tuser, tid, tlast = frm.to_beats()
    assert tdata == [0x0001, 0x0200]
    assert tkeep == [3, 2]
    assert tdest == [1, 1]
    assert tuser == [2, 2]
    assert tid == [3, 3]
    assert tlast == [0, 1]

    d = [i for i in range(6)]

    # test that tdest not consistent for each element within a beat
    with pytest.raises(ValueError):
        frm = AXIStreamFrame(
            data=d,
            dest=[0, 0, 0, 1, 1, 0],
            user=2,
            tid=3,
            element_size_bits=8,
            elements_per_beat=3,
        )
        tdata, tkeep, tdest, tuser, tid, tlast = frm.to_beats()

    # test that user not consistent for each element within a beat
    with pytest.raises(ValueError):
        frm = AXIStreamFrame(
            data=d,
            dest=0,
            user=[0, 1, 0, 1, 1, 1],
            tid=3,
            element_size_bits=8,
            elements_per_beat=3,
        )
        tdata, tkeep, tdest, tuser, tid, tlast = frm.to_beats()

    # test that user not consistent for each element within a beat
    with pytest.raises(ValueError):
        frm = AXIStreamFrame(
            data=d,
            dest=0,
            user=1,
            tid=[1, 1, 0, 1, 1, 1],
            element_size_bits=8,
            elements_per_beat=3,
        )
        tdata, tkeep, tdest, tuser, tid, tlast = frm.to_beats()


def test_frame_from_beats():
    """
    Testing that from_beats works properly
    """
    frm = AXIStreamFrame()
    tdata = [0, 1, 2, 3]
    tkeep = [1, 1, 1, 1]
    tdest = [1, 1, 1, 1]
    tuser = [2, 2, 2, 2]
    tid = [3, 3, 3, 3]
    tlast = [0, 0, 0, 1]
    # test elements_per_beat = 1 and that self.keep,dest,user,tid,last arrays get populated properly
    frm.from_beats(tdata=tdata, tkeep=tkeep, tdest=tdest, tuser=tuser, tid=tid, tlast=tlast)
    assert frm.data == tdata
    assert frm.keep == tkeep
    assert frm.dest == tdest
    assert frm.user == tuser
    assert frm.tid == tid
    assert frm.last == tlast

    # test elements_per_beat = 1 no tkeep, tlast inputs, tdest,tuser,tid assumed to be 0s
    frm.from_beats(tdata=tdata)
    assert frm.data == tdata
    assert frm.keep == tkeep
    assert frm.dest == [0, 0, 0, 0]
    assert frm.user == [0, 0, 0, 0]
    assert frm.tid == [0, 0, 0, 0]
    assert frm.last == tlast

    # test elements_per_beat = 2 and that self.keep,dest,user,tid,last arrays get populated properly
    # last tkeep not full beat
    tdata = [0x1100, 0x3322, 0x5544, 0x7766]
    tkeep = [3, 3, 3, 1]
    frm = AXIStreamFrame(elements_per_beat=2)
    frm.from_beats(tdata=tdata, tkeep=tkeep, tdest=tdest, tuser=tuser, tid=tid, tlast=tlast)
    assert frm.data == [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66]
    assert frm.keep == [1, 1, 1, 1, 1, 1, 1]
    assert frm.dest == [1, 1, 1, 1, 1, 1, 1]
    assert frm.user == [2, 2, 2, 2, 2, 2, 2]
    assert frm.tid == [3, 3, 3, 3, 3, 3, 3]
    assert frm.last == [0, 0, 0, 0, 0, 0, 1]

    # test elements_per_beat = 2 and that self.keep,dest,user,tid,last arrays get populated properly
    # last tkeep not full beat
    # endian = big
    tkeep = [3, 3, 3, 2]
    frm = AXIStreamFrame(elements_per_beat=2, endian="big")
    frm.from_beats(tdata=tdata, tkeep=tkeep, tdest=tdest, tuser=tuser, tid=tid, tlast=tlast)
    assert frm.data == [0x11, 0x00, 0x33, 0x22, 0x55, 0x44, 0x77]
    assert frm.keep == [1, 1, 1, 1, 1, 1, 1]
    assert frm.dest == [1, 1, 1, 1, 1, 1, 1]
    assert frm.user == [2, 2, 2, 2, 2, 2, 2]
    assert frm.tid == [3, 3, 3, 3, 3, 3, 3]
    assert frm.last == [0, 0, 0, 0, 0, 0, 1]

    # test elements_per_beat = 2 and that self.keep,dest,user,tid,last arrays get populated properly
    # only tdata input
    frm = AXIStreamFrame(elements_per_beat=2, endian="little")
    frm.from_beats(tdata=tdata)
    assert frm.data == [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77]
    assert frm.keep == [1, 1, 1, 1, 1, 1, 1, 1]
    assert frm.dest == [0, 0, 0, 0, 0, 0, 0, 0]
    assert frm.user == [0, 0, 0, 0, 0, 0, 0, 0]
    assert frm.tid == [0, 0, 0, 0, 0, 0, 0, 0]
    assert frm.last == [0, 0, 0, 0, 0, 0, 0, 1]

    # test elements_per_beat = 2 and that self.keep has leading zeros
    tdata = [0x1100, 0x3322, 0x5544, 0x7766]
    tkeep = [2, 3, 3, 1]
    frm = AXIStreamFrame(elements_per_beat=2, endian="little")
    frm.from_beats(tdata=tdata, tkeep=tkeep)
    assert frm.data == [0x11, 0x22, 0x33, 0x44, 0x55, 0x66]
    assert frm.keep == [1, 1, 1, 1, 1, 1]
    assert frm.dest == [0, 0, 0, 0, 0, 0]
    assert frm.user == [0, 0, 0, 0, 0, 0]
    assert frm.tid == [0, 0, 0, 0, 0, 0]
    assert frm.last == [0, 0, 0, 0, 0, 1]

    # test elements_per_beat = 2 and that self.keep has leading zeros and capture_leading is True
    tdata = [0x1100, 0x3322, 0x5544, 0x7766]
    tkeep = [2, 3, 3, 1]
    frm = AXIStreamFrame(elements_per_beat=2, endian="little")
    frm.from_beats(tdata=tdata, tkeep=tkeep, capture_leading=True)
    assert frm.data == [0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66]
    assert frm.keep == [0, 1, 1, 1, 1, 1, 1]
    assert frm.dest == [0, 0, 0, 0, 0, 0, 0]
    assert frm.user == [0, 0, 0, 0, 0, 0, 0]
    assert frm.tid == [0, 0, 0, 0, 0, 0, 0]
    assert frm.last == [0, 0, 0, 0, 0, 0, 1]

    # test elements_per_beat = 2 and that self.keep has leading zeros
    tdata = [0x1100, 0x3322, 0x5544, 0x7766]
    tkeep = [1, 3, 3, 2]
    frm = AXIStreamFrame(elements_per_beat=2, endian="big")
    frm.from_beats(tdata=tdata, tkeep=tkeep)
    assert frm.data == [0x00, 0x33, 0x22, 0x55, 0x44, 0x77]
    assert frm.keep == [1, 1, 1, 1, 1, 1]
    assert frm.dest == [0, 0, 0, 0, 0, 0]
    assert frm.user == [0, 0, 0, 0, 0, 0]
    assert frm.tid == [0, 0, 0, 0, 0, 0]
    assert frm.last == [0, 0, 0, 0, 0, 1]

    # test elements_per_beat = 2 and that self.keep has leading zeros and capture_leading is True
    tdata = [0x1100, 0x3322, 0x5544, 0x7766]
    tkeep = [1, 3, 3, 2]
    frm = AXIStreamFrame(elements_per_beat=2, endian="big")
    frm.from_beats(tdata=tdata, tkeep=tkeep, capture_leading=True)
    assert frm.data == [0x11, 0x00, 0x33, 0x22, 0x55, 0x44, 0x77]
    assert frm.keep == [0, 1, 1, 1, 1, 1, 1]
    assert frm.dest == [0, 0, 0, 0, 0, 0, 0]
    assert frm.user == [0, 0, 0, 0, 0, 0, 0]
    assert frm.tid == [0, 0, 0, 0, 0, 0, 0]
    assert frm.last == [0, 0, 0, 0, 0, 0, 1]


def test_frame_from_beats_exceptions():
    """
    Testing that from_beats raises proper exceptions
    """
    frm = AXIStreamFrame(element_size_bits=8, elements_per_beat=1)
    tdata = [0, 1, 2, 3]
    tkeep = [1, 1, 1, 1]
    tdest = [1, 1, 1, 1]
    tuser = [2, 2, 2, 2]
    tid = [3, 3, 3, 3]
    tlast = [0, 0, 0, 1]

    # no data array
    with pytest.raises(ValueError):
        frm.from_beats(tdata=None)

    # length of keep doesn't match length of data
    with pytest.raises(AssertionError):
        frm.from_beats(
            tdata=tdata,
            tkeep=tkeep[:-1],
            tdest=tdest,
            tuser=tuser,
            tid=tid,
            tlast=tlast,
        )

    # length of tdest doesn't match length of data
    with pytest.raises(AssertionError):
        frm.from_beats(
            tdata=tdata,
            tkeep=tkeep,
            tdest=tdest[:-1],
            tuser=tuser,
            tid=tid,
            tlast=tlast,
        )

    # length of tuser doesn't match length of data
    with pytest.raises(AssertionError):
        frm.from_beats(
            tdata=tdata,
            tkeep=tkeep,
            tdest=tdest,
            tuser=tuser[:-1],
            tid=tid,
            tlast=tlast,
        )

    # length of tid doesn't match length of data
    with pytest.raises(AssertionError):
        frm.from_beats(
            tdata=tdata,
            tkeep=tkeep,
            tdest=tdest,
            tuser=tuser,
            tid=tid[:-1],
            tlast=tlast,
        )

    # length of tlast doesn't match length of data
    with pytest.raises(AssertionError):
        frm.from_beats(
            tdata=tdata,
            tkeep=tkeep,
            tdest=tdest,
            tuser=tuser,
            tid=tid,
            tlast=tlast[:-1],
        )

    # test beat too big
    with pytest.raises(BeatSizeError):
        frm.from_beats(tdata=[0, 1, 2, 256])

    # test tdata something other than a list of ints
    with pytest.raises(ValueError):
        frm.from_beats(tdata=5)


def test_frame_to_bytes():
    frm = AXIStreamFrame(data=[0, 1, 2, 3], element_size_bits=9, elements_per_beat=1)
    with pytest.raises(ElementSizeError):
        frm.to_bytes()

    frm = AXIStreamFrame(data=[0, 1, 2, 3], element_size_bits=8, elements_per_beat=1)
    assert frm.to_bytes() == bytearray([0, 1, 2, 3])


def test_frame_eq():
    d = [i for i in range(4)]
    frm1 = AXIStreamFrame(data=d, dest=1, user=2, tid=3, element_size_bits=8)
    frm2 = AXIStreamFrame(data=d, dest=1, user=2, tid=3, element_size_bits=8)
    assert frm1 == frm2

    # different data
    frm2 = AXIStreamFrame(
        data=[i + 1 for i in range(4)],
        dest=0,
        user=2,
        tid=3,
        element_size_bits=8,
    )
    assert frm1 != frm2

    # different dest
    frm2 = AXIStreamFrame(data=d, dest=0, user=2, tid=3, element_size_bits=8)
    assert frm1 != frm2

    # different user
    frm2 = AXIStreamFrame(data=d, dest=1, user=0, tid=3, element_size_bits=8)
    assert frm1 != frm2

    # different tid
    frm2 = AXIStreamFrame(data=d, dest=1, user=2, tid=0, element_size_bits=8)
    assert frm1 != frm2

    # different last
    frm2 = AXIStreamFrame(data=d, dest=1, user=2, tid=3, last=[0, 0, 0, 0], element_size_bits=8)
    assert frm1 != frm2

    # comparison to something other than AXIStreamFrame
    with pytest.raises(TypeError):
        if frm1 == 3:  # noqa: PLR2004
            pass

    frm1 = AXIStreamFrame(data=d, dest=1, user=2, tid=3, allow_trailing=True)

    # different length of data, but allow trailing = True
    frm2 = AXIStreamFrame(data=d, dest=1, user=2, tid=3, allow_trailing=True)
    frm2.data = [*frm2.data, 0]
    assert frm1 == frm2

    # different length of dest, but allow trailing = True
    frm2 = AXIStreamFrame(data=d, dest=1, user=2, tid=3, allow_trailing=True)
    frm2.dest = [*frm2.dest, 0]
    assert frm1 == frm2

    # different length of user, but allow trailing = True
    frm2 = AXIStreamFrame(data=d, dest=1, user=2, tid=3, allow_trailing=True)
    frm2.user = [*frm2.user, 0]
    assert frm1 == frm2

    # different length of tid, but allow trailing = True
    frm2 = AXIStreamFrame(data=d, dest=1, user=2, tid=3, allow_trailing=True)
    frm2.tid = [*frm2.tid, 0]
    assert frm1 == frm2

    # different length of last, but allow trailing = True
    frm2 = AXIStreamFrame(data=d, dest=1, user=2, tid=3, allow_trailing=True)
    frm2.last = [*frm2.last, 0]
    assert frm1 == frm2


def frame_send_receive(
    clk=None,
    m_axis=None,
    s_axis=None,
    simlen=None,
    DATA_WIDTH=None,
    USER_WIDTH=None,
    DEST_WIDTH=None,
    ID_WIDTH=None,
    ELEMENT_SIZE_BITS=None,
):
    for _ in range(simlen):
        data_max = 2**ELEMENT_SIZE_BITS - 1
        d = [random.randint(0, data_max) for _ in range(random.randint(1, 100))]
        dest_max = 2**DEST_WIDTH - 1
        dest_val = random.randint(0, dest_max)
        dest = [dest_val for _ in d]
        tid_max = 2**ID_WIDTH - 1
        tid_val = random.randint(0, tid_max)
        tid = [tid_val for _ in d]
        user_max = 2**USER_WIDTH - 1
        user_val = random.randint(0, user_max)
        user = [user_val for _ in d]

        snd_frm = AXIStreamFrame(
            data=d,
            dest=dest,
            tid=tid,
            user=user,
            elements_per_beat=DATA_WIDTH // ELEMENT_SIZE_BITS,
            element_size_bits=ELEMENT_SIZE_BITS,
        )
        m_axis.send(snd_frm)
        while s_axis.empty():
            yield clk.posedge
        rcv_frm = s_axis.recv()
        assert snd_frm == rcv_frm


def test_streams():
    tb_main(
        DATA_WIDTH=16,
        USER_WIDTH=1,
        DEST_WIDTH=1,
        ID_WIDTH=1,
        ELEMENT_SIZE_BITS=8,
        repr_items=-1,
        simlen=100,
        vcdtrace=False,
        stim_fn=frame_send_receive,
    )
    tb_main(
        DATA_WIDTH=8,
        USER_WIDTH=3,
        DEST_WIDTH=4,
        ID_WIDTH=5,
        ELEMENT_SIZE_BITS=8,
        repr_items=-1,
        simlen=100,
        vcdtrace=False,
        stim_fn=frame_send_receive,
    )
    tb_main(
        DATA_WIDTH=27,
        USER_WIDTH=3,
        DEST_WIDTH=4,
        ID_WIDTH=5,
        ELEMENT_SIZE_BITS=9,
        repr_items=-1,
        simlen=100,
        vcdtrace=False,
        stim_fn=frame_send_receive,
    )


if __name__ == "__main__":
    test_frame_from_beats()
