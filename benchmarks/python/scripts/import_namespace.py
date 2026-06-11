import sys
for k in list(sys.modules):
    if k == 'os' or k.startswith('os.'):
        del sys.modules[k]

import os
import posix
import numpy