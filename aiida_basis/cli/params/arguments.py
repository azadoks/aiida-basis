# -*- coding: utf-8 -*-
"""Reusable arguments for CLI commands."""
from aiida.cmdline.params.arguments import OverridableArgument
from .types import BasisSetParam

__all__ = ('BASIS_SET',)

BASIS_SET = OverridableArgument('basis_set', type=BasisSetParam(sub_classes=('aiida.groups:basis.set',)))
