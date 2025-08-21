"""
This contains the object IntensityTraceFigurePanel, which serves as the graphical component of the application.

Created by - { alias : lambdacoffee :: author : Marcos Cervantes }
"""


from trace_manager import IntensityTrace
import matplotlib.pyplot as plt


class FigurePanel:

    """
    Object representing the interface panel that displays traces for User.

    Attributes
    ----------
    num_rows : int
        number of rows to display per panel
    num_columns : int
        number of columns to display per panel
    num_traces : int
        number of traces to account for in total
    panel_width : int
        width of the panel in inches
    panel_height : int
        height of the panel in inches

    Methods
    -------
    todo: this section
    """

    def __init__(self, num_rows, num_columns, num_traces, panel_width=12, panel_height=5):
        """
        :param num_rows: number of rows to display per panel
        :param num_columns: number of columns to display per panel
        :param num_traces: number of traces to account for in total
        :param panel_width: width of the panel in inches, default=12
        :param panel_height: height of the panel in inches, default=5
        """

        self.rows = num_rows
        self.cols = num_columns
        self.ntraces = num_traces
        self.dim = (self.rows, self.cols, (self.ntraces // (self.rows * self.cols)) + 1)
        self.single = False
        self.isInverted = False
        self.textcolor = "black"
        self.panels = [[[IntensityTrace() for _ in range(self.dim[1])] for _ in range(self.dim[0])] for _ in range(self.dim[2])]
        self.coordinates = self.set_coordinate_grid()
        self.width = panel_width
        self.height = panel_height
        self.fig, self.axs = self.form_panel()
        self.time = []
        self.isDisplay = True
        self.showChangepoints = False
        self.disp = {True: plt.ion, False: plt.ioff}
        if self.rows == self.cols == 1:
            self.single = True

    def __len__(self):
        return self.dim[-1]

    def __next__(self):
        if self.panel_value >= self.dim[-1]:
            raise StopIteration
        self.panel_value += 1
        start_index = (self.rows * self.cols) * (self.panel_value - 1)
        stop_index = start_index + (self.rows * self.cols)
        self.window = slice(start_index, stop_index)
        return self.panel_value - 1

    def __iter__(self):
        self.panel_value = 0
        return self

    def __getitem__(self, index):
        return self.panels[index]

    def set_text_color(self):
        self.textcolor = "black" if not self.isInverted else "white"

    def allocate(self, traces, start_frame):
        for i in range(self.__len__()):
            for j in range(self.rows):
                for k in range(self.cols):
                    try:
                        intensity_trace = traces[k + (j * self.cols) + (i * self.rows * self.cols) + 1]
                        intensity_trace.start = start_frame
                    except KeyError:
                        continue
                    else:
                        self.panels[i][j][k] = intensity_trace
                        if len(self.time) == 0:
                            self.time = [t for t in range(1, len(intensity_trace.raw) + 1)]
        return 0

    def rearrange(self, number_rows, number_columns):
        plt.close()
        temp_array = []
        for i in range(len(self)):
            for j in range(self.rows):
                for k in range(self.cols):
                    trace_obj = self.panels[i][j][k]
                    if trace_obj.num != 0:
                        temp_array.append(trace_obj)
        self.rows = number_rows
        self.cols = number_columns
        self.dim = (self.rows, self.cols, (self.ntraces // (self.rows * self.cols)) + 1)
        self.panels = [[[IntensityTrace() for _ in range(self.dim[1])] for _ in range(self.dim[0])] for _ in range(self.dim[2])]
        self.coordinates = self.set_coordinate_grid()
        for idx in range(len(temp_array)):
            trace_object = temp_array[idx]
            coords = self.coordinates[idx % len(self.coordinates)]
            panel_idx = idx // (self.rows * self.cols)
            self.panels[panel_idx][coords[0]][coords[1]] = trace_object
        return self.window.start

    def invert_colors(self):
        if self.isInverted:
            self.fig.set_facecolor("black")
            for coords in self.coordinates:
                if self.rows == 1:
                    coords = (coords[1],)
                self.axs[coords].set_facecolor("gray")
                self.axs[coords].tick_params(color="white", labelcolor="white")
        else:
            self.fig.set_facecolor("white")
            for coords in self.coordinates:
                if self.rows == 1:
                    coords = (coords[1],)
                self.axs[coords].set_facecolor("white")
                self.axs[coords].tick_params(color="black", labelcolor="black")

    def fill(self):
        self.fig.suptitle("Figure Panel {} of {}".format(self.panel_value, len(self)), fontsize=16, color=self.textcolor)
        with self.disp[self.isDisplay]():
            for idx in range(self.window.start, self.window.stop):
                coords = self.coordinates[idx % len(self.coordinates)]
                panel_idx = idx // (self.rows * self.cols)
                trace = self.panels[panel_idx][coords[0]][coords[1]]
                if self.rows == 1:
                    coords = (coords[1],)
                self.axs[coords].clear()
                if trace.num == 0:
                    continue
                if self.showChangepoints:
                    for p in trace.changepoints:
                        self.axs[coords].axvline(x=p, color="black", linestyle="dashed", zorder=0)
                isFusion = trace.isFused
                if isFusion:
                    if trace.start == 0:
                        self.axs[coords].axvline(x=trace.binding, color="tab:orange", linestyle="dashed", zorder=0)
                    fusion_interval_points = trace.get_fusion_data()
                    self.axs[coords].axvline(x=fusion_interval_points[0], color="r", linestyle="dashed", zorder=0)
                    self.axs[coords].axvline(x=fusion_interval_points[1], color="r", zorder=0)
                    self.axs[coords].axvline(x=fusion_interval_points[2], color="r", linestyle="dashed", zorder=0)
                if trace.start != 0:
                    self.axs[coords].axvline(x=trace.start, color=trace.start_color, linestyle="dashed")
                self.axs[coords].plot(self.time, trace.norm, color=trace.color)
                self.axs[coords].set_title("Trace {} of {}".format(trace.num, self.ntraces), fontsize=8, color=self.textcolor)
                self.axs[coords].label_outer()
        self.fig.tight_layout()
        if self.isDisplay:
            plt.pause(0.0001)
        return 0

    def set_coordinate_grid(self):
        res = [(i, j) if self.rows > 1 else (0, j) for i in range(self.rows) for j in range(self.cols)]
        return res

    def form_panel(self):
        fig, axs = plt.subplots(self.rows, self.cols)
        fig.set_size_inches(self.width, self.height)
        return fig, axs

    def get_trace(self, trace_number):
        coordinates = self.coordinates[(trace_number - 1) % len(self.coordinates)]
        panel_idx = (trace_number - 1) // (self.rows * self.cols)
        trace = self.panels[panel_idx][coordinates[0]][coordinates[1]]
        return trace

    def undo_trace(self, trace_number):
        trace = self.get_trace(trace_number)
        trace.undo()

    def exclude_trace(self, trace_number):
        trace = self.get_trace(trace_number)
        trace.exclude()

    def mark_fusion(self, trace_number):
        trace = self.get_trace(trace_number)
        fig = plt.figure()
        ax = plt.gca()
        with plt.ion():
            if self.isInverted:
                fig.set_facecolor("black")
                ax.set_facecolor("gray")
                ax.tick_params(color="white", labelcolor="white")
            plt.rcParams["figure.figsize"] = (self.width, self.height)
            plt.plot(self.time, trace.norm, color=trace.color)
            plt.axvline(x=trace.start, color=trace.start_color, linestyle="dashed", zorder=0)
            plt.title("Trace {}".format(trace.num), fontsize=16, color=self.textcolor)
            plt.xticks(ticks=[200 * i for i in range(len(self.time) // 200)])
            plt.pause(0.0001)
        nClicks = 3 if trace.start == 0 else 2
        print("Waiting for User to press any key to continue...")
        zoom_ok = False
        while not zoom_ok:
            zoom_ok = plt.waitforbuttonpress()
        print("Use mouse to left-click on {} points in the trace.".format(nClicks))
        fusion_times = plt.ginput(n=nClicks, timeout=0, show_clicks=True)
        fusion_times = [round(fusion_times[i][0]) for i in range(len(fusion_times))]
        plt.close()
        return trace, fusion_times

    def mark_reviewed(self):
        for idx in range(self.window.start, self.window.stop):
            coords = self.coordinates[idx % len(self.coordinates)]
            panel_idx = idx // (self.rows * self.cols)
            trace = self.panels[panel_idx][coords[0]][coords[1]]
            if trace.num != 0:
                trace.isReviewed = True

    def write(self, destination_filepath):
        with open(destination_filepath, "r") as dst:
            mat_filename = dst.readline().strip()
        with open(destination_filepath, "w+") as dst:
            dst.writelines(mat_filename + "\n")
            for i in range(self.dim[2]):
                for j in range(self.rows):
                    for k in range(self.cols):
                        trace = self.panels[i][j][k]
                        if trace.num == 0:
                            continue
                        line = trace.get_line_components()
                        line = [str(int(i)) for i in line]
                        line = ",".join(line)
                        dst.writelines(line + "\n")

    def read(self, text_filepath):
        with open(text_filepath, "r") as txt:
            text_lines = txt.readlines()
        text_lines = text_lines[1:]
        for idx in range(len(text_lines)):
            line = text_lines[idx]
            line_array = line.split(",")
            line_array = [int(i) for i in line_array]
            panel_idx = idx // (self.rows * self.cols)
            row_idx = (idx % (self.rows * self.cols)) // self.cols
            col_idx = (idx % (self.rows * self.cols)) % self.cols
            trace = self.panels[panel_idx][row_idx][col_idx]
            trace.load_line_components(line_array)
            if not trace.isReviewed:
                return panel_idx
            self.panels[panel_idx][row_idx][col_idx] = trace
        return -1
