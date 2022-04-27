from trace_data_manager import TraceDataLearningManager
from sklearn.metrics import confusion_matrix, f1_score, accuracy_score
from sklearn.ensemble import VotingClassifier
from pyts.classification import BOSSVS, TimeSeriesForest
from sklearn.svm import SVC
from tqdm import tqdm
from time import time
import numpy as np
import joblib
import os


class TimeSeriesClassifier:

    def __init__(self, identifier):
        self.id = identifier
        self.classifier = None
        self.time = 0

    def build(self, *args):
        if self.id == "BOSSVS":
            self.classifier = BOSSVS(word_size=args[0], n_bins=args[1], window_size=args[2], window_step=args[3],
                                     strategy=args[4])
        elif self.id == "Soft":
            component_models = [("poly1", SVC(probability=True, kernel="poly", degree=args[0], verbose=0)),
                                ("poly2", SVC(probability=True, kernel="poly", degree=args[1], verbose=0)),
                                ("poly3", SVC(probability=True, kernel="poly", degree=args[2], verbose=0))]
            self.classifier = VotingClassifier(estimators=component_models, voting="soft", n_jobs=6)
        elif self.id == "Hard":
            component_models = [(mode, args[0][mode].classifier) for mode in args[0]]
            self.classifier = VotingClassifier(estimators=component_models, voting="hard", n_jobs=6)
        elif self.id == "Forest":
            self.classifier = TimeSeriesForest(random_state=42, n_jobs=6)

    def train(self, trace_data, trace_labels):
        self.clock()
        self.classifier.fit(trace_data, trace_labels)
        elapsed_time_str = self.clock()
        msg = "\nProcess: {}\nTime Elapsed: {} s".format("Fitting Data", elapsed_time_str)
        print(msg + "\n")

    def predict(self, test_data):
        res = []
        progbar = tqdm(range(0, len(test_data)), ascii=" >", desc="Predicting", ncols=100)
        for n in progbar:
            progbar.update()
            trace = [test_data[n]]
            res.append(self.classifier.predict(trace))
        res = np.array(res).flatten()
        return res

    def score(self, test_data, label_data):
        self.clock()
        res = self.classifier.score(test_data, label_data)
        elapsed_time_str = self.clock()
        print("\nProcess: {}\nTime Elapsed: {} s".format("Scoring Data", elapsed_time_str))
        return res

    def clock(self):
        if self.time == 0:
            self.time = time()
            return 0
        else:
            curr = time()
            res = str(round(curr - self.time))
            self.time = 0
            return res

    def write(self, filepath, f1, scoring, conf_mtx, predictions):
        header_dict = self.classifier.get_params()
        header_labels = list(header_dict.keys())
        header_vals = list(header_dict.values())
        header_lst = ["type=" + self.id] + [i + "=" + str(j) for i, j in zip(header_labels, header_vals)]
        header = "\n".join(header_lst)
        with open(filepath, "w+") as dst:
            dst.writelines(header + "\n")
            dst.write("f1=" + str(f1) + "\n")
            dst.write("Scoring=" + str(scoring) + "\n")
            dst.write("ConfMtx=" + str(conf_mtx) + "\n")
            dst.write("Predictions:\n")
            for p in predictions:
                dst.write(str(p) + "\n")


class LearningModelManager:

    def __init__(self):
        self.contents = {}
        self.num_traces = 0

    def add_model(self, id_key, model):
        if not isinstance(id_key, str):
            raise TypeError("id_key must be type(str)!")
        else:
            self.contents.update({id_key: {"Classifier": model, "Predictions": [], "Scoring": 0, "CMtx": [], "f1": 0}})
        return 0

    def load_training(self, parent_directory):
        source_subdir = os.path.join(parent_directory, "classifiers", "obj")
        if not os.path.isdir(source_subdir):
            raise FileNotFoundError("Classifier object subdirectory not found.")
        filelist = os.listdir(source_subdir)
        for filename in filelist:
            id_key = os.path.splitext(filename)[0].split("_")[0]
            classifier_model = joblib.load(os.path.join(source_subdir, filename))
            self.add_model(id_key, classifier_model)
        return 0

    def read_training(self, parent_directory):
        source_subdir = os.path.join(parent_directory, "classifiers", "info")
        if not os.path.isdir(source_subdir):
            raise FileNotFoundError("Classifier text subdirectory not found.")
        filelist = os.listdir(source_subdir)
        for filename in filelist:
            name = os.path.splitext(filename)[0].split("_")[0]
            with open(os.path.join(source_subdir, filename), "r") as src:
                whole_text = src.read()
                score_tag = "Scoring="
                cnf_mtx_tag = "ConfMtx="
                prdxns_tag = "Predictions:"
                f1_tag = "f1="
                score_substr = whole_text[
                               whole_text.index(score_tag) + len(score_tag) + 1:whole_text.index(cnf_mtx_tag) - 1]
                self.contents[name]["Scoring"] = float(score_substr)
                cnf_mtx_substr = whole_text[
                                 whole_text.index(cnf_mtx_tag) + len(cnf_mtx_tag) + 1:whole_text.index(prdxns_tag) - 2]
                self.contents[name]["CMtx"] = [int(i) for i in cnf_mtx_substr.split(", ")]
                predictions_str = whole_text[whole_text.index(prdxns_tag) + len(prdxns_tag) + 1:]
                self.contents[name]["Predictions"] = np.array([int(i) for i in predictions_str.split("\n")[:-1]])
                f1_substr = whole_text[
                               whole_text.index(f1_tag) + len(f1_tag) + 1:whole_text.index(score_tag) - 1]
                self.contents[name]["f1"] = float(f1_substr)
            if self.num_traces == 0:
                self.num_traces = len(self.contents[name]["Predictions"])
            else:
                if self.num_traces != len(self.contents[name]["Predictions"]):
                    raise TypeError("FATAL ERROR: Models have different number of predictions!")
        return 0


