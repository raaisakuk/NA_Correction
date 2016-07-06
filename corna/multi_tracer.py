from numpy.linalg import pinv
import re
import pandas as pd
import numpy as np
import helpers as hl
from itertools import product
import algorithms as algo






def multi_label_matrix(na_dict, formula_dict, eleme_corr_list):

    correction_vector = [1.]
    correction_matrix = [1.]

    for trac in eleme_corr_list:
        no_atom_tracer = formula_dict[trac]
        eleme_corr = {}
        matrix_tracer = algo.corr_matrix(str(trac), formula_dict, eleme_corr, no_atom_tracer, na_dict, correction_vector)
        correction_matrix = np.kron(correction_matrix, matrix_tracer)

    return correction_matrix

def multi_label_correc(na_dict, formula_dict, eleme_corr_list, intensities_list):

    M = multi_label_matrix(na_dict, formula_dict, eleme_corr_list)

    Minv=pinv(M)

    icorr = np.matmul(Minv,intensities_list)

    return icorr



def eleme_corr_to_list(iso_tracers, eleme_corr):

    trac_atoms = algo.get_atoms_from_tracers(iso_tracers)

    eleme_corr_list = []
    for i in trac_atoms:
        eleme_corr_list.append([i])
        if i in eleme_corr.keys():
            eleme_corr_list.append(eleme_corr[i])

    return sum(eleme_corr_list, [])



def filter_tuples(tuple_list, value_dict, positions):
    result_tuples = []
    for tuples in tuple_list:
        tuple_l = list(tuples)
        filtered_tuple = [tuple_l[x] for x in positions]
        if sum(filtered_tuple) == 0:
            rqrd_pos = [tuple_l[x] for x in range(0,len(tuple_l)) if x not in positions]
            rqrd_tup = tuple(rqrd_pos)
            if rqrd_tup in value_dict.keys():
                result_tuples.append(value_dict[rqrd_tup][0])
            else:
                result_tuples.append(0)
        else:
            result_tuples.append(0)
    return result_tuples


def multi_trac_na_correc(merged_df, iso_tracers, eleme_corr, na_dict):

    labels_std = hl.convert_labels_to_std(merged_df, iso_tracers)
    merged_df['Label'] = labels_std
    sample_label_dict = algo.samp_label_dcit(iso_tracers, merged_df)
    formula_dict = algo.formuladict(merged_df)
    trac_atoms = algo.get_atoms_from_tracers(iso_tracers)
    fragments_dict = algo.fragmentsdict_model(merged_df)

    if not eleme_corr:
        eleme_corr_list = trac_atoms
    else:
        eleme_corr_list = eleme_corr_to_list(iso_tracers, eleme_corr)



    no_atom_tracers = []
    for i in eleme_corr_list:
        no_atom_tracers.append(formula_dict[i])

    corr_intensities_dict = {}
    for samp_name, lab_dict in sample_label_dict.iteritems():
        intens_idx_dict = {}
        l = [np.arange(x+1) for x in no_atom_tracers]
        tup_list = list(product(*l))

        indist_sp = sum(eleme_corr.values(),[])

        tup_pos = [i for i, e in enumerate(eleme_corr_list) if e in indist_sp]

        intensities_list = filter_tuples(tup_list, lab_dict, tup_pos)

        icorr = multi_label_correc(na_dict, formula_dict, eleme_corr_list, intensities_list)
        print 'corrected inten'
        print icorr
        ############### line below is incorroect dictionary for now
        # to do here, this is input data dict only - to get the icorr values with keys here
        intens_idx_dict = lab_dict

        corr_intensities_dict[samp_name] = intens_idx_dict

    sample_list = algo.check_samples_ouputdict(corr_intensities_dict)
    # { 0: { sample1 : val, sample2: val }, 1: {}, ...}
    lab_samp_dict = algo.label_sample_dict(sample_list, corr_intensities_dict)

    nacorr_dict_model = algo.fragmentdict_model(iso_tracers, fragments_dict, lab_samp_dict)

    return nacorr_dict_model