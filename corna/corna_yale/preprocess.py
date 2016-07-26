
import math

import numpy as np
from scipy.misc import comb

import corna.helpers as hl

def background_noise(unlabel_intensity, na, parent_atoms, parent_label, daughter_atoms, daughter_label):
    noise = unlabel_intensity*math.pow(na, parent_label)\
            *comb(parent_atoms - daughter_atoms, parent_label - daughter_label)\
            *comb(daughter_atoms, daughter_label)
    return noise

def backround_subtraction(input_intensity, noise):
    intensity = input_intensity - noise
    return intensity

def background(list_of_replicates, input_fragment_value, unlabeled_fragment_value):
    parent_frag, daughter_frag = input_fragment_value[0]
    data = input_fragment_value[1]
    iso_elem = hl.get_isotope_element(parent_frag.isotracer)
    parent_label = parent_frag.get_num_labeled_atoms_isotope(parent_frag.isotracer)
    parent_atoms = parent_frag.number_of_atoms(iso_elem)
    na = hl.get_isotope_na(parent_frag.isotracer)
    daughter_atoms = daughter_frag.number_of_atoms(iso_elem)
    daughter_label = daughter_frag.get_num_labeled_atoms_isotope(parent_frag.isotracer)
    unlabeled_data = unlabeled_fragment_value[1]
    background_list = []
    for sample_name in list_of_replicates:
        noise = background_noise(unlabeled_data[sample_name], na, parent_atoms,
                                 parent_label, daughter_atoms, daughter_label)
        background = backround_subtraction(data[sample_name], noise)
        background_list.append(background)
    return background_list

def background_correction(background_list, sample_data, decimals):
    background = max(background_list)
    corrected_sample_data = {}
    for key, value in sample_data.iteritems():
        new_value = np.around(value - background, decimals)
        corrected_sample_data[key] = new_value
    return corrected_sample_data

def bulk_background_correction(fragment_dict, list_of_samples, background_sample, decimals):
    input_fragments = []
    unlabeled_fragment = []
    corrected_fragments_dict = {}
    for key, value in fragment_dict.iteritems():
        unlabel = value[2]
        if unlabel:
            unlabeled_fragment.append((key,value))
            input_fragments.append((key,value))
        else:
            input_fragments.append((key,value))
    try:
        assert len(unlabeled_fragment) == 1
    except AssertionError:
        raise AssertionError('The input should contain atleast and only one unlabeled fragment data'
                             'Please check metadata or raw data files')
    for input_fragment in input_fragments:
        background_list = background(background_sample, input_fragment[1], unlabeled_fragment[0][1])
        sample_data = {}
        data = input_fragment[1][1]
        for sample_name in list_of_samples:
            sample_data[sample_name] = data[sample_name]
        corrected_sample_data = background_correction(background_list, sample_data, decimals)
        corrected_fragments_dict[input_fragment[0]] = [input_fragment[1][0], corrected_sample_data,
                                                       input_fragment[1][2], input_fragment[1][3]]
    return corrected_fragments_dict