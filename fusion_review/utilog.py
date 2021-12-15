"""

"""


from fusion_review.figpan import IntensityTraceFigurePanel
import matplotlib.pyplot as plt
import numpy as np
import os


class UserInputHandler:

    def __init__(self, num_rows, num_cols, current_index, intensity_database):
        self.start_trace = current_index - (num_rows * num_cols) + 1
        self.end_trace = current_index + 1
        self.id = intensity_database
        self.quit_flag = "q"
        self.resume_flag = "r"
        self.previous_flag = "p"
        self.fusion_flag = "f"
        self.next_flag = "n"
        self.undo_flag = "u"
        self.exclude_flag = "x"
        self.save_flag = "s"
        self.write_flag = "w"
        self.invert_flag = "i"
        self.arrange_flag = "a"
        self.help_flag = "h"
        self.prompt_msg = "User Review Traces - input command below, press \'" + self.help_flag + "\' for help:\n"

    def handle_fusion(self, trace_num):
        print("Select the fusion start point followed by the fusion end point...")
        itfp = IntensityTraceFigurePanel(self.id.num_traces, 1, 1, self.id)
        itfp.curridx = trace_num - 1
        itfp.handle_single_plot(trace_num)
        points = plt.ginput(n=2, timeout=0, show_clicks=True)
        self.id.df["Status"][trace_num - 1] = 1
        self.id.df["isFusion"][trace_num - 1] = 1
        self.id.df["FusionStart"][trace_num - 1] = round(points[0][0])
        self.id.df["FusionEnd"][trace_num - 1] = round(points[1][0])
        output_str = "Fusion Start: {}\nFusion Median: {}\nFusion End: {}\n".format(
            str(self.id.df["FusionStart"][trace_num - 1]),
            str(round(np.median([self.id.df["FusionStart"][trace_num - 1], self.id.df["FusionEnd"][trace_num - 1]]))),
            str(self.id.df["FusionEnd"][trace_num - 1]))
        print(output_str)

    def handle_exclusion(self, trace_num):
        self.id.df["isExclusion"][trace_num - 1] = 1
        self.id.df["isFusion"][trace_num - 1] = 0
        self.id.df["FusionStart"][trace_num - 1] = 0
        self.id.df["FusionEnd"][trace_num - 1] = 0

    def handle_undo(self, trace_num):
        self.id.df["isFusion"][trace_num - 1] = 0
        self.id.df["FusionStart"][trace_num - 1] = 0
        self.id.df["FusionEnd"][trace_num - 1] = 0
        self.id.df["isExclusion"][trace_num - 1] = 0

    def handle_status(self):
        for i in range(self.start_trace-1, self.end_trace-1):
            self.id.df["Status"][i] = 1

    def handle_resume(self, output_file):
        with open(output_file, "r") as txt:
            txt_lines = txt.readlines()[1:]
            for line in txt_lines:
                line_split = line.split(",")
                trace_idx = int(line_split[0]) - 1
                self.id.df["Status"][trace_idx] = int(line_split[1])
                isFusion = int(line_split[2])
                self.id.df["isFusion"][trace_idx] = isFusion
                if isFusion:
                    self.id.df["FusionStart"][trace_idx] = int(line_split[3])
                    self.id.df["FusionEnd"][trace_idx] = int(line_split[4])
                isExclusion = int(line_split[5][:-1])
                self.id.df["isExclusion"][trace_idx] = isExclusion
                
    def handle_arrangement(self):
        while True:
            try:
                rows, cols = [int(x) for x in input("Enter number of desired rows & columns separated by a space:\n").split()]
            except ValueError:
                print("User must input 2 valid integers separated by a space!")
                continue
            else:
                self.num_rows, self.num_cols = int(rows), int(cols)
                if self.num_rows < 1 or self.num_cols <= 1:
                    print("User must input valid numbers - figure panel must have at least 1 row & >1 columns!")
                    continue
                return 0

    def handle_help(self):
        help_msg = "Available terminal command flags are as listed:\n"
        help_msg += "\'" + self.quit_flag + "\'" + " - quit\n"
        help_msg += "\'" + self.next_flag + "\'" + " - advance to the next panel\n"
        help_msg += "\'" + self.previous_flag + "\'" + " - return to the previous panel\n"
        help_msg += "\'" + self.resume_flag + "\'" + " - resume previous re-scoring at last reviewed panel\n"
        help_msg += "\'" + self.fusion_flag + "\'" + " - mark a trace on the current panel as fusion\n"
        help_msg += "\'" + self.undo_flag + "\'" + " - mark a trace on the current panel as NOT fusion\n"
        help_msg += "\'" + self.exclude_flag + "\'" + " - mark a trace on the current panel for exclusion in efficiency\n"
        help_msg += "\'" + self.save_flag + "\'" + " - save the current progression***\n***NOTE: THIS MUST BE USED TO " \
                                                   "SAVE PROGRESS, OTHERWISE RE-SCORING WILL *NOT* BE SAVED!!!\n"
        help_msg += "\'" + self.write_flag + "\'" + " - write all traces, including those not reviewed yet, to .txt output file\n"
        help_msg += "\'" + self.arrange_flag + "\'" + " - arrange the figure panel as an array of m_rows x n_columns\n"
        help_msg += "\'" + self.invert_flag + "\'" + " - invert colors (great for night time & reducing eye strain!)\n"
        print(help_msg)

    def handle_usr_input(self):
        while True:
            usr_input = input(self.prompt_msg)
            if usr_input == self.quit_flag:
                return -1
            elif usr_input == self.next_flag:
                self.handle_status()
                return 0
            elif usr_input == self.previous_flag:
                return 1
            elif usr_input == self.save_flag:
                dw = DataWriter(self.id)
                dw.set_output_dst()
                dw.update_fusion_output()
                return 4
            elif usr_input == self.undo_flag:
                while True:
                    trace_input = input("Trace number to undo fusion/exclusion: ")
                    try:
                        int(trace_input)
                    except ValueError:
                        if trace_input == self.quit_flag:
                            return -1
                        print("User must input a number!")
                        continue
                    else:
                        trace_input = int(trace_input)
                        if trace_input < self.start_trace or trace_input > self.end_trace-1:
                            print("User must input a valid number!")
                            continue
                        plt.close()
                        self.handle_undo(trace_input)
                        return 3
            elif usr_input == self.exclude_flag:
                while True:
                    trace_input = input("Trace number to exclude from efficiency calculation: ")
                    try:
                        int(trace_input)
                    except ValueError:
                        if trace_input == self.quit_flag:
                            return -1
                        print("User must input a number!")
                        continue
                    else:
                        trace_input = int(trace_input)
                        if trace_input < self.start_trace or trace_input > self.end_trace-1:
                            print("User must input a valid number!")
                            continue
                        plt.close()
                        self.handle_exclusion(trace_input)
                        return 8
            elif usr_input == self.fusion_flag:
                while True:
                    trace_input = input("Trace number to mark fusion: ")
                    try:
                        int(trace_input)
                    except ValueError:
                        if trace_input == self.quit_flag:
                            return -1
                        print("User must input a number!")
                        continue
                    else:
                        trace_input = int(trace_input)
                        if trace_input < self.start_trace or trace_input > self.end_trace-1:
                            print("User must input a valid number!")
                            continue
                        plt.close()
                        self.handle_fusion(trace_input)
                        return 2
            elif usr_input == self.resume_flag:
                dw = DataWriter(self.id)
                dw.set_output_dst()
                if os.path.exists(dw.output):
                    self.handle_resume(dw.output)
                else:
                    print("No fusion data exist yet!")
                    return 6
                return 5
            elif usr_input == self.invert_flag:
                print("Invert colors.")
                return 7
            elif usr_input == self.write_flag:
                dw = DataWriter(self.id)
                dw.set_output_dst()
                dw.write()
                return 9
            elif usr_input == self.arrange_flag:
                return 10
            elif usr_input == self.help_flag:
                self.handle_help()
                continue
            else:
                print("User must input a valid option flag!")


