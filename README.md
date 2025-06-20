# veri-quickbench

[![Tests Status](https://github.com/chiplukes/python-example-application/actions/workflows/test.yml/badge.svg)]
[![Changelog](https://img.shields.io/github/v/release/chiplukes/python-example-application?include_prereleases&label=changelog)](https://github.com/chiplukes/python-example-application/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](https://github.com/chiplukes/python-example-package/blob/main/LICENSE)

Quick Python based testbench generator for Verilog Files with AXI and AXI-Stream Interfaces.

# Description

This primary use of this project is as a tool for quickly creating MyHDL based testbenches for testing either Verilog or MyHDL modules.

It also has some simple interface driver models (see src\veri_quickbench\tb_endpoints) for the following:

* AXI Stream source and sink
* AXI4 source and sink

Note: these are not full Bus Functional Models just helpful code for generating AXI transactions.

A command line menu system is used as part of the testbench creation to navigate to source folders and query the user about aspects of the generated testbench.

Once the creation of the testbench framework is complete, test specific code can be written.

# Pre-Requisites

* Python
    * See www.python.org for standalone install
    * For UV based install see https://docs.astral.sh/uv/getting-started/installation/

## Dependencies
* Questionary
* MyHDL
* Pyparsing

## Clone repository

```bash
git clone git+https://github.com/chiplukes/veri-quickbench
```

## Package Installation (via uv)

To create a virtual environment (
venv) for your Python project with uv, especially when managing it within a GitHub repository, follow these steps:
1. Navigate to your project directory:
Open your terminal or command prompt and change your current directory to your project's root folder.
2. Create the virtual environment:
Run the command ```uv venv```

    By default, uv will create a directory named .venv in your project's root. This is the standard practice and is often automatically recognized by development tools like VS Code.
    You can specify a different name for the virtual environment directory if you prefer, like ```uv venv my_env```
    To specify a particular Python version, you can use the --python flag, for example: ```uv venv --python 3.11```. If the specified version is not available on your system, uv can even download it for you.

3. Activate the virtual environment:
Before you can use the packages within the virtual environment, you need to activate it. The activation command depends on your operating system and shell:

    * Linux/macOS: ```source .venv/bin/activate```
    * Windows (PowerShell): ```.venv\Scripts\activate```
    * Windows (Bash/Git Bash): ```source .venv/Scripts/activate```

4. Install Package:
    * ```uv pip install .```
    * or ```uv pip install -e .[dev,test]``` for an editable install (useful when developing a module)

## Package Installation (pip)

To create a virtual environment (
venv) for your Python project with uv, especially when managing it within a GitHub repository, follow these steps:
1. Navigate to your project directory:
Open your terminal or command prompt and change your current directory to your project's root folder.
2. Create the virtual environment:
Run the command ```python -m venv .venv```

    By default, uv will create a directory named .venv in your project's root. This is the standard practice and is often automatically recognized by development tools like VS Code.

3. Activate the virtual environment:
Before you can use the packages within the virtual environment, you need to activate it. The activation command depends on your operating system and shell:

    * Linux/macOS: ```source .venv/bin/activate```
    * Windows (PowerShell): ```.venv\Scripts\activate```
    * Windows (Bash/Git Bash): ```source .venv/Scripts/activate```

4. Install Package:
    * ```uv pip install .```
    * or ```uv pip install -e .[dev,test]``` for an editable install (useful when developing a module)


## Creating a testbench
```bash
python -m veri_quickbench --create
```

## To run the tests:
```bash
pytest
```

## Setup pre-commit hooks (optional):
```bash
pre-commit install
```


# Usage

The way I typically use this project is to check it out next to a source folder in an ip repository.

Example folder structure:

```
.some_ip
├── ...
├── veri-quickbench             # folder of this github project! Note: I usually rename this to something like "pysim".
│   ├── examples                # examples of Verilog and MyHDL UUT, can be removed.
│   ├── src                     # packages used by testbench
│   |   └── veri_quickbench     # examples of Verilog and MyHDL UUT, can be removed.
|   |       |── tb_creator      # library used to hep create and run the testbench
|   |       └── tb_endpoints    # library of testbench endpoints (AXI-MM, AXI-Stream)
│   ├── testbench               # WHERE THE CREATED TESTBENCH CODE WILL RESIDE
│   └── tests                   # tests for the
├── src                         # where the source code for the UUT resides
└── ...                         # other folders related to ip
```

This is intended to run in Linux due to the communication between Icarus Verilog and Python.  I tend to run this using Windows Subsystem for Linux (WSL) see here <link to my WSL setup scripts>

However, any Linux environment with Python + Icarus Verilog + MyHDL installed should work.

Once a Linux environment is set up, create the testbench framework by:

* open some_ip folder
* open command prompt and type bash to get into WSL
* create a virtual environment (see Package Installation steps above)
* navigate to \some_ip\testbench
* ```python -m veri_quickbench --create```
* use menu system navigate to top level HDL file location
* answer questions
* upon completion, you will have the following files created

Generated testbench files:
```
testbench                   # testbench folder
├── create_testbench.py     # run this to create the testbench framework
├── test_<uutname>.py       # testbench code
├── tf_config.py            # testbench configuration
├── tf_sigs.py              # testbench signals
└── ...                     # other folders/files related to testbench
```

## Testbench creator questions:

1. **Select type of testbench.**
    * VERILOG - UUT written in Verilog, testbench written in MyHDL
    * MYHDL_ONLY - UUT written in MyHDL, testbench written in MyHDL _(WORK IN PROGRESS)_
    * MYHDL_COSIM - UUT written in MyHDL, testbench written in MyHDL + step where MyHDL code is automatically converted to Verilog and the same testbench is used to simulate. _(WORK IN PROGRESS)_
1. **Navigate to top level HDL file.  There is a menu system that helps navigate the file system.**
1. **Select header file format.**
    * NONE
    * MIT
    * CUSTOM
1. **Add all files from source folder?** _(adds any other source files from source folder)_
    * Yes
    * No
1. **Add additional source files from testbench root folder.** _(Verilog helper files such as UNISIM primitives, etc.)_
    * Yes
    * No
1. **Do the top level ports look correct?** _(a list of ports are shown)_
    * Yes
    * No
1. **Is PARAMETER1-n used for the UUT interface?** _(parameters that are use to modify top level ports widths, etc. are treadted different than parameters that change UUT behavior)_
    * Yes
    * No
1. **Choose default value for PARAMETER1-n**  _(an attempt to parse the default value from the Verilog is made, but an option to enter the value manually is also given)_
1. **Overwrite tf_config.py?** _(if file already exists, option to keep existing file)_
    * Yes
    * No
1. **Overwrite tf_sigs.py?** _(if file already exists, option to keep existing file)_
    * Yes
    * No
1. **Is "clk" a clock?** _(this question is given for any ports that have "clk" or "clock" in the name)_
    * Yes
    * No
    ```python
    # This adds clock driver code into the testfixture

    #######################
    # Clocks
    #######################

    # Note: may want to change the period here
    @always(delay(4))
    def clk_gen():
        tf.clk.next = not tf.clk
    ```
1. **Is "rst" a reset?** _(this question is given for any ports that have "rst" or "reset" in the name)_
    * Yes
    * No
1. **Is "rst" active high?**
    * Yes
    * No
    ```python
    # This add a reset assertion at beginning of testbench

    #######################
    # Resets
    #######################
    yield tf.clk.posedge
    tf.rst.next = 1
    yield tf.clk.posedge
    tf.rst.next = 0
    for _ in range(10):
        yield tf.clk.posedge
    ```
1. **Choose clock associated with (a given reset, or detected interface)**
    * detected clock 1
    * ...
    * detected clock n
    ```
1. **Add Pause logic for (any detected AXI or AXI Stream interface)?**
    * Yes
    * No
    ```python
    # This adds random pause on any of the AXI streams

    #######################
    # Pause Logic
    #######################
    s_axis_pause = Signal(bool(0))
    @instance
    def s_axis_randPause():
        while 1:
            s_axis_pause.next = random.randint(1, PAUSE_FACTOR) == 1
            yield tf.clk.posedge
    #
    m_axi_pause_araddr = Signal(bool(0))
    m_axi_pause_rdata = Signal(bool(0))
    m_axi_pause_awaddr = Signal(bool(0))
    m_axi_pause_wdata = Signal(bool(0))
    m_axi_pause_bresp = Signal(bool(0))
    @instance
    def m_axi_randPause():
        while 1:
            m_axi_pause_araddr.next = random.randint(1, PAUSE_FACTOR) == 1
            m_axi_pause_rdata.next = random.randint(1, PAUSE_FACTOR) == 1
            m_axi_pause_awaddr.next = random.randint(1, PAUSE_FACTOR) == 1
            m_axi_pause_wdata.next = random.randint(1, PAUSE_FACTOR) == 1
            m_axi_pause_bresp.next = random.randint(1, PAUSE_FACTOR) == 1
            yield tf.m_axi_aclk.posedge
    #
    s_axi_pause_araddr = Signal(bool(0))
    s_axi_pause_rdata = Signal(bool(0))
    s_axi_pause_awaddr = Signal(bool(0))
    s_axi_pause_wdata = Signal(bool(0))
    s_axi_pause_bresp = Signal(bool(0))
    @instance
    def s_axi_randPause():
        while 1:
            s_axi_pause_araddr.next = random.randint(1, PAUSE_FACTOR) == 1
            s_axi_pause_rdata.next = random.randint(1, PAUSE_FACTOR) == 1
            s_axi_pause_awaddr.next = random.randint(1, PAUSE_FACTOR) == 1
            s_axi_pause_wdata.next = random.randint(1, PAUSE_FACTOR) == 1
            s_axi_pause_bresp.next = random.randint(1, PAUSE_FACTOR) == 1
            yield tf.s_axi_aclk.posedge

    ```
1. **Add example code?** _(for any of the detected interfaces found in the UUT ports such as AXI, AXI Stream)_
    * Yes
    * No
    ```python
    # This adds example code for driving a logic interfaces

    #######################
    # Example Code
    #######################
    # Notes:
    #  - see test_axi_ep.py and test_axis_ep.py for more use cases
    #######################
    #
    # Create packet and sent it on source_s_axis
    snd_frm = send_axis(source=source_s_axis, data=[i for i in range(10)], list_is_beats=True, tid=0, tdest=0, tuser=0, debug=True)
    # can also pass array of elements into here and set list_is_beats = False
    #snd_frm = send_axis(source=source_s_axis, data=[i for i in range(10)], list_is_beats=True, tid=0, tdest=0, tuser=0, debug=True)
    #
    # Wait for packet on sink_m_axis
    yield wait_axis(sink=sink_m_axis, clk=tf.clk, timeout=2000, msg="waiting m_axis")
    rcv_frm = sink_m_axis.recv()
    assert rcv_frm.data == snd_frm.data # Note: likely need more stuff here!
    #
    # example sink_m_axi read
    #can pre-fill the memory like this
    sink_m_axi.clear()
    sink_m_axi.a = [ _ for _ in range(256)]
    sink_m_axi.d = [ _ for _ in range(256)]
    sink_m_axi.tid = [ _ for _ in range(256)]
    # #can also use a function to simulate data
    # def rd_storage_fn_sink_m_axi(adr,num_beats):
    #     """
    #     function to return data from fake sdram
    #     returns array of rdata beats
    #     """
    #     data_beats = [adr+d for d in range(4*num_beats)]
    #     return data_beats
    # axi_s.rd_storage_fn = rd_storage_fn
    #
    # # for checking writes, can do the following:
    sink_m_axi.clear()
    # wait for write to happen!
    wr_a_actual, wr_d_actual, wr_tid_actual = sink_m_axi.get_write_log()
    #
    # issue AXI write and read requests on source_s_axi
    din = [ _ for _ in range(256)] # 256 bytes
    source_s_axi.issue_write(addr=0, data=din, tid=0)
    source_s_axi.issue_read(addr=0,len_beats=1,arid=0)
    # check source_s_axi.a and source_s_axi.d for returned read data
    #
    ```


## Example Verilog Testbench

myhdl_lib\examples\testbench has an example testbench.  The intent of this is to have a Verilog module that contains AXI and AXI Streaming master and slave interfaces.  This tests the majority of the testbench_creator logic.  It is also a funtional testbench that can be ran.

Run the testbench and then run the tb_creator to see how the files are generated.  Note: it does take a while to get through some of the testbench generator menus in this case.

# FAQ

## Why not just write a testbench in Verilog?

Once you use a high level language such as Python for running a testbench, you will understand! :)

That said, at times it is still best to use a Verilog testbench for portability reasons or when simulation speed is important.

Also, Verilator is a good option for cases where simulation speed is of primary importance.

## Why not just use something like cocotb?

Cocotb is very powerful and is where people should look first for using Python for writing a HDL testbench.  However, having testbench code written using asyncio can be difficult to follow.  Also, when developing a more complex testbench I like to leverage the Python debugger and have found that debugging async code is just painful.  So, my preference has been to just use MyHDL.

## Why did something crash?

This project has evolved over many years and some of the code is pretty old (sometimes fragile) and due for future clean up... However, it has worked pretty well for me over many years.  The intent is that it will be useful to others.  I am happy to help debug anything that breaks.

## License

[MIT](https://choosealicense.com/licenses/mit/)
