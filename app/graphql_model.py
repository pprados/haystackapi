# -*- coding: utf-8 -*-
# Haystack API Provider module
# See the accompanying LICENSE Apache V2.0 file.
# (C) 2021 Engie Digital
#
# vim: set ts=4 sts=4 et tw=78 sw=4 si:
"""
Model to inject a another graphene model, to manage the haystack layer.
See the blueprint_graphql to see how to integrate this part of global GraphQL model.
"""
import json
import logging
from datetime import datetime, date, time
from typing import Optional, List, Any, Dict, Union, Type

import graphene
from graphql import ResolveInfo
from graphql.language.ast import StringValue, IntValue, FloatValue, BooleanValue, EnumValue

import haystackapi
from haystackapi import Ref, Uri, Coordinate, parse_hs_datetime_format, Grid
from haystackapi.grid_filter import parse_hs_time_format, parse_hs_date_format
from haystackapi.providers.haystack_interface import get_singleton_provider, parse_date_range
from haystackapi.zincdumper import dump_hs_date_time, dump_hs_time, dump_hs_date

BOTO3_AVAILABLE = False
try:
    # Check the presence of boto3
    import boto3  # pylint: disable=unused-import

    BOTO3_AVAILABLE = True
except ImportError:
    pass

log = logging.getLogger("haystackapi")


class HSScalar(graphene.Scalar):
    """Haystack Scalar"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Update name for AWS"""
        name = "AWSJSON" if BOTO3_AVAILABLE else "JSONString"

    @staticmethod
    def serialize(hs_scalar: Any) -> Any:
        """
        Args:
            hs_scalar (Any):
        """
        return json.loads(haystackapi.dump_scalar(hs_scalar,
                                                  haystackapi.MODE_JSON,
                                                  version=haystackapi.VER_3_0))

    @staticmethod
    def parse_literal(node: Union[IntValue, FloatValue, StringValue, BooleanValue, EnumValue]) -> Any:
        """
        Args:
            node:
        """
        if isinstance(node, StringValue):
            str_value = node.value
            if len(str_value) >= 2 and str_value[1] == ':':
                return haystackapi.parse_scalar(node.value,
                                                haystackapi.MODE_JSON)
        return node.value

    @staticmethod
    def parse_value(value: Any) -> Any:
        """
        Args:
            value (Any):
        """
        return haystackapi.parse_scalar(value, haystackapi.MODE_JSON)


class HSDateTime(graphene.String):
    """Haystack compatible date format."""

    class Meta:  # pylint: disable=missing-class-docstring
        name = "AWSDateTime" if BOTO3_AVAILABLE else "DateTime"

    @staticmethod
    def serialize(date_time: datetime) -> str:
        # Call to convert python object to graphql result
        """
        Args:
            date_time (datetime):
        """
        assert isinstance(date_time, datetime), \
            'Received not compatible datetime "{}"'.format(repr(date_time))
        return dump_hs_date_time(date_time)

    @staticmethod
    def parse_literal(node: StringValue) -> datetime:  # pylint: disable=arguments-differ
        # Call to convert graphql parameter to python object
        """
        Args:
            node (StringValue):
        """
        assert isinstance(node, StringValue), \
            'Received not compatible datetime "{}"'.format(repr(node))
        return HSDateTime.parse_value(node.value)

    @staticmethod
    def parse_value(value: Union[datetime, str]) -> datetime:
        # Call to convert graphql variable to python object
        """
        Args:
            value:
        """
        if isinstance(value, datetime):
            return value
        return parse_hs_datetime_format(value)


class HSDate(graphene.String):
    """Haystack date for GraphQL"""

    class Meta:  # pylint: disable=missing-class-docstring
        name = "AWSDate" if BOTO3_AVAILABLE else "Date"

    @staticmethod
    def serialize(a_date: date) -> str:
        """
        Args:
            a_date (date):
        """
        assert isinstance(a_date, date), 'Received not compatible date "{}"'.format(repr(a_date))
        return dump_hs_date(a_date)

    @staticmethod
    def parse_literal(node: StringValue) -> date:  # pylint: disable=arguments-differ
        """
        Args:
            node (StringValue):
        """
        assert isinstance(node, StringValue), 'Received not compatible date "{}"'.format(repr(node))
        return HSDate.parse_value(node.value)

    @staticmethod
    def parse_value(value: Union[date, str]) -> date:
        """
        Args:
            value:
        """
        if isinstance(value, date):
            return value
        return parse_hs_date_format(value)


