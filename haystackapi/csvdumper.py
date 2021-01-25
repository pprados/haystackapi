# -*- coding: utf-8 -*-
# Grid CSV dumper
# See the accompanying LICENSE Apache V2.0 file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Save a `Grid` in CSV file, conform with the specification describe
here (https://www.project-haystack.org/doc/Csv)
"""
from __future__ import unicode_literals

import datetime
import functools
import re
from typing import AnyStr, List, Dict, Any, Match

from .datatypes import Quantity, Coordinate, Ref, Bin, Uri, \
    MARKER, NA, REMOVE, STR_SUB, XStr
from .grid import Grid
from .sortabledict import SortableDict
from .version import LATEST_VER, VER_3_0, Version
from .zincdumper import dump_grid as zinc_dump_grid
from .zincdumper import dump_scalar as zinc_dump_scalar

URI_META = re.compile(r'([\\`\u0080-\uffff])')
STR_META = re.compile(r'([\\"$\u0080-\uffff])')

CSV_SUB = [
    ('\\"', '""'),
    ('\\\\', '\\'),
    ('\\u2713', '\u2713'),
]


def str_sub(match: Match) -> AnyStr:
    """
    Args:
        match (Match):
    """
    char = match.group(0)
    order = ord(char)
    if order >= 0x0080:
        # Unicode
        return '\\u%04x' % order
    if char in '\\"$':
        return '\\%s' % char
    return char


def str_csv_escape(str_value: str) -> AnyStr:
    """
    Args:
        str_value (str):
    """
    str_value = STR_META.sub(str_sub, str_value)
    for orig, esc in CSV_SUB:
        str_value = str_value.replace(orig, esc)
    return str_value


def uri_sub(match: Match) -> AnyStr:
    """
    Args:
        match (Match):
    """
    char = match.group(0)
    order = ord(char)
    if order >= 0x80:
        # Unicode
        return '\\u%04x' % order
    if char in '\\`':
        return '\\%s' % char
    return char


def dump_grid(grid: Grid) -> AnyStr:
    """Dump a single grid to its CSV representation.

    Args:
        grid (Grid):
    """

    # Use list and join
    csv_result = []
    dump_columns(csv_result, grid.column)
    dump_rows(csv_result, grid)
    return ''.join(csv_result)


def dump_columns(csv_result: List[str], cols: SortableDict) -> None:
    """
    Args:
        csv_result:
        cols (SortableDict):
    """
    _dump = functools.partial(dump_column)
    csv_result.extend(map(_dump, cols.keys()))
    # Remove last comma
    if csv_result:
        csv_result[-1] = csv_result[-1][:-1]
    csv_result.append('\n')


def dump_column(col: str) -> str:
    """
    Args:
        col (str):
    """
    return dump_id(col) + ","


def dump_rows(csv_result: List[str], grid: Grid) -> None:
    """
    Args:
        csv_result:
        grid (Grid):
    """
    list(map(functools.partial(dump_row, csv_result, grid), grid))


def dump_row(csv_result: List[str], grid: Grid, row: Dict[str, Any]) -> None:
    """
    Args:
        csv_result:
        grid (Grid):
        row:
    """
    row_in_csv = [dump_scalar(row.get(c), version=grid.version) + "," for c in grid.column.keys()]
    row_in_csv[-1] = row_in_csv[-1][:-1] + '\n'
    if len(row_in_csv) == 1 and row_in_csv[0] == '\n':
        row_in_csv[0] = ",\n"
    csv_result.extend(row_in_csv)


def dump_id(id_str: str) -> str:
    """
    Args:
        id_str (str):
    """
    return id_str


def dump_str(str_value: str) -> str:
    """
    Args:
        str_value (str):
    """
    return '"' + str_csv_escape(str_value) + '"'


def dump_uri(uri_value: Uri) -> str:
    # Replace special characters.
    """
    Args:
        uri_value (Uri):
    """
    uri_value = URI_META.sub(uri_sub, str(uri_value))
    # Replace other escapes.
    for orig, esc in STR_SUB:
        uri_value = uri_value.replace(orig, esc)
    return '`%s`' % uri_value


def dump_bin(bin_value: Bin) -> str:
    """
    Args:
        bin_value (Bin):
    """
    return 'Bin(%s)' % bin_value


def dump_xstr(xstr_value: XStr) -> str:
    """
    Args:
        xstr_value (XStr):
    """
    return '"' + str_csv_escape(str(xstr_value)) + '"'


def dump_quantity(quantity: Quantity) -> str:
    """
    Args:
        quantity (Quantity):
    """
    if (quantity.unit is None) or (quantity.unit == ''):
        return dump_decimal(quantity.m)
    return '%s%s' % (dump_decimal(quantity.m),
                     quantity.unit)


def dump_decimal(decimal: float) -> str:
    """
    Args:
        decimal (float):
    """
    return str(decimal)


def dump_bool(bool_value: bool) -> str:
    """
    Args:
        bool_value (bool):
    """
    return 'true' if bool(bool_value) else 'false'


def dump_coord(coordinate: Coordinate) -> str:
    """
    Args:
        coordinate (Coordinate):
    """
    return '"' + zinc_dump_scalar(coordinate) + '"'


def dump_ref(ref: Ref) -> str:
    """
    Args:
        ref (Ref):
    """
    if ref.has_value:
        str_ref = '@%s %s' % (ref.name, ref.value)
        if '"' in str_ref or ',' in str_ref:
            str_ref = '"' + str_ref + '"'
        return str_ref
    return '@%s' % ref.name


def dump_date(a_date: datetime.date) -> str:
    """
    Args:
        a_date (datetime.date):
    """
    return a_date.isoformat()


def dump_time(time: datetime.time) -> str:
    """
    Args:
        time (datetime.time):
    """
    return time.isoformat()


def dump_date_time(date_time: datetime.datetime) -> str:
    # tz_name = timezone_name(date_time)
    # return '%s %s' % (date_time.isoformat(), tz_name)
    """
    Args:
        date_time (datetime.datetime):
    """
    return '%s' % (date_time.isoformat())  # Note: Excel can not parse the date time with tz_name


def dump_scalar(scalar: Any, version: Version = LATEST_VER) -> str:
    """
    Args:
        scalar (Any):
        version (Version):
    """
    if scalar is None:
        return ''
    if scalar is NA:
        if version < VER_3_0:
            raise ValueError('Project Haystack version %s '
                             'does not support NA'
                             % version)
        return 'NA'
    if scalar is MARKER:
        return '\u2713'
    if scalar is REMOVE:
        return 'R'
    if isinstance(scalar, bool):
        return dump_bool(scalar)
    if isinstance(scalar, Ref):
        return dump_ref(scalar)
    if isinstance(scalar, Bin):
        return dump_bin(scalar)
    if isinstance(scalar, XStr):
        return dump_xstr(scalar)
    if isinstance(scalar, Uri):
        return dump_uri(scalar)
    if isinstance(scalar, str):
        return dump_str(scalar)
    if isinstance(scalar, datetime.datetime):
        return dump_date_time(scalar)
    if isinstance(scalar, datetime.time):
        return dump_time(scalar)
    if isinstance(scalar, datetime.date):
        return dump_date(scalar)
    if isinstance(scalar, Coordinate):
        return dump_coord(scalar)
    if isinstance(scalar, Quantity):
        return dump_quantity(scalar)
    if isinstance(scalar, (float, int)):
        return dump_decimal(scalar)
    if isinstance(scalar, list):
        return '"' + str_csv_escape(zinc_dump_scalar(scalar, version=version)) + '"'
    if isinstance(scalar, dict):
        return '"' + str_csv_escape(zinc_dump_scalar(scalar, version=version)) + '"'
    if isinstance(scalar, Grid):
        return '"' + str_csv_escape("<<" + zinc_dump_grid(scalar) + ">>") + '"'
    return '"' + str_csv_escape(zinc_dump_scalar(scalar)) + '"'
