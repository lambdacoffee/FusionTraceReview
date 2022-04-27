"""
This is the __main__ script for -- Project: FusionTraceReview -- and contains support for command line execution.

Created by - { alias : lambdacoffee :: author : Marcos Cervantes }

To use:
    $ python3 -m fusion_review "../path/to/data_analysis_parent_directory"
"""


from fusion_review.utilities import UserInputHandler, DataWriter, TracePanelWriter, LearningExporter
from fusion_review.intensities import IntensitySuperStructure, IntensityDatabase, DefocusHandler
from fusion_review.figpan import IntensityTraceFigurePanel
import fusion_review.multiprocutils as mpu
import matplotlib.pyplot as plt
import matplotlib as mpl
import pygetwindow
import argparse
import os


def handle_input_codes(panel_num, trace_panel, input_handler):
    """
    This handles the logic associated with each user_input_code returned from UserInputHandler object instance.
    Codes are as follows (taken from the utilities.py file):
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
        * 11: toggle de-focusing events
        * 12: binding-fusion

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
    elif user_input_code == 2 or user_input_code == 3 or user_input_code == 8 or user_input_code == 12:
        # fusion! or undo-fusion/exclusion or exclusion! or binding-fusion!
        panel_num -= 1
        trace_panel.curridx = input_handler.start_trace - 1
    elif user_input_code == 4:
        print("Progress has been saved & written.")
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
        print("Fusion data for all traces has been written.")
        panel_num -= 1
        trace_panel.curridx = input_handler.start_trace - 1
    elif user_input_code == 10:
        input_handler.handle_arrangement()
        trace_panel.rows = input_handler.itfp.rows
        trace_panel.cols = input_handler.itfp.cols
        trace_panel.figs = ((input_handler.id.num_traces - trace_panel.stidx) // (trace_panel.rows * trace_panel.cols)) + 1
        print("Updated figure panel to new configuration.")
        panel_num -= 1
        trace_panel.curridx = input_handler.start_trace - 1
    elif user_input_code == 11:
        # toggle de-focusing events
        panel_num -= 1
        dw = DataWriter(trace_panel.id)
        try:
            input_handler.dh.read(dw)
        except FileNotFoundError:
            print("\n* WARNING *\n\n"
                  "Trace changepoint analysis output not found - to view, quit & re-run program with flag \'c\'.")
        else:
            trace_panel.curridx = input_handler.start_trace - 1
            trace_panel.show_defocus = not trace_panel.show_defocus
    return panel_num


def preStart(parent_source_directory):
    """
    Collates data from /TraceText subdirectory into a .csv file to load into intensity superstructure.

    Args:
        parent_source_directory: the top-level directory for the entire data analysis, specified by User

    Returns:
        0
    """
    iss = IntensitySuperStructure(parent_source_directory)
    if not os.path.exists(iss.output):
        iss.get_info()
        print("Gathering data, please wait...")
        iss.gather_data()
    return 0


def prompt_user_choice(superstructure):
    prompt_msg = ["Input corresponding number to desired trace container:\n"
                  "additional options: \'q\' - quit, "
                  "\'j\' - draw to tifs,"
                  "\'c\' - perform trace changepoint analysis,"
                  "\'l\' - export data for learning"]
    i = 1
    sources = list(superstructure.sources)
    sources.sort()
    for source in sources:
        line = "{} - {}".format(i, source)
        prompt_msg.append(line)
        i += 1
    while True:
        usr_input = input("\n".join(prompt_msg) + "\n")
        try:
            int(usr_input)
        except ValueError:
            if usr_input == "q":
                exit(0)
            elif usr_input == "j":
                confirmation = input("Create drawings and export traces to tifs?\n\'y\' or \'n\': ")
                if confirmation == "y":
                    handle_drawing_process(superstructure)
                continue
            elif usr_input == "c":
                confirmation = input("Proceed with analyzing traces for changepoint events?\n\'y\' or \'n\': ")
                if confirmation == "y":
                    handle_defocus_analysis_process(superstructure)
                continue
            elif usr_input == "l":
                confirmation = input("Proceed with exporting data and labels for learning?\n\'y\' or \'n\': ")
                if confirmation == "y":
                    handle_export(superstructure)
                continue
            print("User must input valid number or flag!")
            continue
        else:
            return sources[int(usr_input) - 1]


def handle_export(intensity_superstructure):
    le = LearningExporter(intensity_superstructure)
    le.set_label_data()
    le.collect_data()
    le.export_learning()


def handle_drawing_process(intensity_superstructure):
    tpw = TracePanelWriter(intensity_superstructure)
    if multi_core_request():
        mpu.mpu_draw_to_tifs(intensity_superstructure, tpw)
    else:
        for src in intensity_superstructure.sources:
            tpw.draw(src)


def handle_defocus_analysis_process(intensity_superstructure):
    if multi_core_request():
        mpu.mpu_analyze_defocusing_events(intensity_superstructure)
    else:
        analyze_defocusing_events(intensity_superstructure)


def analyze_defocusing_events(intensity_superstructure):
    flow_dictionary = intensity_superstructure.get_flux_start()
    for src in intensity_superstructure.sources:
        datum_key = intensity_superstructure.get_datum_key(src)
        ID = IntensityDatabase(intensity_superstructure.par, datum_key)
        ID.set_source(src)
        ID.get_traces(intensity_superstructure)
        ID.set_times(flow_dictionary[datum_key])
        dw = DataWriter(ID)
        dw.defocus_output(isMulti=False)


def multi_core_request():
    num_cores = mpu.ncpus()
    if num_cores > 1:
        confirmation = input("Multiple CPU cores detected. Utilize multi-core processing?\n\'y\' or \'n\': ")
        if confirmation == "y":
            return True
    return False


def main(par_src_dir):
    preStart(par_src_dir)
    iss = IntensitySuperStructure(par_src_dir)
    iss.get_info()
    iss.reread()
    flow_start_dict = iss.get_flux_start()
    cli_title = pygetwindow.getActiveWindow().title
    source_path = prompt_user_choice(iss)
    datum_key = iss.get_datum_key(source_path)
    ID = IntensityDatabase(iss.par, datum_key)
    ID.set_source(source_path)
    ID.get_traces(iss)
    ID.set_times(flow_start_dict[datum_key])
    print("Assuming mode: {}".format(ID.mode))
    # ID is now dict
    dh = DefocusHandler(ID)
    rows = 3
    cols = 4
    mpl.use("Tkagg")
    while True:
        #ID.get_predictions(os.path.join(par_src_dir, "TraceAnalysis", "LearningAnalysis"))
        itfp = IntensityTraceFigurePanel(rows, cols, ID, dh)
        panel = itfp.stidx
        print("Displaying traces for: " + os.path.split(source_path)[-1])
        while panel < itfp.figs:
            if itfp.isSingle:
                itfp.handle_single_plot(panel + 1)
            else:
                fig, axes = itfp.form_panel(panel + 1)
                itfp.handle_multiple_plots(axes)
                fig.canvas.draw_idle()
                fig.canvas.flush_events()
            plt.pause(0.1)
            try:
                cli = pygetwindow.getWindowsWithTitle(cli_title)[0]
                cli.activate()
            except pygetwindow.PyGetWindowException:
                print("Command Line Interface blocked - failed to grab and activate.")
            finally:
                uih = UserInputHandler(itfp, ID, dh)
                panel = handle_input_codes(panel + 1, itfp, uih)
                plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parent source directory path: ")
    parser.add_argument("src_path", help="path of the data directory", type=str)
    arg = parser.parse_args()
    main(arg.src_path)
