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


def work_header(author="", company="", date="", comment="#"):
    ret_str = f"""
{comment} This software constitutes an unpublished work and contains valuable trade
{comment} secrets and proprietary information belonging to {company}
{comment} None of the source code may be copied, duplicated or disclosed without
{comment} the express written permission of {company}.
{comment} Author(s):
{comment}  {author} {date}
"""
    return ret_str


def mit_header(author="", date="", comment="#"):
    ret_str = f"""
{comment} MIT License
{comment}
{comment} Copyright (c) {date} {author}
{comment}
{comment} Permission is hereby granted, free of charge, to any person obtaining a copy
{comment} of this software and associated documentation files (the "Software"), to deal
{comment} in the Software without restriction, including without limitation the rights
{comment} to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
{comment} copies of the Software, and to permit persons to whom the Software is
{comment} furnished to do so, subject to the following conditions:
{comment}
{comment} The above copyright notice and this permission notice shall be included in all
{comment} copies or substantial portions of the Software.
{comment}
{comment} THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
{comment} IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
{comment} FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
{comment} AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
{comment} LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
{comment} OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
{comment} SOFTWARE.
"""
    return ret_str
