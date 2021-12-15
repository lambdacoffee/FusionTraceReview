"""

"""


import pandas as pd
import numpy as np


class IntensityTrace:

    def __init__(self, trace_number, intensity_database):
        # where origin is text filepath for trace data
        self.num = trace_number
        self.time = intensity_database.full_time
        self.id = intensity_database
        self.idf = pd.DataFrame(dtype=np.float32)
        self.isFusion = intensity_database.df["isFusion"][trace_number-1]
        self.isExclusion = intensity_database.df["isExclusion"][trace_number - 1]
        if self.isFusion:
            color = "tab:blue"
        elif self.isExclusion:
            color = "tab:red"
        else:
            color = "black"
        self.datad = {"TruncDataNorm": {"time": [], "data": [], "c": color, "z": 2}}

    def set_raw_norm_data(self):
        raw_trace = np.asarray(self.id.df["Data"][self.num-1], dtype=np.float32)
        self.id.df["RawDataNorm"][self.num-1] = (raw_trace - raw_trace.mean()) / raw_trace.std(ddof=0)
        self.idf["TruncDataRaw"] = raw_trace[self.id.start-1:self.id.end]
        norm_trace = (self.idf["TruncDataRaw"] - self.idf["TruncDataRaw"].mean()) / self.idf["TruncDataRaw"].std(ddof=0)
        self.idf["TruncDataNorm"] = norm_trace
        self.datad["TruncDataNorm"]["time"] = self.id.truncated_time
        self.datad["TruncDataNorm"]["data"] = self.idf["TruncDataNorm"].to_list()

    def get_fusion_data(self):
        if self.id.df["isFusion"][self.num-1]:
            fusion_start_time = self.id.df["FusionStart"][self.num-1]
            fusion_end_time = self.id.df["FusionEnd"][self.num-1]
            fusion_med_time = np.median([fusion_start_time, fusion_end_time])
            return (fusion_start_time, fusion_med_time, fusion_end_time)

    def __str__(self):
        return self.set_raw_norm_data()
