"""This module helps to do validation using validation package olmonk"""

import pandas as pd

from datum import helpers as dat_hlp
from olmonk import ConfigDataValidator as CDV
from olmonk import helpers as hlp

from corna import constants as const


def get_validation_df(path, required_columns=None):
    """takes path of the file, validates it and returns result

    Using path of the file, it instantiates the validation class
    and use its methods to validate file and returns result of
    that. If file not passes the validation checks, then it will
    raise an error, otherwise it will returns validated df.
    Args:
        path: file path for which validation is needed

    Returns: instance of validated df
    """
    # TODO: add olmonk 0.1.3 CDV to this
    try:
        validated_df = dat_hlp.read_file(path)
        return validated_df
    except Exception as e:
        raise Exception(e)


def get_class_inst(class_name, file_path, required_columns):
    """
    Instantiates class with its argument and returns it
    """

    return class_name(file_path, required_columns)


def basic_validation_result(basic_validator):
    """
    Takes instance of BASIC VALIDATION class, do basic validation
    such as if file path exists, is file empty. This function will
    raise an error if any check fails.
    """

    try:
        basic_validator.check_path_exist()
        basic_validator.check_file_empty()
        basic_validator.check_if_convert_to_df()
    except Exception as e:
        raise Exception(e)


def data_validation_raw_df(input_df, is_sample_metadata):
    """do datavalidtaion for raw_file_df and returns report_df

    It takes df of raw_mq file, creates an instance of DataValidation
    using this df. It then does validation related to file and returns
    the report_df.

    Args:
        df: raw_mq_file df

    Returns:
        report_df contains report of error & warning in this df
    """
    # :TODO: update doc when this function will be updated
    try:
        raw_mq_dict = dict(const.RAW_MQ_DICT)
        if is_sample_metadata:
            raw_mq_dict['required_columns'] = const.RAW_FILE_REQUIRED_COLS_WITH_SAMPLE_METADATA
        else:
            raw_mq_dict['required_columns'] = const.RAW_FILE_REQUIRED_COLS_WITHOUT_SAMPLE_METADATA
        raw_mq_dict["df"] = input_df
        cdv = CDV(raw_mq_dict)
        cdv.validate()
        return cdv.dv.corrected_df, cdv.dv.logs
    except Exception as e:
        logs = {"errors": [e.message], "warnings": {"action": [],
                                                    "message": []
                                                    }
                }
        return pd.DataFrame(), logs


def data_validation_metadata_df(path):
    """do datavalidtaion for metadata_mq_df and returns instance of
    DATA VALIDATION class.

    It takes df of metadata_mq file, creates an instance of DataValidation
    using this df. It then does validation related to file and returns
    the report_df.

    Args:
        df: metadata_mq_file df

    Returns:
        report_df contains report of error & warning in this df
    """
    # :TODO: update doc when this function will be updated
    try:
        metadata_dict = dict(const.METADATA_MQ_DICT)
        metadata_dict[const.FILE_PATH] = path
        cdv = CDV(metadata_dict)
        cdv.validate()
        return cdv.dv.corrected_df, cdv.dv.logs
    except Exception as e:
        logs = {"errors": [e.message], "warnings": {"action": [],
                                                    "message": []
                                                    }
                }
        return pd.DataFrame(), logs


def data_validation_sample_metadata_df(input_df):
    """do datavalidtaion for metadata_mq_df and returns instance of
    DATA VALIDATION class.

    It takes df of metadata_mq file, creates an instance of DataValidation
    using this df. It then does validation related to file and returns
    the report_df.

    Args:
        df: metadata_mq_file df

    Returns:
        report_df contains report of error & warning in this df
    """
    # :TODO: update doc when this function will be updated
    try:
        sample_metadata_dict = dict(const.SAMPLE_METADATA_DICT)
        sample_metadata_dict["df"] = input_df
        cdv = CDV(sample_metadata_dict)
        cdv.validate()
        return cdv.dv.corrected_df, cdv.dv.logs
    except Exception as e:
        logs = {"errors": [e.message], "warnings": {"action": [],
                                                    "message": []
                                                    }
                }
        return pd.DataFrame(), logs


def find_missing_samples(raw_df, meta_df, file_name):
    """
    Function to check the missing samples in the metadata
    which are present in the metadata file.
    """
    missing_sample_dict = {}
    msgs_list = []
    meta_msg_list = []
    raw_samples_set = set(raw_df[const.SAMPLE_NAME])
    meta_sample_set = set(meta_df[const.SAMPLE_NAME])
    raw_missing_samples = list(raw_samples_set - meta_sample_set)
    meta_missing_samples = list(meta_sample_set - raw_samples_set)
    if len(raw_samples_set) == len(raw_missing_samples):
        error_msg = "No matching samples in the Raw Intensity file and Metadata file"
        return {'error': True, 'msg' : [error_msg]}
    
    for sample in raw_missing_samples:
        index = raw_df[const.SAMPLE_NAME][raw_df[const.SAMPLE_NAME] == sample].index.tolist()[0]
        msgs_list.append("Row Number <b>{}</b> : column <b>{}</b> is <b>not present in {}</b> file.".\
            format(index, const.SAMPLE_NAME, file_name))
    return {'error': False, 'msg': msgs_list}
