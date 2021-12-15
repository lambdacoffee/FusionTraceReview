"""

"""


import pandas as pd
import numpy as np
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

    def set_times(self, start_frame):
        self.full_time = [_ for _ in range(1, len(self.df.loc[1, "Data"]) + 1)]
        self.start = start_frame
        if self.end == 0:
            # has not been overwritten, will use default approach
            self.end = len(self.df.loc[1, "Data"])
        self.truncated_time = [_ for _ in range(self.start, self.end + 1)]
        self.extend()
        self.to_dict()

    def extend(self):
        new_lst_columns = ("RawDataNorm",)
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
