"""Inspection and metadata extraction modules for SoLEXS FITS products."""

from solar_flare.inspection.fits_inspect import (
    list_hdus,
    read_header_dict,
    describe_columns,
    summarise_time_columns,
    summarise_numeric_columns,
    InspectionError,
)
from solar_flare.inspection.time_systems import extract_time_system_metadata
from solar_flare.inspection.inventory import build_inventory

__all__ = [
    "list_hdus",
    "read_header_dict",
    "describe_columns",
    "summarise_time_columns",
    "summarise_numeric_columns",
    "InspectionError",
    "extract_time_system_metadata",
    "build_inventory",
]