class HSTime(graphene.String):
    """Haystack time for GraphQL"""

    class Meta:  # pylint: disable=missing-class-docstring
        name = "AWSTime" if BOTO3_AVAILABLE else "Time"

    @staticmethod
    def serialize(a_time: time) -> str:
        """
        Args:
            a_time (time):
        """
        assert isinstance(a_time, time), 'Received not compatible time "{}"'.format(repr(a_time))
        return dump_hs_time(a_time)

    @staticmethod
    def parse_literal(node: StringValue) -> time:  # pylint: disable=arguments-differ
        """
        Args:
            node (StringValue):
        """
        assert isinstance(node, StringValue), 'Received not compatible time "{}"'.format(repr(node))
        return HSTime.parse_value(node.value)

    @staticmethod
    def parse_value(value: Union[time, str]) -> time:
        """
        Args:
            value:
        """
        if isinstance(value, time):
            return value
        return parse_hs_time_format(value)


class HSUri(graphene.String):
    """Haystack URI for GraphQL"""

    class Meta:  # pylint: disable=too-few-public-methods,missing-class-docstring
        name = "AWSURL" if BOTO3_AVAILABLE else "HSURL"

    @staticmethod
    def serialize(a_uri: Uri) -> str:
        """
        Args:
            a_uri (Uri):
        """
        assert isinstance(a_uri, Uri), 'Received not compatible uri "{}"'.format(repr(a_uri))
        return str(a_uri)

    @staticmethod
    def parse_literal(node: StringValue) -> Uri:  # pylint: disable=arguments-differ
        """
        Args:
            node (StringValue):
        """
        return HSUri.parse_value(node.value)

    @staticmethod
    def parse_value(value: str) -> Uri:
        """
        Args:
            value (str):
        """
        if value.startswith("u:"):
            return haystackapi.parse_scalar(value, haystackapi.MODE_JSON, version=haystackapi.VER_3_0)
        return Uri(value)


