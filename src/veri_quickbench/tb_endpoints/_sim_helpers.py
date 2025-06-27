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
import random

from myhdl import StopSimulation, delay, now

from ._axis_ep import AXIStreamFrame


def wait_axis(sink=None, clk=None, timeout=2000, msg=""):
    """
    waits for pkt on sink
    sink - AXIStreamSink object
    clk - clock
    timeout - max # of cycles to wait for pkt on sink
    msg - message to print if timeout happens
    """
    i = 0
    while sink.empty():
        yield clk.posedge
        if not i < timeout:
            raise Exception("Whoops, took too long to receive packet")
        i = i + 1
        if i >= timeout:
            print(f"Error, timeout waiting for axis @ {now()} : {msg}", flush=True)
            # sometimes it takes a longer simulation run to get print statements to work...
            yield delay(10000)
            raise StopSimulation


def send_axis(  # noqa: PLR0913
    source=None,
    data=None,
    list_is_beats=True,
    tid=0,
    tdest=0,
    tuser=0,
    debug=True,
    tuser_first_beat=True,
    no_tlast=False,
    endian="little",
):
    """
    source - AXIStreamSource object
    data - array of either beats or elements to send
    list_is_beats - boolean - when True, data is beats, else data is elements that need to be constructed into beats
    debug - boolean - prints axi stream beats when
    endian - controls placement of element within axi beat
              - 'little' - first data element stored in lower portion of first axi beat
              - 'big' - first data element stored in upper portion of first axi beat
    """
    if list_is_beats:
        # tdata list is in beats
        # AXIStreamFrame expects lists to be in elements, so convert here
        dest_lst = [tdest for _ in data]
        tid_lst = [tid for _ in data]
        if tuser_first_beat:
            tuser_lst = [0 for _ in data]
            tuser_lst[0] = 1
        else:
            tuser_lst = [tuser for _ in data]
        frm = AXIStreamFrame(
            elements_per_beat=source.elements_per_beat,
            element_size_bits=source.element_size_bits,
            repr_items=0,
            endian=endian,
        )
        frm.from_beats(tdata=data, tkeep=None, tdest=dest_lst, tuser=tuser_lst, tid=tid_lst)
    else:
        # tdata list is in elements
        if tuser_first_beat:
            tuser_lst = [0 for _ in data]
            for i in range(source.elements_per_beat):
                tuser_lst[i] = 1
        else:
            tuser_lst = [tuser for _ in data]
        frm = AXIStreamFrame(
            data=data,
            keep=None,
            dest=tdest,
            tid=tid,
            user=tuser_lst,
            elements_per_beat=source.elements_per_beat,
            element_size_bits=source.element_size_bits,
            repr_items=0,
        )

    if no_tlast:
        frm.last[-1] = 0
    source.send(frm)
    tdata_i, tkeep_i, tdest_i, tuser_i, tid_i, tlast_i = frm.to_beats()

    # TODO: format size of data based on bus widths
    if debug:
        print("Axis beats:")
        print("    tdata:")
        for b in tdata_i:
            print(f"        {b:0{frm.elements_per_beat * frm.element_size_bits // 4}x}")
        print("    tkeep:")
        for b in tkeep_i:
            print(f"        {b:0{frm.elements_per_beat // frm.element_size_bits}x}")
        print("    tuser:")
        for b in tuser_i:
            print(f"        {b:01x}")

    return frm


# Old Stuff below, may be useful still...

SIM_MAX_WAIT = 10000


def lineinfo():
    """
    reports line that this function was called on
    """
    callerframerecord = inspect.stack()[1]  # 0=this line, 1=line at caller
    frame = callerframerecord[0]
    return "CODE: {}\nLINE: {}".format(
        inspect.getframeinfo(frame).code_context,
        inspect.getframeinfo(frame).lineno,
    )


def checker(eq, msg, maxdelay=100000):
    """
    checks eq==True, if not exits simulation gracefully
    """
    if not eq:
        simtime = now()
        # hopefully clear out anything (fifos etc) that may be
        # producing messages.  Want stuff below to be last
        # at console :)
        yield delay(maxdelay)
        print(msg)
        print("Simulation Error.  Look at {}ns in wave file :) !!!".format(simtime))
        raise StopSimulation


def tkeep_resize(numbytes, keep_bits):
    """
    figures out keep array for desired number of keep_bits
    """
    keep_rem = numbytes % keep_bits
    keep_beats = int(numbytes / keep_bits)
    keep_beat_full = 2**keep_bits - 1
    keep = [keep_beat_full for i in range(keep_beats)]
    if keep_rem:
        keep.append(2**keep_rem - 1)

    return keep


