# csv
from utils import *


def get_csv_filename():
    return max(all_files_under("/share/aps/csrc/data/"))
