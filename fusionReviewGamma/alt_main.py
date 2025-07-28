import matplotlib.pyplot as plt
import numpy
import pandas
import tsfresh.feature_extraction.settings
from tsfresh import extract_features, select_features, extract_relevant_features
from tsfresh.utilities.dataframe_functions import impute
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.metrics import confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.manifold import TSNE
from sklearn import svm
import os


pardir = "D:\\ImagingData\\DataAnalysis\\20221028-Analysis"

def build(keys):
    from fusionReview.trace_manager import TraceManager
    from fusionReview.figpan import ReviewMode

    tm = TraceManager(pardir)
    tm.get_info()
    tm.configure()
    tm.get_mode()
    modality = ReviewMode().lookup
    tm.get_mat_files(modality[tm.mode]["FileTag"])
    tm.set_dst_files()
    tm.initialize_fusion_output_files()
    for datum_key in keys:
        #tm.setup()
        tm.gather(datum_key)
        tm.normalize_traces(datum_key, method="zscore")
        tm.assign_modes(datum_key)
        tm.set_start()
        tm.load_changepoints(datum_key)

        fusion_output_filepath = os.path.join(pardir, "TraceAnalysis\\FusionOutput\\Datum-{}-Traces_FusionOutput.txt".format(datum_key))
        with open(fusion_output_filepath, "r") as txt:
            text_lines = txt.readlines()
        text_lines = text_lines[1:]
        for idx in range(len(text_lines)):
            line = text_lines[idx]
            line_array = line.split(",")
            line_array = [int(i) for i in line_array]
            trace = tm.traces[datum_key]["TraceData"][line_array[0]]
            trace.num = line_array[0]
            trace.isReviewed = bool(line_array[1])
            trace.isFused = bool(line_array[2])
            if trace.isFused:
                trace.fuse((line_array[3], line_array[4]))
            trace.isExcluded = bool(line_array[5])
            if trace.isExcluded:
                trace.exclude()
            tm.traces[datum_key]["TraceData"][trace.num] = trace
            trace.changepoints.sort()
    return tm


def extract(key_list):
    tm = build(key_list)
    indexes = []
    labels = []
    kept_traces = []
    for datum_key in key_list:

        trace_data = list(tm.traces[datum_key]["TraceData"].values())
        kept_traces += trace_data
        #trace_data = [trace for trace in raw_trace_objs if len(trace.changepoints) > 0]
        index_list = [int(str(trace.num) + "0{}".format(datum_key)) for trace in trace_data]
        indexes += index_list
        label_list = []
        for trace in trace_data:
            trace.sampled = [trace.raw[i] for i in range(0, len(trace.raw)) if i % 2 == 0]
            if trace.isFused:
                label_list.append(1)
            else:
                if len(trace.changepoints) > 0:
                    label_list.append(2)
                else:
                    label_list.append(0)
        labels += label_list

    classification_series = pandas.Series(data=labels, dtype=int, index=indexes)

    extended_indexes = []
    flattened_trace_data = []
    time = []
    for trace, idx in zip(kept_traces, indexes):
        for i in range(len(trace.sampled)):
            flattened_trace_data.append(trace.sampled[i])
            extended_indexes.append(idx)
            time.append(i)
    extended_indexes = numpy.array(extended_indexes)
    flattened_trace_data = numpy.array(flattened_trace_data)
    time = numpy.array(time)

    #trace_series = pandas.Series(data=flattened_trace_data, index=extended_indexes, dtype=float)
    #changepoint_series = [[1 if t in trace.changepoints else 0 for t in range(0, len(trace.norm))] for trace in kept_traces]
    #changepoint_series = pandas.Series(data=changepoint_series, index=indexes, dtype=object)

    time_col = pandas.Series(data=time)
    intensities_col = pandas.Series(data=flattened_trace_data)
    #changepoints_col = pandas.Series(numpy.array([changepoint_series[n] for n in indexes]).flatten())
    id_col = pandas.Series(data=extended_indexes)
    dataframe = pandas.DataFrame()
    dataframe["id"] = id_col
    dataframe["time"] = time_col
    dataframe["Intensities"] = intensities_col
    #dataframe["Changepoints"] = changepoints_col
    print(dataframe)
    print(classification_series)

    features = extract_features(dataframe, column_id="id", column_sort="time")
    impute(features)
    filtered_features = select_features(features, classification_series)
    filtered_features.to_csv(os.path.join(pardir, "filteredFeatures.csv"))
    #fc_params = tsfresh.feature_extraction.settings.from_columns(features)
    #print(fc_params["Intensities"])
    #with open(os.path.join(pardir, "params.txt"), "w+") as dst:
    #    dst.write(str(fc_params["Intensities"]))


