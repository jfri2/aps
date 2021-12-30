# utils
import os


def write_to_file(filepath, data):
    file = open(filepath, "w")
    file.write(data)
    file.close()


def read_from_file(filepath):
    file = open(filepath, "r")
    text = file.read()
    file.close()
    return text


def all_files_under(path):
    for cur_path, _, filenames in os.walk(path):
        for filename in filenames:
            yield os.path.join(cur_path, filename)
