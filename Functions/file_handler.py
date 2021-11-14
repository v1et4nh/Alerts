import os
import json
import pickle


def save_pickle(save_obj, str_file_path):
    try:
        with open(str_file_path, 'wb') as f:
            pickle.dump(save_obj, f, pickle.HIGHEST_PROTOCOL)
        return 'SUCCESS'
    except:
        return 'ERROR'


def load_pickle(str_file_path):
    if os.path.exists(str_file_path):
        with open(str_file_path, 'rb') as f:
            tmp_file = pickle.load(f)
            return tmp_file
    else:
        dict_tmp = {'Error': 'File does not exist'}
        return dict_tmp


def save_json(save_obj, str_file_path):
    try:
        with open(str_file_path, 'w') as f:
            json.dump(save_obj, f, indent=4)
        return 'SUCCESS'
    except:
        return 'ERROR'


def load_json(str_file_path):
    if os.path.exists(str_file_path):
        with open(str_file_path, 'r') as f:
            tmp_file = json.load(f)
            return tmp_file
    else:
        dict_tmp = {'Error': 'File does not exist'}
        return dict_tmp
