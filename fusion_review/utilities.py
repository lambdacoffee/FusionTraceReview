"""

"""


from fusion_review.intensities import DefocusHandler, IntensityDatabase
from fusion_review.figpan import IntensityTraceFigurePanel
import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np
import imageio
import os


class UserInputHandler:

    def __init__(self, figure_panel, intensity_database, defocus_handler):
        self.itfp = figure_panel
        self.start_trace = self.itfp.curridx - (self.itfp.rows * self.itfp.cols) + 1
        self.end_trace = self.itfp.curridx + 1
        self.id = intensity_database
        self.dh = defocus_handler
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
        self.defocus_flag = "d"
        self.help_flag = "h"
        self.prompt_msg = "User Review Traces - input command below, press \'" + self.help_flag + "\' for help:\n"

    def handle_fusion(self, trace_num):
        print("Select the fusion start point followed by the fusion end point...")
        single_itfp = IntensityTraceFigurePanel(1, 1, self.id, self.dh)
        if self.itfp.show_defocus:
            single_itfp.show_defocus = True
        single_itfp.curridx = trace_num - 1
        single_itfp.handle_single_plot(trace_num)
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

    def handle_binding_fusion(self, trace_num):
        print("Select the (1) binding point, followed by the (2) fusion start point & the (3) fusion end point...")
        single_itfp = IntensityTraceFigurePanel(1, 1, self.id, self.dh)
        if self.itfp.show_defocus:
            single_itfp.show_defocus = True
        single_itfp.curridx = trace_num - 1
        single_itfp.handle_single_plot(trace_num)
        points = plt.ginput(n=3, timeout=0, show_clicks=True)
        self.id.df["Status"][trace_num - 1] = 1
        self.id.df["isFusion"][trace_num - 1] = 1
        self.id.df["Binding"][trace_num - 1] = round(points[0][0])
        self.id.df["FusionStart"][trace_num - 1] = round(points[1][0])
        self.id.df["FusionEnd"][trace_num - 1] = round(points[2][0])
        output_str = "Binding: {}\nFusion Start: {}\nFusion Median: {}\nFusion End: {}\n".format(
            str(self.id.df["Binding"][trace_num - 1]),
            str(self.id.df["FusionStart"][trace_num - 1]),
            str(round(np.median([self.id.df["FusionStart"][trace_num - 1], self.id.df["FusionEnd"][trace_num - 1]]))),
            str(self.id.df["FusionEnd"][trace_num - 1]))
        print(output_str)

    def handle_exclusion(self, trace_num):
        self.id.df["isExclusion"][trace_num - 1] = 1
        for col in self.id.col_names:
            if col != "isExclusion" and col != "Status":
                self.id.df[col][trace_num - 1] = 0
        """self.id.df["isFusion"][trace_num - 1] = 0
        self.id.df["FusionStart"][trace_num - 1] = 0
        self.id.df["FusionEnd"][trace_num - 1] = 0"""

    def handle_undo(self, trace_num):
        for col in self.id.col_names:
            if col != "Status":
                self.id.df[col][trace_num - 1] = 0

    def handle_status(self):
        for i in range(self.start_trace-1, self.end_trace-1):
            self.id.df["Status"][i] = 1

    def handle_resume(self, output_file):
        with open(output_file, "r") as txt:
            txt_lines = txt.readlines()[1:]
            for line in txt_lines:
                line_split = line.split(",")
                trace_idx = int(line_split[0]) - 1
                for col, n in zip(self.id.col_names, line_split):
                    self.id.df[col][trace_idx] = int(n)
                """self.id.df["Status"][trace_idx] = int(line_split[1])
                isFusion = int(line_split[2])
                self.id.df["isFusion"][trace_idx] = isFusion
                if isFusion:
                    self.id.df["FusionStart"][trace_idx] = int(line_split[3])
                    self.id.df["FusionEnd"][trace_idx] = int(line_split[4])
                isExclusion = int(line_split[5][:-1])
                self.id.df["isExclusion"][trace_idx] = isExclusion"""
                
    def handle_arrangement(self):
        while True:
            try:
                rows, cols = [int(x) for x in input("Enter number of desired rows & columns separated by a space:\n").split()]
            except ValueError:
                print("User must input 2 valid integers separated by a space!")
                continue
            else:
                self.itfp.rows, self.itfp.cols = int(rows), int(cols)
                if self.itfp.rows < 1 or self.itfp.cols <= 1:
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
        help_msg += "\'" + self.defocus_flag + "\'" + " - toggle displaying potential de-focusing events\n"
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
                        if self.id.mode == "Lambda":
                            self.handle_fusion(trace_input)
                        elif self.id.mode == "Sigma":
                            self.handle_binding_fusion(trace_input)
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
            elif usr_input == self.defocus_flag:
                print("Toggle de-focusing events.")
                return 11
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

    def set_defocus_dst(self):
        pardir = self.id.pardir
        dst_dir = os.path.join(pardir, "TraceAnalysis", "ChangepointAnalysis")
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)
        filename = self.get_src_file_name("ChangepointEvents", ".txt")
        dst_path = os.path.join(dst_dir, filename)
        return dst_path

    def update_fusion_output(self):
        with open(self.output, "w+") as dst:
            dst.write(self.srcmat + "\n")
            for i in range(0, self.id.num_traces + 1):
                if self.id.df["Status"][i] == 1:
                    line = [str(self.id.df[key][i]) for key in self.id.col_names if key != "Data" and
                            key != "RawDataNorm" and key != "Prediction"]
                    line = ",".join(line)
                    dst.write(line + "\n")

    def write(self):
        with open(self.output, "w+") as dst:
            dst.write(self.srcmat + "\n")
            for i in range(0, self.id.num_traces):
                line = [str(self.id.df[key][i]) for key in self.id.col_names if key != "Data" and
                        key != "RawDataNorm" and key != "Prediction"]
                line = ",".join(line)
                dst.write(line + "\n")

    def defocus_output(self, isMulti):
        dh = DefocusHandler(self.id)
        output_txt_file = self.set_defocus_dst()
        dh.output = output_txt_file
        if os.path.exists(dh.output):
            print("Previous analysis found:\n{}".format(dh.output))
            return 0
        if isMulti:
            dh.multi = True
        dh.determine_defocusing_events()
        with open(output_txt_file, "a+") as dst:
            defocus_headline = "TotalDefocusingEvents,"
            defocus_events_list = list(dh.events)
            defocus_events_list.sort()
            defocus_events_list = [str(i) for i in defocus_events_list]
            defocus_events_str = ",".join(defocus_events_list)
            defocus_headline += defocus_events_str + "\n"
            dst.write(defocus_headline)
            rare_headline = "TotalRareEvents,"
            rare_events_list = list(dh.rares)
            rare_events_list.sort()
            rare_events_list = [str(i) for i in rare_events_list]
            rare_events_str = ",".join(rare_events_list)
            rare_headline += rare_events_str + "\n"
            dst.write(rare_headline)
            dst.write("Trace,FiltPoints,ExtremaPoints,Step\n")
            for n in range(1, dh.id.num_traces+1):
                filts = list(dh.filtpoints[n])
                extrema = list(dh.extrema[n])
                step = dh.steps[n]
                filts.sort()
                extrema.sort()
                line_components = (filts, extrema)
                line = (str(n),)
                for group in line_components:
                    str_line = [str(i) for i in group]
                    line += (",".join(str_line),)
                line += (str(step),)
                line = ";".join(line)
                dst.write(line + "\n")


