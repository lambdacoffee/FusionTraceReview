"""

"""


from statsmodels.tsa import seasonal
import skimage.io as skio
import numpy
import os


class TraceManager:

    def __init__(self, parent_source_directory):
        self.sources = []
        self.traces = dict()
        self.regions = dict()
        self.par = parent_source_directory
        self.destinations = {"Fusion": {"Dir": os.path.join(self.par, "FusionOutput"),
                                        "Tag": "_FusionOutput",
                                        "Ext": ".txt",
                                        "Correlation": "OutputPath"},
                             "Drawing": {"Dir": os.path.join(self.par, "TraceDrawings"),
                                         "Tag": "_Collated",
                                         "Ext": ".tif",
                                         "Correlation": "DrawingPath"},
                             "Finding": {"Dir": os.path.join(self.par, "ChangepointSearch"),
                                         "Tag": "_Changepoints",
                                         "Ext": ".txt",
                                         "Correlation": "ChangeFinderPath"},
                             "Times": {"Dir": os.path.join(self.par, "DwellTimes"),
                                         "Tag": "_Times",
                                         "Ext": ".txt",
                                         "Correlation": "DwellTimePath"},
                             "Detection": {"Dir": os.path.join(self.par, "Detections"),
                                       "Tag": "_DetectedChangepoints",
                                       "Ext": ".txt",
                                       "Correlation": "DetectionsPath"}
                             }
        self.info = dict()
        self.results = dict()

    def get_info(self):
        info_file_path = os.path.join(self.par, "info.txt")
        if os.path.exists(info_file_path):
            with open(info_file_path, "r") as txt:
                header = txt.readline().strip().split(",")
                key_count = 1
                for line in txt.readlines():
                    split_line = line.strip().split(",")
                    try:
                        split_line[0]
                    except ValueError or IndexError:
                        raise ValueError("{} is either corrupted or in wrong configuration.".format(info_file_path))
                    else:
                        self.info[key_count] = {header[0]: split_line[0],
                                                header[1]: int(split_line[1]),
                                                header[2]: float(split_line[2]),
                                                header[3]: split_line[3]}
                        key_count += 1
        else:
            raise FileNotFoundError("Info text file cannot be found!")

    def get_total_video_intensity(self, datum_key):
        vid_filepath = self.regions[datum_key]["SourcePath"]
        print("Reading source video file {}\nplease wait...".format(vid_filepath))
        video = skio.imread(vid_filepath, plugin="tifffile")
        frames = video.shape[0]
        video_partitions = {n: numpy.zeros(frames) for n in range(1, 4 + 1)}
        for f in range(frames):
            video_partitions[1][f] = numpy.sum(video[f, 0:512, 0:512])
            video_partitions[2][f] = numpy.sum(video[f, 512:1024, 0:512])
            video_partitions[3][f] = numpy.sum(video[f, 0:512, 512:1024])
            video_partitions[4][f] = numpy.sum(video[f, 512:1024, 512:1024])
        for partition_key in video_partitions:
            self.regions[datum_key]["TraceData"][partition_key] = IntensityTrace()
            trace = self.regions[datum_key]["TraceData"][partition_key]
            trace.num = partition_key
            trace.raw = video_partitions[partition_key]
            trace.normalize("minmax")
            self.regions[datum_key]["TraceData"][partition_key] = trace
        return 0

    def gather(self, datum_key):
        """
        Constructs IntensityTrace objects for each particle in corresponding source video, storing each intensity
        summation as a 1D array read from corresponding traces text file.

        :param int datum_key: corresponding datum key number of video
        :return: int 0
        :raises: FileNotFoundError if source text file cannot be found
        """
        data_path = self.traces[datum_key]["SourcePath"]
        if not os.path.exists(data_path):
            raise FileNotFoundError("Cannot find source path for key value {}\ngiven file {}".format(str(datum_key), data_path))
        with open(data_path, "r") as file:
            data = file.read()
            data = data.split("@")
        for trace in data:
            if trace == "":
                continue
            trace_num = int(trace[:trace.index("\n")])
            data_str_lst = trace[trace.index("\n") + 1:].split(",")
            datapoints = [float(i) for i in data_str_lst if i != "\n" and i != ""]
            it = IntensityTrace()
            it.num = trace_num
            it.raw = datapoints
            self.traces[datum_key]["TraceData"][trace_num] = it
        return 0

    def record_changepoints(self, datum_key):
        dst_path = self.traces[datum_key]["ChangeFinderPath"]
        with open(dst_path, "w+") as dst:
            for trace_num in self.traces[datum_key]["TraceData"]:
                trace = self.traces[datum_key]["TraceData"][trace_num]
                trace.changepoints.sort()
                line = (str(trace_num),) + tuple(str(p) for p in trace.changepoints)
                line = ",".join(line)
                dst.write(line + "\n")
        return 0

    def load_changepoints(self, datum_key):
        source_text_filepath = self.traces[datum_key]["ChangeFinderPath"]
        if not os.path.exists(source_text_filepath):
            return -1
        with open(source_text_filepath, "r") as src:
            text = src.read()
        text_lines = text.split("\n")
        if len(text_lines) < 2:
            return -2
        for line in text_lines:
            split_line = line.split(",")
            try:
                split_line = [int(i) for i in split_line]
            except ValueError:
                continue
            trace_num = split_line[0]
            self.traces[datum_key]["TraceData"][trace_num].changepoints = split_line[1:]
        return 0

    def normalize_traces(self, datum_key, method="minmax"):
        for trace_num in self.traces[datum_key]["TraceData"]:
            trace = self.traces[datum_key]["TraceData"][trace_num]
            trace.normalize(method)
        return 0

    def get_key(self, filename):
        for key in self.info:
            if self.info[key]["Label"] in filename:
                return key
        return -1

    def configure(self):
        trace_text_subdir = os.path.join(self.par, "ExtractedTraces")
        file_lst = os.listdir(trace_text_subdir)
        for filename in file_lst:
            filepath = os.path.join(trace_text_subdir, filename)
            if not os.path.isdir(filepath):
                datum_key = self.get_key(filename)
                if datum_key == -1:
                    raise FileNotFoundError("Cannot determine DatumKey value for {}".format(filepath))
                self.traces[datum_key] = {"SourcePath": filepath, "TraceData": dict()}
                self.regions[datum_key] = {"SourcePath": self.info[datum_key]["Filepath"], "TraceData": dict(),
                                           "RegionalChangepoints": dict(), "DefocusPoints": set()}
        return 0

    def set_start(self):
        for key in self.traces:
            start_frame = self.info[key]["StartFrame"]
            for n in self.traces[key]["TraceData"]:
                self.traces[key]["TraceData"][n].start = start_frame
        return 0

    def setup(self, user_input):
        self.gather(user_input)
        self.normalize_traces(user_input)
        self.set_start()
        self.load_changepoints(user_input)
        return 0

    def set_dst_files(self):
        for key in self.destinations:
            if not os.path.exists(self.destinations[key]["Dir"]):
                os.mkdir(self.destinations[key]["Dir"])
        for datum_key in self.traces:
            src_filename = os.path.splitext(os.path.split(self.traces[datum_key]["SourcePath"])[-1])[0]
            for dst_type in self.destinations:
                dst_filename = src_filename + self.destinations[dst_type]["Tag"] + self.destinations[dst_type]["Ext"]
                dst_filepath = os.path.join(self.destinations[dst_type]["Dir"], dst_filename)
                self.traces[datum_key][self.destinations[dst_type]["Correlation"]] = dst_filepath

    def initialize_fusion_output_files(self):
        for datum_key in self.traces:
            fusion_output_filepath = self.traces[datum_key][self.destinations["Fusion"]["Correlation"]]
            if not os.path.exists(fusion_output_filepath):
                with open(fusion_output_filepath, "w+") as dst:
                    if self.info[datum_key]["StartFrame"] == 0:
                        dst.write("TraceNum,isReviewed,isFusion,BindingFrame,FusionStartFrame,FusionEndFrame,isExcluded")
                    else:
                        dst.write("TraceNum,isReviewed,isFusion,FusionStartFrame,FusionEndFrame,isExcluded")

    def initialize_changepoint_detection_output_files(self):
        for datum_key in self.traces:
            detections_ouput_filepath = self.traces[datum_key][self.destinations["Detection"]["Correlation"]]
            if not os.path.exists(detections_ouput_filepath):
                with open(detections_ouput_filepath, "w+") as dst:
                    if self.info[datum_key]["StartFrame"] == 0:
                        dst.write("TraceNum,isReviewed,isFusion,BindingFrame,FusionStartFrame,FusionEndFrame,isExcluded\n")
                    else:
                        dst.write("TraceNum,isReviewed,isFusion,FusionStartFrame,FusionEndFrame,isExcluded\n")

    def output_changepoint_analysis(self, key):
        dst_filepath = self.traces[key][self.destinations["Detection"]["Correlation"]]
        with open(dst_filepath, "a") as dst:
            for trace_num in self.traces[key]["TraceData"]:
                intensity_trace = self.traces[key]["TraceData"][trace_num]
                line = intensity_trace.get_line_components()
                text_line = ",".join([str(int(i)) for i in line])
                dst.write(text_line + "\n")

    def generate_curve(self, key):
        self.results[key] = {"X": [], "Y": []}
        dwell_times = []
        for trace_num in self.traces[key]["TraceData"]:
            intensity_trace = self.traces[key]["TraceData"][trace_num]
            if intensity_trace.isFused and not intensity_trace.isExcluded:
                if intensity_trace.start == 0:
                    # binding to fuse time
                    t = (intensity_trace.fusionStart - intensity_trace.binding) * self.info[key]["TimeInterval[s]"]
                else:
                    # flow-start to fuse time
                    t = (intensity_trace.fusionStart - intensity_trace.start) * self.info[key]["TimeInterval[s]"]
                dwell_times.append(t)
        dwell_times.sort()
        y_vals = [(i / len(dwell_times)) for i in range(1, len(dwell_times) + 1)]
        self.results[key]["X"] = dwell_times
        self.results[key]["Y"] = y_vals
        return 0

    def generate_curve_from_changepoints(self, key):
        self.results[key] = {"X": [], "Y": []}
        dwell_times = []
        for trace_num in self.traces[key]["TraceData"]:
            intensity_trace = self.traces[key]["TraceData"][trace_num]
            intensity_trace.isReviewed = True
            intensity_trace.start = self.info[key]["StartFrame"]
            if intensity_trace.start == 0:
                # binding to fuse time
                if len(intensity_trace.changepoints) > 2:
                    intensity_trace.isFused = True
                    intensity_trace.binding = intensity_trace.changepoints[0]
                    intensity_trace.fusionStart = intensity_trace.changepoints[1]
                    intensity_trace.fusionEnd = intensity_trace.changepoints[1]
                    t = (intensity_trace.fusionStart - intensity_trace.binding) * self.info[key]["TimeInterval[s]"]
                    dwell_times.append(t)
            else:
                # flow-start to fuse time
                if len(intensity_trace.changepoints) > 1:
                    intensity_trace.isFused = True
                    intensity_trace.fusionStart = intensity_trace.changepoints[0]
                    intensity_trace.fusionEnd = intensity_trace.changepoints[0]
                    t = (intensity_trace.fusionStart - intensity_trace.start) * self.info[key]["TimeInterval[s]"]
                    dwell_times.append(t)
            self.traces[key]["TraceData"][trace_num] = intensity_trace
        dwell_times.sort()
        y_vals = [(i / len(dwell_times)) for i in range(1, len(dwell_times) + 1)]
        self.results[key]["X"] = dwell_times
        self.results[key]["Y"] = y_vals
        return 0

    def record_dwell_times(self, datum_key):
        dst_path = self.traces[datum_key][self.destinations["Times"]["Correlation"]]
        with open(dst_path, "w+") as dst:
            line = ",".join(str(t) for t in self.results[datum_key]["X"])
            dst.write(line)
        return 0

    def load_dwell_times(self, key):
        source_text_filepath = self.traces[key][self.destinations["Times"]["Correlation"]]
        if not os.path.exists(source_text_filepath):
            return -1
        self.results[key] = {"X": [], "Y": []}
        with open(source_text_filepath, "r") as src:
            text = src.read()
        try:
            dwell_times = [float(t) for t in text.split(",")]
        except ValueError:
            return -2
        y_vals = [(i / len(dwell_times)) for i in range(1, len(dwell_times) + 1)]
        self.results[key]["X"] = dwell_times
        self.results[key]["Y"] = y_vals
        return 0


