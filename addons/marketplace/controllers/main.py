# -*- coding: utf-8 -*-
"""Legacy controller entrypoint.

This module used to contain all controllers in a single file.
It now only imports the modularized controllers so that the addon's
`controllers/__init__.py` can keep importing `main` without breaking.
"""

from . import auth  # noqa: F401
from . import cart  # noqa: F401
from . import live  # noqa: F401
from . import order  # noqa: F401
from . import product  # noqa: F401
from . import vendor  # noqa: F401