class EnsembleModel:

    def __init__(self, model_manager):
        self.manager = model_manager
        self.p_mtx = np.array([])
        self.predictions = []

    def handle_weights(self):
        names = list(self.manager.contents.keys())
        f_scores = [self.manager.contents[i]["f1"] for i in names]
        conf_matrices = [self.manager.contents[i]["CMtx"] for i in names]
        recalls = [cmtx[3] / (cmtx[2] + cmtx[3]) for cmtx in conf_matrices]
        weights = [np.average((f_scores[i], recalls[i])) for i in range(0, len(names))]
        print(weights)
        for p in range(0, self.manager.num_traces):
            weighted_guesses = []
            for j, w in zip(names, weights):
                guess = self.manager.contents[j]["Predictions"][p]
                weighted_guesses.append(guess * w)
            prdxn = sum(weighted_guesses)
            self.predictions.append(prdxn)

    def weigh(self):
        baked_goods = [0 if p < np.mean(self.predictions) else 1 for p in self.predictions]
        self.predictions = baked_goods

    def calculate_probability_matrix(self, verbose=False):
        temp = []
        for id_key in self.manager.contents:
            conf_mtrx = self.manager.contents[id_key]["CMtx"]
            negatives = conf_mtrx[0] + conf_mtrx[1]
            positives = conf_mtrx[2] + conf_mtrx[3]
            temp.append([(conf_mtrx[0] / negatives - conf_mtrx[1] / negatives),
                         (conf_mtrx[3] / positives - conf_mtrx[2] / positives)])
        self.p_mtx = np.array(temp)
        if verbose:
            print("\nEnsemble Probability Matrix:")
            print(str(np.array(self.p_mtx)))

    def mix_raw_predictions(self):
        manager_key_lst = list(self.manager.contents.keys())
        for p in range(0, self.manager.num_traces):
            guesses = [self.manager.contents[id_key]["Predictions"][p] for id_key in manager_key_lst]
            weighted_guesses = [self.p_mtx[j, 1] if guesses[j] == 1 else - self.p_mtx[j, 0]
                                for j in range(0, len(guesses))]
            prdxn = sum(weighted_guesses)
            self.predictions.append(prdxn)

    def cook(self):
        baked_goods = [0 if i <= 0 else 1 for i in self.predictions]
        self.predictions = baked_goods

    def output(self, trace_data_manager, directory, correlating_tag):
        try:
            int(correlating_tag)
        except ValueError:
            filename = "EnsemblePredictions_" + correlating_tag + ".txt"
        else:
            filename = "EnsemblePredictions_Datum-" + correlating_tag + ".txt"
        dst_filepath = os.path.join(directory, filename)
        correlating_predictions = [self.predictions[i] for i in range(0, len(self.predictions))
                                   if trace_data_manager.test["set"][i] == correlating_tag]
        with open(dst_filepath, "a+") as dst:
            for p in range(0, len(correlating_predictions)):
                dst.write(",".join((str(p + 1), str(correlating_predictions[p]))) + "\n")


