# -*- coding: utf-8 -*-
# Zinc dumping and parsing module
# See the accompanying LICENSE file.
# (C) 2016 VRT Systems
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:

# Functional test with different complexes scenario
# and with different providers with real database.

import copy
import datetime
from typing import cast

import psycopg2
import pytz
from nose import SkipTest
from pymongo.errors import ServerSelectionTimeoutError

from shaystack import Ref, Grid, VER_3_0
from shaystack.providers import get_provider
from shaystack.providers.db_haystack_interface import DBHaystackInterface

FAKE_NOW = datetime.datetime(2020, 10, 1, 0, 0, 0, 0, tzinfo=pytz.UTC)

_db_providers = [
    ["shaystack.providers.sql",
     "sqlite3:///test.db:#haystack", True],
    ["shaystack.providers.sql",
     "postgresql://postgres:password@localhost:5432/postgres?connect_timeout=100#haystack", True],
    ["shaystack.providers.mongodb",
     "mongodb://localhost/haystackdb?serverSelectionTimeoutMS=100#haystack", True],
]


def _wrapper(function, provider, db, idx):
    try:
        function(provider, db)
    except ServerSelectionTimeoutError as ex:
        _db_providers[idx][2] = False
        raise SkipTest("Mongo db not started") from ex
    except psycopg2.OperationalError as ex:
        _db_providers[idx][2] = False
        raise SkipTest("Postgres db not started") from ex


def _for_each_provider(function):
    for idx, (provider, db, status) in enumerate(_db_providers):
        if status:
            yield _wrapper, function, provider, db, idx


def _get_grids():
    sample_grid = Grid(version=VER_3_0, columns=["id", "col", "dis"])
    sample_grid.append({"id": Ref("id1"), "col": 1, "dis": "Dis 1"})
    sample_grid.append({"id": Ref("id2"), "col": 2, "dis": "Dis 2"})
    version_1 = datetime.datetime(2020, 10, 1, 0, 0, 1, 0, tzinfo=pytz.UTC)
    version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
    version_3 = datetime.datetime(2020, 10, 1, 0, 0, 3, 0, tzinfo=pytz.UTC)
    g1 = copy.deepcopy(sample_grid)
    g1.metadata = {"v": "1"}
    g2 = copy.deepcopy(sample_grid)
    g2.metadata = {"v": "2"}
    g2[0]["col"] += 2
    g2[1]["col"] += 2
    g3 = copy.deepcopy(sample_grid)
    g3.metadata = {"v": "last"}
    g3[0]["col"] += 4
    g3[1]["col"] += 4

    return [
        (g1, version_1),
        (g2, version_2),
        (g3, version_3),
    ]


def _populate_db(provider: DBHaystackInterface) -> None:
    provider.purge_db()
    for grid, version in _get_grids():
        provider.update_grid(grid, version, "", version)


# @patch.object(ping.Provider, 'point_write_read')
def _test_update_grid_in_db(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db},
                                                use_cache=False)) as provider:
        provider.purge_db()
        provider.create_db()
        left = Grid(columns={"id": {}, "a": {}, "b": {}, "c": {}})
        left.append({"id": Ref("id1"), "a": 1, "b": 2})
        left.append({"id": Ref("id2"), "a": 2, "b": 2})
        left.append({"id": Ref("id3"), "a": 3, "b": 2})
        left.append({"id": Ref("id4"), "a": 4, "b": 2})
        left.append({"id": Ref("old_id"), "a": 1, "b": 2})
        right = Grid(columns={"id": {}, "a": {}, "b": {}, "c": {}})
        right.append({"id": Ref("id1"), "a": 3, "c": 5})
        provider.update_grid(left, version=None, customer_id="customer", now=FAKE_NOW)
        NEXT_FAKE = FAKE_NOW + datetime.timedelta(minutes=1)
        provider.update_grid(right - left, version=None, customer_id="customer", now=NEXT_FAKE)
        grid = provider.read_grid("customer", None)
        assert len(grid) == 1
        grid = provider.read_grid("customer", FAKE_NOW)
        assert len(grid) == 5


