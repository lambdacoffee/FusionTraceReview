import tensorflow as tf
import keras
import seaborn
from keras import layers, callbacks, losses, metrics, initializers, models
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report
import numpy as np
import os


def gather_data(data_subdirectory):
    filelist = os.listdir(data_subdirectory)
    label_arr = []
    data_arr = []
    for filename in filelist:
        with open(os.path.join(data_subdirectory, filename), "r") as src:
            linelist = src.readlines()
            for line in linelist:
                split_line = line.split(":")
                label = int(split_line[0])
                label_arr.append(label)
                data = split_line[1].split(",")
                data = np.array(tuple(float(i) for i in data))
                data_arr.append(data)
    norm_data = normalize(np.array(data_arr, dtype=np.float32))
    print(data_subdirectory)
    return {"labels": np.array(label_arr), "data": norm_data}


def normalize(raw_data):
    for i in range(0, raw_data.shape[0]):
        raw_trace = raw_data[i]
        norm_trace = (raw_trace - raw_trace.mean()) / raw_trace.std(ddof=0)
        raw_data[i] = norm_trace
    return raw_data


def load(parent_directory):
    training_data_subdir = os.path.join(parent_directory, "train")
    validation_data_subdir = os.path.join(parent_directory, "valid")
    test_data_subdir = os.path.join(parent_directory, "test")
    train_data = gather_data(training_data_subdir)
    valid_data = gather_data(validation_data_subdir)
    test_data = gather_data(test_data_subdir)
    return {"train": train_data, "valid": valid_data, "test": test_data}


def drop(dataset):
    class_labels = dataset["labels"]
    fusions = np.array([i for i in class_labels if i])
    trace_data = dataset["data"]
    reduced_labels = [_ for _ in fusions]
    reduced_trace_data = [trace_data[n] for n in range(0, len(trace_data)) if class_labels[n]]
    for _ in range(0, len(fusions)):
        while True:
            idx = np.random.randint(0, len(trace_data))
            if not class_labels[idx]:
                break
        reduced_trace_data.append(trace_data[idx])
        reduced_labels.append(class_labels[idx])
    dataset["labels"] = np.array(reduced_labels)
    dataset["data"] = np.array(reduced_trace_data, dtype=np.float32)
    return 0


def augment(dataset):
    class_labels = dataset["labels"]
    not_fusions = np.array([i for i in class_labels if not i])
    trace_data = dataset["data"]
    augmented_labels = [_ for _ in not_fusions]
    augmented_trace_data = [trace_data[n] for n in range(0, len(trace_data)) if not class_labels[n]]
    for _ in range(0, len(not_fusions)):
        while True:
            idx = np.random.randint(0, len(trace_data))
            if class_labels[idx]:
                break
        augmented_trace_data.append(trace_data[idx])
        augmented_labels.append(class_labels[idx])
    dataset["labels"] = np.array(augmented_labels)
    dataset["data"] = np.array(augmented_trace_data, dtype=np.float32)
    return 0


