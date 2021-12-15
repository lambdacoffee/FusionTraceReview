"""

"""


from fusion_review.intensities import IntensitySuperStructure, IntensityDatabase
from fusion_review.figpan import IntensityTraceFigurePanel
from fusion_review.utilog import UserInputHandler, DataWriter
import matplotlib.pyplot as plt
import numpy as np
import argparse
import imageio
import os


def handle_input_codes(panel_num, trace_panel, input_handler):
    """
    This handles the logic associated with each user_input_code returned from UserInputHandler object instance.
    Codes are as follows (taken from the utilog.py file):
        * -1: quit
        * 0: previous
        * 2: fusion
        * 3: undo
        * 4: save
        * 5: resume
        * 6: resume failed - no fusion data output .txt file exists yet
        * 7: invert
        * 8: exclude
        * 9: write
        * 10: change #rows, #columns

    :param panel_num: the current panel number of the current dataset
    :param trace_panel: the current panel object to be displayed
    :param input_handler: UserInputHandler object instance
    :return: panel_num: the panel number to display after handling logic
    """
    user_input_code = input_handler.handle_usr_input()
    if user_input_code == -1:
        print("Terminating sequence - abort process")
        exit(user_input_code)
    elif user_input_code == 1:
        # previous panel
        if panel_num > 1:
            panel_num -= 2
            new_idx = input_handler.start_trace - (trace_panel.rows * trace_panel.cols) - 1
            trace_panel.curridx = new_idx if new_idx > 0 else 0
        else:
            panel_num -= 1
            trace_panel.curridx = input_handler.start_trace - 1
    elif user_input_code == 2 or user_input_code == 3 or user_input_code == 8:
        # fusion! or undo-fusion/exclusion or exclusion!
        panel_num -= 1
        trace_panel.curridx = input_handler.start_trace - 1
    elif user_input_code == 4:
        print("Progress has been saved & written!")
        panel_num -= 1
        trace_panel.curridx = input_handler.start_trace - 1
    elif user_input_code == 5:
        # resume session
        for trace in range(0, len(trace_panel.id.df["Status"])):
            if not trace_panel.id.df["Status"][trace]:
                trace_panel.curridx = trace
                break
        panel_num = (trace_panel.curridx + 1) // (trace_panel.rows * trace_panel.cols)
    elif user_input_code == 6:
        panel_num -= 1
        trace_panel.curridx = input_handler.start_trace - 1
    elif user_input_code == 7:
        # invert colors
        panel_num -= 1
        trace_panel.curridx = input_handler.start_trace - 1
        trace_panel.inverted = not trace_panel.inverted
        trace_panel.invert_colors()
    elif user_input_code == 9:
        print("Fusion data for all traces has been written!")
        panel_num -= 1
        trace_panel.curridx = input_handler.start_trace - 1
    elif user_input_code == 10:
        input_handler.handle_arrangement()
        trace_panel.rows = input_handler.num_rows
        trace_panel.cols = input_handler.num_cols
        trace_panel.figs = ((input_handler.id.num_traces - trace_panel.stidx) // (trace_panel.rows * trace_panel.cols)) + 1
        print("Updated figure panel to new configuration.")
        panel_num -= 1
        trace_panel.curridx = input_handler.start_trace - 1
    return panel_num


def preStart(parent_source_directory):
    iss = IntensitySuperStructure(parent_source_directory)
    if not os.path.exists(iss.output):
        iss.get_info()
        print("Gathering data...please wait...")
        iss.gather_data()
    return 0


def prompt_user_choice(superstructure):
    promt_msg = ["Input corresponding number to desired trace container:\n"
                 + "additional options: \'q\' - quit, \'j\' - draw to tifs"]
    i = 1
    sources = list(superstructure.sources)
    sources.sort()
    for source in sources:
        line = "{} - {}".format(i, source)
        promt_msg.append(line)
        i += 1
    while True:
        usr_input = input("\n".join(promt_msg) + "\n")
        try:
            int(usr_input)
        except ValueError:
            if usr_input == "q":
                exit(0)
            elif usr_input == "j":
                confirmation = input("Create drawings and export traces to tifs?\n\'y\' or \'n\': ")
                if confirmation == "y":
                    print("Confirmation Accepted, proceeding with drawing process...")
                    draw_to_tifs(superstructure)
                    exit(0)
                continue
            print("User must input valid number!")
            continue
        else:
            return sources[int(usr_input) - 1]


def draw_to_tifs(intensity_superstructure):
    flow_start_dict = intensity_superstructure.get_flux_start()
    for src in intensity_superstructure.sources:
        print("Drawing in progress, source:\n{}".format(src))
        datum_key = intensity_superstructure.get_datum_key(src)
        ID = IntensityDatabase(intensity_superstructure.par, datum_key)
        ID.set_source(src)
        ID.get_traces(intensity_superstructure)
        ID.set_times(flow_start_dict[datum_key])

        itfp = IntensityTraceFigurePanel(ID.num_traces, 3, 4, ID)
        imarr = []
        dw = DataWriter(ID)
        dst_path = dw.set_drawings_dst()
        dw.set_output_dst()
        uih = UserInputHandler(itfp.rows, itfp.cols, itfp.curridx, ID)
        if os.path.exists(dw.output):
            uih.handle_resume(dw.output)
        trace_drawings_subdir = os.path.split(dst_path)[0]
        temp_path = os.path.join(trace_drawings_subdir, "temp.tif")
        itfp.disp = False
        for panel in range(itfp.stidx, itfp.figs):
            if itfp.isSingle:
                itfp.handle_single_plot(panel + 1)
            else:
                fig, axes = itfp.form_panel(panel + 1)
                itfp.handle_multiple_plots(axes)
                fig.savefig(temp_path)
            plt.close()
            im = imageio.imread(temp_path, format="TIFF")
            imarr.append(im)
        os.remove(temp_path)
        imageio.mimwrite(dst_path, np.asarray(imarr), format="TIFF")


def main(par_src_dir):
    preStart(par_src_dir)
    iss = IntensitySuperStructure(par_src_dir)
    iss.get_info()
    iss.reread()
    flow_start_dict = iss.get_flux_start()
    source_path = prompt_user_choice(iss)
    datum_key = iss.get_datum_key(source_path)
    ID = IntensityDatabase(iss.par, datum_key)
    ID.set_source(source_path)
    ID.get_traces(iss)
    ID.set_times(flow_start_dict[datum_key])
    # ID is now dict
    rows = 3
    cols = 4
    while True:
        itfp = IntensityTraceFigurePanel(ID.num_traces, rows, cols, ID)
        panel = itfp.stidx
        print("Displaying traces for: " + os.path.split(source_path)[-1])
        while panel < itfp.figs:
            if itfp.isSingle:
                itfp.handle_single_plot(panel + 1)
            else:
                fig, axes = itfp.form_panel(panel + 1)
                itfp.handle_multiple_plots(axes)
            plt.pause(0.1)
            uih = UserInputHandler(itfp.rows, itfp.cols, itfp.curridx, ID)
            panel = handle_input_codes(panel + 1, itfp, uih)
            plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parent source directory path: ")
    parser.add_argument("src_path", help="path of the data directory", type=str)
    arg = parser.parse_args()
    main(arg.src_path)
