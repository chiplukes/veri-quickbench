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

"""
Helper functions for testbenches
"""

import os
from inspect import currentframe, getargvalues
from pathlib import Path


def get_fname() -> str:
    """gets name of a function from within said function"""
    return currentframe().f_back.f_code.co_name


def param_changes(dict1, dict2):
    """
    finds changes between dict1 and dict2
    """
    return dict(set(dict1.items()) ^ set(dict2.items()))


def param_dict_to_str(pdict):
    """
    returns dictionary of parameters as string "PARAM1_VALUE_PARAM2_VALUE"
    """
    return "_".join([f"{key}_{pdict[key]}" for key in pdict])


def print_param_changes(dict1, dict2):
    """
    prints string showing differences between dict1 and dict2
    """
    return param_dict_to_str(pdict=dict(set(dict1.items()) ^ set(dict2.items())))


def get_kwargs_str():
    """
    gets parameters passed to a function from within said function
    returns them as string "PARAM1_VALUE_PARAM2_VALUE"
    """
    frame = currentframe().f_back
    keys, _, _, values = getargvalues(frame)
    kwargs_str = ""
    for key in keys:
        if key != "self":
            kwargs_str += f"{key}_{values[key]}"
    return kwargs_str


def get_kwargs_dict():
    """gets dictionary of parameters passed to a function from within said function"""
    frame = currentframe().f_back
    keys, _, _, values = getargvalues(frame)
    kwargs_dict = {}
    for key in keys:
        if key != "self":
            kwargs_dict[key] = values[key]
    return kwargs_dict


def mk_test_folder(folder=None):
    """
    makes a new folder and changes to that directory
    folder is a path object
    """
    if not isinstance(folder, (Path,)):
        raise TypeError(f"{folder} must be a pathlib Path object")
    folder.mkdir(parents=True, exist_ok=True)
    # cd into unique subfolder so generated files placed there
    os.chdir(folder)
    return folder