class IntensityTrace:

    def __init__(self):
        self.raw = []
        self.norm = []
        self.grad = []
        self.changepoints = []
        self.num = 0
        self.start = 0
        self.isReviewed = False
        self.isFused = False
        self.isExcluded = False
        self.fusionStart = 0
        self.fusionEnd = 0
        self.binding = 0
        self.color = "black"
        self.start_color = "tab:blue"
        self.decomposition = {"Trend": [], "Seasonality": [], "Residuals": []}

    def normalize(self, method):
        if method == "minmax":
            mininmum = min(self.raw)
            maximum = max(self.raw)
            self.norm = [(i - mininmum) / (maximum - mininmum) for i in self.raw]
        elif method == "zscore":
            mean = numpy.mean(self.raw)
            std = numpy.std(self.raw)
            self.norm = [i - (mean / std) for i in self.raw]
        self.grad = numpy.gradient(self.norm)

    def search(self, search_function, penalty):
        signal = numpy.array(self.norm)
        algo = search_function.fit(signal)
        bkps = algo.predict(pen=penalty)
        accepted_bkps = []
        for p in bkps:
            if self.grad[p - 1] > 0 and self.start < p < len(self.norm):
                accepted_bkps.append(p)
        self.changepoints = accepted_bkps

    def decompose(self, normalized=True):
        res = seasonal.seasonal_decompose(x=self.norm if normalized else self.raw, period=10, model="additive")
        self.decomposition["Trend"] = res.trend
        self.decomposition["Seasonality"] = res.seasonal
        self.decomposition["Residuals"] = res.resid

    def load_changepoints_as_fusion_data(self):
        if self.start == 0:
            # binding to fusion dwell times
            if len(self.changepoints) > 2:
                self.binding = self.changepoints[0]
                self.fusionStart = self.changepoints[1]
                self.fusionEnd = self.changepoints[1]
                self.isFused = True
        self.isReviewed = True

    def undo(self):
        self.isFused = False
        self.isExcluded = False
        self.binding = 0
        self.fusionStart = 0
        self.fusionEnd = 0
        self.color = "black"

    def exclude(self):
        self.isFused = False
        self.isExcluded = True
        self.binding = 0
        self.fusionStart = 0
        self.fusionEnd = 0
        self.color = "red"

    def fuse(self, fusion_time_points):
        if self.start != 0:
            self.fusionStart = int(fusion_time_points[0])
            self.fusionEnd = int(fusion_time_points[1])
        elif self.start == 0:
            self.binding = int(fusion_time_points[0])
            self.fusionStart = int(fusion_time_points[1])
            self.fusionEnd = int(fusion_time_points[2])
        self.isFused = True
        self.color = "tab:blue"
        self.start_color = "orange"

    def get_fusion_data(self):
        if self.isFused is True:
            fusion_med_time = numpy.median([self.fusionStart, self.fusionEnd])
            return self.fusionStart, fusion_med_time, self.fusionEnd

    def get_line_components(self):
        line = []
        if self.start != 0:
            line = [self.num, self.isReviewed, self.isFused, self.fusionStart, self.fusionEnd, self.isExcluded]
        elif self.start == 0:
            line = [self.num, self.isReviewed, self.isFused, self.binding, self.fusionStart, self.fusionEnd,
                    self.isExcluded]
        return line

    def load_line_components(self, line_components):
        self.num = line_components[0]
        self.isReviewed = bool(line_components[1])
        self.isFused = bool(line_components[2])
        if self.start != 0:
            if self.isFused:
                self.fuse((line_components[3], line_components[4]))
            self.isExcluded = bool(line_components[5])
        elif self.start == 0:
            if self.isFused:
                self.fuse((line_components[3], line_components[4], line_components[5]))
            self.isExcluded = bool(line_components[6])
        if self.isExcluded:
            self.exclude()
        return 0

    def __len__(self):
        return len(self.raw)
