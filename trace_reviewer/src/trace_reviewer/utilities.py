"""

"""


import matplotlib
import matplotlib.pyplot as plt
from figpan import FigurePanel
from functools import partial
import multiprocessing
from tqdm import tqdm
import numpy as np
import imageio.v2 as imageio
import ruptures
import scipy
import os


class InitialChoicePrompt:

    def __init__(self):
        self.msg = "Input corresponding number to desired trace container or give additional option:\n"
        self.ncores = multiprocessing.cpu_count() - 1
        self.confirm = "y"
        self.negate = "n"
        multival = True if self.ncores > 1 else False
        self.opts = {"q": {"Msg": "quit",
                               "Function": self.abort,
                               "Confirmation": "Exit?",
                               "Multi": False},
                     "j": {"Msg": "draw to tifs",
                               "Function": self.draw,
                               "Confirmation": "Create drawings and export traces to tifs?",
                               "Multi": multival},
                     "c": {"Msg": "perform trace changepoint analysis",
                               "Function": self.find_changepoints,
                               "Confirmation": "Proceed with analyzing traces for changepoint events?",
                               "Multi": multival},
                     "l": {"Msg": "export data for learning",
                               "Function": self.export_learning,
                               "Confirmation": "Proceed with exporting data and labels for learning?",
                               "Multi": multival},
                     "e": {"Msg": "generate ECDF curves",
                               "Function": self.stats,
                               "Confirmation": "Generate ECDF curves & calculate statistics?",
                               "Multi": multival}}
        self.mapping = dict()
        
    @staticmethod
    def abort(*args):
        exit(-1)

    @staticmethod
    def draw_trace_set(trace_manager, datum_number):
        print("Drawing in progress, source: {}".format(trace_manager.traces[datum_number]["SourcePath"]))
        trace_manager.setup(datum_number)
        rows = 3
        columns = 4
        matplotlib.use("Tkagg")
        fp = FigurePanel(rows, columns, len(trace_manager.traces[datum_number]["TraceData"]))
        fp.allocate(trace_manager.traces[datum_number]["TraceData"], trace_manager.info[datum_number]["StartFrame"])
        fp.isDisplay = False
        fp.read(trace_manager.traces[datum_number]["OutputPath"])
        img_arr = []
        dst_path = trace_manager.traces[datum_number]["DrawingPath"]
        temp_path = os.path.join(trace_manager.destinations["Drawing"]["Dir"], str(datum_number) + "-temp.tif")
        progbar = tqdm(range(0, len(fp)), ascii=" >", desc="Drawing Figure Panels", ncols=100, leave=False, position=datum_number)
        iter(fp)
        for panel in progbar:
            next(fp)
            fp.fig.suptitle("Figure Panel {} of {}".format(panel + 1, len(fp)), fontsize=16)
            fp.fill()
            fp.fig.canvas.draw()
            plt.savefig(temp_path)
            img = imageio.imread(temp_path, format="TIFF")
            img_arr.append(img)
        os.remove(temp_path)
        imageio.mimwrite(dst_path, np.asarray(img_arr), format="TIFF")

    @staticmethod
    def calculate_statistics(trace_manager, key):
        trace_manager.setup(key)
        fusion_output_filepath = trace_manager.traces[key][trace_manager.destinations["Fusion"]["Correlation"]]
        if not os.path.exists(fusion_output_filepath):
            print("Cannot locate FusionOutput text file for {}".format(trace_manager.info[key]["Label"]))
            return -1
        with open(fusion_output_filepath, "r") as txt:
            text_lines = txt.readlines()
        if len(text_lines) == 1:
            print("No data from manual trace review found in file: {]".format(fusion_output_filepath))
            return -2
        text_lines = text_lines[1:]
        for idx in range(len(text_lines)):
            line = text_lines[idx]
            line_array = line.split(",")
            line_array = [int(i) for i in line_array]
            trace_manager.traces[key]["TraceData"][line_array[0]].load_line_components(line_array)

        trace_manager.generate_curve(key)
        trace_manager.record_dwell_times(key)

    @staticmethod
    def changepoint_search(trace_manager, datum_number):
        trace_manager.setup(datum_number)
        continue_flag = trace_manager.load_changepoints(datum_number)
        if continue_flag == 0:
            return 0
        trace_manager.get_total_video_intensity(datum_number)

        print("Searching for changepoints in progress, source: {}".format(trace_manager.traces[datum_number]["SourcePath"]))

        #search_method = ruptures.Window(model="rank", width=50, jump=1)
        #penalty_int = 3
        search_method = ruptures.Window(model="mahalanobis", width=50, jump=1)
        penalty_int = 5

        for region_number in trace_manager.regions[datum_number]["TraceData"]:
            trace = trace_manager.regions[datum_number]["TraceData"][region_number]
            algo = search_method.fit(np.array(trace.norm))
            bkps = algo.predict(pen=penalty_int)
            accepted_bkps = []
            for p in bkps:
                if trace.grad[p - 1] > 0 and trace.start < p < len(trace.norm):
                    accepted_bkps.append(p)
            trace_manager.regions[datum_number]["RegionalChangepoints"][region_number] = accepted_bkps
            trace_manager.regions[datum_number]["DefocusPoints"].update(accepted_bkps)


        progbar = tqdm(range(1, len(trace_manager.traces[datum_number]["TraceData"]) + 1), ascii=" >",
                       desc="Searching for changepoints", ncols=100, leave=False, position=datum_number)
        for trace_num in progbar:
            trace = trace_manager.traces[datum_number]["TraceData"][trace_num]
            trace.search(search_method, penalty_int)
            defocus_points = trace_manager.regions[datum_number]["DefocusPoints"]
            possible_fusion_points = set(trace.changepoints).difference(defocus_points)

            trace.decompose()
            trend_grad = np.gradient(trace.decomposition["Trend"])
            possible_fusion_points = [p for p in possible_fusion_points if trend_grad[p - 1] >= 0]

            trace_manager.traces[datum_number]["TraceData"][trace_num].changepoints = possible_fusion_points

        trace_manager.record_changepoints(datum_number)

    def build_prompt(self, trace_manager):
        options_lst = [" - ".join(["\'" + i + "\'", self.opts[i]["Msg"]]) for i in self.opts]
        self.msg += ", ".join(options_lst)
        source_keys = list(trace_manager.traces.keys())
        source_keys.sort()
        for key in source_keys:
            line = "\n{} - {}".format(key, trace_manager.info[key]["Label"])
            self.msg += line

    def get_input(self, trace_manager):
        while True:
            user_input = input(self.msg + "\n")
            try:
                int(user_input)
            except ValueError:
                try:
                    self.opts[user_input]
                except KeyError:
                    print("User must input valid number or flag!")
                    continue
                else:
                    yes_no_str = "\n\'{}\' or \'{}\': ".format(self.confirm, self.negate)
                    confirm_input = input(self.opts[user_input]["Confirmation"] + yes_no_str)
                    if confirm_input == self.confirm:
                        confirm_multiprocessing = False
                        if self.opts[user_input]["Multi"] is True:
                            confirm_multiprocessing = self.multi_core_request(yes_no_str)
                        self.opts[user_input]["Function"](confirm_multiprocessing, trace_manager)
            else:
                return int(user_input)

    def multi_core_request(self, yes_no_string):
        while True:
            confirmation = input("Multiple CPU cores detected. Utilize multi-core processing?" + yes_no_string)
            if confirmation == self.confirm:
                return True
            elif confirmation == self.negate:
                return False
            else:
                print("User must input valid option!")

    def draw(self, isMulti, trace_manager):
        if isMulti:
            pool = multiprocessing.Pool(self.ncores)
            temp_function = partial(self.draw_trace_set, trace_manager)
            pool.map(func=temp_function, iterable=trace_manager.traces.keys())
            pool.close()
            pool.join()
            print("Multiple processes successfully converged.")
        else:
            for key in trace_manager.traces:
                trace_manager.setup(key)
                self.draw_trace_set(trace_manager, key)
        print("Drawing completed.")
        return 0

    @staticmethod
    def calculate_gamma_fit(trace_manager, datum_key):
        gamma_fit_calculation_safety_check = trace_manager.load_dwell_times(datum_key)
        if gamma_fit_calculation_safety_check < 0:
            print("Skipping {} - {}...".format(datum_key, trace_manager.info[datum_key]["Label"]))
            return 0
        dwell_times = trace_manager.results[datum_key]["X"]
        fit_params = scipy.stats.gamma.fit(dwell_times, method="MLE")
        N = fit_params[0]  # shape
        tau = fit_params[2]  # scale
        loc = fit_params[1]
        fit_cdf = scipy.stats.gamma.cdf(dwell_times, a=N, loc=loc, scale=tau)
        trace_manager.results[datum_key]["N"] = N
        trace_manager.results[datum_key]["loc"] = loc
        trace_manager.results[datum_key]["tau"] = tau
        trace_manager.results[datum_key]["fit"] = fit_cdf

        mean_squared_dwell_times = sum([t**2 for t in dwell_times]) / len(dwell_times)
        squared_mean_of_dwell_times = (sum(dwell_times) / len(dwell_times)) ** 2
        randomness = (mean_squared_dwell_times - squared_mean_of_dwell_times) / squared_mean_of_dwell_times
        trace_manager.results[datum_key]["N_min"] = 1 / randomness

        prob_vals = [t / len(dwell_times) for t in range(1, len(dwell_times) + 1)]
        mean_prob_val = sum(prob_vals) / len(prob_vals)
        residual_sum_squares = sum([(prob_vals[i] - fit_cdf[i]) ** 2 for i in range(0, len(prob_vals))])
        total_sum_squares = sum([(t - mean_prob_val) ** 2 for t in prob_vals])
        r_squared = 1 - (residual_sum_squares / total_sum_squares)
        trace_manager.results[datum_key]["R^2"] = r_squared

        print("N (shape): {}\ntau (scale): {}\nlocation: {}\nN_min: {}\nR^2: {}\n".format(
            N, tau, loc, 1 / randomness, r_squared))
        return 0

    @staticmethod
    def plot_results(trace_manager, showEmpirical=True, showFit=True):
        #matplotlib.interactive(True)
        for key in trace_manager.results:
            # trace_manager.load_dwell_times(key)   # this will initialize
            if showEmpirical:
                plt.figure(1)
                try:
                    plt.step(trace_manager.results[key]["X"], trace_manager.results[key]["Y"], label=trace_manager.info[key]["Label"])
                except KeyError:
                    continue
                plt.xlabel("Dwell Time [s]")
                plt.ylabel("Proportion of Fused Events")
                plt.title("Empirical CDFs")
                plt.legend(loc="lower right")
            if showFit:
                plt.figure(2)
                try:
                    plt.plot(trace_manager.results[key]["X"], trace_manager.results[key]["fit"], label=trace_manager.info[key]["Label"])
                except KeyError:
                    continue
                plt.xlabel("Dwell Time [s]")
                plt.ylabel("Proportion of Fused Events")
                plt.title("Gamma Fit to eCDFs")
                plt.legend(loc="lower right")
            print("Label: {}\nN (shape): {}\ntau (scale): {}\nlocation: {}\nN_min: {}\nR^2: {}\n".format(
                trace_manager.info[key]["Label"], trace_manager.results[key]["N"],
                trace_manager.results[key]["tau"], trace_manager.results[key]["loc"],
                trace_manager.results[key]["N_min"], trace_manager.results[key]["R^2"]))
        plt.show()

    def stats(self, isMulti, trace_manager):
        if isMulti:
            pool = multiprocessing.Pool(self.ncores)
            temp_function = partial(self.calculate_statistics, trace_manager)
            pool.map(func=temp_function, iterable=trace_manager.traces.keys())
            pool.close()
            pool.join()
            print("Multiple processes successfully converged.")
        else:
            for key in trace_manager.traces:
                trace_manager.setup(key)
                self.calculate_statistics(trace_manager, key)
                self.calculate_gamma_fit(trace_manager, key)
        while True:
            print("\nDwell times calculated and written. Plot results? (y/n)")
            is_plot = input()
            if is_plot == "y":
                self.plot_results(trace_manager)
                break
            elif is_plot == "n":
                break
            else:
                print("User must input valid answer!")
        return 0

    def export_learning(self):
        print("Under construction, please check back later.")
        """
        le = LearningExporter(intensity_superstructure)
        le.set_label_data()
        le.collect_data()
        le.export_learning()
        """

    def find_changepoints(self, isMulti, trace_manager):
        if isMulti:
            pool = multiprocessing.Pool(self.ncores)
            temp_function = partial(self.changepoint_search, trace_manager)
            pool.map(func=temp_function, iterable=trace_manager.traces.keys())
            pool.close()
            pool.join()
            print("Multiple processes successfully converged.")
        else:
            for key in trace_manager.traces:
                self.changepoint_search(trace_manager, key)
        print("Searching completed, changepoints recorded.")
        while True:
            user_input = input("Attempt to pull and analyze dwell times? (y/n)")
            if user_input == "y":
                for key in trace_manager.traces:
                    trace_manager.setup(key)
                    trace_manager.generate_curve_from_changepoints(key)
                    trace_manager.record_dwell_times(key)
                    trace_manager.output_changepoint_analysis(key)
                    self.calculate_gamma_fit(trace_manager, key)
                while True:
                    print("\nDwell times calculated and written. Plot results? (y/n)")
                    is_plot = input()
                    if is_plot == "y":
                        self.plot_results(trace_manager)
                        break
                    elif is_plot == "n":
                        break
                    else:
                        print("User must input valid answer!")
                return 0
            elif user_input == "n":
                break
            else:
                print("User must input either \'y\' or \'n\'")
        return 0