class TracePanelWriter:

    def __init__(self, intensity_superstructure):
        self.iss = intensity_superstructure
        self.paths = {source: ["", ""] for source in self.iss.sources}
        self.set_dst()

    def get_src_file_name(self, src_txt_file, tag, fmt):
        src_filename = os.path.split(src_txt_file)[1]
        src_filename = src_filename[:src_filename.index(".txt")]
        dst_filename = "".join([src_filename, "_", tag, fmt])
        return dst_filename

    def set_dst(self):
        for src in self.paths:
            draw_dst_dir = os.path.join(self.iss.par, "TraceAnalysis", "TraceDrawings")
            draw_filename = self.get_src_file_name(src, "Collated", ".tif")
            draw_dst_path = os.path.join(draw_dst_dir, draw_filename)
            fusion_dst_dir = os.path.join(self.iss.par, "TraceAnalysis", "FusionOutput")
            fusion_filename = self.get_src_file_name(src, "FusionOutput", ".txt")
            fusion_dst_path = os.path.join(fusion_dst_dir, fusion_filename)
            self.paths[src][0] = draw_dst_path
            self.paths[src][1] = fusion_dst_path

    def draw(self, src):
        print("Drawing in progress, source:\n{}".format(src))
        datum_key = self.iss.get_datum_key(src)
        flow_dictionary = self.iss.get_flux_start()
        intensity_database = IntensityDatabase(self.iss.par, datum_key)
        intensity_database.set_source(src)
        intensity_database.get_traces(self.iss)
        intensity_database.set_times(flow_dictionary[datum_key])
        defocus_handler = DefocusHandler(intensity_database)
        data_writer = DataWriter(intensity_database)
        data_writer.set_output_dst()
        #defocus_handler.read(data_writer)
        itfp = IntensityTraceFigurePanel(3, 4, intensity_database, defocus_handler)
        imarr = []
        user_input_handler = UserInputHandler(itfp, intensity_database, defocus_handler)
        dst_path = self.paths[src][0]
        if os.path.exists(data_writer.output):
            user_input_handler.handle_resume(data_writer.output)
        trace_drawings_subdir = os.path.split(dst_path)[0]
        temp_path = os.path.join(trace_drawings_subdir, str(datum_key) + "-temp.tif")
        itfp.disp = False
        progbar = tqdm(range(itfp.stidx, itfp.figs), ascii=" >", desc="Drawing Figure Panels", ncols=100)
        for panel in progbar:
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
        print("Drawing completed:\n{}".format(dst_path))