def train(datum_key, classifications):

    features = pandas.read_csv(os.path.join(pardir, "filteredFeatures.csv"))

    class_dict = classifications.to_dict()
    #relevant_indexes = numpy.array([n for n in class_dict if int(str(n)[-1]) == datum_key])
    relevant_indexes = numpy.array([n for n in class_dict if int(str(n)[-1]) == datum_key])
    training_classifications = classifications[relevant_indexes]
    training_features = features[features["Unnamed: 0"].isin(relevant_indexes)]

    scaler = StandardScaler()
    data = scaler.fit_transform(training_features)
    color_labels = {0: "gray", 1: "blue", 2: "orange"}
    grouping = [color_labels[label] for label in training_classifications]

    lda = LinearDiscriminantAnalysis(solver="svd")
    data_fit = lda.fit_transform(data, training_classifications)

    plt.scatter(x=data_fit[:, 0], y=data_fit[:, 1], color=grouping)
    plt.show()

    tsne = TSNE(n_components=2, verbose=1, random_state=12345)
    tsne_res = tsne.fit_transform(data_fit)
    plt.scatter(tsne_res[:, 0], tsne_res[:, 1], color=grouping)
    plt.show()

    #svc = svm.SVC(kernel="rbf")
    #svc.fit(tsne_res, training_classifications)

    #predictions = svc.predict(tsne_res)
    #print(accuracy_score(training_classifications, predictions))

    predictions = lda.predict(tsne_res)
    print(accuracy_score(training_classifications, predictions))

    exit()

    return 0


def analyze(key_list):
    tm = build(key_list)

    indexes = []
    labels = []
    kept_traces = []
    for datum_key in key_list:

        trace_data = list(tm.traces[datum_key]["TraceData"].values())
        kept_traces += trace_data
        index_list = [int(str(trace.num) + "0{}".format(datum_key)) for trace in trace_data]
        indexes += index_list
        label_list = []
        for trace in trace_data:
            trace.sampled = [trace.norm[i] for i in range(0, len(trace.norm)) if i % 5 == 0]
            if trace.isFused:
                label_list.append(1)
            else:
                if len(trace.changepoints) > 0:
                    label_list.append(2)
                else:
                    label_list.append(0)
        labels += label_list

    classification_series = pandas.Series(data=labels, dtype=int, index=indexes)

    extended_indexes = []
    flattened_trace_data = []
    time = []
    for trace, idx in zip(kept_traces, indexes):
        for i in range(len(trace.sampled)):
            flattened_trace_data.append(trace.sampled[i])
            extended_indexes.append(idx)
            time.append(i)
    extended_indexes = numpy.array(extended_indexes)
    flattened_trace_data = numpy.array(flattened_trace_data)
    time = numpy.array(time)

    time_col = pandas.Series(data=time)
    intensities_col = pandas.Series(data=flattened_trace_data)
    id_col = pandas.Series(data=extended_indexes)

    dataframe = pandas.DataFrame()
    dataframe["id"] = id_col
    dataframe["Intensities"] = intensities_col

    training_key = 3
    model = train(training_key, classification_series)

    features = pandas.read_csv(os.path.join(pardir, "filteredFeatures.csv"))

    class_dict = classification_series.to_dict()
    relevant_indexes = numpy.array([n for n in class_dict if int(str(n)[-1]) != training_key])
    testing_features = features[features["Unnamed: 0"].isin(relevant_indexes)]
    testing_classifications = classification_series[relevant_indexes]
    color_labels = {0: "gray", 1: "blue", 2: "orange"}
    grouping = [color_labels[label] for label in testing_classifications]

    scaler = StandardScaler()
    data = scaler.fit_transform(testing_features)

    pca = PCA(n_components=10)
    princomps = pca.fit_transform(data)

    tsne = TSNE(n_components=2, verbose=1, random_state=12345)
    tsne_res = tsne.fit_transform(princomps)

    plt.scatter(tsne_res[:, 0], tsne_res[:, 1], color=grouping)
    plt.show()

    predictions = model.predict(tsne_res)

    cm = confusion_matrix(testing_classifications, predictions)
    acc = accuracy_score(testing_classifications, predictions)
    print(cm)
    print(acc)


if __name__ == "__main__":
    #extract([1, 2, 3])
    analyze([1, 2, 3])


