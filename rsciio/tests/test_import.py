# -*- coding: utf-8 -*-
# Copyright 2007-2023 The HyperSpy developers
#
# This file is part of RosettaSciIO.
#
# RosettaSciIO is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RosettaSciIO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RosettaSciIO. If not, see <https://www.gnu.org/licenses/#GPL>.

import importlib

import pytest


def test_import_version():
    from rsciio import __version__


def test_rsciio_dir():
    import rsciio

    assert dir(rsciio) == ["IO_PLUGINS", "__version__"]


def test_import_all():
    from rsciio import IO_PLUGINS

    plugin_name_to_remove = []

    # Remove plugins which require not installed optional dependencies
    try:
        import skimage
    except Exception:
        plugin_name_to_remove.append("Blockfile")

    try:
        import mrcz
    except Exception:
        plugin_name_to_remove.append("MRCZ")

    try:
        import tifffile
    except Exception:
        plugin_name_to_remove.append("TIFF")
        plugin_name_to_remove.append("Phenom")

    try:
        import pyUSID
    except Exception:
        plugin_name_to_remove.append("USID")

    try:
        import zarr
    except Exception:
        plugin_name_to_remove.append("ZSPY")

    IO_PLUGINS = list(
        filter(
            lambda plugin: plugin["name"] not in plugin_name_to_remove,
            IO_PLUGINS,
        )
    )

    for plugin in IO_PLUGINS:
        importlib.import_module(plugin["api"])


def test_format_name_aliases():
    from rsciio import IO_PLUGINS

    for reader in IO_PLUGINS:
        assert isinstance(reader["name"], str)
        assert isinstance(reader["name_aliases"], list)
        if reader["name_aliases"]:
            for aliases in reader["name_aliases"]:
                assert isinstance(aliases, str)
        assert isinstance(reader["description"], str)
        assert isinstance(reader["full_support"], bool)
        assert isinstance(reader["file_extensions"], list)
        for extensions in reader["file_extensions"]:
            assert isinstance(extensions, str)
        assert isinstance(reader["default_extension"], int)
        if isinstance(reader["writes"], list):
            for i in reader["writes"]:
                assert isinstance(i, list)
        else:
            assert isinstance(reader["writes"], bool)
        assert isinstance(reader["non_uniform_axis"], bool)


def test_dir_plugins():
    from rsciio import IO_PLUGINS

    for plugin in IO_PLUGINS:
        plugin_string = "rsciio.%s" % plugin["name"].lower()
        # skip for missing optional dependencies
        if plugin["name"] == "Blockfile":
            pytest.importorskip("skimage")
        elif plugin["name"] == "MRCZ":
            pytest.importorskip("mrcz")
        elif plugin["name"] in ["TIFF", "Phenom"]:
            pytest.importorskip("tifffile")
        elif plugin["name"] == "USID":
            pytest.importorskip("pyUSID")
        elif plugin["name"] == "ZSPY":
            pytest.importorskip("zarr")
        plugin_module = importlib.import_module(plugin_string)
        if plugin["writes"] is False:
            assert dir(plugin_module) == ["file_reader"]
        elif plugin["name"] == "MSA":
            assert dir(plugin_module) == [
                "file_reader",
                "file_writer",
                "parse_msa_string",
            ]
        else:
            assert dir(plugin_module) == ["file_reader", "file_writer"]
