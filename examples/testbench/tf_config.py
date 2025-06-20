# Configuration file for the testbench

from pathlib import Path

# Name of Verilog or MyHDL module being simulated (must match file name)
UUT_NAME = "passthru"

# Paths Setup

# Testbench Temporary Folder
TB_DIR = Path(__file__)
TB_DIR = TB_DIR.parent / ".tmptst"

# Path to Source code
SRC_DIR = Path(__file__).parents[1] / "src"

# Additional Verilog source files
srcs = []
srcs.append(str(Path(__file__).parents[1] / "src" / "passthru.v"))
VERILOG_SRC_FILES = " ".join(srcs)


# Parameters used for uut interface
PARAMS_IFACE = {
    "DATA_WIDTH": 256,
    "USER_WIDTH": 1,
    "DEST_WIDTH": 1,
    "ID_WIDTH": 1,
    "AXI_ADDR_WIDTH": 32,
    "AXI_ID_WIDTH": 8,
    "AXI_DATA_WIDTH": 256,
}


# Parameters for uut core functionality (timeouts, etc.)
PARAMS_CORE = {}


# Save VCD (True, False)
TRACE = True