class HSCoordinate(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """Haystack coordinate for GraphQL"""
    latitude = graphene.Float(required=True,
                              description="Latitude")
    longitude = graphene.Float(required=True,
                               description="Longitude")


class HSAbout(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """Result of 'about' haystack operation"""
    haystackVersion = graphene.String(required=True,
                                      description="Haystack version implemented")
    tz = graphene.String(required=True,
                         description="Server time zone")
    serverName = graphene.String(required=True,
                                 description="Server name")
    serverTime = graphene.Field(graphene.NonNull(HSDateTime),
                                description="Server current time")
    serverBootTime = graphene.Field(graphene.NonNull(HSDateTime),
                                    description="Server boot time")
    productName = graphene.String(required=True,
                                  description="Server Product name")
    productUri = graphene.Field(graphene.NonNull(HSUri),
                                description="Server URL")
    productVersion = graphene.String(required=True,
                                     description="Product version")
    moduleName = graphene.String(required=True,
                                 description="Module name")
    moduleVersion = graphene.String(required=True,
                                    description="Module version")


class HSOps(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """Result of 'ops' haystack operation"""

    name = graphene.String(description="Name of operation (see https://project-haystack.org/doc/Ops)")
    summary = graphene.String(description="Summary of operation")


class HSTS(graphene.ObjectType):  # pylint: disable=too-few-public-methods,too-many-instance-attributes
    """Result of 'hisRead' haystack operation"""
    ts = graphene.Field(HSDateTime, description="Date time of event")
    val = graphene.Field(HSScalar, description="Haystack JSON format of value")

    int = graphene.Int(required=False, description="Integer version of the value")
    float = graphene.Float(required=False, description="Float version of the value")
    str = graphene.String(required=False, description="Float version of the value")
    bool = graphene.Boolean(required=False, description="Boolean version of the value")
    uri = graphene.String(required=False, description="URI version of the value")
    ref = graphene.String(required=False, description="Reference version of the value")
    date = HSDate(required=False, description="Date version of the value")
    time = HSTime(required=False, description="Time version of the value")
    datetime = HSDateTime(required=False, description="Date time version of the value")
    coord = graphene.Field(HSCoordinate,
                           description="Geographic Coordinate")


class HSPointWrite(graphene.ObjectType):  # pylint: disable=too-few-public-methods
    """Result of 'pointWrite' haystack operation"""
    level = graphene.Int(description="Current level")
    levelDis = graphene.String(description="Description of level")
    val = graphene.Field(HSScalar, description="Value")
    who = graphene.String(description="Who has updated the value")


# PPR: see the batch approach
class ReadHaystack(graphene.ObjectType):
    """Ontology conform with Haystack project"""

    class Meta:  # pylint: disable=too-few-public-methods,missing-class-docstring
        name = "Haystack"

    about = graphene.NonNull(HSAbout,
                             description="Versions of api")

    ops = graphene.NonNull(graphene.List(
        graphene.NonNull(HSOps)),
        description="List of operation implemented")

    tag_values = graphene.NonNull(graphene.List(graphene.NonNull(graphene.String),
                                                ),
                                  tag=graphene.String(required=True,
                                                      description="Tag name"),
                                  version=HSDateTime(description="Date of the version "
                                                                 "or nothing for the last version"),
                                  description="All values for a specific tag")

    versions = graphene.NonNull(graphene.List(graphene.NonNull(HSDateTime)),
                                description="All versions of data")

    entities = graphene.List(
        graphene.NonNull(HSScalar),
        ids=graphene.List(graphene.ID,
                          description="List of ids to return (if set, ignore filter and limit)"),
        select=graphene.String(default_value='*',
                               description="List of tags to return"),
        limit=graphene.Int(default_value=0,
                           description="Maximum number of items to return"),
        filter=graphene.String(default_value='',
                               description="Filter or item (see https://project-haystack.org/doc/Filters"),
        version=HSDateTime(description="Date of the version or nothing for the last version"),
        description="Selected entities of ontology"
    )

    histories = graphene.List(graphene.NonNull(graphene.List(graphene.NonNull(HSTS))),
                              ids=graphene.List(graphene.ID,
                                                description="List of ids to return"),
                              dates_range=graphene.String(description="today, yesterday, "
                                                                      "{date}, {date},{date}, "
                                                                      "{datetime}, "
                                                                      "{datetime},{datetime}"
                                                          ),
                              version=HSDateTime(
                                  description="Date of the version or nothing for the last version"),
                              description="Selected time series")

    point_write = graphene.List(
        graphene.NonNull(HSPointWrite),
        id=graphene.ID(required=True,
                       description="Id to read (accept @xxx, r:xxx or xxx)"),
        version=HSDateTime(description="Date of the version or nothing for the last version"),
        description="Point write values"
    )

    @staticmethod
    def resolve_about(parent: 'ReadHaystack',
                      info: ResolveInfo):
        """
        Args:
            parent:
            info (ResolveInfo):
        """
        log.debug("resolve_about(parent,info)")
        grid = get_singleton_provider().about("http://localhost")
        result = ReadHaystack._conv_entity(HSAbout, grid[0])
        result.serverTime = grid[0]["serverTime"]  # pylint: disable=invalid-name
        result.bootTime = grid[0]["serverBootTime"]  # pylint: disable=invalid-name, attribute-defined-outside-init
        return result

    @staticmethod
    def resolve_ops(parent: 'ReadHaystack',
                    info: ResolveInfo):
        """
        Args:
            parent:
            info (ResolveInfo):
        """
        log.debug("resolve_about(parent,info)")
        grid = get_singleton_provider().ops()
        return ReadHaystack._conv_list_to_object_type(HSOps, grid)

    @staticmethod
    def resolve_tag_values(parent: 'ReadHaystack',
                           info: ResolveInfo,
                           tag: str,
                           version: Optional[HSDateTime] = None):
        """
        Args:
            parent:
            info (ResolveInfo):
            tag (str):
            version:
        """
        log.debug("resolve_values(parent,info,%s)", tag)
        return get_singleton_provider().values_for_tag(tag, version)

    @staticmethod
    def resolve_versions(parent: 'ReadHaystack',
                         info: ResolveInfo):
        """
        Args:
            parent:
            info (ResolveInfo):
        """
        log.debug("resolve_versions(parent,info)")
        return get_singleton_provider().versions()

    @staticmethod
    def resolve_entities(parent: 'ReadHaystack',
                         info: ResolveInfo,
                         ids: Optional[List[str]] = None,
                         select: str = '*',
                         filter: str = '',  # pylint: disable=redefined-builtin
                         limit: int = 0,
                         version: Optional[HSDateTime] = None):
        """
        Args:
            parent:
            info (ResolveInfo):
            ids:
            select (str):
            filter (str):
            limit (int):
            version:
        """
        log.debug(
            "resolve_entities(parent,info,ids=%s, "
            "select=%s, filter=%s, "
            "limit=%s, version=%s)", ids, select, filter, limit, version)
        if ids:
            ids = [Ref(ReadHaystack._filter_id(entity_id)) for entity_id in ids]
        grid = get_singleton_provider().read(limit, select, ids, filter, version)
        return grid

    @staticmethod
    def resolve_histories(parent: 'ReadHaystack',
                          info: ResolveInfo,
                          ids: Optional[List[str]] = None,
                          dates_range: Optional[str] = None,
                          version: Union[str, datetime, None] = None):
        """
        Args:
            parent:
            info (ResolveInfo):
            ids:
            dates_range:
            version:
        """
        if version:
            version = HSDateTime.parse_value(version)
        log.debug("resolve_histories(parent,info,ids=%s, range=%s, version=%s)",
                  ids, dates_range, version)
        provider = get_singleton_provider()
        grid_date_range = parse_date_range(dates_range, provider.get_tz())
        return [ReadHaystack._conv_history(
            provider.his_read(Ref(ReadHaystack._filter_id(entity_id)), grid_date_range, version),
            info
        )
            for entity_id in ids]

    @staticmethod
    def resolve_point_write(parent: 'ReadHaystack',
                            info: ResolveInfo,
                            entity_id: str,
                            version: Union[datetime, str, None] = None):
        """
        Args:
            parent:
            info (ResolveInfo):
            entity_id (str):
            version:
        """
        if version:
            version = HSDateTime.parse_value(version)
        log.debug("resolve_point_write(parent,info, entity_id=%s, version=%s)",
                  entity_id, version)
        ref = Ref(ReadHaystack._filter_id(entity_id))
        grid = get_singleton_provider().point_write_read(ref, version)
        return ReadHaystack._conv_list_to_object_type(HSPointWrite, grid)

    @staticmethod
    def _conv_value(entity: Dict[str, Any],
                    info: ResolveInfo) -> HSTS:
        """
        Args:
            entity:
            info (ResolveInfo):
        """
        selection = info.field_asts[0].selection_set.selections
        cast_value = HSTS()
        value = entity["val"]
        cast_value.ts = entity["ts"]  # pylint: disable=invalid-name
        cast_value.val = value
        for sel in selection:
            name = sel.name.value
            if name in ['ts', 'val']:
                continue

            if name == 'int' and isinstance(value, (int, float)):
                cast_value.int = int(value)
            elif name == 'float' and isinstance(value, float):
                cast_value.float = value
            elif name == 'str':
                cast_value.str = str(value)
            elif name == 'bool':
                cast_value.bool = bool(value)
            elif name == 'uri' and isinstance(value, Uri):
                cast_value.uri = str(value)
            elif name == 'ref' and isinstance(value, Ref):
                cast_value.ref = '@' + value.name
            elif name == 'date' and isinstance(value, date):
                cast_value.date = value
            elif name == 'date' and isinstance(value, datetime):
                cast_value.date = value.date()
            elif name == 'time' and isinstance(value, time):
                cast_value.time = value
            elif name == 'time' and isinstance(value, datetime):
                cast_value.time = value.time()
            elif name == 'datetime' and isinstance(value, datetime):
                cast_value.datetime = value
            elif name == 'coord' and isinstance(value, Coordinate):
                cast_value.coord = HSCoordinate(value.latitude, value.longitude)
        return cast_value

    @staticmethod
    def _conv_history(entities, info: ResolveInfo):
        """
        Args:
            entities:
            info (ResolveInfo):
        """
        return [ReadHaystack._conv_value(entity, info) for entity in entities]

    @staticmethod
    def _filter_id(entity_id: str) -> str:
        """
        Args:
            entity_id (str):
        """
        if entity_id.startswith("r:"):
            return entity_id[2:]
        if entity_id.startswith('@'):
            return entity_id[1:]
        return entity_id

    @staticmethod
    def _conv_entity(target_class: Type, entity: Dict[str, Any]):
        """
        Args:
            target_class (Type):
            entity:
        """
        entity_result = target_class()
        for key, val in entity.items():
            if key in entity:
                entity_result.__setattr__(key, val)
        return entity_result

    @staticmethod
    def _conv_list_to_object_type(target_class: Type, grid: Grid):
        """
        Args:
            target_class (Type):
            grid (Grid):
        """
        result = []
        for row in grid:
            result.append(ReadHaystack._conv_entity(target_class, row))
        return result
