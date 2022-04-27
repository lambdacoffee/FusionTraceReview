"""

"""


from fusion_review.itrace import IntensityTrace
from scipy.signal import argrelmax, argrelmin
from tqdm import tqdm
import pandas as pd
import numpy as np
import changefinder
import ruptures
import os


class IntensitySuperStructure:

    def __init__(self, parent_source_directory):
        self.sources = set()
        self.df = pd.DataFrame(dtype=object)
        self.par = parent_source_directory
        self.info = dict()
        self.output = os.path.join(self.par, "TraceAnalysis", "gathered_data_book.csv")

    def get_info(self):
        info_file_path = os.path.join(self.par, "info.txt")
        if os.path.exists(info_file_path):
            with open(info_file_path, "r") as txt:
                lines = txt.readlines()
                lines = [i for i in lines[1:len(lines)]]
                for line in lines:
                    split_line = line.split(",")
                    split_line[-1] = split_line[-1][:-1]
                    datum_key = split_line[0][split_line[0].index("Datum-")+6:]
                    self.info[int(datum_key)] = split_line[1:]
        else:
            raise FileNotFoundError("Info text file cannot be found!")

    @staticmethod
    def get_datapoints(trace_data):
        res = {}
        for trace in trace_data:
            if trace == "":
                continue
            trace_num = int(trace[:trace.index("\n")])
            data_str_lst = trace[trace.index("\n") + 1:].split(",")
            datapoints = [float(i) for i in data_str_lst if i != "\n" and i != ""]
            res[trace_num] = datapoints
        return res

    def build(self, data_path):
        with open(data_path, "r") as file:
            data = file.read()
            data = data.split("@")
        datapoints = self.get_datapoints(data)
        for trace_num in datapoints:
            self.df = self.df.append({"Data_Path": data_path, "Trace": trace_num, "Data": datapoints[trace_num]},
                           ignore_index=True)

    def gather_data(self):
        trace_analysis_subdir = os.path.join(self.par, "TraceAnalysis")
        trace_text_subdir = os.path.join(trace_analysis_subdir, "TraceText")
        file_lst = os.listdir(trace_text_subdir)
        file_lst = [i for i in file_lst if not os.path.isdir(os.path.join(trace_text_subdir, i))]
        for filename in file_lst:
            self.sources.add(filename)
            data_filepath = os.path.join(trace_text_subdir, filename)
            self.build(data_filepath)
        self.df.to_csv(self.output, index=False, columns=["Trace", "Data_Path", "Data"])
        dst_dir = os.path.join(trace_analysis_subdir, "AnalysisReviewed")
        if not os.path.exists(dst_dir):
            os.mkdir(dst_dir)

    def reread(self):
        book_path = os.path.join(self.par, "TraceAnalysis", "gathered_data_book.csv")
        if os.path.exists(book_path):
            self.df = pd.read_csv(book_path, dtype=object)
            for data_path in self.df["Data_Path"]:
                self.sources.add(data_path)
        else:
            raise(FileNotFoundError("Book cannot be found!"))

    def get_flux_start(self):
        res_dict = dict()
        for datum_key in self.info:
            xtrxn_filepath = self.info[datum_key][1]
            if os.path.exists(xtrxn_filepath):
                with open(xtrxn_filepath, "r") as opts:
                    xtrxn_dict = {split_line[0]: split_line[1] for split_line in
                                  [line.split(",") for line in opts.readlines()]}
                    res_dict[datum_key] = int(xtrxn_dict["PHdropFrameNum"])
            else:
                raise(FileNotFoundError("SetupOptions subdirectory cannot be found!"))
        return res_dict

    def get_datum_key(self, source_path):
        filename = os.path.split(source_path)[1]
        datum_key = int(filename[filename.index("Datum-")+6:][:filename[filename.index("Datum-")+6:].index("-")])
        return datum_key


