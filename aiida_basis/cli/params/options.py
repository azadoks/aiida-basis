# -*- coding: utf-8 -*-
"""Reusable options for CLI commands."""
import shutil

import click

from aiida.cmdline.params.options import OverridableOption
from .types import BasisSetTypeParam, BasisTypeParam

__all__ = (
    'VERSION', 'PROTOCOL', 'TRACEBACK', 'BASIS_SET_TYPE', 'ARCHIVE_FORMAT'
)

VERSION = OverridableOption(
    '-v', '--version', type=click.STRING, required=False, help='Select the version of the installed configuration.'
)

PROTOCOL = OverridableOption(
    '-p', '--protocol', type=click.STRING, required=False, help='Select the protocol of the installed configuration.'
)

HARDNESS = OverridableOption(
    '-h', '--hardness', type=click.STRING, required=False, help='Select the hardness of the installed configuration.'
)

TRACEBACK = OverridableOption(
    '-t', '--traceback', is_flag=True, help='Include the stacktrace if an exception is encountered.'
)

BASIS_SET_TYPE = OverridableOption(
    '-T',
    '--basis-set-type',
    type=BasisSetTypeParam(),
    default='basis.set',
    show_default=True,
    help='Choose the type of basis set to create.'
)

BASIS_TYPE = OverridableOption(
    '-B',
    '--basis-type',
    type=BasisTypeParam(),
    default='basis.basis',
    show_default=True,
    help='Choose the type of basis to use.'
)

ARCHIVE_FORMAT = OverridableOption(
    '-F', '--archive-format', type=click.Choice([fmt[0] for fmt in shutil.get_archive_formats()])
)
