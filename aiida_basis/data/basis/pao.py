# -*- coding: utf-8 -*-
"""Module for data plugin to represent a basis in PAO format."""
import re
import typing
import pathlib

from aiida.common.constants import elements

from .basis import BasisData

__all__ = ('PaoData',)

PATTERN_FLOAT = r'[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?'
REGEX_ATOMIC_NUMBER = re.compile(r"""\s*AtomSpecies\s*(?P<atomic_number>[\d]{1,3})\s*""", re.I)
REGEX_Z_VALENCE = re.compile(r"""\s*valence\.electron\s*(?P<z_valence>""" + PATTERN_FLOAT + r""")\s*""", re.I)
REGEX_R_CUTOFF = re.compile(r"""\s*radial\.cutoff\.pao\s*(?P<r_cutoff>""" + PATTERN_FLOAT + r""")\s*""", re.I)
REGEX_MAX_OCC_N = re.compile(r"""\s*max\.o[c]{1,2}upied\.N\s*(?P<max_occ_n>[\d]+)\s*""", re.I)
REGEX_MAX_L = re.compile(r"""\s*maxL\.pao\s*(?P<max_l>[\d]+)\s*""", re.I)
REGEX_NUM_PAO = re.compile(r"""\s*num\.pao\s*(?P<num_pao>[\d]+)\s*""", re.I)


def parse_element(content: str):
    """Parse the content of the PAO file to determine the element.

    :param content: the decoded content of the file.
    :return: the symbol of the element following the IUPAC naming standard.
    """
    match = REGEX_ATOMIC_NUMBER.search(content)

    if match:
        atomic_number = match.group('atomic_number')

        try:
            atomic_number = int(atomic_number)
        except ValueError as exception:
            raise ValueError(
                f'parsed value for the atomic number `{atomic_number}` is not a valid number.'
            ) from exception

        try:
            element = elements[atomic_number]['symbol']
        except KeyError as exception:
            raise ValueError(
                f'parsed value for the atomic number `{atomic_number}` is not in aiida.common.constants.elements.'
            ) from exception

        return element

    raise ValueError(f'could not parse the element from the PAO content: {content}')


def parse_z_valence(content: str):
    """Parse the content of the PAO file to determine the Z valence.

    :param content: the decoded content of the file.
    :return: the number of valence electrons for which the basis was generated.
    """
    match = REGEX_Z_VALENCE.search(content)

    if match:
        z_valence = match.group('z_valence')

        try:
            z_valence = float(z_valence)
        except ValueError as exception:
            raise ValueError(f'parsed value for the Z valence `{z_valence}` is not a valid number.') from exception

        if int(z_valence) != z_valence:
            raise ValueError(f'parsed value for the Z valence `{z_valence}` is not an integer')

        return int(z_valence)

    raise ValueError(f'could not parse the Z valence from the PAO content: {content}')


def parse_r_cutoff(content: str):
    """Parse the content of the PAO file to determine the radial cutoff.

    :param content: the decoded content of the file.
    :return: the radial cutoff in Bohr.
    """
    match = REGEX_R_CUTOFF.search(content)

    if match:
        r_cutoff = match.group('r_cutoff')

        try:
            r_cutoff = float(r_cutoff)
        except ValueError as exception:
            raise ValueError(f'parsed value for the radial cutoff `{r_cutoff}` is not a valid number.') from exception

        return float(r_cutoff)

    raise ValueError(f'could not parse the radial cutoff from the PAO content: {content}')


def parse_max_occ_n(content: str):
    """Parse the content of the PAO file to determine the maximum occupied `n`.

    :param content: the decoded content of the file.
    :return: the maximum occupied `n`
    """
    match = REGEX_MAX_OCC_N.search(content)

    if match:
        max_occ_n = match.group('max_occ_n')

        try:
            max_occ_n = int(max_occ_n)
        except ValueError as exception:
            raise ValueError(
                f'parsed value for the maximum occupied `n` `{max_occ_n}` is not a valid number.'
            ) from exception

        return int(max_occ_n)

    raise ValueError(f'could not parse the maximum occupied `n` from the PAO content: {content}')


def parse_max_l(content: str):
    """Parse the content of the PAO file to determine the maximum `l`.

    :param content: the decoded content of the file.
    :return: the maximum `l`
    """
    match = REGEX_MAX_L.search(content)

    if match:
        max_l = match.group('max_l')

        try:
            max_l = int(max_l)
        except ValueError as exception:
            raise ValueError(f'parsed value for the maximum `l` `{max_l}` is not a valid number.') from exception

        return int(max_l)

    raise ValueError(f'could not parse the maximum `l` from the PAO content: {content}')