class IntensityDatabase:

    """
    Repurposed dataframe representing channels on flow-cell, each channel linking to its several intensity traces
    """

    def __init__(self, parent_directory, datum):
        self.src = ""
        self.df = pd.DataFrame(dtype=object)
        self.start = 0
        self.end = 0
        self.num_traces = 0
        self.full_time = []
        self.truncated_time = []
        self.pardir = parent_directory
        self.datum = datum
        self.col_names = []
        self.defocus_events = []
        self.mode = "Lambda"

    def convert_data(self):
        for i in range(0, self.df.shape[0]):
            row_str = self.df.loc[i, "Data"][1:-1]
            row_str.replace("\n", "")
            row_str_split = row_str.split(", ")
            self.df.loc[i, "Data"] = np.array([float(j) for j in row_str_split if j != ""], dtype=np.float32)
            self.df.loc[i, "Trace"] = int(float(self.df.loc[i, "Trace"]))
        return 0

    def get_traces(self, superstructure):
        if self.src == "":
            raise ValueError("Source file is undefined!")
        loc_idxs = superstructure.df.index.to_numpy()
        for i in range(loc_idxs[0], loc_idxs[-1]+1):
            if superstructure.df.loc[i, "Data_Path"] == self.src:
                self.df = self.df.append({"Trace": superstructure.df.loc[i, "Trace"],
                                           "Data": superstructure.df.loc[i, "Data"]}, ignore_index=True)
        self.convert_data()
        self.num_traces = self.df.shape[0]
        return 0

    def set_source(self, channel_source_text_filepath):
        self.src = channel_source_text_filepath

    def get_datum_key(self, source_path):
        filename = os.path.split(source_path)[1]
        tag = "Datum-"
        start_idx = filename.index(tag)+len(tag)
        substr = filename[start_idx:]
        end_idx = 1
        while end_idx < len(filename):
            try:
                int(substr[end_idx + 1])
            except ValueError:
                break
            else:
                end_idx += 1
        datum_key = int(substr[:end_idx])
        return datum_key

    def set_times(self, start_frame):
        self.full_time = [_ for _ in range(1, len(self.df.loc[1, "Data"]) + 1)]
        self.start = start_frame
        if self.end == 0:
            # has not been overwritten, will use default approach
            self.end = len(self.df.loc[1, "Data"])
        self.truncated_time = [_ for _ in range(self.start, self.end + 1)]
        self.extend()
        self.to_dict()

    def get_predictions(self, learning_analysis_directory):
        src_datum_num = self.get_datum_key(self.src)
        filelist = os.listdir(learning_analysis_directory)
        source_filename = ""
        for filename in filelist:
            datum_num = self.get_datum_key(filename)
            if datum_num == src_datum_num:
                source_filename = filename
                break
        source_filepath = os.path.join(learning_analysis_directory, source_filename)
        with open(source_filepath, "r") as src:
            text = src.read()
            lines = text.splitlines()
            for txt_line in lines:
                line_split = txt_line.split(",")
                self.df["Prediction"][int(line_split[0])] = int(line_split[1])

    def extend(self):
        new_lst_columns = ("RawDataNorm",)
        if self.start == 1 and self.truncated_time == self.full_time:
            # measuring binding & fusion
            new_int_columns = ("Status", "isFusion", "Binding", "FusionStart", "FusionEnd", "isExclusion")
            self.mode = "Sigma"
        else:
            new_int_columns = ("Status", "isFusion", "FusionStart", "FusionEnd", "isExclusion")
        for col in (new_lst_columns + new_int_columns):
            self.df[col] = pd.Series(dtype=object)
        for i in range(0, self.num_traces):
            for col in new_lst_columns:
                self.df.at[i, col] = [0.0 for _ in range(self.start - 1, self.end)]
            for col in new_int_columns:
                self.df.at[i, col] = 0

    def to_dict(self):
        dd = self.df.to_dict()
        self.col_names = [i for i in self.df.columns if i != "Data" and i != "RawDataNorm"]
        self.df = dd


