# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
if os.path.exists('version.py'):
    from .version import __version__

from .core import *