class UserInputHandler:

    def __init__(self, figure_panel, output_text_file):
        self.figurePanel = figure_panel
        self.out = output_text_file
        self.user_choice = ""
        self.prompt_msg = "User Review Traces - input command below, press \'h\' for help:\n"
        self.flags = {"q": {"msg": "Terminating sequence - abort process",
                            "help": "quit and return to command shell",
                            "panelChange": 0,
                            "fxn": self.abort},
                      "r": {"msg": "Resuming from save point.",
                            "help": "resume last reviewed panel",
                            "panelChange": 0,
                            "fxn": self.resume},
                      "n": {"msg": "Displaying next panel.",
                            "help": "advance to next panel",
                            "panelChange": 1,
                            "fxn": self.advance},
                      "p": {"msg": "Displaying previous panel.",
                            "help": "return to previous panel",
                            "panelChange": -1,
                            "fxn": self.retreat},
                      "f": {"msg": "Trace number to mark for fusion:",
                            "help": "mark trace on current panel as fusion",
                            "panelChange": 0,
                            "fxn": self.handle_fusion},
                      "x": {"msg": "Trace number to exclude:",
                            "help": "mark trace to be excluded from efficiency calculation",
                            "panelChange": 0,
                            "fxn": self.exclude},
                      "s": {"msg": "Wrote trace information to output text file.",
                            "help": "Save & write all traces to output file",
                            "panelChange": 0,
                            "fxn": self.save},
                      "i": {"msg": "Inverted colors.",
                            "help": "invert colors (great for night time & reducing eye strain!)",
                            "panelChange": 0,
                            "fxn": self.invert},
                      "a": {"msg": "",
                            "help": "arrange figure panel as array of m_rows x n_columns",
                            "panelChange": 0,
                            "fxn": self.arrange},
                      "u": {"msg": "Trace number to undo fusion or exclusion:",
                            "help": "mark trace on current panel as NOT fusion",
                            "panelChange": 0,
                            "fxn": self.undo},
                      "c": {"msg": "Toggle changepoints.",
                            "help": "reveals results from changefinder algorithm as vertical lines on trace graphs",
                            "panelChange": 0,
                            "fxn": self.display_changepoints},
                      "h": {"msg": "Available terminal command flags are as listed:\n",
                            "help": "display these options",
                            "panelChange": 0,
                            "fxn": self.help}}

    @staticmethod
    def abort():
        exit(0)

    @staticmethod
    def retreat():
        return 0

    @staticmethod
    def get_arrangement():
        while True:
            try:
                rows, cols = [int(x) for x in
                              input("Enter number of desired rows & columns separated by a space:\n").split()]
            except ValueError:
                print("User must input 2 valid integers separated by a space!")
                continue
            else:
                if rows < 1 or cols < 1:
                    print("User must input valid numbers - figure panel must have at least 1 row & 1 column!")
                    continue
                return rows, cols

    def display_changepoints(self):
        self.figurePanel.showChangepoints = True

    def invert(self):
        self.figurePanel.isInverted = not self.figurePanel.isInverted
        self.figurePanel.set_text_color()
        self.figurePanel.invert_colors()

    def exclude(self):
        trace_num = self.validate_trace_number()
        self.figurePanel.exclude_trace(trace_num)

    def undo(self):
        trace_num = self.validate_trace_number()
        self.figurePanel.undo_trace(trace_num)

    def advance(self):
        self.figurePanel.mark_reviewed()

    def save(self):
        self.figurePanel.write(self.out)

    def resume(self):
        starting_panel_idx = self.figurePanel.read(self.out)
        iter(self.figurePanel)
        self.figurePanel.panel_value = starting_panel_idx

    def handle_fusion(self):
        trace_num = self.validate_trace_number()
        trace_object, fusion_times = self.figurePanel.mark_fusion(trace_num)
        trace_object.fuse(fusion_times)
        fusion_message = "Fusion Start: {}\nFusion End: {}\n".format(trace_object.fusionStart, trace_object.fusionEnd)
        if trace_object.binding != 0:
            fusion_message = "Binding: {}\n".format(trace_object.binding) + fusion_message
        print(fusion_message)
        return 0

    def validate_trace_number(self):
        while True:
            trace_number_input = input()
            try:
                trace_input = int(trace_number_input)
            except ValueError:
                print("User must input a valid trace number!")
                continue
            else:
                if trace_input <= self.figurePanel.window.start or trace_input > self.figurePanel.window.stop:
                    print("User must input a valid trace number: {} < n <= {}".format(self.figurePanel.window.start,
                                                                                      self.figurePanel.window.stop))
                    continue
                return trace_input

    def arrange(self):
        n_rows, n_columns = self.get_arrangement()
        starting_index = self.figurePanel.rearrange(n_rows, n_columns)
        iter(self.figurePanel)
        self.figurePanel.fig, self.figurePanel.axs = self.figurePanel.form_panel()
        self.figurePanel.set_text_color()
        if self.figurePanel.isInverted:
            self.figurePanel.invert_colors()
        self.figurePanel.panel_value = starting_index // (self.figurePanel.rows * self.figurePanel.cols) + 1
        print("Successfully rearranged traces.")

    def help(self):
        msg = ""
        for flag in self.flags:
            msg += "\'" + flag + "\' - " + self.flags[flag]["help"] + "\n"
        print(msg)
        return 0

    def handle_input(self):
        while True:
            user_input = input(self.prompt_msg)
            try:
                self.flags[user_input]
            except KeyError:
                print("User must input a valid option flag!")
                continue
            else:
                self.user_choice = user_input
                print(self.flags[user_input]["msg"])
                self.flags[user_input]["fxn"]()
                return 0


"""
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
                            label = int(line_split[2])  # isFused
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
"""