class DefocusHandler:

    def __init__(self, intensity_database):
        self.id = intensity_database
        self.changepoints = {n: set() for n in range(1, self.id.num_traces + 1)}
        self.steps = {n: 0 for n in range(1, self.id.num_traces + 1)}
        self.filtpoints = {n: [] for n in range(1, self.id.num_traces + 1)}
        self.extrema = {n: [] for n in range(1, self.id.num_traces + 1)}
        self.uniques = {}
        self.events = set()
        self.output = ""
        self.multi = False
        self.rares = set()

    def determine_changepoints(self):
        progbar = tqdm(range(0, self.id.num_traces), ascii=" >", desc="Analyzing Traces", ncols=100)
        for i in progbar:
            if not self.multi:
                progbar.update()
            it = IntensityTrace(i+1, self.id)
            it.set_raw_norm_data()
            it.set_filter()
            #it.set_rms()
            it.set_gradients()
            it.set_cumsum()
            """
            filt_signal = np.array(it.datad["TruncDataNormFilt"]["data"])
            cf = changefinder.ChangeFinder(r=0.2, order=2, smooth=10)
            raw_scores = np.asarray([cf.update(p) for p in filt_signal])
            norm_scores = (raw_scores - raw_scores.mean()) / raw_scores.std(ddof=0)
            maj_scores = pd.Series(norm_scores).nlargest(100)
            maj_scores = maj_scores.index
            condensed_scores_filt = set(maj_scores)
            remove_scores = set()
            scan_range = 20
            for p in maj_scores:
                subscan = {_ for _ in range(p - scan_range, p + scan_range + 1)}
                subscan.remove(p)
                intrsxn = subscan.intersection(condensed_scores_filt)
                remove_scores = remove_scores.union(intrsxn)
            for p in remove_scores:
                condensed_scores_filt.remove(p)
            condensed_scores_filt = list(condensed_scores_filt)
            #self.stpoints[i+1] = condensed_scores_filt
            self.changepoints[i+1] += condensed_scores_filt
            self.changepoints[i+1].sort()
            """

            filt_signal = np.array(it.datad["TruncDataNormFilt"]["data"])
            step = np.hstack((np.ones(len(filt_signal)), -1 * np.ones(len(filt_signal))))
            dary_step = np.convolve(filt_signal, step, mode="valid")
            step_idx = np.argmax(dary_step)
            self.steps[i+1] = step_idx

            cumsum_signal = np.array(it.datad["TruncCumSum"]["data"])
            maxes = argrelmax(cumsum_signal)
            mins = argrelmin(cumsum_signal)
            self.extrema[i+1] = list(maxes[0]) + list(mins[0])
            self.extrema[i+1].sort()

            breakpoints = len(self.extrema[i+1])
            binseg_model = "l2"
            binseg_algo = ruptures.Binseg(model=binseg_model).fit(filt_signal)
            binseg_predxns = binseg_algo.predict(breakpoints)
            self.filtpoints[i+1] = binseg_predxns

            self.changepoints[i+1].add(step_idx)
            self.changepoints[i+1].update(binseg_predxns)
            self.changepoints[i+1].update(self.extrema[i+1])
            """
            grad_signal = np.array(it.datad["TruncDataNormGrad"]["data"])
            changepoints_model = "l2"
            changepoints_algo = ruptures.Binseg(model=changepoints_model, min_size=20, jump=2).fit(grad_signal)
            changepoint_predxns = changepoints_algo.predict(self.id.num_traces // 50)

            filt_signal = np.array(it.datad["TruncDataNormFilt"]["data"])
            win_model = "rank"
            win_algo = ruptures.Window(model=win_model, width=10).fit(filt_signal)
            win_predxns = win_algo.predict(2)
            self.stpoints[i+1] = win_predxns[:-1]
            
            breakpoints = len(condensed_scores)
            filt_signal = np.array(it.datad["TruncDataNormFilt"]["data"])
            binseg_model = "l2"
            binseg_algo = ruptures.Binseg(model=binseg_model).fit(filt_signal)
            binseg_predxns = binseg_algo.predict(breakpoints)
            self.stpoints[i + 1] = binseg_predxns[:-1]

            #self.changepoints[i+1] = changepoint_predxns + binseg_predxns
            #self.changepoints[i + 1].sort()
            """
            # ruptures.show.display(signal, [0],computed_chg_pts=predxns)
            for p in self.changepoints[i+1]:
                if p in self.uniques:
                    self.uniques[p] += 1
                else:
                    self.uniques[p] = 1

    def determine_defocusing_events(self):
        self.determine_changepoints()
        weights = {p: np.float16(self.uniques[p] / max(list(self.uniques.values()))) for p in self.uniques}
        self.events = set(tuple(p for p in self.uniques if weights[p] >= np.percentile(list(weights.values()), 85)))
        self.determine_possible_fusion_events()

    def determine_possible_fusion_events(self):
        weights = {p: np.float16(self.uniques[p] / max(list(self.uniques.values()))) for p in self.uniques}
        self.rares = set(tuple(p for p in self.uniques if weights[p] <= np.percentile(list(weights.values()), 15)))

    def read(self, data_writer):
        if not os.path.exists(self.output):
            self.output = data_writer.set_defocus_dst()
            if not os.path.exists(self.output):
                raise FileNotFoundError("File cannot be found: {}".format(self.output))
        with open(self.output, "r") as src:
            events_line = src.readline()
            events_line_split = events_line.split(",")
            self.events = set([int(i) for i in events_line_split[1:]])
            rares_line = src.readline()
            rares_line_split = rares_line.split(",")
            self.rares = set(int(i) for i in rares_line_split[1:])
            _ = src.readline()
            for n in range(1, self.id.num_traces+1):
                line = src.readline()
                line_split = line.split(";")
                trace_num = int(line_split[0])
                filtpoints_str = line_split[1].split(",")
                self.filtpoints[trace_num] = [int(j) for j in filtpoints_str]
                extrema_str = line_split[2].split(",")
                self.extrema[trace_num] = [int(j) for j in extrema_str]
                steps_str = line_split[3]
                self.steps[trace_num] = int(steps_str)
                self.changepoints[trace_num].update(self.filtpoints[trace_num])
                self.changepoints[trace_num].update(self.extrema[trace_num])
                self.changepoints[trace_num].add(self.steps[trace_num])