def parse_num_pao(content: str):
    """Parse the content of the PAO file to determine the number of PAOs.

    :param content: the decoded content of the file.
    :return: the number of PAOs
    """
    match = REGEX_NUM_PAO.search(content)

    if match:
        num_pao = match.group('num_pao')

        try:
            num_pao = int(num_pao)
        except ValueError as exception:
            raise ValueError(f'parsed value for the number of PAOs `{num_pao}` is not a valid number.') from exception

        return int(num_pao)

    raise ValueError(f'could not parse the number of PAOs from the PAO content: {content}')


class PaoData(BasisData):
    """Data plugin to represent a basis in PAO format."""

    _key_z_valence = 'z_valence'
    _key_xc_type = 'xc_type'
    _key_r_cutoff = 'r_cutoff'
    _key_max_occ_n = 'max_occ_n'
    _key_max_l = 'max_l'
    _key_num_pao = 'num_pao'

    def set_file(self, source: typing.Union[str, pathlib.Path, typing.BinaryIO], filename: str = None, **kwargs):  # pylint: disable=arguments-differ,unsubscriptable-object
        """Set the file content.

        :param source: a filelike object with the binary content of the file.
        :param filename: optional explicit filename to give to the file stored in the repository.
        :raises ValueError: if the element symbol is invalid.
        """
        source = self.prepare_source(source)
        super().set_file(source, filename, **kwargs)

        source.seek(0)

        content = source.read().decode('utf-8')
        self.element = parse_element(content)
        self.z_valence = parse_z_valence(content)
        self.r_cutoff = parse_r_cutoff(content)
        self.max_occ_n = parse_max_occ_n(content)
        self.max_l = parse_max_l(content)  # pylint: disable=attribute-defined-outside-init
        self.num_pao = parse_num_pao(content)

    @property
    def z_valence(self) -> typing.Union[int, None]:  # pylint: disable=unsubscriptable-object
        """Return the Z valence.

        :return: the Z valence.
        """
        return self.get_attribute(self._key_z_valence, None)

    @z_valence.setter
    def z_valence(self, value: int):
        """Set the valence.

        :param value: the valence.
        :raises ValueError: if the value is not a positive integer
        """
        if not isinstance(value, int) or value < 0:
            raise ValueError(f'`{value}` is not a positive integer.')

        self.set_attribute(self._key_z_valence, value)

    @property
    def r_cutoff(self) -> typing.Union[float, None]:  # pylint: disable=unsubscriptable-object
        """Return the radial cutoff in Bohr.

        :return: the radial cutoff in Bohr.
        """
        return self.get_attribute(self._key_r_cutoff, None)

    @r_cutoff.setter
    def r_cutoff(self, value: float):
        """Set the radial cutoff.

        :param value: the radial cutoff.
        :raises ValueError: if the value is not a positive float
        """
        if not isinstance(value, float) or value <= 0:
            raise ValueError(f'`{value}` is not a positive float.')

        self.set_attribute(self._key_r_cutoff, value)

    @property
    def max_occ_n(self) -> typing.Union[int, None]:  # pylint: disable=unsubscriptable-object
        """Return the maximum occupied `n`.

        :return: the maximum occupied `n`.
        """
        return self.get_attribute(self._key_max_occ_n, None)

    @max_occ_n.setter
    def max_occ_n(self, value: int):
        """Set the maximum occupied `n`.

        :param value: the maximum occupied `n`.
        :raises ValueError: if the value is not a positive integer
        """
        if not isinstance(value, int) or value < 0:
            raise ValueError(f'`{value}` is not a positive integer.')

        self.set_attribute(self._key_max_occ_n, value)

    @property
    def key_max_l(self) -> typing.Union[int, None]:  # pylint: disable=unsubscriptable-object
        """Return the maximum `l`.

        :return: the maximum `l`
        """
        return self.get_attribute(self._key_key_max_l, None)

    @key_max_l.setter
    def key_max_l(self, value: int):
        """Set the maximum `l`.

        :param value: the maximum `l`
        :raises ValueError: if the value is not a positive integer
        """
        if not isinstance(value, int) or value < 0:
            raise ValueError(f'`{value}` is not a positive integer.')

        self.set_attribute(self._key_key_max_l, value)

    @property
    def num_pao(self) -> typing.Union[int, None]:  # pylint: disable=unsubscriptable-object
        """Return the number of PAOs.

        :return: the number of PAOs
        """
        return self.get_attribute(self._key_num_pao, None)

    @num_pao.setter
    def num_pao(self, value: int):
        """Set the number of PAOs.

        :param value: the number of PAOs
        :raises ValueError: if the value is not a positive integer
        """
        if not isinstance(value, int) or value < 0:
            raise ValueError(f'`{value}` is not a positive integer.')

        self.set_attribute(self._key_num_pao, value)
