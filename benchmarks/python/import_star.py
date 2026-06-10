import sys
import timeit

for k in list(sys.modules):
    if k == 'os' or k.startswith('os.'):
        del sys.modules[k]

from os import *
from posix import *
from numpy import *