def send_axis_packets(  # noqa: PLR0913
    axis_source,
    num_pkts,
    s_keep_bits,
    m_keep_bits,
    dest_bits,
    inject_error,
    use_keep=0,
    repr_items=-1,
):
    """
    sends a bunch of packets
    """
    exp_lst = []  # list of packets expected
    for i in range(num_pkts):
        axis_frame = AXIStreamFrame(repr_items=repr_items)
        axis_frame.data = bytearray(
            [random.randint(0, 255) for x in range(i + 2)]  # noqa: S311
        )
        # tdest
        rdest = random.randint(0, 2**dest_bits - 1)  # noqa: S311
        if dest_bits:
            axis_frame.dest = [rdest for x in axis_frame.data]
        axis_frame.build()
        axis_source.send(axis_frame)

        # expected tkeep
        if use_keep == 0:
            axis_frame.allow_trailing = True  # allows equality to pass with extra bytes
        elif s_keep_bits or m_keep_bits:
            axis_frame.keep = tkeep_resize(len(axis_frame.data), m_keep_bits)
        # expected tdest
        if dest_bits:
            axis_frame.dest = [rdest for x in tkeep_resize(len(axis_frame.data), m_keep_bits)]

        exp_lst.append(axis_frame)
        # exp_lst[-1].repr_items=-1
        # print("in exp queue", exp_lst[-1])
        # print("in source queue", axis_source.queue[-1])

    # if wanting to sanity check the simulation :)
    if inject_error is True:
        err_loc = random.randint(0, len(exp_lst) - 1)  # noqa: S311
        err_typ = random.randint(0, 1)  # noqa: S311
        if err_typ == 0:
            # mess up expected axis data
            exp_lst[err_loc].data[0] = 0xFF ^ exp_lst[err_loc].data[0]
        else:
            exp_lst[err_loc].keep[0] = 0xFF ^ exp_lst[err_loc].keep[0]

    return exp_lst


def chk_axis_packets(axis_sink, exp_lst, clk, dropped_pkt, sim_max_wait=1000):
    """
    checks a bunch of packets
    """
    simtime = 0
    sdrops = 0  # drops observed on slave interface
    mdrops = 0  # drops observed on master interface
    packets_sent = len(exp_lst)
    packets_received = 0
    while packets_sent > (packets_received + sdrops) and simtime < sim_max_wait:
        simtime += 1
        if not simtime < sim_max_wait:
            raise Exception("Error: waiting for packet.")

        if not axis_sink.empty():
            simtime = 0
            rx_frame = axis_sink.recv()
            exp_frame = exp_lst.pop(0)
            packets_received += 1
            rx_frame.repr_items = -1
            exp_frame.repr_items = -1
            # print('Received frame:', rx_frame)
            # print('Expected frame:', exp_frame)
            # print(rx_frame==exp_frame)

            # keep poppin from exp_lst until expected packet found or
            # exp_lst empty or mdrops > sdrops
            while exp_frame != rx_frame:
                mdrops += 1
                exp_frame.repr_items = -1
                # print("dropped", exp_frame)
                msg = "Simulation Error.  Look at {}ns in wave file :) !!!".format(now())
                msg += "\nReceived:{}\n\nExpected:{}\n".format(rx_frame, exp_frame)
                msg += "Error: Drops on slave: {}, Drops on master: {}".format(sdrops, mdrops)
                if not exp_lst:
                    raise Exception(msg)  # exp_lst should not be empty here, last entry bad?
                exp_frame = exp_lst.pop(0)
                if not (sdrops >= mdrops):
                    raise Exception(msg)

            # done?
            if not exp_lst:
                return

        if dropped_pkt:
            print("d", end="", flush=True)  # dropped packet
            sdrops += 1

        yield clk.posedge


def beats2bytes(adr, data, data_bits):
    """
    Converts arrays of adr and data where data is 16, 24, 32 etc bit integers (or lists of)
    data_bits - # bits used for each element in data
    TODO: make this work on data when data elements are bursts :)
    """
    adr_exp = []
    data_exp = []
    for i, d in enumerate(data):
        for b in range(int(data_bits / 8)):
            adr_exp.append(adr[i] + b)
            data_exp.append((d >> (8 * b)) & 0xFF)
    return adr_exp, data_exp


def bytestobeats(adr, data, data_bits):
    """
    Converts arrays of adr and data where data is an 8 bit integer
    to an array of 16, 24, 32 etc bit integers
    data_bits - # bits used for each element in data output array
    """
    adr_exp = []
    data_exp = []
    for i in range(0, len(data), int(data_bits / 8)):
        adr_exp.append(adr[i])
        d = 0
        for b in range(int(data_bits / 8)):
            d = d + (data[i + b] << (b * 8))
        data_exp.append(d)
    return adr_exp, data_exp


def beats2bytearray(data, num_bytes, data_bits):
    """
    Converts arrays of data where data is 16, 24, 32 etc bit integers (or lists of)
    data_bits - # bits used for each element in data
    TODO: make this work on data when data elements are bursts :)
    """
    ba = bytearray()
    for d in data:
        ba.extend(d.to_bytes(int(data_bits / 8), byteorder="little"))
    return ba[:num_bytes]


def axi4_wait_read_data(axi4, axi4clk, adr, len_beats, sim_max_wait=1000):
    """
    waits for len_beats of data to be read from adr
    """
    simtime = 0
    axi4.clear()  # clear out any existing read data
    # issue read request
    axi4.issue_read(adr, len_beats)
    # wait for read data to come back
    rd_a, rd_d = axi4.get_read_log()
    while not rd_d:
        yield axi4clk.posedge
        rd_a, rd_d = axi4.get_read_log()
        simtime += 1
        if not simtime < sim_max_wait:
            raise Exception("Error: waiting for packet.")


def axi4_wait_bit(axi4, axi4clk, adr, bits, sim_max_wait=1000):
    """
    waits on bits present in adr read from axi4 interface
    """
    # wait for bits
    simtime = 0
    while True:
        axi4.clear()  # clear out any existing read data
        axi4.issue_read(adr, 0)
        # wait for read data to come back
        rd_a, rd_d = axi4.get_read_log()
        while not rd_d:
            yield axi4clk.posedge
            rd_a, rd_d = axi4.get_read_log()
            simtime += 1
            if not simtime < sim_max_wait:
                raise Exception("Error: waiting for packet.")

        if rd_d[0] & bits:  # packet present
            break
