# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# (C) 2016 VRT Systems
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

import warnings

# First verify if pint is available
PINT_AVAILABLE = False
try:
    from pint import UnitRegistry

    PINT_AVAILABLE = UnitRegistry is not None
    from .pintutil import define_haystack_units

    unit_reg = define_haystack_units()
except ImportError:  # pragma: no cover
    # For setup.py to interrogate the version information.  This should *NOT*
    # get executed in production, and if it did, things wouldn't work anyway.
    unit_reg = {'Quantity': None}

try:
    import pytz  # Hack for the link between setup.py and __init__
    from .grid import Grid
    from .dumper import dump, dump_scalar
    from .parser import parse, parse_scalar, MODE_JSON, MODE_ZINC, MODE_CSV, suffix_to_mode, mode_to_suffix
    from .grid_filter import parse_filter, parse_date_format
    from .metadata import MetadataObject
    from .datatypes import Quantity, Coordinate, Uri, Bin, MARKER, NA, \
        REMOVE, Ref, XStr, use_pint
    from .version import Version, VER_2_0, VER_3_0, LATEST_VER

    __all__ = ['Grid', 'dump', 'parse', 'dump_scalar', 'parse_scalar', 'parse_filter',
               'MetadataObject', 'unit_reg', 'zoneinfo',
               'Coordinate', 'Uri', 'Bin', 'XStr', 'Quantity', 'MARKER', 'NA', 'REMOVE', 'Ref',
               'MODE_JSON', 'MODE_ZINC', 'MODE_CSV', 'suffix_to_mode', 'mode_to_suffix',
               'parse_date_format', 'use_pint',
               'VER_2_0', 'VER_3_0', 'LATEST_VER', 'Version', '__version__']
except ModuleNotFoundError as import_error:  # pragma: no cover
    # For setup.py to interrogate the version information.  This should *NOT*
    # get executed in production, and if it did, things wouldn't work anyway.
    pass
except ImportError as import_error:  # pragma: no cover
    # For setup.py to interrogate the version information.  This should *NOT*
    # get executed in production, and if it did, things wouldn't work anyway.
    warnings.warn(
        'Failed to import libraries: %s, dependencies may be missing' % import_error)
    raise

__author__ = 'VRT Systems'
__copyright__ = 'Copyright 2016, VRT Systems'
__credits__ = ['VRT Systems', 'Philippe PRADOS']
__license__ = 'BSD'
__version__ = '1.3.2a'
__maintainer__ = 'VRT Systems'
__email__ = 'support@vrt.com.au'