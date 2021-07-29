# -*- coding: utf-8 -*-
"""Command to install a basis set."""
import pathlib
import tempfile

import click
import requests
from sqlalchemy.sql.elements import True_
from tqdm import tqdm
from aiida.cmdline.params import options as options_core
from aiida.cmdline.params import types
from aiida.cmdline.utils import decorators, echo
from aiida.orm import Group, QueryBuilder
from aiida_basis import __version__
from aiida_basis.groups.set.openmx import OpenmxBasisSet, OpenmxConfiguration

from .params import options
from .root import cmd_root
from .utils import (attempt, create_basis_set_from_archive,
                    create_basis_set_from_directory)


def download_openmx(
    configuration: OpenmxConfiguration,
    dirpath: pathlib.Path,
    traceback: bool = False
) -> None:
    """Download the PAO files for an OpenMX configuration to a directory on disk.
    
    :param configuration: the OpenMX configuration to download.
    :param dirpath: absolute dirpath to the directory in which to download the PAO files.
    :param traceback: boolean, if true, print the traceback if an exception occurs.
    """    
    # pylint: disable=too-many-locals


    url_base = 'https://t-ozaki.issp.u-tokyo.ac.jp/'
    url_version = {
        '19': 'vps_pao2019/',
        '13': 'vps_pao2013/'
    }

    metadata = OpenmxBasisSet.get_configuration_metadata(configuration)

    with attempt('downloading selected PAO basis set files... ', include_traceback=traceback):
        pbar = tqdm(metadata.items(), desc="Downloading")
        for element, element_metadata in pbar:
            pbar.set_description(f'Downloading {element_metadata["filename"]}')
            
            if element_metadata.get('hardness') == 'hard':
                url = f'{url_base}/{url_version[configuration.version]}/{element}/{element}_Hard/{element_metadata["filename"]}'
            elif element_metadata.get('hardness') == 'soft':
                url = f'{url_base}/{url_version[configuration.version]}/{element}/{element}_Soft/{element_metadata["filename"]}'
            elif element_metadata.get('open_core') is True:
                url = f'{url_base}/{url_version[configuration.version]}/{element}/{element}_OC/{element_metadata["filename"]}'
            elif element_metadata.get('open_core') is False:
                url = f'{url_base}/{url_version[configuration.version]}/{element}/{element}/{element_metadata["filename"]}'
            else:
                url = f'{url_base}/{url_version[configuration.version]}/{element}/{element_metadata["filename"]}'
                

            response = requests.get(url)
            response.raise_for_status()
            with open(dirpath / element_metadata["filename"], 'wb') as stream:
                stream.write(response.content)
                stream.flush()


@cmd_root.group('install')
def cmd_install():
    """Install basis sets."""


@cmd_install.command('basisset')
@click.argument('archive', type=types.FileOrUrl(mode='rb'))
@click.argument('label', type=click.STRING)
@options_core.DESCRIPTION(help='Description for the basis set.')
@options.ARCHIVE_FORMAT()
@options.BASIS_SET_TYPE()
@options.BASIS_TYPE()
@options.TRACEBACK()
@decorators.with_dbenv()
def cmd_install_basis_set(archive, label, description, archive_format, basis_set_type, basis_type, traceback):  # pylint: disable=too-many-arguments
    """Install a standard basis set from an ARCHIVE."""
    if isinstance(archive, pathlib.Path) and archive.is_dir():
        with attempt(f'creating a basis_set from directory `{archive}`...', include_traceback=traceback):
            basis_set = basis_set_type.create_from_folder(archive, label, basis_type=basis_type)
    elif isinstance(archive, pathlib.Path) and archive.is_file():
        with attempt('unpacking archive and parsing basis... ', include_traceback=traceback):
            basis_set = create_basis_set_from_archive(
                basis_set_type, label, archive, fmt=archive_format, basis_type=basis_type
            )
    else:
        # At this point, we can assume that it is not a valid filepath on disk, but rather a URL and the ``archive``
        # variable will contain the result objects from the ``requests`` library. The validation of the URL will already
        # have been done by the ``PathOrUrl`` parameter type, so the URL is reachable. The content of the URL must be
        # copied to a local temporary file because `create_basis_set_from_archive` does currently not accept filelike
        # objects, because in turn the underlying `shutil.unpack_archive` does not. In addition, `unpack_archive` will
        # attempt to deduce the archive format from the filename extension, so it is important we maintain the original
        # filename. Of course if this fails, users can specify the archive format explicitly with the corresponding
        # option. We get the filename by converting the URL to a ``Path`` object and taking the filename, using that as
        # a suffix for the temporary file that is generated on disk to copy the content to.
        suffix = pathlib.Path(archive.url).name
        with tempfile.NamedTemporaryFile(mode='w+b', suffix=suffix) as handle:
            handle.write(archive.content)
            handle.flush()

            with attempt('unpacking archive and parsing basis... ', include_traceback=traceback):
                basis_set = create_basis_set_from_archive(
                    basis_set_type, label, pathlib.Path(handle.name), fmt=archive_format, basis_type=basis_type
                )

    basis_set.description = description
    echo.echo_success(f'installed `{label}` containing {basis_set.count()} bases')


@cmd_install.command('openmx')
@options.VERSION(type=click.Choice(['19']), default='19', show_default=True)
@options.PROTOCOL(type=click.Choice(['quick', 'standard', 'precise']), default='standard', show_default=True)
@options.HARDNESS(type=click.Choice(['soft', 'hard']), default='soft', show_default=True)
@options.TRACEBACK()
@decorators.with_dbenv()
def cmd_install_openmx(version, protocol, hardness, traceback):
    """Install an OpenMX configuration.

    The OpenMX configuration will be automatically downloaded from t-ozaki.issp.u-tokyo.ac.jp to create a new
    `OpenmxBasisSet`.
    """
    # pylint: disable=too-many-locals
    configuration = OpenmxConfiguration(version, protocol, hardness)

    if configuration not in OpenmxBasisSet.valid_configurations:
        echo.echo_critical(f'{version} {hardness} {protocol} is not a valid OpenMX basis set configuration')
    
    label = OpenmxBasisSet.format_configuration_label(configuration)
    description = f'OpenMX 20{version} {hardness} {protocol} installed with aiida-basis v{__version__}'
    metadata = OpenmxBasisSet.get_configuration_metadata(configuration)

    if QueryBuilder().append(OpenmxBasisSet, filters={'label': label}).first():
        echo.echo_critical(f'{OpenmxBasisSet.__name__}<{label}> is already installed')

    with tempfile.TemporaryDirectory() as dirpath:
        dirpath = pathlib.Path(dirpath)
        download_openmx(configuration, dirpath)
        
        with attempt('parsing PAOs... ', include_traceback=traceback):
            basis_set = create_basis_set_from_directory(OpenmxBasisSet, label, dirpath)

        orbital_configurations = {}
        
        for element, values in metadata.items():
            if basis_set.get_basis(element).md5 != values['md5']:
                Group.objects.delete(basis_set.pk)
                msg = f'md5 of PAO for element {element} does not match that of the metadata {values["md5"]}'
                echo.echo_critical(msg)
            
            orbital_configurations[element] = metadata[element]['orbital_configuration']

        basis_set.description = description
        basis_set.set_orbital_configurations(orbital_configurations)

        echo.echo_success(f'installed `{label}` containing `{basis_set.count()}` orbital bases')
