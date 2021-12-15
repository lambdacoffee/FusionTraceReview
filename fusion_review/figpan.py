"""

"""


from fusion_review.itrace import IntensityTrace
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


class IntensityTraceFigurePanel:

    def __init__(self, num_traces, num_rows, num_columns, intensity_database):
        #GET RID OF NUM_TRACES AND JUST USE ID.NUM_TRACES
        self.id = intensity_database
        self.stidx = 0
        self.curridx = self.stidx
        self.rows = num_rows
        self.cols = num_columns
        self.isSingle = False
        self.inverted = False
        self.disp = True
        self.figs = ((num_traces - self.stidx) // (self.rows * self.cols)) + 1
        if self.rows == self.cols == 1:
            self.isSingle = True
            self.figs -= 1

    def invert_colors(self):
        if self.inverted:
            mpl.rc("axes", edgecolor="white", facecolor="gray", labelcolor="white")
            mpl.rc("text", color="white")
            mpl.rc("figure", facecolor="black")
            mpl.rc("xtick", color="white")
            mpl.rc("ytick", color="white")
        else:
            mpl.rc("axes", edgecolor="black", facecolor="white", labelcolor="black")
            mpl.rc("text", color="black")
            mpl.rc("figure", facecolor="white")
            mpl.rc("xtick", color="black")
            mpl.rc("ytick", color="black")

    def handle_multiple_plots(self, axes):
        for row_idx in range(0, self.rows):
            for col_idx in range(0, self.cols):
                if self.rows > 1:
                    coords = (row_idx, col_idx)
                else:
                    coords = (col_idx,)
                axes[coords].label_outer()
                if self.curridx >= self.id.num_traces:
                    break
                self.setup(axes[coords])
                axes[coords].set_title("Trace {} of {}".format(self.curridx+1, self.id.num_traces), fontsize=8)
                start_line_color = "orange" if self.id.df["isFusion"][self.curridx] else "tab:blue"
                axes[coords].axvline(x=self.id.start, color=start_line_color, linestyle="dashed")
                self.curridx += 1
            if self.curridx >= self.id.num_traces:
                break
        if self.disp:
            plt.show(block=False)

    def handle_single_plot(self, panel_count):
        self.setup(plt)
        plt.axvline(x=self.id.start, color="b", linestyle="dashed", zorder=0)
        plt.title("Trace {} of {}".format(panel_count, self.figs), fontsize=16)
        fig = plt.gcf()
        fig.set_size_inches(12, 5)
        plt.xticks(ticks=[200*i for i in range(0, len(self.id.full_time) // 200)])
        if self.disp:
            plt.show(block=False)
        self.curridx += 1

    def setup(self, axes):
        it = IntensityTrace(self.curridx+1, self.id)
        it.set_raw_norm_data()
        for key in it.datad:
            curr_color = it.datad[key]["c"]
            curr_z = it.datad[key]["z"]
            if key == "TruncDataNorm":
                axes.plot(self.id.full_time, np.asarray(self.id.df["RawDataNorm"][self.curridx]), zorder=curr_z, color=curr_color)
                continue
        if it.isFusion:
            fusion_interval_points = it.get_fusion_data()
            axes.axvline(x=fusion_interval_points[0], color="r", linestyle="dashed", zorder=0)
            axes.axvline(x=fusion_interval_points[1], color="r", zorder=0)
            axes.axvline(x=fusion_interval_points[2], color="r", linestyle="dashed", zorder=0)
        return axes

    def form_plot(self):
        for panel in range(self.stidx, self.figs):
            fig, axes = self.form_panel(panel + 1)
            if self.isSingle:
                self.handle_single_plot(axes)
            else:
                self.handle_multiple_plots(axes)

    def form_panel(self, panel_count):
        if not self.isSingle:
            fig, ax = plt.subplots(self.rows, self.cols)
            plt.subplots_adjust(hspace=0.4)
            fig.suptitle("Figure Panel {} of {}".format(panel_count, self.figs), fontsize=16)
            fig.set_size_inches(12, 5)
            return fig, ax
