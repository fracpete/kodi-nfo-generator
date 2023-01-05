# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# setup.py
# Copyright (C) 2020-2023 Fracpete (fracpete at gmail dot com)

from setuptools import setup


def _read(f):
    """
    Reads in the content of the file.
    :param f: the file to read
    :type f: str
    :return: the content
    :rtype: str
    """
    return open(f, 'rb').read()


setup(
    name="kodi-nfo-generator",
    description=" Simple Python-based command-line tool to generate .nfo files for movies and TV shows for Kodi. ",
    long_description=(
        _read('DESCRIPTION.rst') + b'\n' +
        _read('CHANGES.rst')).decode('utf-8'),
    url="https://github.com/fracpete/kodi-nfo-generator",
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Topic :: Multimedia :: Video',
        'Programming Language :: Python :: 3',
    ],
    license='GNU General Public License version 3.0 (GPLv3)',
    package_dir={
        '': 'src'
    },
    packages=[
        "kodi",
    ],
    version="0.0.9",
    author='Peter "fracpete" Reutemann',
    author_email='fracpete@gmail.com',
    install_requires=[
        "requests",
        "beautifulsoup4!=4.9.*",
    ],
    entry_points={
        "console_scripts": [
            "kodi-nfo-gen=kodi.generator:sys_main",
            "kodi-nfo-guess=kodi.guess:sys_main",
            "kodi-nfo-rename=kodi.rename:sys_main",
            "kodi-nfo-export=kodi.exports:sys_main",
            "kodi-nfo-import=kodi.imports:sys_main",
        ]
    }
)
