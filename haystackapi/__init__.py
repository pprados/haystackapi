# -*- coding: utf-8 -*-
# Haystack module
# See the accompanying LICENSE Apache V2.0 file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Implementation of Haystack project https://www.project-haystack.org/
Propose API :
- to read or write Haystack file (Zinc, JSon, CSV)
- to manipulate ontology in memory (Grid class)
- to implement REST API (https://www.project-haystack.org/doc/Rest)
- to implement GraphQL API

With some sample provider:
- Import ontology on S3 bucket
- Import ontology on SQLite or Postgres
- and expose the data via Flask or AWS Lambda
"""
from .datatypes import Quantity, Coordinate, Uri, Bin, MARKER, NA, \
    REMOVE, Ref, XStr
from .dumper import dump, dump_scalar
from .grid import Grid
from .grid_filter import parse_filter, parse_hs_datetime_format
from .metadata import MetadataObject
from .ops import *
from .parser import parse, parse_scalar, MODE_JSON, MODE_ZINC, MODE_CSV, \
    suffix_to_mode, mode_to_suffix
from .pintutil import unit_reg
from .providers import HaystackInterface
from .version import Version, VER_2_0, VER_3_0, LATEST_VER

__all__ = ['Grid', 'dump', 'parse', 'dump_scalar', 'parse_scalar', 'parse_filter',
           'MetadataObject', 'unit_reg', 'zoneinfo',
           'Coordinate', 'Uri', 'Bin', 'XStr', 'Quantity', 'MARKER', 'NA', 'REMOVE', 'Ref',
           'MODE_JSON', 'MODE_ZINC', 'MODE_CSV', 'suffix_to_mode', 'mode_to_suffix',
           'parse_hs_datetime_format',
           'VER_2_0', 'VER_3_0', 'LATEST_VER', 'Version', '__version__',

           "HaystackInterface",
           "about",
           "ops",
           "formats",
           "read",
           "nav",
           "watch_sub",
           "watch_unsub",
           "watch_poll",
           "point_write",
           "his_read",
           "his_write",
           "invoke_action",
           ]

__pdoc__ = {
    "csvdumper": False,
    "csvparser": False,
    "datatypes": False,
    "dumper": False,
    "filter_ast": False,
    "grid": False,
    "grid_diff": False,
    "grid_filter": False,
    "jsondumper": False,
    "jsonparser": False,
    "metadata": False,
    "ops": False,
    "parser": False,
    "pintutil": False,
    "sortabledict": False,
    "version": False,
    "zincdumper": False,
    "zincparser": False,
    "zoneinfo": False,
}
__author__ = 'Ph. Prados, VRT Systems'
__copyright__ = 'Copyright 2016-2020, Ph. Prados & VRT System'
__credits__ = ['Philippe PRADOS',
               'VRT Systems',
               'Engie digital'
               'Christian Tremblay',
               'SamuelToh',
               'Stuart Longland',
               'joyfun'
               ]
__license__ = 'BSD'
__version__ = '0.1'
__maintainer__ = 'Philippe PRADOS'
__email__ = 'haystackapi@prados.fr'