class DataWriter:

    def __init__(self, intensity_database):
        self.id = intensity_database
        self.output = ""
        self.srcmat = ""

    def get_src_file_name(self, tag, fmt):
        src_txt_file = self.id.src
        src_filename = os.path.split(src_txt_file)[1]
        src_filename = src_filename[:src_filename.index(".txt")]
        dst_filename = "".join([src_filename, "_", tag, fmt])
        return dst_filename

    def get_src_mat_file(self):
        pardir = self.id.pardir
        trace_analysis_subdir = os.path.join(pardir, "TraceAnalysis")
        src_txt_filename = os.path.split(self.id.src)[1]
        src_mat_filename = "".join([src_txt_filename[:src_txt_filename.index(".txt")], "-Rvd", ".mat"])
        src_mat_filepath = os.path.join(trace_analysis_subdir, src_mat_filename)
        if os.path.exists(src_mat_filepath):
            return src_mat_filepath
        else:
            raise FileNotFoundError("Cannot find source .mat file for: {}".format(self.id.src))

    def set_output_dst(self):
        pardir = self.id.pardir
        dst_dir = os.path.join(pardir, "TraceAnalysis", "FusionOutput")
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        filename = self.get_src_file_name("FusionOutput", ".txt")
        dst_path = os.path.join(dst_dir, filename)
        src_mat_filepath = self.get_src_mat_file()
        self.srcmat = src_mat_filepath
        self.output = dst_path

    def set_drawings_dst(self):
        pardir = self.id.pardir
        dst_dir = os.path.join(pardir, "TraceAnalysis", "TraceDrawings")
        filename = self.get_src_file_name("Collated", ".tif")
        dst_path = os.path.join(dst_dir, filename)
        return dst_path

    def update_fusion_output(self):
        with open(self.output, "w+") as dst:
            dst.write(self.srcmat + "\n")
            for i in range(0, self.id.num_traces):
                if self.id.df["Status"][i] == 1:
                    line = [str(self.id.df[key][i]) for key in self.id.col_names if key != "Data" and
                            key != "RawDataNorm"]
                    line = ",".join(line)
                    dst.write(line + "\n")

    def write(self):
        with open(self.output, "w+") as dst:
            dst.write(self.srcmat + "\n")
            for i in range(0, self.id.num_traces):
                line = [str(self.id.df[key][i]) for key in self.id.col_names if key != "Data" and
                        key != "RawDataNorm"]
                line = ",".join(line)
                dst.write(line + "\n")
