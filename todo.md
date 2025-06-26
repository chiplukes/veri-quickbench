* verbosity from cli
* test more files in source folder and in testbench folder
* if only 1 clock in module skip association with axi,axis
* nicer output when verilog has errors
* when choice to not add all other files from source folder, still need to add the selected source file
* pull corresponding comment from module parameters and print it during testfixture config.  Ie. give explanantion of of ELEMENT_SIZE_BITS
* tdest, tid, etc. signals cannot be size 0, even if they are not used, fix this!
* better exceptions than just things like AssertionError
* option to choose CUSTOM file header.
* add example of how to pull parameters from the tf_config.PARAMS_CORE
* _verilog_iface.py line 104, connect of axi bus parameters is not correct:
    * if the AXI_DATA_WIDTH in params_iface['AXI_DATA_WIDTH'] was named something else in the UUT, then this breaks
* organize example source code before sink code
* somehow identify interface as being master or slave
* various asserts in endpoints should print out user friendly messages
* clean up scaffolding section in test_*.py file.  Since I removed the MyHDL uut support maybe this can be cleaner.
* when creating tf_config for myhdl, query for parameters for signal sizing and parameters for uut, then add to tf_config, see test__axis_fifo.py
* get_kwargs_str inside functions isn't great when parameters are passed in as a dict, instead unpack the dict and use those names
* add a couple of verilog file tests for _verilog_module.py parser
* port add in back to back read requests (as many as exist in read queue - see axi_crossbar3x1 )
* add example logic for interfaces, clocks found when parsing verilog file, or just ask for example code in questionary

cleaning up:
replace pyparsing with lark
replace questionary filesystem stuff with package that does that
