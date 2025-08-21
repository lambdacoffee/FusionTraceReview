"""
This is the __main__ script for -- Project: SPITRev (SingleParticleIntensityTraceReview) -- and contains support for
command line execution from the End User.

Created by - { alias : lambdacoffee :: author : Marcos Cervantes }

To use:
    $ python3 -m trace_reviewer "../path/to/data_analysis_parent_directory"
"""


import matplotlib
import argparse
from utilities import InitialChoicePrompt, UserInputHandler
from trace_manager import TraceManager
from figpan import FigurePanel
import os


def main(par_src_dir):
    if not os.path.isdir(par_src_dir):
        raise FileNotFoundError("Could not find {}".format(par_src_dir))
    tm = TraceManager(par_src_dir)
    tm.get_info()
    tm.configure()
    tm.set_dst_files()
    tm.initialize_fusion_output_files()
    tm.initialize_changepoint_detection_output_files()
    icp = InitialChoicePrompt()
    icp.build_prompt(tm)
    user_input = icp.get_input(tm)

    tm.setup(user_input)
    rows = 3
    columns = 4
    matplotlib.use("Tkagg")
    fp = FigurePanel(rows, columns, len(tm.traces[user_input]["TraceData"]))
    fp.allocate(tm.traces[user_input]["TraceData"], tm.info[user_input]["StartFrame"])
    input_handler = UserInputHandler(fp, tm.traces[user_input]["OutputPath"])
    iter(fp)
    while True:
        try:
            next(fp)
        except StopIteration:
            fp.panel_value = 1
        fp.fill()
        fp.fig.canvas.draw()
        fp.fig.canvas.flush_events()
        input_handler.handle_input()
        panel_change = input_handler.flags[input_handler.user_choice]["panelChange"]
        fp.panel_value += (panel_change - 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parent source directory path: ")
    parser.add_argument("src_path", help="path of the data directory", type=str)
    arg = parser.parse_args()
    main(arg.src_path)
