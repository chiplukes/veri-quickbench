"""

Copyright (c) 2014-2016 Alex Forencich

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

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

import copy

from myhdl import (
    Signal,
    always_comb,
    block,
    instance,
    instances,
)

from ._intfc import axis as axis_iface


class ElementSizeError(Exception):
    pass


class BeatSizeError(Exception):
    pass


class AXIStreamFrame(object):  # noqa: PLW1641
    def __init__(  # noqa: PLR0912, PLR0913, PLR0915
        self,
        data=None,
        keep=None,
        dest=0,
        tid=0,
        user=0,
        last=None,
        elements_per_beat=1,
        element_size_bits=8,
        repr_items=-1,
        allow_trailing=False,
        endian="little",
    ):
        """
        Takes the following and converts to axi beats:
        data - can be one of the following:
                - bytearray if element size is multiple of 8 bits
                - array of elements
        keep - can be one of the following:
                - None, init will create keep array based on length of data and elements_per_beat
                - array of 1,0,bool of same length as data
        tdest   - can be one of the following:
                - integer, init will create tdest array based on length of data and elements_per_beat
                - array of ints of same length as data
        tid  - can be one of the following:
                - integer, init will create tid array based on length of data and elements_per_beat
                - array of ints of same length as data
        user - can be one of the following:
                - integer, init will create user array based on length of data and elements_per_beat
                - array of ints of same length as data
        last - can be one of the following:
                - None, init will create tlast array based on length of data and elements_per_beat, zeros until last beat
                - array of ints of same length as data
        element_size_bits - size in bits of each element within an axi beat.
        elements_per_beat - number of elements within an axi beat
        repr_items - number of items to print in data, keep, etc. arrays when printing an AXIStreamFrame, -1=full, 0=none
        allow_trailing - if True, then data comparison allows one object to have trailing data
        endian - controls placement of element within axi beat
                    - 'little' - first data element stored in lower portion of first axi beat
                    - 'big' - first data element stored in upper portion of first axi beat
        """

        self.elements_per_beat = elements_per_beat
        self.element_size_bits = element_size_bits
        self.element_max = 2 ** (element_size_bits) - 1
        self.beat_max = 2 ** (element_size_bits * elements_per_beat) - 1
        self.data = []
        self.keep = []
        self.dest = []
        self.tid = []
        self.user = []
        self.last = []
        self.repr_items = repr_items
        self.allow_trailing = allow_trailing
        self.endian = endian

        if type(data) is AXIStreamFrame:
            self.elements_per_beat = data.elements_per_beat
            self.element_size_bits = data.element_size_bits
            self.element_max = data.element_max
            self.beat_max = data.beat_max
            self.data = data.data
            self.keep = data.keep
            self.dest = data.dest
            self.tid = data.tid
            self.user = data.user
            self.last = data.last
            self.repr_items = data.repr_items
            self.allow_trailing = data.allow_trailing
            self.endian = data.endian
        else:
            if isinstance(data, (bytes, bytearray)):
                if self.element_size_bits % 8 != 0:
                    raise ElementSizeError("data is bytes like, element size not a byte multiple.")
                element_size_bytes = element_size_bits // 8
                for i in range(0, len(data), element_size_bytes):
                    self.data.append(
                        int.from_bytes(
                            data[i : i + element_size_bytes],
                            byteorder="little",
                            signed=False,
                        )
                    )  # always assume little endian here?
            elif isinstance(data, (list,)):
                for d in data:
                    if d > self.element_max:
                        raise ElementSizeError(f"{hex(d)} in data > element_size_bits({self.element_size_bits})")
                self.data = data
            elif data is not None:
                raise ValueError("data is not bytes object or list of elements")

            if keep is None:
                self.keep = [1 for _ in self.data]
            elif isinstance(keep, (list,)):
                if len(keep) != len(self.data):
                    raise AssertionError("keep array must match length of data array")
                for _, k in enumerate(keep):
                    if k in [1, 0, True, False]:
                        self.keep.append(int(k))
                    else:
                        raise ValueError("keep entries should be 1,0,True,False")
            else:
                raise ValueError("keep should be None or list of ints/bools")

            if isinstance(dest, (int,)):
                self.dest = [dest for _ in self.data]
            elif isinstance(dest, (list,)):
                if len(dest) != len(self.data):
                    raise AssertionError("dest array must match length of data array")
                self.dest = dest
            else:
                raise ValueError("dest should be int or list of ints")

            if isinstance(tid, (int,)):
                self.tid = [tid for _ in self.data]
            elif isinstance(tid, (list,)):
                if len(tid) != len(self.data):
                    raise AssertionError("tid array must match length of data array")
                self.tid = tid
            else:
                raise ValueError("tid should be int or list of ints")

            if isinstance(user, (int,)):
                self.user = [user for _ in self.data]
            elif isinstance(user, (list,)):
                if len(user) != len(self.data):
                    raise AssertionError("user array must match length of data array")
                self.user = user
            else:
                raise ValueError("user should be int or list of ints")

            if last is None:
                self.last = [0 for _ in self.data]
                if self.last:
                    self.last[-1] = 1
            elif isinstance(last, (list,)):
                if len(last) != len(self.data):
                    raise AssertionError("last array must match length of data array")
                for _, k in enumerate(last):
                    if k in [1, 0, True, False]:
                        self.last.append(int(k))
                    else:
                        raise ValueError("last entries should be 1,0,True,False")
            else:
                raise ValueError("last should be None or list of ints/bools")

    def clear(self):
        """
        clears data,keep,dest,tid,user,last arrays
        """
        self.data = []
        self.keep = []
        self.dest = []
        self.tid = []
        self.user = []
        self.last = []

    def to_beats(self):
        """
        returns tdata, tkeep, tdest, tuser, tid, tlast arrays of beats
        """
        tdata = []
        tkeep = []
        tdest = []
        tid = []
        tuser = []
        tlast = []
        j = 0
        data = 0
        keep = 0
        tdest_beat = set()
        tid_beat = set()
        tuser_beat = set()
        for i, d in enumerate(self.data):
            if self.endian == "little":
                data = data | (d << (j * self.element_size_bits))
                keep = keep | (self.keep[i] << j)
            else:
                data = data | (d << ((self.elements_per_beat - j - 1) * self.element_size_bits))
                keep = keep | (self.keep[i] << (self.elements_per_beat - j - 1))
            tdest_beat.add(self.dest[i])
            tid_beat.add(self.tid[i])
            tuser_beat.add(self.user[i])
            j += 1
            if j >= self.elements_per_beat or i == (len(self.data) - 1):
                tdata.append(data)
                tkeep.append(keep)
                tlast.append(self.last[i])

                if len(tdest_beat) != 1:
                    raise ValueError("dest must match for all elements within a beat")
                else:
                    tdest.append(tdest_beat.pop())

                if len(tid_beat) != 1:
                    raise ValueError("tid must match for all elements within a beat")
                else:
                    tid.append(tid_beat.pop())

                if len(tuser_beat) != 1:
                    raise ValueError("tuser must match for all elements within a beat")
                else:
                    tuser.append(tuser_beat.pop())
                data = 0
                keep = 0
                j = 0
        return tdata, tkeep, tdest, tuser, tid, tlast

    def from_beats(  # noqa: PLR0912, PLR0913, PLR0915
        self,
        tdata,
        tkeep=None,
        tdest=None,
        tuser=None,
        tid=None,
        tlast=None,
        capture_leading=False,
        capture_trailing=False,
    ):
        """
        takes tdata, tkeep, tdest, tuser, tid, tlast arrays of beats and converts to AXIStreamFrame
        capture_leading - capture elements with keep=0 bits during first beat
        capture_leading - capture elements with keep=0 bits during last beat
        """

        if capture_trailing is not False:
            raise NotImplementedError("Not implemented yet!")

        mask = 2**self.element_size_bits - 1

        if tdata is None or not isinstance(tdata, (list,)):
            raise ValueError("tdata must be defined and must be a list")
        else:
            if tdest is not None:
                if len(tdest) != len(tdata):
                    raise AssertionError("length of tdest and tdata arrays must be the same")
            if tuser is not None:
                if len(tuser) != len(tdata):
                    raise AssertionError("length of tuser and tdata arrays must be the same")
            if tid is not None:
                if len(tid) != len(tdata):
                    raise AssertionError("length of tid and tdata arrays must be the same")
            if tlast is not None:
                if len(tlast) != len(tdata):
                    raise AssertionError("length of tlast and tdata arrays must be the same")
            self.data = []
            self.dest = []
            self.user = []
            self.tid = []
            self.last = []
            self.keep = []

            if tkeep is None:
                keep_full = 2**self.elements_per_beat - 1
                tkeep = [keep_full for _ in tdata]  # just make a keep vector so below code works

            if len(tkeep) != len(tdata):
                raise AssertionError("length of tkeep and tdata arrays must be the same")
            for i, d in enumerate(tdata):
                if d > self.beat_max:
                    raise BeatSizeError(f"{d} in tdata > element_size_bits({self.element_size_bits})")
                set_last = False
                for j in range(self.elements_per_beat):
                    k = False
                    if self.endian == "little":
                        kv = (tkeep[i] >> j) & 1
                        if kv or ((i == 0) and capture_leading):
                            self.data.append((d >> (j * self.element_size_bits)) & mask)
                            k = True
                    else:
                        kv = (tkeep[i] >> (self.elements_per_beat - j - 1)) & 0x1
                        if kv or ((i == 0) and capture_leading):
                            self.data.append((d >> ((self.elements_per_beat - j - 1) * self.element_size_bits)) & mask)
                            k = True
                    if k:
                        self.keep.append(kv)
                        if tdest:
                            self.dest.append(tdest[i])
                        else:
                            self.dest.append(0)
                        if tuser:
                            self.user.append(tuser[i])
                        else:
                            self.user.append(0)
                        if tid:
                            self.tid.append(tid[i])
                        else:
                            self.tid.append(0)

                        # this gets a little tricky
                        self.last.append(0)
                        if tlast is not None and tlast[i]:
                            set_last = True
                if set_last:
                    self.last[-1] = 1
            if tlast is None:
                self.last[-1] = 1

    def to_bytes(self):
        """
        returns bytearray of self.data
        """
        if self.element_size_bits != 8:  # noqa: PLR2004
            raise ElementSizeError("to_bytes needs element_size_bits to be 8.")
        else:
            return bytearray(self.data)

    def to_elements(self, endian="little"):
        """
        returns array of self.data in individual elements
        """
        mask = 2**self.element_size_bits - 1
        d_array = []
        for i, d in enumerate(self.data):
            for e in range(self.elements_per_beat):
                if endian == "little":
                    if self.keep[i] & (1 << e):
                        d_array.append((d >> (self.element_size_bits * e)) & mask)
                elif self.keep[i] & (1 << (self.elements_per_beat - e - 1)):
                    d_array.append((d >> (self.element_size_bits * (self.elements_per_beat - e - 1))) & mask)
        return d_array

    def __eq__(self, other):  # noqa: PLR0912
        if not isinstance(other, (AXIStreamFrame,)):
            raise TypeError("Objects being compared must be of type AXIStreamFrame.")

        # check keep
        # allow special case when one axi stream has some trailing don't
        if self.allow_trailing is True or other.allow_trailing is True:
            self_len = len(self.keep)
            other_len = len(other.keep)
            klen = min(self_len, other_len)
        else:
            klen = len(self.keep)
        keep_match = self.keep[0:klen] == other.keep[0:klen]

        # check dest
        # allow special case when one axi stream has some trailing don't care keeps
        if self.allow_trailing is True or other.allow_trailing is True:
            self_len = len(self.dest)
            other_len = len(other.dest)
            dstlen = min(self_len, other_len)
        else:
            dstlen = len(self.dest)
        dest_match = self.dest[0:dstlen] == other.dest[0:dstlen]

        # check user
        # allow special case when one axi stream has some trailing don't care keeps
        if self.allow_trailing is True or other.allow_trailing is True:
            self_len = len(self.user)
            other_len = len(other.user)
            userlen = min(self_len, other_len)
        else:
            userlen = len(self.tid)
        user_match = self.user[0:userlen] == other.user[0:userlen]

        # check tid
        # allow special case when one axi stream has some trailing don't care keeps
        if self.allow_trailing is True or other.allow_trailing is True:
            self_len = len(self.tid)
            other_len = len(other.tid)
            tidlen = min(self_len, other_len)
        else:
            tidlen = len(self.tid)
        tid_match = self.tid[0:tidlen] == other.tid[0:tidlen]

        # check last
        # allow special case when one axi stream has some trailing don't care keeps
        if self.allow_trailing is True or other.allow_trailing is True:
            self_len = len(self.last)
            other_len = len(other.last)
            lastlen = min(self_len, other_len)
        else:
            lastlen = len(self.last)
        last_match = self.last[0:lastlen] == other.last[0:lastlen]

        # check data
        # allow special case when one axi stream has some trailing don't care data
        if self.allow_trailing is True or other.allow_trailing is True:
            self_len = len(self.data)
            other_len = len(other.data)
            dlen = min(self_len, other_len)
        else:
            dlen = len(self.data)
        data_match = self.data[0:dlen] == other.data[0:dlen]

        return data_match and keep_match and dest_match and user_match and tid_match and last_match

    def __repr__(self):
        """
        This could use a little more work...
        """
        if self.repr_items == 0:
            return ""
        elif self.repr_items == -1:
            rlen = len(self.data)
        else:
            rlen = min(self.repr_items, len(self.data))
        keep = "\n\tkeep={}".format(repr(self.keep[:rlen]))
        dest = "\n\tdest={}".format(repr(self.dest[:rlen]))
        tid = "\n\ttid={}".format(repr(self.tid[:rlen]))
        user = "\n\tuser={}".format(repr(self.user[:rlen]))
        data = "\n\tdata={}".format(repr(self.data[:rlen]))
        return "AXIStreamFrame" + data + keep + dest + user + tid

    def __iter__(self):
        return self.data.__iter__()


class AXIStreamSource(object):
    def __init__(self, repr_items=-1, elements_per_beat=None, element_size_bits=None):
        self.has_logic = False
        self.queue = []
        self.repr_items = repr_items
        # note: the following are typically updated during create_logic call
        self.elements_per_beat = elements_per_beat
        self.element_size_bits = element_size_bits

    def send(self, frame):
        self.queue.append(AXIStreamFrame(frame))

    def write(self, data):
        self.send(data)

    def count(self):
        return len(self.queue)

    def empty(self):
        return self.count() == 0

    @block
    def create_logic(  # noqa: PLR0915
        self,
        clk,
        rst,
        axis=None,
        pause=0,
        xname=None,
    ):
        if axis is None:
            axis = axis_iface()

        if self.has_logic:
            raise RuntimeError("Logic has already been created for this AXIStreamSource instance.")
        self.has_logic = True

        tready_int = Signal(bool(False))
        tvalid_int = Signal(bool(False))

        @always_comb
        def pause_logic():
            tready_int.next = axis.tready and not pause
            axis.tvalid.next = tvalid_int and not pause

        @instance
        def logic():  # noqa: PLR0912, PLR0915
            frame = AXIStreamFrame(repr_items=self.repr_items)
            data = []
            keep = []
            dest = []
            tid = []
            user = []
            last = []

            # set these unless they are being overwritten
            if self.elements_per_beat is None:
                self.elements_per_beat = len(axis.tkeep)
            if self.element_size_bits is None:
                self.element_size_bits = int((len(axis.tdata) + self.elements_per_beat - 1) / self.elements_per_beat)

            while True:
                yield clk.posedge, rst.posedge

                if rst:
                    axis.tdata.next = 0
                    axis.tkeep.next = 0
                    axis.tdest.next = 0
                    axis.tid.next = 0
                    axis.tuser.next = False
                    tvalid_int.next = False
                    axis.tlast.next = False
                else:
                    if tready_int and axis.tvalid:
                        if len(data) > 0:
                            axis.tdata.next = data.pop(0)
                            axis.tkeep.next = keep.pop(0)
                            axis.tdest.next = dest.pop(0)
                            axis.tid.next = tid.pop(0)
                            axis.tuser.next = user.pop(0)
                            tvalid_int.next = True
                            axis.tlast.next = last.pop(0)
                        else:
                            tvalid_int.next = False
                            axis.tlast.next = False
                    if (axis.tlast and tready_int and axis.tvalid) or not tvalid_int:
                        if len(self.queue) > 0:
                            frame = self.queue.pop(0)
                            frame.elements_per_beat = self.elements_per_beat
                            frame.element_size_bits = self.element_size_bits
                            data, keep, dest, user, tid, last = frame.to_beats()
                            if xname is not None:
                                if frame.repr_items != 0:
                                    print("[%s] Sending frame %s" % (xname, repr(frame)))
                                else:
                                    print("s", end="", flush=True)
                            axis.tdata.next = data.pop(0)
                            axis.tkeep.next = keep.pop(0)
                            axis.tdest.next = dest.pop(0)
                            axis.tid.next = tid.pop(0)
                            axis.tuser.next = user.pop(0)
                            tvalid_int.next = True
                            axis.tlast.next = last.pop(0)

        return instances()


class AXIStreamSink(object):
    def __init__(self, repr_items=-1, skip_asserts=False, capture_leading=False):
        """
        capture_leading - capture elements with keep=0 bits during first beat
        """
        self.has_logic = False
        self.queue = []
        self.read_queue = []
        self.repr_items = repr_items
        self.skip_asserts = skip_asserts
        self.capture_leading = capture_leading

    def recv(self):
        """
        returns AXIS Frame that was received
        """
        if len(self.queue) > 0:
            return self.queue.pop(0)
        return None

    def read(self, count=-1):
        """
        returns accumulated data from any AXIS Frames received
        """
        while len(self.queue) > 0:
            self.read_queue.extend(self.queue.pop(0).data)
        if count < 0:
            count = len(self.read_queue)
        data = self.read_queue[:count]
        del self.read_queue[:count]
        return data

    def count(self):
        return len(self.queue)

    def empty(self):
        return self.count() == 0

    @block
    def create_logic(  # noqa: PLR0915
        self,
        clk,
        rst,
        axis=None,
        pause=0,
        xname=None,
    ):
        if axis is None:
            axis = axis_iface()

        if self.has_logic:
            raise RuntimeError("Logic has already been created for this AXIStreamSink instance.")
        self.has_logic = True
        tready_int = Signal(bool(False))
        tvalid_int = Signal(bool(False))

        @always_comb
        def pause_logic():
            axis.tready.next = tready_int and not pause
            tvalid_int.next = axis.tvalid and not pause

        @instance
        def logic():  # noqa: PLR0912, PLR0915
            frame = AXIStreamFrame(
                repr_items=self.repr_items,
                elements_per_beat=len(axis.tkeep),
                element_size_bits=len(axis.tdata) // len(axis.tkeep),
            )
            data = []
            keep = []
            dest = []
            tid = []
            user = []
            last = []
            first = True

            while True:
                yield clk.posedge, rst.posedge

                if rst:
                    tready_int.next = False
                    frame.clear()
                    data = []
                    keep = []
                    dest = []
                    tid = []
                    user = []
                    last = []
                    first = True
                else:
                    tready_int.next = True
                    if tvalid_int:
                        if not self.skip_asserts:
                            # zero tkeep not allowed
                            if int(axis.tkeep) == 0:
                                raise AssertionError("tkeep must not be zero")
                            # tkeep must be contiguous
                            # i.e. 0b00011110 allowed, but 0b00011010 not allowed
                            b = int(axis.tkeep)
                            while b & 1 == 0:
                                b = b >> 1
                            while b & 1 == 1:
                                b = b >> 1
                            if b != 0:
                                raise AssertionError("tkeep must be contiguous (no gaps allowed)")
                            # tkeep must not have gaps across cycles
                            if not first:
                                # not first cycle; lowest bit must be set
                                if not (int(axis.tkeep) & 1):
                                    raise AssertionError("Lowest bit of tkeep must be set on non-first cycle")
                            if not axis.tlast:
                                # not last cycle; highest bit must be set
                                if (int(axis.tkeep) & (1 << (len(axis.tkeep) - 1))) == 0:
                                    raise AssertionError("Highest bit of tkeep must be set on non-last cycle")

                        data.append(int(axis.tdata))
                        keep.append(int(axis.tkeep))
                        dest.append(int(axis.tdest))
                        tid.append(int(axis.tid))
                        user.append(int(axis.tuser))
                        last.append(int(axis.tlast))
                        first = False
                        if axis.tlast:
                            frame.from_beats(
                                tdata=data,
                                tkeep=keep,
                                tdest=dest,
                                tuser=user,
                                tid=tid,
                                tlast=last,
                                capture_leading=self.capture_leading,
                            )
                            self.queue.append(copy.deepcopy(frame))
                            if xname is not None:
                                if self.repr_items != 0:
                                    print("[%s] Got frame %s" % (xname, repr(frame)))
                                else:
                                    print("r", end="", flush=True)
                            frame.clear()
                            data = []
                            keep = []
                            dest = []
                            tid = []
                            user = []
                            last = []
                            first = True

        return logic, pause_logic
