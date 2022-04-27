"""

"""


from fusion_review.intensities import IntensityDatabase
from fusion_review.utilities import DataWriter
from functools import partial
import multiprocessing as mp


def ncpus():
    return mp.cpu_count() - 1


def mpu_draw_to_tifs(intensity_superstructure, trace_panel_writer):
    src_tuple = tuple(source for source in intensity_superstructure.sources)
    num_cores = ncpus()
    pool = mp.Pool(num_cores)
    temp = partial(mpu_draw, trace_panel_writer)
    pool.map(func=temp, iterable=src_tuple)
    pool.close()
    pool.join()
    print("Multiple processes converged.")


def mpu_draw(tpw, src):
    tpw.draw(src)


def mpu_analyze_defocusing_events(intensity_superstructure):
    flow_dictionary = intensity_superstructure.get_flux_start()
    src_tuple = tuple(source for source in intensity_superstructure.sources)
    num_cores = ncpus()
    if num_cores >= len(src_tuple):
        num_cores = len(src_tuple)
    print("Utilizing multi-core processing for trace changepoint analysis...")
    pool = mp.Pool(num_cores)
    temp = partial(defocus, flow_dictionary, intensity_superstructure)
    pool.map(func=temp, iterable=src_tuple)
    pool.close()
    pool.join()
    print("Multiple processes converged.")


def defocus(flow_dict, iss, src):
    datum_key = iss.get_datum_key(src)
    ID = IntensityDatabase(iss.par, datum_key)
    ID.set_source(src)
    ID.get_traces(iss)
    ID.set_times(flow_dict[datum_key])
    dw = DataWriter(ID)
    dw.defocus_output(isMulti=True)
