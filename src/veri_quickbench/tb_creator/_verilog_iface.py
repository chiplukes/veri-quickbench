# MIT License
#
# Copyright (c) 2023 Chip Lukes
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


class verilog_iface:
    """
    Verilog Interface Class
    """

    def __init__(  # noqa: PLR0913
        self,
        iface_type=None,
        name=None,
        associated_clock=None,
        associated_reset=None,
        port_lst=None,
        pause=None,
        example=None,
    ):
        """
        iface_type - interface type ()
        name - string name of interface
        associated_clock - string name of associated clock
        associated_reset - string name of associated reset
        example - boolean - show example code when True
        """
        self.iface_type = iface_type
        self.name = name

        if associated_clock is None:
            raise Exception("interface must have an associated clock")
        else:
            self.associated_clock = associated_clock
        self.associated_reset = associated_reset
        self.port_lst = port_lst
        self.pause = pause

        # check if master or slave interface
        # fixme: for now just check if name starts with s_ or m_
        self.is_master = True
        if self.name[0:2].lower() == "s_":
            self.is_master = False

        self.example = example

    def create_iface_endpoint_template_myhdl(self):
        """
        creates a template for MyHDL for TBD
        """
        if self.associated_reset is None:
            reset_str = "Signal(bool(0))"
        else:
            reset_str = f"tf.{self.associated_reset}"

        if self.pause is False or self.pause is None:
            pause_axi_waddr = "Signal(bool(0))"
            pause_axi_wdata = "Signal(bool(0))"
            pause_axi_bresp = "Signal(bool(0))"
            pause_axi_araddr = "Signal(bool(0))"
            pause_axi_rdata = "Signal(bool(0))"
            pause_axis = "Signal(bool(0))"
        else:
            pause_axi_waddr = f"{self.name}_pause_awaddr"
            pause_axi_wdata = f"{self.name}_pause_wdata"
            pause_axi_bresp = f"{self.name}_pause_bresp"
            pause_axi_araddr = f"{self.name}_pause_araddr"
            pause_axi_rdata = f"{self.name}_pause_rdata"
            pause_axis = f"{self.name}_pause"

        if "axis" in self.iface_type:
            if self.is_master:
                return f"""
    sink_{self.name} = AXIStreamSink(repr_items=0)
    sink_logic_{self.name} = sink_{self.name}.create_logic(
        clk = tf.{self.associated_clock},
        rst = {reset_str},
        axis = tf.{self.name},
        pause = {pause_axis},
        xname='{self.name}'
    )
    """
            else:
                return f"""
    source_{self.name} = AXIStreamSource(repr_items=0)
    source_logic_{self.name} = source_{self.name}.create_logic(
        clk = tf.{self.associated_clock},
        rst = {reset_str},
        axis = tf.{self.name},
        pause = {pause_axis},
        xname='{self.name}'
    )
    """
        elif "axi" in self.iface_type:
            if self.is_master:
                return f"""
    sink_{self.name} = AXISlave(data_width=params_iface['AXI_DATA_WIDTH'], addr_width=params_iface['AXI_ADDR_WIDTH'], allow_narrow=True, allow_unaligned=True, repr_items=0, store_as_beats=False,rd_storage_fn=None, fill=0xdc)
    sink_{self.name}_logic = sink_{self.name}.create_logic(
        clk = tf.{self.associated_clock},
        rst = {reset_str},
        axi = tf.{self.name},
        pause_waddr={pause_axi_waddr},
        pause_wdata={pause_axi_wdata},
        pause_bresp={pause_axi_bresp},
        pause_araddr={pause_axi_araddr},
        pause_rdata={pause_axi_rdata},
        xname='{self.name}'
    )
    """
            else:
                return f"""
    source_{self.name} = AXIMaster(data_width=params_iface['AXI_DATA_WIDTH'], addr_width=params_iface['AXI_ADDR_WIDTH'], allow_narrow=True, allow_unaligned=True, repr_items=0, store_as_beats=False,aw_first=False, check_bresp=True )
    source_{self.name}_logic = source_{self.name}.create_logic(
        clk = tf.{self.associated_clock},
        rst = {reset_str},
        axi = tf.{self.name},
        pause_waddr={pause_axi_waddr},
        pause_wdata={pause_axi_wdata},
        pause_bresp={pause_axi_bresp},
        pause_araddr={pause_axi_araddr},
        pause_rdata={pause_axi_rdata},
        xname='axi_{self.name}'
    )
    """
        else:
            print(f"Warning: interface {self.iface_type} has no endpoint template")

    def create_iface_pause_template_myhdl(self):
        """
        creates pause logic for any interfaces
        """
        if self.pause is False:
            return ""
        if "axis" in self.iface_type:
            return f"""
    {self.name}_pause = Signal(bool(0))
    @instance
    def {self.name}_randPause():
        while 1:
            {self.name}_pause.next = random.randint(1, PAUSE_FACTOR) == 1
            yield tf.{self.associated_clock}.posedge
    """
        elif "axi" in self.iface_type:
            return f"""
    {self.name}_pause_araddr = Signal(bool(0))
    {self.name}_pause_rdata = Signal(bool(0))
    {self.name}_pause_awaddr = Signal(bool(0))
    {self.name}_pause_wdata = Signal(bool(0))
    {self.name}_pause_bresp = Signal(bool(0))
    @instance
    def {self.name}_randPause():
        while 1:
            {self.name}_pause_araddr.next = random.randint(1, PAUSE_FACTOR) == 1
            {self.name}_pause_rdata.next = random.randint(1, PAUSE_FACTOR) == 1
            {self.name}_pause_awaddr.next = random.randint(1, PAUSE_FACTOR) == 1
            {self.name}_pause_wdata.next = random.randint(1, PAUSE_FACTOR) == 1
            {self.name}_pause_bresp.next = random.randint(1, PAUSE_FACTOR) == 1
            yield tf.{self.associated_clock}.posedge
    """
        else:
            print(f"Warning: interface {self.iface_type} has no endpoint template")
            return ""

    def create_iface_example_template_myhdl(self):
        """
        creates example template for any interfaces
        """

        if self.example is True:
            if "axis" in self.iface_type:
                if self.is_master:
                    return f"""
        yield wait_axis(sink=sink_{self.name}, clk=tf.{self.associated_clock}, timeout=2000, msg="waiting {self.name}")
        rcv_frm = sink_{self.name}.recv()
        assert rcv_frm.data == snd_frm.data # Note: likely need more stuff here!
        """
                else:
                    return f"""
        snd_frm = send_axis(source=source_{self.name}, data=[i for i in range(10)], list_is_beats=True, tid=0, tdest=0, tuser=0, debug=True, endian="little")
        # can also pass array of elements into here and set list_is_beats = False
        #snd_frm = send_axis(source=source_{self.name}, data=[i for i in range(10)], list_is_beats=False, tid=0, tdest=0, tuser=0, debug=True, endian="little")
        """
            elif "axi" in self.iface_type:
                if self.is_master:
                    return f'''
        # example sink_{self.name} read
        #can pre-fill the memory like this
        sink_{self.name}.clear()
        sink_{self.name}.a = [ a for a in range(256)]
        sink_{self.name}.d = [ d%256 for d in range(256)]
        sink_{self.name}.tid = [ 0 for _ in range(256)]
        # #can also use a function to simulate data
        # def rd_storage_fn_sink_{self.name}(adr,num_beats):
        #     """
        #     function to return data from fake sdram
        #     returns array of rdata beats
        #     """
        #     data_beats = [adr+d for d in range(4*num_beats)]
        #     return data_beats
        # axi_s.rd_storage_fn = rd_storage_fn
        #
        # # for checking writes, can do the following:
        sink_{self.name}.clear()
        # wait for write to happen!
        wr_a_actual, wr_d_actual, wr_tid_actual = sink_{self.name}.get_write_log()
        #'''
                else:
                    return f"""
        # example source_{self.name}
        din = [ d%256 for d in range(256)] # 256 bytes
        source_{self.name}.issue_write(addr=0, data=din, tid=0)
        source_{self.name}.issue_read(addr=0,len_beats=1,arid=0)
        # check source_{self.name}.a and source_{self.name}.d for returned read data
        """
            else:
                print(f"Warning: interface {self.iface_type} has no endpoint template")

        else:
            return ""
