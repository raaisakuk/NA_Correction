
import numpy as np
import helpers as hl
import numpy
import math
from scipy import optimize
import file_parser as fp
import isotopomer as iso

# MULTIQUANT
def na_correct_mimosa_algo(parent_frag_m, daughter_frag_n, intensity_m_n, intensity_m_1_n, intensity_m_1_n_1,
                      isotope, na, decimals):
    p = parent_frag_m.get_number_of_atoms_isotope(isotope)
    d = daughter_frag_n.get_number_of_atoms_isotope(isotope)
    m = parent_frag_m.get_num_labeled_atoms_tracer()
    n = daughter_frag_n.get_num_labeled_atoms_tracer()

    corrected_intensity = intensity_m_n * (1+na*(p-m)) - intensity_m_1_n * na * ((p-d) - (m-n-1)) -\
                         intensity_m_1_n_1 * na * (d - (n-1))
    return np.around(corrected_intensity, decimals)

def na_correct_mimosa_algo_array(parent_frag_m, daughter_frag_n, intensity_m_n, intensity_m_1_n, intensity_m_1_n_1,
                      isotope, na, decimals):
    p = parent_frag_m.get_number_of_atoms_isotope(isotope)
    d = daughter_frag_n.get_number_of_atoms_isotope(isotope)
    m = parent_frag_m.get_num_labeled_atoms_tracer()
    n = daughter_frag_n.get_num_labeled_atoms_tracer()
    corrected_intensity = intensity_m_n * (1+na*(p-m)) - intensity_m_1_n * na * ((p-d) - (m-n-1)) -\
                         intensity_m_1_n_1 * na * (d - (n-1))

    return np.around(corrected_intensity, decimals)

def arrange_fragments_by_mass(fragments_dict):
    fragment_dict_mass = {}
    for key, value in fragments_dict.iteritems():
        parent_frag, daughter_frag = value[0]
        fragment_dict_mass[(parent_frag.isotope_mass, daughter_frag.isotope_mass)] = value
    return fragment_dict_mass

def na_correction_mimosa_by_fragment(fragments_dict, decimals):
    fragment_dict_mass = arrange_fragments_by_mass(fragments_dict)
    corrected_dict_mass = {}
    for key, value in fragment_dict_mass.iteritems():
        m_1_n = (key[0]-1, key[1])
        m_1_n_1 = (key[0]-1, key[1]-1)
        parent_frag_m, daughter_frag_n = value[0]
        isotope = parent_frag_m.isotope
        na = hl.get_isotope_na(isotope)
        data = value[1]
        corrected_data = {}
        for sample_name, intensity_m_n in data.iteritems():
            try:
                intensity_m_1_n = fragment_dict_mass[m_1_n][1][sample_name]
            except KeyError:
                intensity_m_1_n = np.zeros(len(intensity_m_n))
            try:
                intensity_m_1_n_1 = fragment_dict_mass[m_1_n_1][1][sample_name]
            except KeyError:
                intensity_m_1_n_1 = np.zeros(len(intensity_m_n))
            corrected_data[sample_name] = na_correct_mimosa_algo_array(parent_frag_m,
                                        daughter_frag_n, intensity_m_n, intensity_m_1_n,
                                        intensity_m_1_n_1, isotope, na, decimals)

        corrected_dict_mass[key] = [value[0], corrected_data, value[2], value[3]]
    return corrected_dict_mass

# MAVEN





def excluded_elements(iso_tracer, formula_dict, eleme_corr):
    el_excluded = []
    for key, value in formula_dict.iteritems():
        if iso_tracer in eleme_corr.keys():
            if key not in eleme_corr[iso_tracer]:
                el_excluded.append(key)
    return el_excluded


def calc_mdv(formula_dict, iso_tracer, eleme_corr, na_dict):
    """
    Calculate a mass distribution vector (at natural abundancy),
    based on the elemental compositions of both metabolite's and
    derivative's moieties.
    The element corresponding to the isotopic tracer is not taken
    into account in the metabolite moiety.
    """
    el_excluded = excluded_elements(iso_tracer, formula_dict, eleme_corr)

    correction_vector = [1.]
    for el, n in formula_dict.iteritems():

        if not el == iso_tracer and el not in el_excluded:

            for i in range(n):
                correction_vector = numpy.convolve(correction_vector, na_dict[el])

    return list(correction_vector)


