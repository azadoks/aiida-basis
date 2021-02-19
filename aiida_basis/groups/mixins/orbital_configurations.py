# -*- coding: utf-8 -*-
"""Mixin that adds support of recommended orbital configurations to a ``Group`` subclass, using its extras."""
from typing import Union

from aiida.common.lang import type_check
from aiida.plugins import DataFactory

StructureData = DataFactory('structure')  # pylint: disable=invalid-name

__all__ = ('RecommendedOrbitalConfigurationMixin',)


class RecommendedOrbitalConfigurationMixin:
    """Mixin that adds support of recommended orbital configurations to a ``Group`` subclass, using its extras.
    This class assumes that the maximum orbital angular momentum is 3 (`f`).
    """

    _key_orbital_configurations = '_orbital_configurations'
    # _key_default_stringency = '_default_stringency'

    @classmethod
    def validate_orbital_configurations(cls, elements: set, orbital_configurations: dict) -> None:
        """Validate an orbital configurations dictionary for a given set of elements.
        :param elements: set of elements for which to validate the orbital configurations dictionary.
        :param orbital_configurations: dictionary with recommended orbital configurations. Format: a dictionary in 
            which an orbital configuration, provided as a length-4 tuple of integers (s, p, d, f), is provided for each
            element symbol for which the basis set contains a basis.
        :raises ValueError: if the set of elements and those defined in the recommended orbital configurations do not
            match exactly, or if the orbital configurations dictionary has an invalid format.
        """
        elements_family = set(elements)

        elements_orbital_configurations = set(orbital_configurations.keys())
        elements_diff = elements_family ^ elements_orbital_configurations

        if elements_family < elements_orbital_configurations:
            raise ValueError(f'orbital configurations defined for unsupported elements: {elements_diff}')

        if elements_family > elements_orbital_configurations:
            raise ValueError(f'orbital configurations not defined for all family elements: {elements_diff}')

        for element, orbital_configuration in orbital_configurations.items():
            if len(orbital_configuration) != 4:
                raise ValueError(
                    f'invalid length of orbital configuration for element {element}: {orbital_configuration}'
                )
            if any(not isinstance(n, int) for n in orbital_configuration):
                raise ValueError(
                    f'invalid orbital configuration values for element {element}: {orbital_configuration}'
                )

    def _get_orbital_configurations(self) -> dict:
        """Return the orbital_configurations dictionary.
        :return: the orbital_configurations extra or an empty dictionary if it has not yet been set.
        """
        return self.get_extra(self._key_orbital_configurations, {})

    def set_orbital_configurations(self, orbital_configurations: dict) -> None:
        """Set the recommended orbital_configurations for the pseudos in this family.
        :param orbital_configurations: dictionary with recommended orbital configurations. Format: a dictionary in 
            which an orbital configuration, provided as a length-4 tuple of integers (s, p, d, f), is provided for each
            element symbol for which the basis set contains a basis.
        :raises ValueError: if the orbital_configurations have an invalid format
        """
        self.validate_orbital_configurations(set(self.elements), orbital_configurations)
        self.set_extra(self._key_orbital_configurations, orbital_configurations)

    def get_orbital_configurations(self) -> Union[dict, None]:
        """Return a set of orbital_configurations.
        :return: the orbital_configurations or ``None`` if no orbital_configurations whatsoever have been defined for
            this basis set.
        """
        return self._get_orbital_configurations()

    def get_recommended_orbital_configurations(self, *, elements=None, structure=None):
        """Return dictionary of orbital configurations for the given elements or ``StructureData``.
        .. note:: at least one and only one of arguments ``elements`` or ``structure`` should be passed.
        :param elements: single or tuple of elements.
        :param structure: a ``StructureData`` node.
        :return: dictionary of recommended orbital configurations.
        :raises: ValueError if one of the elements does not have an orbital configuration defined
        """
        if (elements is None and structure is None) or (elements is not None and structure is not None):
            raise ValueError('at least one and only one of `elements` or `structure` should be defined')

        type_check(elements, (tuple, str), allow_none=True)
        type_check(structure, StructureData, allow_none=True)

        if structure is not None:
            symbols = structure.get_symbols_set()
        elif isinstance(elements, tuple):
            symbols = elements
        else:
            symbols = (elements,)

        orbital_configurations = self.get_orbital_configurations()

        values = {}
        for element in symbols:
            try:
                values[element] = orbital_configurations[element]
            except KeyError:
                raise ValueError(
                    f'element {element} does not have an orbital configuration defined'
                )

        return values