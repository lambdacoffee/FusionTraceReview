"""
This contains the object IntensityTraceFigurePanel, which serves as the graphical component of the application.

Created by - { alias : lambdacoffee :: author : Marcos Cervantes }
"""


from sklearn.neighbors._kde import KernelDensity
from fusion_review.itrace import IntensityTrace
from scipy.signal import argrelmax
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np


class IntensityTraceFigurePanel:

    def __init__(self, num_rows, num_columns, intensity_database, defocus_handler):
        self.id = intensity_database
        self.dh = defocus_handler
        self.stidx = 0
        self.curridx = self.stidx
        self.rows = num_rows
        self.cols = num_columns
        self.isSingle = False
        self.inverted = False
        self.show_defocus = False
        self.disp = True
        self.figs = ((self.id.num_traces - self.stidx) // (self.rows * self.cols)) + 1
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
        it.set_filter()
        it.set_rms()
        it.set_gradients()
        it.set_cumsum()
        it.set_rms()
        it.guess = True if self.id.df["Prediction"][self.curridx] == 1 else False
        if it.guess:
            it.datad["TruncDataNorm"]["c"] = "tab:purple"
        norm_data = []
        norm_z = 0
        for key in it.datad:
            curr_color = it.datad[key]["c"]
            curr_z = it.datad[key]["z"]
            if key == "TruncDataNorm":
                norm_data, = axes.plot(self.id.full_time, np.asarray(self.id.df["RawDataNorm"][self.curridx]), zorder=curr_z,
                          color=curr_color)
                norm_z = curr_z
            elif key == "TruncDataNormGrad":
                #axes.plot(it.datad[key]["time"], np.asarray(it.datad[key]["data"]), zorder=curr_z, color=curr_color)
                pass
            elif key == "TruncDataNormFilt" and it.guess:
                axes.plot(it.datad[key]["time"], np.asarray(it.datad[key]["data"]), zorder=curr_z, color=curr_color)
            elif key == "TruncCumSum":
                #axes.plot(it.datad[key]["time"], np.asarray(it.datad[key]["data"]), zorder=curr_z, color=curr_color)
                pass
            elif key == "TruncDataNormRMS":
                axes.plot(it.datad[key]["time"], np.asarray(it.datad[key]["data"]), zorder=curr_z, color=curr_color)
        if self.show_defocus and it.guess:
            trace_points = self.dh.changepoints[self.curridx+1]
            defocus_events_intrsxn = self.dh.events.intersection(trace_points)
            possible_fusion_events_intrsxn = trace_points.difference(defocus_events_intrsxn)
            rares = self.dh.rares.intersection(possible_fusion_events_intrsxn)
            displayed_points = []
            """for p in defocus_events_intrsxn:
                axes.axvline(x=p, color="k", linestyle="dashed", zorder=0)
                displayed_points.append(p)"""
            # handle step point
            step = self.dh.steps[self.curridx+1]
            if step in possible_fusion_events_intrsxn and it.datad["TruncDataNormGrad"]["data"][step] >= 0:
                color = "tab:blue" if step in rares else "tab:purple"
                axes.axvline(x=step, color=color, linestyle="solid", zorder=0)
                displayed_points.append(step)
            # handle filter points
            fusion_filter_points = possible_fusion_events_intrsxn.intersection(self.dh.filtpoints[self.curridx+1])
            for p in fusion_filter_points:
                if it.datad["TruncDataNormGrad"]["data"][p] >= 0:
                    line_style = "solid" if p in rares else "dashed"
                    axes.axvline(x=p, color="tab:orange", linestyle=line_style, zorder=0)
                    displayed_points.append(p)

            focus_array = defocus_events_intrsxn
            if len(focus_array) > 1:
                focus_array = list(focus_array)
                focus_array.sort()
                focus_array = np.array(focus_array)
                kde = KernelDensity(bandwidth=20, kernel="gaussian")
                kde.fit(focus_array.reshape(-1, 1))
                data = np.exp(kde.score_samples(focus_array.reshape(-1, 1)))
                peaks = argrelmax(data)[0]
                peaks.sort()
                for p in peaks:
                    axes.axvline(x=focus_array[p], color="k", linestyle="solid")

            # handle extrema from cumsum data
            fusion_extrema_points = possible_fusion_events_intrsxn.intersection(self.dh.extrema[self.curridx+1])
            for p in fusion_extrema_points:
                if it.datad["TruncDataNormGrad"]["data"][p] > 0:
                    linestyle = "solid" if p in rares else "dashed"
                    line_color = "white" if p-5 <= step <= p+5 else "red"
                    axes.axvline(x=p, color=line_color, linestyle=linestyle, zorder=0)
                    if line_color == "white":
                        lower = 0
                        upper = 0
                        q = p
                        while it.datad["TruncDataNormGrad"]["data"][q] > 0 and q >= self.id.start:
                            lower = q
                            q -= 1
                        q = p
                        while it.datad["TruncDataNormGrad"]["data"][q] > 0 and q <= len(self.id.full_time)-self.id.start-1:
                            upper = q
                            q += 1
                        if any([j for j in focus_array if j in range(lower, upper+1)]):
                            axes.axvline(x=lower, color="tab:green", linestyle="solid", zorder=norm_z+1)
                            axes.axvline(x=upper, color="tab:green", linestyle="solid", zorder=norm_z+1)
                    displayed_points.append(p)

            #trace_fusion_intrsxn = self.dh.fusions.intersection()
            #for p in self.dh.fusions:
            #    if it.datad["TruncDataNormGrad"]["data"][p - self.id.start] > 0:
            #        axes.axvline(x=p, color="tab:orange", linestyle="dashed", zorder=0)
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
