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


from ..tb_endpoints import get_intfc_lst


class verilog_port:
    """
    Verilog Port Class
    """

    def __init__(  # noqa: PLR0912, PLR0913
        self,
        pstyle=None,
        pdir=None,
        ptype=None,
        psign=None,
        psize=None,
        pname=None,
        pvalue=None,
        debug=False,
    ):
        """
        style is string 'parameter' or 'port'
        dir is a string such as 'input' or 'output'
        type is a string such as 'integer, 'reg', 'wire', 'tri', or '' if none
        sign is a string such as 'signed' or '' if none
        size is a string such as '[7:0]' or '' if none
        name (name of port)
        value is any string after name or '' if none
        """
        if pstyle in {"port", "parameter"}:
            self.pstyle = pstyle
        else:
            raise Exception("Unknown port style, should be parameter or port")

        if pdir in {"", "input", "output", "inout"}:
            self.pdir = pdir
        else:
            raise Exception("Unknown port dir, should be input, output, or inout")

        if ptype in {"", "integer", "reg", "wire", "tri"}:
            self.ptype = ptype
        else:
            raise Exception("Unknown port type, should be integer, reg, wire, or tri")

        if psign in {"", "signed"}:
            self.psign = psign
        else:
            raise Exception("Unknown port sign, should be signed")

        # fixme parse this into upper and lower indices
        self.psize = psize

        self.pname = pname

        # search for signals that may be part of an interface
        self.is_iface = False
        if_lst = get_intfc_lst(debug=debug)
        for intfc_nm in if_lst:
            if intfc_nm in self.pname:
                s = self.pname.split(intfc_nm)
                if len(s) == 0:
                    if debug:
                        print(f"{self.pname} not in {if_lst}")
                    self.is_iface = False
                    self.iface_name = ""
                    self.iface = ""
                elif len(s) == 1:
                    raise Exception(f"Name {self.pname} either has no unique part before or after interface type")
                elif len(s) == 2:  # noqa: PLR2004
                    self.is_iface = True
                    self.iface = intfc_nm.strip("_")  # remove underscore from interface

                    if "_" in s[1][1:]:
                        iface_full = s[1].split("_")
                        self.iface_name = s[0] + intfc_nm + "_".join(iface_full[:-1])
                        self.iface_sig = iface_full[-1]
                    else:
                        self.iface_name = s[0] + self.iface
                        self.iface_sig = s[1]
                else:
                    raise Exception(f"signal split has too many parts {s}")
        new_value = pvalue
        if ";" in pvalue:
            new_value, _ = pvalue.split(";")
        if "=" in new_value:
            _, new_value = new_value.split("=")
        self.pvalue = "=" + new_value

    def format_lparam(self, pvalue_override=None, width_lst=None):
        """
        return formatted localparam
        Ie:
            localparam opt_type opt_size param_name1 opt_value;
        width_list = lengths of the following [pdir, ptype, psign, psize, pname, pvalue]
        """
        if len(width_lst) != 6:  # noqa: PLR2004
            raise Exception("Whoops, width_lst not correct size")
        else:
            ret_lst = ["localparam"]
            if width_lst[0] != 0:
                ret_lst.append("{:{width}}".format(self.pdir, width=width_lst[0]))
            if width_lst[1] != 0:
                ret_lst.append("{:{width}}".format(self.ptype, width=width_lst[1]))
            if width_lst[2] != 0:
                ret_lst.append("{:{width}}".format(self.psign, width=width_lst[2]))
            if width_lst[3] != 0:
                ret_lst.append("{:{width}}".format(self.psize, width=width_lst[3]))
            if width_lst[4] != 0:
                ret_lst.append("{:{width}}".format(self.pname, width=width_lst[4]))
            if pvalue_override is None:
                if width_lst[5] != 0:
                    ret_lst.append("{:{width}}".format(self.pvalue, width=width_lst[5]))
            elif width_lst[5] != 0:
                ret_lst.append("{:{width}}".format(pvalue_override, width=width_lst[5]))
            ret_lst.append(";\n")
            return " ".join(ret_lst)

    def format_signal(self, width_lst=None, strip_defaults=False, dflt_ptype="localparam"):
        """
        return formatted signal
        Ie:
            reg some_reg = 0;
            wire some_wire = 0;
        width_list = lengths of the following [pdir, ptype, psign, psize, pname, pvalue]
        """
        if len(width_lst) != 6:  # noqa: PLR2004
            raise Exception("Whoops, width_lst not correct size")
        else:
            ret_lst = [dflt_ptype]

            if self.pdir == "input":
                ret_lst = ["reg "]
            elif self.pdir == "output":
                ret_lst = ["wire"]
            if width_lst[2] != 0:
                ret_lst.append("{:{width}}".format(self.psign, width=width_lst[2]))
            if width_lst[3] != 0:
                ret_lst.append("{:{width}}".format(self.psize, width=width_lst[3]))
            if width_lst[4] != 0:
                ret_lst.append("{:{width}}".format(self.pname, width=width_lst[4]))
            if width_lst[5] != 0:
                if strip_defaults:
                    ret_lst.append("{:{width}}".format("", width=width_lst[5]))
                else:
                    ret_lst.append("{:{width}}".format(self.pvalue, width=width_lst[5]))
            ret_lst.append(";\n")
            return " ".join(ret_lst)
