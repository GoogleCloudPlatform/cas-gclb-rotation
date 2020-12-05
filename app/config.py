"""
Defines the common config functionality.
"""

from dataclasses import dataclass, fields, is_dataclass
import datetime
from typing import Any, Optional, List, get_args

from googleapiclient import discovery
import yaml


@dataclass
class SimpleResource:
    project: str
    location: str
    name: str

    def isGlobal(self) -> bool:
        return self.location == 'global'


@dataclass
class RotationProfile:
    """Describes the entity to be rotated."""
    lb: SimpleResource
    issuingCa: SimpleResource
    # TODO: consider extracting these fields into a CertificateConfig
    dnsName: str
    lifetimeDays: int
    rotationThreshold: float

    @property
    def lifetime(self) -> datetime.timedelta:
        return datetime.timedelta(self.lifetimeDays)

    def isGlobal(self) -> bool:
        return self.lb.isGlobal()


@dataclass
class AppConfig:
    profiles: List[RotationProfile]


@dataclass
class AppContext:
    config: AppConfig
    computeClient: discovery.Resource
    casClient: discovery.Resource


def _isList(field_type: type, value: Any) -> bool:
    """Checks whether the given field should be treated as a list."""
    isListField = '_name' in vars(
        field_type) and field_type._name == List._name
    isListValue = isinstance(value, list)
    return isListField and isListValue


def _isSubMessage(field_type: type, value: Any) -> bool:
    """Checks whether the given field should be treated as a submessage."""
    isDataClassField = is_dataclass(field_type)
    isDictValue = isinstance(value, dict)
    return isDataClassField and isDictValue


def _parseDataClass(raw_values: dict, cls: type) -> Any:
    """Recursively populates a new dataclass of type 'cls' from the given dictionary of values."""
    values = {}
    for field in fields(cls):
        # Add a stub value for any missing fields. This avoids crashing on
        # sparse configs, but effectively makes all fields optional.
        if not field.name in raw_values:
            values[field.name] = None
            continue

        value = raw_values[field.name]

        if _isList(field.type, value):
            # Recursively expand all list items.
            item_type = get_args(field.type)[0]
            value = [_parseDataClass(item, item_type) for item in value]
        elif _isSubMessage(field.type, value):
            # Recursively expand all submessages.
            value = _parseDataClass(value, field.type)

        values[field.name] = value

    return cls(**values)


def loadConfig(filename: str = 'config.yaml') -> AppConfig:
    """Loads an AppConfig from the given YAML file."""
    with open(filename) as file:
        config_dict = yaml.safe_load(file)
    return _parseDataClass(config_dict, AppConfig)
