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


def write_tf_sigs(f, module=None, connect_fn=None):
    """
    Writes a tf_sigs file
    f = file
    module = verilog_module object
    myhdl - if True, add get_sigs_dict_myhdl() method
    cosim - if True, add get_sigs_dict_cosim() method
    """
    if module is None:
        # User expected to create this file, give example
        mh_sigs = """            # TODO: fill in this section with actual signals!
        self.clk = Signal(bool(0))
        self.rst = Signal(bool(0))
        self.s_axis = axis(DATA_WIDTH=DATA_WIDTH,USER_WIDTH=USER_WIDTH,DEST_WIDTH=DEST_WIDTH,ID_WIDTH=ID_WIDTH,ELEMENT_SIZE_BITS=ELEMENT_SIZE_BITS)
        self.m_axis = axis(DATA_WIDTH=DATA_WIDTH,USER_WIDTH=USER_WIDTH,DEST_WIDTH=DEST_WIDTH,ID_WIDTH=ID_WIDTH,ELEMENT_SIZE_BITS=ELEMENT_SIZE_BITS)
        """
        param_names_str = "DATA_WIDTH=32, USER_WIDTH=1, DEST_WIDTH=1, ID_WIDTH=1, ELEMENT_SIZE_BITS=32"
        cosim_dict = """                'clk' : self.clk,
                'rst' : self.clk,
                's_axis_tdata'      : self.s_axis.tdata,
                's_axis_tkeep'      : self.s_axis.tkeep,
                's_axis_tvalid'     : self.s_axis.tvalid,
                's_axis_tready'     : self.s_axis.tready,
                's_axis_tlast'      : self.s_axis.tlast,
                's_axis_tid'        : self.s_axis.tid,
                's_axis_tdest'      : self.s_axis.tdest,
                's_axis_tuser'      : self.s_axis.tuser,
                'm_axis_tdata'      : self.m_axis.tdata,
                'm_axis_tkeep'      : self.m_axis.tkeep,
                'm_axis_tvalid'     : self.m_axis.tvalid,
                'm_axis_tready'     : self.m_axis.tready,
                'm_axis_tlast'      : self.m_axis.tlast,
                'm_axis_tid'        : self.m_axis.tid,
                'm_axis_tdest'      : self.m_axis.tdest,
                'm_axis_tuser'      : self.m_axis.tuser"""
    else:
        mh_sigs = module.print_myhdl_signals(format_str="        self.{} = {}({})", connect_fn=connect_fn)
        param_names_str = module.print_port_names(pstyle="parameter", sep_str=", ", format_str="{}")
        cosim_dict = module.print_cosim_dict()

    if param_names_str != "":
        param_names_str = ", " + param_names_str

    f.writelines(f'''
from myhdl import Signal, intbv
{module.print_myhdl_imports()}

class tf_sigs():
    """
    wrap signals for uut into class
    """
    def __init__( self{param_names_str}):
        # Signal Declarations
{mh_sigs}
''')

    f.writelines(f'''
    def get_sigs_dict_myhdl(self):
        """
        returns a dictionary of signals for this uut when testng a MyHDL uut
        """
        return vars(self)

    def get_sigs_dict_cosim(self):
        """
        returns a dictionary of signals for this uut when testng a Verilog uut
        """
        return (
            {{
{cosim_dict}
            }})

''')
