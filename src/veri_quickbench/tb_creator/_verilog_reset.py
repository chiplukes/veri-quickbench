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


class verilog_reset:
    """
    Verilog Reset Class
    """

    def __init__(self, name=None, polarity_is_positive=True, associated_clock=None):
        """
        name - string name of reset
        polarity_is_positive - boolean true if reset when logic 1
        associated_clock - string name of associated clock
        """
        if name is None:
            raise Exception("reset signel must have a name")
        else:
            self.name = name

        if polarity_is_positive:
            self.reset_assert = 1
            self.reset_deassert = 0
        else:
            self.reset_assert = 0
            self.reset_deassert = 1

        self.associated_clock = associated_clock

    def create_reset_template_myhdl(self):
        """
        creates a reset sequence for MyHDL for a reset
        """
        return f"""
        yield tf.{self.associated_clock}.posedge
        tf.{self.name}.next = {self.reset_assert}
        yield tf.{self.associated_clock}.posedge
        tf.{self.name}.next = {self.reset_deassert}
        for _ in range(10):
            yield tf.{self.associated_clock}.posedge
"""
