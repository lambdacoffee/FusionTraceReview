"""

"""


import pandas as pd
import numpy as np
from scipy import signal


class IntensityTrace:

    def __init__(self, trace_number, intensity_database):
        # where origin is text filepath for trace data
        self.num = trace_number
        self.id = intensity_database
        self.time = self.id.truncated_time
        self.idf = pd.DataFrame(dtype=np.float32)
        self.isFusion = intensity_database.df["isFusion"][trace_number - 1]
        self.isExclusion = intensity_database.df["isExclusion"][trace_number - 1]
        self.guess = False
        if self.isFusion:
            color = "tab:blue"
        elif self.isExclusion:
            color = "tab:red"
        else:
            color = "black"
        self.datad = {"TruncDataNorm": {"time": [], "data": [], "c": color, "z": 2},
                      "TruncDataNormGrad": {"time": [], "data": [], "c": color, "z": 2},
                      "TruncDataNormFilt": {"time": [], "data": [], "c": color, "z": 2},
                      "TruncDataNormRMS": {"time": [], "data": [], "c": color, "z": 2},
                      "TruncCumSum": {"time": [], "data": [], "c": color, "z": 2}}

    def set_raw_norm_data(self):
        raw_trace = np.asarray(self.id.df["Data"][self.num-1], dtype=np.float32)
        self.id.df["RawDataNorm"][self.num-1] = (raw_trace - raw_trace.mean()) / raw_trace.std(ddof=0)
        self.idf["TruncDataRaw"] = raw_trace[self.id.start-1:self.id.end]
        norm_trace = (self.idf["TruncDataRaw"] - self.idf["TruncDataRaw"].mean()) / self.idf["TruncDataRaw"].std(ddof=0)
        self.idf["TruncDataNorm"] = norm_trace
        self.datad["TruncDataNorm"]["time"] = self.time
        self.datad["TruncDataNorm"]["data"] = self.idf["TruncDataNorm"].to_list()

    def set_gradients(self):
        self.datad["TruncDataNormGrad"]["time"] = self.time
        self.datad["TruncDataNormGrad"]["data"] = list(np.gradient(self.datad["TruncDataNormFilt"]["data"]))
        self.datad["TruncDataNormGrad"]["z"] = 5
        self.datad["TruncDataNormGrad"]["c"] = "green"

    def set_filter(self):
        self.datad["TruncDataNormFilt"]["time"] = self.time
        #filt_model = signal.butter(2, 0.05, btype="lowpass", fs=1, output="sos")
        #filt_model = signal.butter(3, 0.5, btype="lowpass", fs=25, output="sos")
        filt_model = signal.butter(2, 0.5, btype="lowpass", fs=35, output="sos")
        self.datad["TruncDataNormFilt"]["data"] = list(signal.sosfilt(filt_model, self.datad["TruncDataNorm"]["data"]))
        self.datad["TruncDataNormFilt"]["z"] = 3
        self.datad["TruncDataNormFilt"]["c"] = "tab:orange"

    def set_cumsum(self):
        self.datad["TruncCumSum"]["time"] = self.time
        data = pd.Series(self.datad["TruncDataNormFilt"]["data"]).cumsum()
        data = np.asarray(data)
        data = [(i - data.mean()) / data.std(ddof=0) for i in data]
        self.datad["TruncCumSum"]["data"] = list(data)
        self.datad["TruncCumSum"]["z"] = 6
        self.datad["TruncCumSum"]["c"] = "tab:red"

    def set_rms(self):
        win_size = 20
        self.datad["TruncDataNormRMS"]["time"] = self.time
        self.datad["TruncDataNormRMS"]["data"] = [i**2 for i in self.datad["TruncDataNormFilt"]["data"]]
        self.datad["TruncDataNormRMS"]["data"] = np.sqrt(np.convolve(self.datad["TruncDataNormRMS"]["data"],
                                                                     np.ones(win_size)/float(win_size), mode="same"))
        self.datad["TruncDataNormRMS"]["data"] = [self.datad["TruncDataNormRMS"]["data"][i]
                                                  if self.datad["TruncDataNormFilt"]["data"][i] >= 0
                                                  else 0-self.datad["TruncDataNormRMS"]["data"][i]
                                                  for i in range(0, len(self.id.truncated_time))
                                                  ]
        self.datad["TruncDataNormRMS"]["z"] = 4
        self.datad["TruncDataNormRMS"]["c"] = "tab:red"

    def get_fusion_data(self):
        if self.id.df["isFusion"][self.num-1]:
            fusion_start_time = self.id.df["FusionStart"][self.num-1]
            fusion_end_time = self.id.df["FusionEnd"][self.num-1]
            fusion_med_time = np.median([fusion_start_time, fusion_end_time])
            return (fusion_start_time, fusion_med_time, fusion_end_time)

    def __str__(self):
        return self.set_raw_norm_data()
