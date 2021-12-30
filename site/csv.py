# csv
from site.utils import all_files_under


def get_csv_filename():
    return max(all_files_under("/share/aps/csrc/data/"))
