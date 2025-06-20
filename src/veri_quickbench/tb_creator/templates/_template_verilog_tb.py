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


def write_verilog_tb(f, module, params=None):
    """
    Writes a verilog testbench file
    """

    uut = module.get_module_name()
    param_declare = module.print_lparams(for_myhdl=True, params=params)
    signals = module.print_signals()
    fmh = module.print_port_names(
        pstyle="port",
        sep_str=",\n",
        format_str="        {}",
        filter_pdir=True,
        pdir=["input"],
    )
    tmh = module.print_port_names(
        pstyle="port",
        sep_str=",\n",
        format_str="        {}",
        filter_pdir=True,
        pdir=["output"],
    )
    params = module.print_inst_ports(pstyle="parameter")
    conn = module.print_inst_ports(pstyle="port")

    f.writelines(f"""
// Language: Verilog 2001

`timescale 1ns / 1ps

/*
 * Testbench for {uut}
 */
module test_{uut};

// Parameters
// __ARGx__ values filled in my MYHDL testbench
{param_declare}

{signals}
initial begin
    // myhdl integration
    $from_myhdl(
{fmh}
    );
    $to_myhdl(
{tmh}
    );

    // dump file
    $dumpfile("test_{uut}.lxt");
    $dumpvars(0, test_{uut});
end

{uut}
""")
    if params:
        f.writelines(f"""
#(
{params}
)
""")

    f.writelines(f"""
{uut}_inst (
{conn}
);

endmodule

""")