def get_models():
    fast_classifier = TimeSeriesClassifier("BOSSVS")
    fast_classifier.build(5, 25, 300, 40, "entropy")
    medium_classifier = TimeSeriesClassifier("BOSSVS")
    medium_classifier.build(5, 25, 250, 15, "entropy")
    slow_classifier = TimeSeriesClassifier("BOSSVS")
    slow_classifier.build(5, 25, 250, 10, "entropy")
    soft_classifier = TimeSeriesClassifier("Soft")
    soft_classifier.build(3, 4, 5)
    hard_classifier = TimeSeriesClassifier("Hard")
    hard_classifier.build({"Fast": fast_classifier, "Med": medium_classifier, "Slow": slow_classifier})
    forest_classifier = TimeSeriesClassifier("Forest")
    forest_classifier.build()

    models = (fast_classifier, medium_classifier, slow_classifier, soft_classifier)
    names = ("Fast", "Medium", "Slow", "Soft")
    return zip(names, models)


def classify_time_traces(model_manager, trace_data_manager):
    for name in model_manager.contents:
        clf = model_manager.contents[name]
        clf["Classifier"].train(trace_data_manager.xtrain, trace_data_manager.ytrain)
        clf["Predictions"] = clf["Classifier"].predict(trace_data_manager.xtest)
        clf["Scoring"] = clf["Classifier"].score(trace_data_manager.xtest, trace_data_manager.ytest)
        clf["CMtx"] = list(confusion_matrix(trace_data_manager.ytest, clf["Predictions"]).flatten())
        fx = f1_score(trace_data_manager.ytest, clf["Predictions"])
        output_filepath = os.path.join(trace_data_manager.pardir, "classifiers", "info", name + "_Classifier.txt")
        clf["Classifier"].write(output_filepath, fx, clf["Scoring"], clf["CMtx"], clf["Predictions"])
        classifier_filepath = os.path.join(trace_data_manager.pardir, "classifiers", "obj", name + "_Classifier.sav")
        joblib.dump(clf["Classifier"].classifier, classifier_filepath)


def handle_loaded_models(model_manager, trace_data_manager):
    for id_key in model_manager.contents:
        model = model_manager.contents[id_key]["Classifier"]
        model_manager.contents[id_key]["Predictions"] = model.predict(trace_data_manager.xtest)
        if model_manager.num_traces == 0:
            model_manager.num_traces = len(model_manager.contents[id_key]["Predictions"])
        else:
            if model_manager.num_traces != len(model_manager.contents[id_key]["Predictions"]):
                raise TypeError("FATAL ERROR: Models have different number of predictions!")
        model_manager.contents[id_key]["Scoring"] = model.score(trace_data_manager.xtest, trace_data_manager.ytest)
        model_manager.contents[id_key]["CMtx"] = list(
            confusion_matrix(trace_data_manager.ytest, model_manager.contents[id_key]["Predictions"]).flatten()
            )
        fx = f1_score(trace_data_manager.ytest, model_manager.contents[id_key]["Predictions"])
        print("\n" + id_key)
        print("Score: {}".format(str(model_manager.contents[id_key]["Scoring"])))
        print("f1_Score: {}".format(str(fx)))
        print("ConfMtrx: {}".format(str(model_manager.contents[id_key]["CMtx"])))


def determine_metrics(trace_data_manager, ensemble_model, verbose=True):
    cmtx = confusion_matrix(trace_data_manager.ytest, ensemble_model.predictions)
    fx = f1_score(trace_data_manager.ytest, ensemble_model.predictions)
    if verbose:
        print("\nConfusion Matrix:\n{}".format(cmtx))
        print("f1: {}".format(str(fx)))


pardir = "D:\\DeepLearning\\FusionTest\\"
tdlm = TraceDataLearningManager(pardir)
tdlm.load()
tdlm.use_rms()
tdlm.scale_data()
tdlm.summarize()
lmm = LearningModelManager()

#mode = "learning"
# mode = "loading"
mode = "reading"

if mode == "learning":
    classifier_models = get_models()
    for n, m in classifier_models:
        lmm.add_model(n, m)
    classify_time_traces(lmm, tdlm)

elif mode == "loading":
    lmm.load_training(pardir)
    handle_loaded_models(lmm, tdlm)

    em = EnsembleModel(lmm)
    em.calculate_probability_matrix(verbose=True)
    em.mix_raw_predictions()
    em.cook()
    determine_metrics(tdlm, em, verbose=True)
    for source_filename in os.listdir(tdlm.testdir):
        organizing_string = tdlm.get_correlating_set_value(source_filename)
        em.output(tdlm, pardir, organizing_string)

elif mode == "reading":
    lmm.load_training(pardir)
    lmm.read_training(pardir)

    em = EnsembleModel(lmm)
    em.handle_weights()
    em.weigh()
    determine_metrics(tdlm, em, verbose=True)
    for source_filename in os.listdir(tdlm.testdir):
        organizing_string = tdlm.get_correlating_set_value(source_filename)
        em.output(tdlm, pardir, organizing_string)
