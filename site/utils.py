# utils
import os
from collections import deque


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


def get_csv_filename():
    return max(all_files_under("/share/aps/csrc/data/"))
    
class Queue:
    '''
    Thread-safe, memory-efficient, maximally-sized queue supporting queueing and
    dequeueing in worst-case O(1) time.
    '''


    def __init__(self, max_size = 10):
        '''
        Initialize this queue to the empty queue.

        Parameters
        ----------
        max_size : int
            Maximum number of items contained in this queue. Defaults to 10.
        '''

        self._queue = deque(maxlen=max_size)


    def enqueue(self, item):
        '''
        Queues the passed item (i.e., pushes this item onto the tail of this
        queue).

        If this queue is already full, the item at the head of this queue
        is silently removed from this queue *before* the passed item is
        queued.
        '''

        self._queue.append(item)


    def dequeue(self):
        '''
        Dequeues (i.e., removes) the item at the head of this queue *and*
        returns this item.

        Raises
        ----------
        IndexError
            If this queue is empty.
        '''

        return self._queue.pop()