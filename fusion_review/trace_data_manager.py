from pyts.preprocessing import StandardScaler
import numpy as np
import os


class TraceDataLearningManager:

    def __init__(self, parent_directory):
        self.pardir = parent_directory
        self.testdir = os.path.join(parent_directory, "test")
        self.org = "Datum-"
        partitions = ("train", "valid", "test")
        self.traces = {p: {"labels": [], "data": [], "set": ""} for p in partitions}
        self.train = self.traces["train"]
        self.valid = self.traces["valid"]
        self.test = self.traces["test"]
        self.xtrain = self.train["data"]
        self.ytrain = self.train["labels"]
        self.xvalid = self.valid["data"]
        self.yvalid = self.valid["labels"]
        self.xtest = self.test["data"]
        self.ytest = self.test["labels"]

    def specify_test(self, test_data_subdirectory):
        if os.path.exists(test_data_subdirectory) and len(os.listdir(test_data_subdirectory)) > 0:
            self.testdir = test_data_subdirectory

    def get_correlating_set_value(self, source_filename):
        try:
            start_ind = source_filename.index(self.org) + len(self.org)
            substr = source_filename[start_ind:]
            organizer_str = substr[:substr.index("_")]
        except ValueError:
            print("WARNING: Can not organize source data for dataset based on filenames.\n"
                  "Increased memory consumption.")
            organizer_str = os.path.splitext(source_filename)[0]
        return organizer_str

    def load(self, load_training=True, load_validation=True, load_testing=True):
        subdir_names = ("train", "valid", "test")
        truthy_vals = (load_training, load_validation, load_testing)
        for i, j in zip(subdir_names, truthy_vals):
            if j:
                subdir = os.path.join(self.pardir, i)
                if os.path.exists(subdir):
                    data_label_partition = self.gather_data(subdir)
                    self.traces[i] = data_label_partition
                else:
                    if i == "test" and os.path.exists(self.testdir):
                        data_label_partition = self.gather_data(self.testdir)
                        self.traces[i] = data_label_partition
                    else:
                        raise FileNotFoundError("Subdirectory {} does not exist!".format(subdir))
        self.update()

    def update(self):
        self.train = self.traces["train"]
        self.valid = self.traces["valid"]
        self.test = self.traces["test"]
        self.xtrain = self.train["data"]
        self.ytrain = self.train["labels"]
        self.xvalid = self.valid["data"]
        self.yvalid = self.valid["labels"]
        self.xtest = self.test["data"]
        self.ytest = self.test["labels"]

    def gather_data(self, data_subdirectory):
        filelist = os.listdir(data_subdirectory)
        label_arr = []
        data_arr = []
        datum_set_arr = []
        for filename in filelist:
            organizer_str = self.get_correlating_set_value(filename)
            with open(os.path.join(data_subdirectory, filename), "r") as src:
                linelist = src.readlines()
                for line in linelist:
                    split_line = line.split(":")
                    label = int(split_line[0])
                    label_arr.append(label)
                    data = split_line[1].split(",")
                    data = np.array(tuple(float(i) for i in data))
                    data_arr.append(data)
                    datum_set_arr.append(organizer_str)
        # norm_data = normalize(np.array(data_arr, dtype=np.float32))
        norm_data = np.array(data_arr, dtype=np.float32)
        return {"labels": np.array(label_arr), "data": norm_data, "set": datum_set_arr}

    def normalize(self, raw_data):
        for i in range(0, raw_data.shape[0]):
            raw_trace = raw_data[i]
            norm_trace = (raw_trace - raw_trace.mean()) / raw_trace.std(ddof=0)
            raw_data[i] = norm_trace
        return raw_data

    def scale_data(self):
        scaler = StandardScaler()
        self.traces["train"]["data"] = scaler.transform(self.xtrain)
        self.traces["valid"]["data"] = scaler.transform(self.xvalid) if len(self.xvalid) > 1 else []
        self.traces["test"]["data"] = scaler.transform(self.xtest) if len(self.xtest) > 1 else []
        self.update()

    def drop(self, data_partition):
        try:
            class_labels = self.traces[data_partition]["labels"]
        except KeyError:
            raise KeyError("{} is not a recognized data partition.".format(str(data_partition)))
        else:
            fusions = np.array([i for i in class_labels if i])
            trace_data = self.traces[data_partition]["data"]
            reduced_labels = [_ for _ in fusions]
            reduced_trace_data = [trace_data[n] for n in range(0, len(trace_data)) if class_labels[n]]
            for _ in range(0, len(fusions)):
                while True:
                    idx = np.random.randint(0, len(trace_data))
                    if not class_labels[idx]:
                        break
                reduced_trace_data.append(trace_data[idx])
                reduced_labels.append(class_labels[idx])
            self.traces[data_partition]["labels"] = np.array(reduced_labels)
            self.traces[data_partition]["data"] = np.array(reduced_trace_data, dtype=np.float32)
            self.update()
        return 0

    def augment(self, data_partition):
        try:
            class_labels = self.traces[data_partition]["labels"]
        except KeyError:
            raise KeyError("{} is not a recognized data partition.".format(str(data_partition)))
        else:
            not_fusions = np.array([i for i in class_labels if not i])
            trace_data = self.traces[data_partition]["data"]
            augmented_labels = [_ for _ in not_fusions]
            augmented_trace_data = [trace_data[n] for n in range(0, len(trace_data)) if not class_labels[n]]
            for _ in range(0, len(not_fusions)):
                while True:
                    idx = np.random.randint(0, len(trace_data))
                    if class_labels[idx]:
                        break
                augmented_trace_data.append(trace_data[idx])
                augmented_labels.append(class_labels[idx])
            self.traces[data_partition]["labels"] = np.array(augmented_labels)
            self.traces[data_partition]["data"] = np.array(augmented_trace_data, dtype=np.float32)
            self.update()
        return 0

    def use_rms(self):
        partitions = ("train", "valid", "test")
        datasets = (self.xtrain, self.xvalid, self.xtest)
        win_size = 20
        for p, q in zip(partitions, datasets):
            if len(q) < 1:
                continue
            for i in range(0, len(q)):
                trace = q[i]
                rms = [i ** 2 for i in trace]
                rms = np.sqrt(np.convolve(rms, np.ones(win_size) / float(win_size), mode="same"))
                rms = [rms[i] if rms[i] >= 0 else 0 - rms[i] for i in range(0, len(rms))]
                self.traces[p]["data"][i] = np.array(rms, dtype=np.float32)
        self.update()
        return 0

    def summarize(self):
        total_num_fused = 0
        total_traces = 0
        res = {}
        for dataset in self.traces:
            dataset_fused = 0
            for label in self.traces[dataset]["labels"]:
                dataset_fused += label
                total_num_fused += label
            total_traces += len(self.traces[dataset]["labels"])
            print("Dataset: {}, Fused: {}, Total: {}".format(dataset, str(dataset_fused),
                                                             str(len(self.traces[dataset]["labels"]))))
            res[dataset] = {"pos": dataset_fused, "neg": len(self.traces[dataset]["labels"]) - dataset_fused}
        print("Summary - Fused: {}, Total: {}".format(str(total_num_fused), total_traces))
        return 0