class LearningExporter:

    def __init__(self, intensity_superstructure):
        self.superstruct = intensity_superstructure
        self.src = tuple(self.superstruct.sources)
        self.datum_keys = tuple(self.superstruct.get_datum_key(source_path) for source_path in self.src)
        self.tab = {key: {"Labels": {}, "Traces": {}, "Dst": ""} for key in self.datum_keys}

    def set_destinations(self, datum_key):
        dst_subdir = os.path.join(self.superstruct.par, "TraceAnalysis", "LearningOutput")
        if not os.path.isdir(dst_subdir):
            os.mkdir(dst_subdir)
        filename = "Datum-{}_LearningData{}".format(str(datum_key), ".txt")
        dst_filepath = os.path.join(dst_subdir, filename)
        self.tab[datum_key]["Dst"] = dst_filepath

    def collect_data(self):
        flow_vals = self.superstruct.get_flux_start()
        for key, source_path in zip(self.datum_keys, self.src):
            database = IntensityDatabase(self.superstruct.par, key)
            database.set_source(source_path)
            database.get_traces(self.superstruct)
            database.set_times(flow_vals[key])
            self.set_destinations(key)
            for n in self.tab[key]["Labels"]:
                data = database.df["Data"][n - 1]
                self.tab[key]["Traces"][n] = data

    def set_label_data(self):
        labels_subdir = os.path.join(self.superstruct.par, "TraceAnalysis", "FusionOutput")
        if not os.path.exists(labels_subdir):
            raise FileNotFoundError("FusionOutput directory cannot be found!")
        filelist = os.listdir(labels_subdir)
        if len(filelist) == 0:
            raise FileNotFoundError("No data has been created yet!")
        for filename in filelist:
            datum_key = int(filename[filename.index("Datum-")+6:][:filename[filename.index("Datum-")+6:].index("-")])
            if datum_key in self.datum_keys:
                with open(os.path.join(labels_subdir, filename), "r") as text:
                    txt_lines = text.readlines()[1:]
                    for line in txt_lines:
                        line_split = line.split(",")
                        trace_num = int(line_split[0])
                        status = int(line_split[1])
                        exclusion = int(line_split[5][:-1])
                        if status and not exclusion:
                            label = int(line_split[2])  # isFusion
                            self.tab[datum_key]["Labels"][trace_num] = label

    def export_learning(self):
        for key in self.tab:
            labels = self.tab[key]["Labels"]
            data = self.tab[key]["Traces"]
            dst_filepath = self.tab[key]["Dst"]
            with open(dst_filepath, "w+") as dst:
                for trace_num in labels:
                    line = [str(labels[trace_num]), ",".join(tuple(str(i) for i in data[trace_num]))]
                    dst.write(":".join(line) + "\n")
