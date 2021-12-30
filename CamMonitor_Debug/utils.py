# utils
import os

def writeToFile(filepath, str):
    f = open(filepath, "w")
    f.write(str)
    f.close()


def readFromFile(filepath):
    f = open(filepath, "r")
    text = f.read()
    f.close()
    return text
    
def all_files_under(path):
    for cur_path, _, filenames in os.walk(path):
        for filename in filenames:
            yield os.path.join(cur_path, filename)    