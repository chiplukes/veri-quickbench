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

# =======================================================================
# good example here https://github.com/cornell-brg/pymtl/blob/master/pymtl/tools/integration/verilog_parser.py
# =======================================================================

import sys

from pyparsing import (
    Group,
    Keyword,
    LineEnd,
    Literal,
    MatchFirst,
    OneOrMore,
    Optional,
    Regex,
    SkipTo,
    StringEnd,
    Suppress,
    cppStyleComment,
    delimitedList,
    oneOf,
)

from ..tb_endpoints import get_intfc_inits
from ._verilog_port import verilog_port


class verilog_module:
    """
    Verilog Port Class

    """

    def __init__(self, ifile=None, debug=False):
        """ """
        # parse input file
        if debug:
            print(f"Parsing {ifile}")
        self.debug = debug

        with open(ifile, "r") as f:
            pars = self.header_parser(debug=debug)
            self.prs = pars.parseFile(f)

        self.name = self.prs["module_name"]

        # create a list of ports/params
        self.ports_lst = []

        # param_lst = self.mk_params_lst(self.prs, debug=self.debug)
        # for x in param_lst:
        #     self.ports_lst.append(verilog_port(pstyle=x[0], pdir=x[1], ptype=x[2], psign=x[3], psize=x[4], pname=x[5], pvalue=x[6], debug=debug))

        p_lst = self.mk_ports_lst(self.prs, debug=self.debug)
        for x in p_lst:
            self.ports_lst.append(
                verilog_port(
                    pstyle=x[0],
                    pdir=x[1],
                    ptype=x[2],
                    psign=x[3],
                    psize=x[4],
                    pname=x[5],
                    pvalue=x[6],
                    debug=False,
                )
            )

    @staticmethod
    def header_parser(debug=False):
        """
        A simple parser for Verilog module interfaces. Collects class
        name, parameter names, and port names.
        """

        to_eol = SkipTo(LineEnd(), include=True)
        identifier = Regex("[a-zA-Z_][a-zA-Z0-9_\\$]*")
        module_identifier = Regex("[a-zA-Z_][a-zA-Z0-9_\\$]*")
        comment = cppStyleComment.suppress()
        vect_size = Group(Optional(Suppress("[") + SkipTo("]") + Suppress("]")))

        # module
        # module_begin = Suppress('module') + module_identifier('module_name') + SkipTo('(')
        module_begin = Suppress("module") + module_identifier("module_name")

        # Params
        bgn_param = oneOf("parameter", caseless=True, asKeyword=True)
        # end_param = Literal(',') + 'parameter' | Literal(')') + '('
        end_param = SkipTo(Literal(",") | LineEnd())
        param_type = Optional(oneOf("integer real realtime time"))
        param_verilog2001 = Group(
            bgn_param
            + param_type("opt_param_type")
            + vect_size("opt_size")
            + identifier("p_name")
            + end_param("opt_value")
        )
        param_verilog95 = Group(
            bgn_param
            + param_type("opt_param_type")
            + vect_size("opt_size")
            + identifier("p_name")
            + to_eol("opt_value")
        )
        list_of_verilog2001_params = Group(
            Suppress("#") + Suppress("(") + delimitedList(Group(param_verilog2001("parameter"))) + Suppress(")")
        )

        # Ports
        port_dir = oneOf("input output inout", caseless=True, asKeyword=True)
        port_type = Optional(oneOf("wire reg", caseless=True, asKeyword=True))
        port_sign = Optional(oneOf("signed", caseless=True, asKeyword=True))
        end_port = Literal(",") | Literal(")")
        port_end_verilog2001 = SkipTo(Literal(",") | Literal(")"))
        port_verilog95 = Group(
            port_dir("port_dir")
            + port_type("opt_type")
            + port_sign("opt_sign")
            + vect_size("opt_size")
            + identifier("p_name")
            + to_eol("opt_value")
        )
        port_verilog2001 = Group(
            port_dir("port_dir")
            + port_type("opt_type")
            + port_sign("opt_sign")
            + vect_size("opt_size")
            + identifier("p_name")
            + port_end_verilog2001("opt_value")
        )
        portname95 = Group(identifier + SkipTo(end_port))
        list_of_verilog95_portnames = Group(Suppress("(") + delimitedList(portname95) + SkipTo(";"))
        list_of_verilog95_ports = Group(
            OneOrMore(
                ~Keyword("endmodule")
                + Group(
                    MatchFirst(
                        [
                            port_verilog95("port"),
                            param_verilog95("parameter"),
                            to_eol,
                        ]
                    )
                )
            )
        )
        list_of_verilog2001_ports = Group(
            Suppress("(") + delimitedList(Group(port_verilog2001("port"))) + Suppress(")")
        )

        # Module
        module = (
            module_begin
            + Optional(list_of_verilog2001_params("list_of_verilog2001_params"))
            + Optional(list_of_verilog2001_ports("list_of_verilog2001_ports"))
            + Optional(list_of_verilog95_portnames("list_verilog95_names"))
            + Optional(list_of_verilog95_ports("list_verilog95_ports"))
            + SkipTo("endmodule")
            + Suppress("endmodule")
        )

        # Debug
        # if debug:
        # def dbg(label, tkn_id=None):
        #     '''
        #     Utility debugging method
        #     '''
        #     def action(s, tkn, smt):
        #         if tkn_id:
        #             print(label, smt[tkn_id])
        #         else:
        #             print(label, smt)
        #     return(action)

        # # For these to work, you cannot set_results_name in the parse object above
        # # Ie. no port95('ports')
        # module_begin     .setParseAction(dbg('module_nm'))  #.setDebug()
        # portname95       .setParseAction(dbg('p95names'))  #.setDebug()
        # param            .setParseAction(dbg('params'))  #.setDebug()
        # port2001         .setParseAction( dbg('ports'))#.setDebug()
        # port95           .setParseAction( dbg('ports95'))#.setDebug()
        # list_of_verilog95_portnames .setParseAction( dbg('ports'))#.setDebug()
        # #list_of_verilog95_ports.setParseAction( dbg('ports'))#.setDebug()
        # #identifier       .setParseAction( dbg('id'))#.setDebug()
        # to_eol           .setParseAction( dbg('skip'))#.setDebug()
        # #module           .setParseAction( dbg('module') )#.setDebug()

        prs = (
            SkipTo("module", ignore=comment).suppress()
            + OneOrMore(module).ignore(comment)
            + SkipTo(StringEnd()).suppress()
        )

        return prs

    def get_module_name(self):
        """
        takes prs and returns module name that was contained in the verilog
        """
        return self.name

    def debug_print_ports(self):
        """
        takes a ports_lst (see mk_ports_lst()) and prints all parameters and interface ports
            ptype psize pname;
            ...
            ptype psize pname;
        """
        max_lens = [0, 10, 0, 20, 25, 0]
        ret_str = ""
        for p in self.ports_lst:
            ret_str += p.format_signal(width_lst=max_lens, strip_defaults=True)
        return ret_str

    def print_lparams(self, for_myhdl=False, params=None):
        """
        makes a list of localparams
        params can be a dict of parameters with values, if present they can be used as defaults
        Ie:
            localparam opt_type opt_size param_name1 opt_value;
            localparam opt_type opt_size param_name2 opt_value;
            ...
            localparam opt_type opt_size param_namex opt_value;
        """
        max_lens = self.max_list_item_len(pstyle="parameter", p_lst=self.ports_lst)
        ret_str = ""
        indx = 0
        for p in self.ports_lst:
            if p.pstyle == "parameter":
                try:
                    p.pvalue = f"= {params[p.pname]}"
                    ret_str += p.format_lparam(pvalue_override=None, width_lst=max_lens)
                except:  # noqa: E722
                    if for_myhdl:
                        ret_str += p.format_lparam(
                            pvalue_override="= __ARGV{}__".format(indx),
                            width_lst=max_lens,
                        )
                    else:
                        ret_str += p.format_lparam(pvalue_override=None, width_lst=max_lens)
                indx += 1
        return ret_str

    def print_signals(self):
        """
        takes a ports_lst (see mk_ports_lst()) and makes a list of signals

        params_str looks like the following:

            opt_type opt_size param_name1 opt_value;
            opt_type opt_size param_name2 opt_value;
            ...
            opt_type opt_size param_namex opt_value;
        """
        max_lens = self.max_list_item_len(pstyle="port", p_lst=self.ports_lst)
        ret_str = ""
        indx = 0
        for p in self.ports_lst:
            if p.pstyle == "port":
                ret_str += p.format_signal(
                    width_lst=max_lens,
                    strip_defaults=True,
                    dflt_ptype="parameter",
                )
                indx += 1
        return ret_str

    def get_clocks(self):
        """
        searches ports for "clk" in the name
        returns list of names
        """
        ret_lst = []
        for p in self.ports_lst:
            if p.pstyle == "port":
                if "clk" in p.pname.lower():
                    ret_lst.append(p.pname)
        return ret_lst

    def get_resets(self):
        """
        searches ports for "rst" or "reset" in the name
        returns list of names
        """
        ret_lst = []
        for p in self.ports_lst:
            if p.pstyle == "port":
                if "rst" in p.pname.lower():
                    if "burst" not in p.pname.lower():  # ignore a(x)burst signals in AXI busses
                        ret_lst.append(p.pname)
                elif "reset" in p.pname.lower():
                    ret_lst.append(p.pname)

        return ret_lst

    def get_params(self, value_format="verilog"):
        """
        searches ports for parameters
        returns list of tuples of (pname,pval)
        format - verilog (keep verilog value string Ie: 8'hff)
               - python (translate verilog value string into python form Ie: 8'hff becomes 0xff)
        """
        ret_lst = []
        for p in self.ports_lst:
            if p.pstyle == "parameter":
                prmv = p.pvalue.split("=")
                if value_format == "verilog":
                    ret_lst.append((p.pname, prmv[1]))
                elif value_format == "python":
                    # crude attempt to convert parameter value to integer
                    if "'h" in prmv[1].lower():
                        # parameter is hex value
                        splt = prmv[1].lower().split("'")
                        try:
                            new_v = f"0x{int(splt[1][1:], 16):x}"
                        except:  # noqa: E722
                            print(
                                f"Error attempting to convert value for {p.pname} from verilog: {prmv[1]} to python integer, will default parameter to 0"
                            )
                            new_v = "0x0"
                    elif "'d" in prmv[1].lower():
                        # parameter is decimal value
                        splt = prmv[1].lower().split("'")
                        try:
                            new_v = f"{int(splt[1][1:])}"
                        except:  # noqa: E722
                            print(
                                f"Error attempting to convert value for {p.pname} from verilog: {prmv[1]} to python integer, will default parameter to 0"
                            )
                            new_v = "0"
                    else:
                        # assume integer
                        try:
                            new_v = prmv[1].lstrip()  # remove leading spaces
                            new_v = f"{int(new_v)}"
                        except:  # noqa: E722
                            print(
                                f"Error attempting to convert value for {p.pname} from verilog: {prmv[1]} to python integer, will default parameter to 0"
                            )
                            new_v = "0"
                    ret_lst.append((p.pname, new_v))

        return ret_lst

    def print_inst_ports(self, pstyle):
        """
        creates the ports section of an instantiation template

        ret_str looks like the following:

            .param1(param1),
            .param2(param2),
            .param3(param3)
        or:
            .port1(port1),
            .port2(port2),
            .port3(port3)
        """
        ports_lst_new = []
        for p in self.ports_lst:
            if p.pstyle == pstyle:
                ports_lst_new.append(p)
        max_lens = self.max_list_item_len(pstyle=pstyle, p_lst=ports_lst_new)
        ret_str = ""
        for p in ports_lst_new:
            ret_str += "    .{:{width}} ({:{width}})".format(p.pname, p.pname, width=max_lens[-2])
            if p is ports_lst_new[-1]:
                ret_str += "\n"
            else:
                ret_str += ",\n"
        return ret_str

    def print_port_names(  # noqa: PLR0913
        self, pstyle, sep_str=", ", format_str="{}", filter_pdir=False, pdir=None, aggregate_interfaces=False
    ):
        """
        prints out port names in a variety of ways
        Ie:
           port0, port1, port2 ... (sep_str=", ", format_str="{}")
           'port0', 'port1', 'port2' ... (sep_str=", ", format_str="'{}'")

        pdir is a list in case more than one direction needs to be filtered
        """
        if pdir is None:
            pdir = ["input"]
        ports_lst_new = []
        for p in self.ports_lst:
            if p.pstyle == pstyle:
                if filter_pdir:
                    for x in pdir:
                        if p.pdir == x:
                            if aggregate_interfaces and p.is_iface:
                                # iface_name = p.iface_name + p.iface
                                iface_name = p.iface_name
                                if iface_name not in ports_lst_new:
                                    ports_lst_new.append(iface_name)
                            else:
                                ports_lst_new.append(p.pname)
                elif aggregate_interfaces and p.is_iface:
                    # iface_name = p.iface_name + p.iface
                    iface_name = p.iface_name
                    if iface_name not in ports_lst_new:
                        ports_lst_new.append(iface_name)
                else:
                    ports_lst_new.append(p.pname)
        ret_str = sep_str.join([format_str.format(i) for i in ports_lst_new])
        return ret_str

    def print_cosim_dict(self, sep_str=",\n", format_str="            '{}' : self.{}"):
        """
        prints out MyHDL Cosimulation connections in dictionary form
        Ie:
                "clk" : self.clk,
                "rst" : self.rst,
                "s_axis_tvalid" : s_axis.tvalid
        """
        ports_lst_new = []
        for p in self.ports_lst:
            if p.pstyle == "port":
                if not p.is_iface:
                    ports_lst_new.append(format_str.format(p.pname, p.pname))
                else:
                    # iface_name = p.iface_name + p.iface + "." + p.iface_sig
                    iface_name = p.iface_name + "." + p.iface_sig
                    ports_lst_new.append(format_str.format(p.pname, iface_name))

        ret_str = sep_str.join(ports_lst_new)
        return ret_str

    def print_myhdl_signals(self, sep_str="\n", format_str="    {} = {}({})", connect_fn=None):
        """
        prints out MyHDL Signals
        Ie:
           clk = Signal(0)
           rst = Signal(0)
           din = Signal(intbv(0)[8:])
           ...
        """
        # ports that are not interfaces
        ports_lst_new = []
        for p in self.ports_lst:
            if p.pstyle == "port":
                if not p.is_iface:
                    ports_lst_new.append(format_str.format(p.pname, "Signal", self.portsize_to_signal(p.psize)))

        # figure out interfaces
        iface_name_lst, iface_type_lst = self.get_ifaces()
        for i, nm in enumerate(iface_name_lst):
            # FIXME, should pip in parameters to interface here!

            if connect_fn is not None:
                # use a passed in function to connect up interface signals
                intfc_sigs = connect_fn(get_intfc_inits(iface_type_lst[i]), nm)
            else:
                # otherwise, leave unconnected
                intfc_sigs = get_intfc_inits(iface_type_lst[i])

            ports_lst_new.append(format_str.format(nm, iface_type_lst[i], intfc_sigs))

        ret_str = sep_str.join(ports_lst_new)
        return ret_str

    def get_ifaces(self):
        """
        get list of interface names and list of interface types
        """

        # figure out interfaces
        iface_name_lst = []
        iface_type_lst = []
        for p in self.ports_lst:
            if p.pstyle == "port":
                if p.is_iface:
                    # nm = p.iface_name + p.iface
                    nm = p.iface_name
                    if nm not in iface_name_lst:
                        iface_name_lst.append(nm)
                        iface_type_lst.append(p.iface)
        return iface_name_lst, iface_type_lst

    def print_myhdl_imports(self):
        """
        prints out endpoint imports for all interface types found
        Ie:
           from tb_endpoints import axis
           from tb_endpoints import axi
           ...
        """
        # figure out interfaces
        iface_type_lst = []
        for p in self.ports_lst:
            if p.pstyle == "port":
                if p.is_iface:
                    iface_type_lst.append("from veri_quickbench.tb_endpoints import " + p.iface)
        iface_type_lst = list(set(iface_type_lst))
        ret_str = "\n".join(iface_type_lst)
        return ret_str

    def inst_template(self):
        """
        returns an instantiation template
        """
        prms = self.print_lparams()
        sigs = self.print_signals()

        ret_val = prms + sigs + "\n{}\n".format(self.get_module_name())
        if prms != "":
            ret_val += "#(\n" + self.print_inst_ports(pstyle="parameter") + ")\n"
        ret_val += "{}_inst\n(\n".format(self.get_module_name())
        ret_val += self.print_inst_ports(pstyle="port") + ");"
        return ret_val

    # @staticmethod
    # def mk_params_lst(prs):
    #     """
    #     takes prs (parse) and returns formatted version of what was contained in the verilog
    #     list form is:
    #     [port_style, port_dir, opt_type, opt_sign, opt_size, param_name, opt_value]
    #     port_style is string 'parameter' or 'port'
    #     port_dir is a string such as 'input' or 'output'
    #     opt_type is a string such as 'integer, 'reg', 'wire', 'tri', or '' if none
    #     opt_sign is a string such as 'signed' or '' if none
    #     opt_size is a string such as '[7:0]' or '' if none
    #     port_name (name of port)
    #     opt_value is any string after name or '' if none
    #     """
    #     params_lst = []
    #     # check if any parameters present, if so return
    #     if 'params' not in prs.keys():
    #     #if prs[0][1][0][0].lower() != 'parameter':
    #         #return None
    #         return params_lst
    #     for e in prs['params']:

    #         # get assigned parameter value
    #         indx = -1
    #         if '=' in e[indx]:
    #             opt_value = e[indx].lstrip()
    #         else:
    #             opt_value = ''
    #         indx -= 1

    #         # get param_name
    #         param_name = e[indx]
    #         indx -= 1

    #         # get opt_size
    #         if not e[indx]:
    #             opt_size = ''
    #         else:
    #             opt_size = '[' + e[indx][0] + ']'
    #         indx -= 1

    #         # get opt_type
    #         if e[indx].lower() != 'parameter':
    #             opt_type = e[indx]
    #             indx -= 1
    #         else:
    #             opt_type = ''

    #         if e[indx].lower == 'parameter':
    #             params_lst.append(['ERROR', '', opt_type, '', opt_size, param_name, opt_value])
    #         else:
    #             params_lst.append(['parameter', '', opt_type, '', opt_size, param_name, opt_value])

    #     return params_lst

    @staticmethod
    def mk_ports_lst(prs, debug=False):  # noqa: PLR0912, PLR0915
        """
        takes prs(parse) and returns formatted version of what was contained in the verilog
        list form is:
        [port_style, port_dir, opt_type, opt_sign, opt_size, param_name, opt_value]
        port_style is string 'parameter' or 'port'
        port_dir is a string such as 'input' or 'output'
        opt_type is a string such as 'integer, 'reg', 'wire', 'tri', or '' if none
        opt_sign is a string such as 'signed' or '' if none
        opt_size is a string such as '[7:0]' or '' if none
        port_name (name of port)
        opt_value is any string after name or '' if none
        """
        keys_lst = []
        port_lst = []
        if "list_of_verilog2001_params" in prs.keys():
            keys_lst.append("list_of_verilog2001_params")
            if "list_of_verilog2001_ports" in prs.keys():
                keys_lst.append("list_of_verilog2001_ports")
        elif "list_verilog95_ports" in prs.keys():
            keys_lst.append("list_verilog95_ports")

        if not keys_lst:
            raise KeyError(f"Could not find Verilog95 or Verilog2001 style ports in {prs}")

        if debug:
            print(f"found {keys_lst}")

        for key in keys_lst:
            for e in prs[key]:
                port = None
                ptype = "ERROR"
                if "parameter" in e.keys():
                    port = e["parameter"]
                    ptype = "parameter"
                    if debug:
                        print(f"parsed parameter: {port}")
                if "port" in e.keys():
                    port = e["port"]
                    ptype = "port"
                    if debug:
                        print(f"parsed port: {port}")
                if port:
                    # get port direction
                    port_dir = ""
                    if "port_dir" in port.keys():
                        port_dir = port["port_dir"].lower()
                    if debug:
                        print(f"   port_dir: {port_dir}")

                    # get opt_type
                    opt_type = ""
                    if "opt_type" in port.keys():
                        opt_type = port["opt_type"].lower()
                    if debug:
                        print(f"   opt_type: {opt_type}")

                    # get opt_sign
                    opt_sign = ""
                    if "opt_sign" in port.keys():
                        opt_sign = port["opt_sign"]
                    if debug:
                        print(f"   opt_sign: {opt_sign}")

                    # get opt_size
                    opt_size = ""
                    if "opt_size" in port.keys():
                        if len(port["opt_size"]) > 0:
                            opt_size = "[" + "".join(port["opt_size"]) + "]"
                    if debug:
                        print(f"   opt_size: {opt_size}")

                    # get port_name
                    port_name = port["p_name"]
                    if debug:
                        print(f"   port_name: {port_name}")

                    # get assigned port value
                    opt_value = ""
                    if "opt_value" in port:
                        opt_value = port["opt_value"]
                        # todo: more needed here likely
                    if debug:
                        print(f"   opt_value: {opt_value}")

                    port_lst.append(
                        [
                            ptype,
                            port_dir,
                            opt_type,
                            opt_sign,
                            opt_size,
                            port_name,
                            opt_value,
                        ]
                    )

        return port_lst

    @staticmethod
    def max_list_item_len(pstyle, p_lst):
        """
        return max size of each port field, for formatting
        purposes
        """
        pdir_len = 0
        ptype_len = 0
        psign_len = 0
        psize_len = 0
        pname_len = 0
        pvalue_len = 0
        for i in p_lst:
            if i.pstyle == pstyle:
                pdir_len = max(pdir_len, len(i.pdir))
                ptype_len = max(ptype_len, len(i.ptype))
                psign_len = max(psign_len, len(i.psign))
                psize_len = max(psize_len, len(i.psize))
                pname_len = max(pname_len, len(i.pname))
                pvalue_len = max(pvalue_len, len(i.pvalue))
        return [
            pdir_len,
            ptype_len,
            psign_len,
            psize_len,
            pname_len,
            pvalue_len,
        ]

    @staticmethod
    def portsize_to_signal(size):
        """
        takes a verilog port size ie '[5:0]' and turns it into a myhdl equivalent
        intbv(0)[6:]
        """
        if size == "":
            return "bool(0)"
        else:
            indices = size.strip(" []").split(":")
            if len(indices) == 2:  # noqa: PLR2004
                msb = indices[0]
                lsb = indices[1]

                if msb == "0":
                    msb = ""
                if lsb == "0":
                    lsb = ""

                if msb.isdigit():
                    msb = "%d" % (int(msb) + 1)
                if lsb.isdigit():
                    lsb = "%d" % (int(lsb) + 1)

                if msb[-2:] == "-1":
                    msb = msb[:-2]
                if lsb[-2:] == "-1":
                    lsb = lsb[:-2]

                return "intbv(0)[%s:%s]" % (msb, lsb)
            else:
                return "intbv(0)[??]"


if __name__ == "__main__":
    if not len(sys.argv) == 2:  # noqa: PLR2004
        print("Usage : python %s <filename>.v" % (sys.argv[0]))
        sys.exit()
    mod = verilog_module(ifile=sys.argv[1])
    print("module name is: {}".format(mod.get_module_name()))

    print("Instantiation Template:")
    print(mod.inst_template())