def test_update_grid_in_db():
    yield from _for_each_provider(_test_update_grid_in_db)


def _test_ops(provider_name: str, db: str):
    envs = {'HAYSTACK_DB': db}
    with get_provider(provider_name, envs) as provider:
        result = provider.ops()
        assert len(result) == 5


def test_ops():
    yield from _for_each_provider(_test_ops)


def _test_read_last_without_filter(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db})) as provider:
        _populate_db(provider)
        result = provider.read(0, None, None, None, None)
        assert result.metadata["v"] == "last"
        assert len(result) == 2
        assert result[Ref("id1")] == {"id": Ref('id1'), 'col': 5, 'dis': 'Dis 1'}
        assert result[Ref("id2")] == {"id": Ref('id2'), 'col': 6, 'dis': 'Dis 2'}


def test_read_last_without_filter():
    yield from _for_each_provider(_test_read_last_without_filter)


def _test_read_version_without_filter(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db})) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, None, date_version=version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 2
        assert result[Ref("id1")] == {"id": Ref('id1'), 'col': 3, 'dis': 'Dis 1'}
        assert result[Ref("id2")] == {"id": Ref('id2'), 'col': 4, 'dis': 'Dis 2'}


def test_read_version_without_filter():
    yield from _for_each_provider(_test_read_version_without_filter)


def _test_read_version_with_filter(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db})) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, None, "id==@id1", version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[Ref("id1")] == {"id": Ref('id1'), 'col': 3, 'dis': 'Dis 1'}


def test_read_version_with_filter():
    yield from _for_each_provider(_test_read_version_with_filter)


def _test_read_version_with_filter_and_select(provider_name: str, db: str):
    # caplog.set_level(logging.DEBUG)
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db})) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, "id,other", None, "id==@id1", version_2)
        assert len(result) == 1
        assert len(result.column) == 2
        assert "id" in result.column
        assert "other" in result.column


def test_read_version_with_filter_and_select():
    yield from _for_each_provider(_test_read_version_with_filter_and_select)


def _test_read_version_with_ids(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db})) as provider:
        _populate_db(provider)
        version_2 = datetime.datetime(2020, 10, 1, 0, 0, 2, 0, tzinfo=pytz.UTC)
        result = provider.read(0, None, [Ref("id1")], None, version_2)
        assert result.metadata["v"] == "2"
        assert len(result) == 1
        assert result[Ref("id1")] == {"id": Ref('id1'), 'col': 3, 'dis': 'Dis 1'}


def test_read_version_with_ids():
    yield from _for_each_provider(_test_read_version_with_ids)


def _test_version(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db})) as provider:
        _populate_db(provider)
        versions = provider.versions()
        assert len(versions) == 3


def test_version():
    yield from _for_each_provider(_test_version)


def _test_values_for_tag_id(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db})) as provider:
        _populate_db(provider)
        values = provider.values_for_tag("id")
        assert len(values) > 1


def test_values_for_tag_id():
    yield from _for_each_provider(_test_values_for_tag_id)


def _test_values_for_tag_col(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db})) as provider:
        _populate_db(provider)
        values = provider.values_for_tag("col")
        assert len(values) > 1


def test_values_for_tag_col():
    yield from _for_each_provider(_test_values_for_tag_col)


def _test_values_for_tag_dis(provider_name: str, db: str):
    with cast(DBHaystackInterface, get_provider(provider_name,
                                                {'HAYSTACK_DB': db})) as provider:
        _populate_db(provider)
        values = provider.values_for_tag("dis")
        assert values == ['Dis 1', 'Dis 2']


def test_values_for_tag_dis():
    yield from _for_each_provider(_test_values_for_tag_dis)