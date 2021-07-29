# -*- coding: utf-8 -*-
"""Subclass of ``BasisSet`` designed to represent an OpenMX configuration."""
import collections
import json
import pathlib
from typing import Sequence
from importlib_resources import files

from aiida_basis.data.basis import PaoData
from ...metadata import openmx as openmx_metadata
from ..mixins import RecommendedOrbitalConfigurationMixin
from .basis import BasisSet

__all__ = ('OpenmxConfiguration', 'OpenmxBasisSet')

OpenmxConfiguration = collections.namedtuple('OpenmxConfiguration', ['version', 'protocol', 'hardness'])


class OpenmxBasisSet(RecommendedOrbitalConfigurationMixin, BasisSet):
    """Subclass of ``BasisSet`` designed to represent a set of OpenMX PAOs.

    The `OpenmxBasisSet` is essentially a `BasisSet` with some additional constraints. It can only
    be used to contain the bases and corresponding metadata of the PAO basis sets included with
    the OpenMX source code.
    """

    _basis_types = (PaoData,)

    label_template = 'OpenMX/{version}/{protocol}/{hardness}'
    default_configuration = OpenmxConfiguration('19', 'standard', 'soft')

    valid_configurations = (
        OpenmxConfiguration('19', 'quick', 'soft'), OpenmxConfiguration('19', 'quick', 'hard'),
        OpenmxConfiguration('19', 'standard', 'soft'), OpenmxConfiguration('19', 'standard', 'hard'),
        OpenmxConfiguration('19', 'precise', 'soft'), OpenmxConfiguration('19', 'precise', 'hard')
        # FUTURE: add 2013 configurations
    )

    url_base = 'https://t-ozaki.issp.u-tokyo.ac.jp/'
    url_version = {'19': 'vps_pao2019/', '13': 'vps_pao2013/'}

    @classmethod
    def get_valid_labels(cls) -> Sequence[str]:
        """Return the tuple of labels of all valid OpenMX basis set configurations.

        :return: valid configuration labels.
        """
        configurations = set(cls.valid_configurations)
        return tuple(cls.format_configuration_label(configuration) for configuration in configurations)

    @classmethod
    def format_configuration_label(cls, configuration: OpenmxConfiguration) -> str:
        """Format a label for an `OpenmxConfiguration` with the required syntax.

        :param configuration: OpenMX basis set configuration.
        :returns: label.
        """
        return cls.label_template.format(
            version=configuration.version, protocol=configuration.protocol, hardness=configuration.hardness
        )

    @classmethod
    def get_configuration_metadata_filepath(cls, configuration: OpenmxConfiguration) -> pathlib.Path:
        """Return the filepath to the metadata JSON of a given `OpenmxConfiguration`.

        :param configuration: OpenMX basis configuration.
        :return: metadata filepath.
        """
        metadata_filename = f'{configuration.version}_{configuration.protocol}_{configuration.hardness}.json'
        return files(openmx_metadata) / metadata_filename

    @classmethod
    def get_configuration_metadata(cls, configuration: OpenmxConfiguration):
        """Return the metadata dictionary for an `OpenmxConfiguration`.

        :param configuration: OpenMX basis set configuration.
        :returns: metadata dictionary.
        """
        metadata_filepath = cls.get_configuration_metadata_filepath(configuration)
        try:
            with open(metadata_filepath, 'r') as stream:
                metadata = json.load(stream)
        except FileNotFoundError as exception:
            raise FileNotFoundError(
                f'Metadata JSON for {cls.format_configuration_label(configuration)} could not be found'
            ) from exception
        except OSError as exception:
            raise OSError(
                f'Error while opening the metadata file for {cls.format_configuration_label(configuration)}'
            ) from exception

        return metadata

    @classmethod
    def get_element_metadata(cls, element: str, configuration: OpenmxConfiguration):
        """Return the metadata dictionary for an element from an OpenMX basis set configuration.

        :param: element IUPAC element symbol.
        :configuration: OpenMX basis set configuration.
        :returns: element metadata.
        :raises: `ValueError` if the element does not exist in the configuration metadata.
        """
        configuration_metadata = cls.get_configuration_metadata(configuration)

        try:
            metadata = configuration_metadata[element]
        except KeyError as exception:
            raise ValueError(
                f'The element {element} does not have an entry in the metadata of '
                '{cls.format_configuration_label(configuration)}'
            ) from exception

        return metadata

    # @classmethod
    # def get_url_file(cls, element: str, configuration: OpenmxConfiguration):
    #     """Return the URL for the PAO file for a given basis set label and element.

    #     :param element: IUPAC element symbol.
    #     :param configuration: basis set configuration.
    #     :returns: the URL from which the PAO basis file can be downloaded.
    #     :raises: `ValueError` if the configuration or the element symbol is invalid.
    #     """
    #     if configuration not in cls.valid_configurations:
    #         raise ValueError(f'{cls.format_configuration_label(configuration)} is not a valid configuration')

    #     element_metadata = cls.get_pao_metadata(element, configuration)

    #     url = cls.url_base + cls.url_version[configuration.version] + f'{element}/' + element_metadata['filename']

    #     return url

    # @classmethod
    # def get_urls_configuration(cls, configuration: OpenmxConfiguration):
    #     """Return the URLs for all the PAO files of a given OpenMX basis set configuration.

    #     :param configuration: OpenMX basis set configuration.
    #     :returns: list of URLs
    #     :raises: `ValueError` is the configuration is invalid.
    #     """
    #     if configuration not in cls.valid_configurations:
    #         raise ValueError(f'{cls.format_configuration_label(configuration)} is not a valid configuration')

    #     configuration_metadata = cls.get_configuration_metadata(configuration)

    #     url_base = cls.url_base + cls.url_version[configuration.version]

    #     urls = [
    #         url_base + f'{element}/' + metadata['filename'] for element, metadata in configuration_metadata.items()
    #     ]

    #     return urls

    @classmethod
    def get_md5s_configuration(cls, configuration: OpenmxConfiguration):
        """Return the MD5s for all the PAO files of a given OpenMX basis set configuration.

        :param configuration: OpenMX basis set configuration.
        :returns: dictionary of MD5s
        :raises: `ValueError` is the configuration is invalid.
        """
        if configuration not in cls.valid_configurations:
            raise ValueError(f'{cls.format_configuration_label(configuration)} is not a valid configuration')

        configuration_metadata = cls.get_configuration_metadata(configuration)

        md5s = {element: metadata['md5'] for element, metadata in configuration_metadata.items()}

        return md5s

    @classmethod
    def get_orbital_configs_configuration(cls, configuration: OpenmxConfiguration):
        """Return the orbital configuration tuples for all the PAO files of a given OpenMX basis set configuration.

        :param configuration: OpenMX basis set configuration.
        :returns: dictionary of MD5s
        :raises: `ValueError` is the configuration is invalid.
        """
        if configuration not in cls.valid_configurations:
            raise ValueError(f'{cls.format_configuration_label(configuration)} is not a valid configuration')

        configuration_metadata = cls.get_configuration_metadata(configuration)

        orbital_configs = {
            element: metadata['orbital_configuration'] for element, metadata in configuration_metadata.items()
        }

        return orbital_configs

    def __init__(self, label=None, **kwargs):
        """Construct a new instance, validating that the label matches the required format."""
        if label not in self.get_valid_labels():
            raise ValueError(f'the label `{label}` is not a valid OpenMX basis set configuration label.')

        super().__init__(label=label, **kwargs)
