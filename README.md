# `aiida-basis`

AiiDA plugin that simplifies working with basis sets.

## Getting started

The easiest way of getting started using `aiida-basis` is to use the command line interface that ships with it.
For example, to install the default [OpenMX](http://http://www.openmx-square.org) basis set (v19 standard precision for soft pseudopotentials), just run:

    aiida-basis install openmx

The version, elements, and name of the basis set in the AiiDA database can be controlled with various options; use `aiida-basis install --help` to see their description.
Installed basis sets can be listed using:

    aiida-basis list

Any basis set installed can be loaded like any other `Group` using the `load_group` utility from `aiida-core`.
Once loaded, it is easy to get the basis for a given element or set of elements:

```python
from aiida.orm import load_group
family = load_group('OpenMX/19/standard/soft')
pseudo = family.get_basis(element='Ga')  # Returns a single basis
pseudos = family.get_bases(elements=('Ga', 'As'))  # Returns a dictionary where the keys are the elements
```

If you have a `StructureData` node, the `get_bases` method also accepts that as an argument to automatically retrieve all the bases required for that structure:

    structure = load_node()  # Load the structure from database or create one
    pseudos = family.get_bases(structure=structure)

If you use `aiida-openmx` the `bases` dictionary returned by `get_bases` can be directly used as an input for `OpenmxCalculation`s.

## Design

The plugin is centered around two concepts: bases and basis sets.
The two concepts are further explained below, especially focusing on how they are implemented in `aiida-basis`, what assumptions are made, and what the limitations are.

### Bases

Bases for a single element are implemented as [data plugins](https://aiida-core.readthedocs.io/en/latest/topics/data_types.html#creating-a-data-plugin), and the base class is `BasisData`.
As such, each basis node, _has_ to have two attributes: the type of basis that it represents and the symbol of chemical element that the basis describes.
The latter follows IUPAC naming conventions as used in the module `aiida.common.constants.elements` of `aiida-core`.

The `BasisData` functions as a base class and does not represent an actual existing basis file format or type of basis.
Rather, it serves as a base, holding common functionality used by different types of basis.