def resbloc(features, in_layer, kernel_seeding):
    conv_x = keras.layers.Conv1D(filters=features, kernel_size=kernel_seeding * 2, padding="same")(in_layer)
    conv_x = keras.layers.BatchNormalization()(conv_x)
    conv_x = keras.layers.Activation("tanh")(conv_x)

    conv_y = keras.layers.Conv1D(filters=features, kernel_size=kernel_seeding, padding="same")(conv_x)
    conv_y = keras.layers.BatchNormalization()(conv_y)
    conv_y = keras.layers.Activation("tanh")(conv_y)

    conv_z = keras.layers.Conv1D(filters=features, kernel_size=kernel_seeding // 2, padding="same")(conv_y)
    conv_z = keras.layers.BatchNormalization()(conv_z)

    # expand channels for the sum
    shortcut_y = keras.layers.Conv1D(filters=features, kernel_size=2, padding="same")(in_layer)
    shortcut_y = keras.layers.BatchNormalization()(shortcut_y)

    output = keras.layers.add([shortcut_y, conv_z])
    output = keras.layers.Activation("tanh")(output)

    return output


def build_model(in_shape, nclasses=2):
    input_layer = keras.layers.Input(in_shape)
    # output_bias = tf.keras.initializers.Constant(output_bias)

    output_layer = keras.layers.Conv1D(filters=5, kernel_size=8, activation="relu", padding="same")(input_layer)
    keras.layers.MaxPooling1D()(output_layer)
    output_layer = keras.layers.Dense(512, activation="tanh")(output_layer)
    output_layer = keras.layers.Dense(128, activation="relu")(output_layer)
    output_layer = keras.layers.Dense(64, activation="tanh")(output_layer)
    output_layer = keras.layers.Dense(16, activation="relu")(output_layer)
    output_layer = keras.layers.Dense(4, activation="relu")(output_layer)

    output_layer = keras.layers.GlobalMaxPooling1D()(output_layer)

    if nclasses <= 2:
        output_layer = keras.layers.Dense(1, activation="sigmoid")(output_layer)
    else:
        output_layer = keras.layers.Dense(nclasses, activation="softmax")(output_layer)

    model = keras.models.Model(inputs=input_layer, outputs=output_layer)
    return model


def summarize_data(data_dictionary):
    total_num_fused = 0
    total_traces = 0
    res = {}
    for dataset in data_dictionary:
        dataset_fused = 0
        for label in data_dictionary[dataset]["labels"]:
            dataset_fused += label
            total_num_fused += label
        total_traces += len(data_dictionary[dataset]["labels"])
        print("Dataset: {}, Fused: {}, Total: {}".format(dataset, str(dataset_fused),
                                                         str(len(data_dictionary[dataset]["labels"]))))
        res[dataset] = {"pos": dataset_fused, "neg": len(data_dictionary[dataset]["labels"]) - dataset_fused}
    print("Summary - Fused: {}, Total: {}".format(str(total_num_fused), total_traces))
    return res


pardir = "D:\\DeepLearning\\FusionTraces\\"
data_dict = load(pardir)
x_train = data_dict["train"]["data"]
y_train = data_dict["train"]["labels"]
x_valid = data_dict["valid"]["data"]
y_valid = data_dict["valid"]["labels"]
x_test = data_dict["test"]["data"]
y_test = data_dict["test"]["labels"]

augment(data_dict["train"])
augment(data_dict["valid"])
augment(data_dict["test"])

drop(data_dict["train"])

data_summary = summarize_data(data_dict)
# init_bias = np.log(data_summary["train"]["pos"] / data_summary["train"]["neg"])

opt = tf.keras.optimizers.Adam(learning_rate=0.0001)
num_epochs = 35
bat_size = 75
n_classes = 2

input_shape = (x_train.shape[-1], 1)

#chkpnt_filepath = os.path.join(pardir, "history", "history.hdf5")
early_stop = callbacks.EarlyStopping(monitor="val_prc", verbose=1, patience=10, mode="max", restore_best_weights=True)

model_metrics = [metrics.TruePositives(name="tp"),
                 metrics.TrueNegatives(name="tn"),
                 metrics.FalsePositives(name="fp"),
                 metrics.FalseNegatives(name="fn"),
                 metrics.BinaryAccuracy(name="ba"),
                 metrics.Precision(name="pc"),
                 metrics.Recall(name="rc"),
                 metrics.AUC(name="auc"),
                 metrics.AUC(name="prc", curve="PR")
                 ]

#res_net_model = build_model(input_shape, output_bias=init_bias)

model_filepath = os.path.join(pardir, "model_v1.h5")
model_weights_filepath = os.path.join(pardir, "weights", "model_weights_v1.h5")
model_metrics_filepath = os.path.join(pardir, "model_metrics_v1.png")

if os.path.exists(model_filepath):
    res_net_model = models.load_model(model_filepath)
    filename = os.path.splitext(os.path.split(model_filepath)[1])[0]
    vnum = int(model_filepath[model_filepath.index("_v")+2:model_filepath.index(".h5")])
    model_filepath = os.path.join(pardir, "model_v" + str(vnum+1) + ".h5")

    res_net_model.summary()

    predictions = res_net_model.predict(x_test, batch_size=25)
    predictions = np.argmax(predictions, axis=1)
    cmtx = confusion_matrix(y_test, predictions)
    ax = seaborn.heatmap(cmtx, annot=True)
    plt.show()
    #plot_metrics(res_net_model.history, model_metrics)
    #plt.savefig(model_metrics_filepath)
else:
    res_net_model = build_model(input_shape)
    res_net_model.compile(optimizer=opt, loss=losses.BinaryCrossentropy(), metrics=model_metrics)

    res_net_model.summary()
    history = res_net_model.fit(x_train, y_train, epochs=num_epochs, batch_size=bat_size, callbacks=early_stop,
                      validation_data=(x_valid, y_valid))
    res_net_model.save(model_filepath)

    predictions = res_net_model.predict(x_test, batch_size=25)
    predictions = np.argmax(predictions, axis=1)
    #plot_metrics(history, model_metrics)
    #plt.savefig(model_metrics_filepath)