"""
intensity_start = []
intensity_end = []
changepoint_start = []
changepoint_end = []
slopes = []
noise_gap = []
grouping = []
relevant_trace_nums = []
changepoint_time_vals = []
win_len = 10
for trace_num in tm.traces[2]["TraceData"]:
    trace = tm.traces[2]["TraceData"][trace_num]
    if len(trace.changepoints) == 0:
        continue
    else:
        relevant_trace_nums.append(trace.num)
        start_idx = 0
        #cumsum = numpy.cumsum(numpy.insert(trace.norm, 0, 0))
        #cumsum = (cumsum[win_len:] - cumsum[:-win_len]) / float(win_len)
        cumsum = numpy.convolve(trace.norm, numpy.ones(win_len), mode="same") / win_len
        extended_trace_norm = trace.norm + trace.norm[-win_len + 1:]
        rolling = numpy.lib.stride_tricks.sliding_window_view(extended_trace_norm, window_shape=win_len)
        rolling_mean = [sum(i) / win_len for i in rolling]
        rolling_stdev = [numpy.var(i) for i in rolling]
        upper = numpy.array([i + j for i, j in zip(rolling_mean, rolling_stdev)])
        lower = numpy.array([i - j for i, j in zip(rolling_mean, rolling_stdev)])
        grad = numpy.gradient(cumsum)
        start_point = 0
        #plt.plot([t for t in range(len(trace.norm))], trace.norm)
        #plt.plot([t for t in range(len(upper))], upper)
        #plt.plot([t for t in range(len(upper))], lower)
        for i in range(len(trace.changepoints)):
            p = trace.changepoints[i]
            changepoint_time_vals.append(p)
            #plt.axvline(x=p)
            end = -1 if i == len(trace.changepoints) - 1 else trace.changepoints[i + 1]
            end_point = end
            for j, q in reversed(list(enumerate(grad[start_idx:p - 1]))):
                if q <= 0:
                    start_point = j + 1 if j + 1 > start_idx else start_idx + 1
                    break
            for j, q in list(enumerate(grad[p + 1:end])):
                if q <= 0:
                    end_point = p + j + 1
                    break

            grp = "orange"
            if trace.isFused:
                if trace.fusionStart < p < trace.fusionEnd:
                    grp = "blue"
                    #start_point = trace.fusionStart
                    #end_point = trace.fusionEnd
            intensity_start.append(numpy.mean(trace.norm[start_idx:p - 1]))
            #intensity_start.append(numpy.mean(trace.norm[start_idx:start_point]))
            intensity_end.append(numpy.mean(trace.norm[p + 1:end]))
            #intensity_end.append(numpy.mean(trace.norm[end_point:end]))
            changepoint_start.append(trace.norm[start_point])
            changepoint_end.append(trace.norm[end_point])
            slopes.append(((trace.norm[end_point] - trace.norm[start_point]) / (end_point - start_point)) / ((rolling_mean[-1] - rolling_mean[0]) / 1800))
            noise_gap.append(lower[end_point] - upper[start_point])
            start_idx = p + 1
            #start_idx = end_point
            grouping.append(grp)

#x = [(j - k) / i for j, k, i in zip(intensity_end, intensity_start, slopes)]
#y = [j / i for i, j in zip(slopes, noise_gap)]
#plt.scatter(x=slopes, y=noise_gap, color=grouping)
#plt.show()


relevant_data = {}
for i in range(len(grouping)):
    relevant_data[i] = [intensity_start[i],
                        intensity_end[i],
                        changepoint_start[i],
                        changepoint_end[i],
                        slopes[i],
                        noise_gap[i]]
data = numpy.array([relevant_data[i] for i in relevant_data])
scaler = StandardScaler()
data = scaler.fit_transform(data)
pca = PCA(n_components=2)
princomps = pca.fit_transform(data)
x = [princomps[i][0] for i in range(princomps.shape[0])]
y = [princomps[i][-1] for i in range(princomps.shape[0])]
plt.scatter(x=x, y=y, color=grouping)
plt.show()
"""

"""
rng = numpy.random.default_rng(12345)
gamma_rng = rng.gamma(shape=numpy.mean(full_list), scale=2, size=len(full_list)//4)
gamma_rng = [round(i) for i in gamma_rng]
sample = []
for i in full_list:
    if i in gamma_rng:
        sample.append(i)
prop_vals = [(i + 1)/len(sample) for i in range(len(sample))]
plt.plot(sample, prop_vals)
plt.show()
"""