def corr_matrix(iso_tracer, formula_dict, eleme_corr, no_atom_tracer, na_dict, correction_vector):

    #no_atom_tracer = formula_dict[iso_tracer]
    el_excluded = excluded_elements(iso_tracer,formula_dict, eleme_corr)
    correction_matrix = numpy.zeros((no_atom_tracer+1, no_atom_tracer+1))
    el_pur = na_dict[iso_tracer]
    el_pur.reverse()

    for i in range(no_atom_tracer+1):

        column = correction_vector[:no_atom_tracer+1]
        #for na in range(i):
            #column = numpy.convolve(column, el_pur)[:no_atom_tracer+1]
        if el_excluded != iso_tracer:
            for nb in range(no_atom_tracer-i):
                column = numpy.convolve(column, na_dict[iso_tracer])[:no_atom_tracer+1]


        correction_matrix[:,i] = column

    return correction_matrix




def na_correction(correction_matrix, intensities, no_atom_tracer, optimization = False):

    if optimization == False:
        matrix = numpy.array(correction_matrix)
        mat_inverse = numpy.linalg.inv(matrix)
        inten_trasp = numpy.array(intensities).transpose()
        corrected_intensites = numpy.dot(mat_inverse, inten_trasp)

    else:
        corrected_intensites, residuum = [], [float('inf')]
        icorr_ini = numpy.zeros(no_atom_tracer+1)
        inten_trasp = numpy.array(intensities).transpose()
        corrected_intensites, r, d = optimize.fmin_l_bfgs_b(cost_function, icorr_ini, fprime=None, approx_grad=0,\
                                           args=(inten_trasp, correction_matrix), factr=1000, pgtol=1e-10,\
                                           bounds=[(0.,float('inf'))]*len(icorr_ini))


    return corrected_intensites


def cost_function(corrected_intensites, intensities, correction_matrix):
    """
    Cost function used for BFGS minimization.
        return : (sum(v_mes - mat_cor * corrected_intensites)^2, gradient)
    """
    x = intensities - numpy.dot(correction_matrix, corrected_intensites)
    # calculate sum of square differences and gradient
    return (numpy.dot(x,x), numpy.dot(correction_matrix.transpose(),x)*-2)

def fragmentsdict_model(merged_df):
    fragments_dict = {}
    std_model_mvn = fp.standard_model(merged_df, parent = False)
    for frag_name, label_dict in std_model_mvn.iteritems():
        fragments_dict.update(iso.bulk_insert_data_to_fragment(frag_name, label_dict, mass=False, number=True, mode=None))

    return fragments_dict


def samp_label_dcit(merged_df):
    fragments_dict = fragmentsdict_model(merged_df)
    universe_values = fragments_dict.values()
    sample_list = []
    for uv in universe_values:
        samples = uv[1].keys()
        sample_list.extend(samples)
    sample_list = list(set(sample_list))

    outer_dict = {}
    for s in sample_list:
        dict_s = {}
        for uv_new in universe_values:
            num = uv_new[0].get_num_labeled_atoms_isotope('C13')
            dict_s[num] = uv_new[1][s]
        outer_dict[s] = dict_s

    return outer_dict

def formuladict(merged_df):
    fragments_dict = fragmentsdict_model(merged_df)
    formula_dict = {}
    for key, value in fragments_dict.iteritems():
        formula_dict =  value[0].get_formula()

    return formula_dict


def na_corrected_output(merged_df, iso_tracers, eleme_corr, na_dict):
    outer_dict = samp_label_dcit(merged_df)
    formula_dict = formuladict(merged_df)
    fragments_dict = fragmentsdict_model(merged_df)

    dict2 = {}
    for key, value in outer_dict.iteritems():

        intensities = numpy.concatenate(numpy.array((value).values()))
        #dict2 = {}

        if len(iso_tracers) == 1:
            iso_tracer = iso_tracers[0]

            no_atom_tracer = formula_dict[iso_tracer]

            correction_vector = calc_mdv(formula_dict, iso_tracer, eleme_corr, na_dict)

            correction_matrix = corr_matrix(iso_tracer, formula_dict, eleme_corr, no_atom_tracer, na_dict, correction_vector)

            icorr = na_correction(correction_matrix, intensities, no_atom_tracer, optimization = True)

            intensities = icorr

        dict2[key] = icorr

        dict1 = {}
        for i in range(0, len(icorr)):
            dict1[i] = icorr[i]

        dict2[key] = dict1


    univ_new = dict2.values()
    inverse_sample = []
    for un_new in univ_new:
        inverse_sample.extend(un_new.keys())
    inverse_sample = list(set(inverse_sample))

    dict_inverse = {}
    for inv in inverse_sample:
        sample_dict = {}
        for sample_tr in dict2.keys():
            k = dict2[sample_tr][inv]
            sample_dict[sample_tr] = numpy.array([k])
        dict_inverse[inv] = sample_dict


    #fragment dict model
    new_fragment_dict = {}
    for key, value in fragments_dict.iteritems():
        new_fragment_dict[key] = [value[0], dict_inverse[value[0].get_num_labeled_atoms_isotope('C13')], value[2], value[3]]

    return new_fragment_dict




