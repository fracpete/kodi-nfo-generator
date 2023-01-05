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

# xml_utils.py
# Copyright (C) 2020-2023 Fracpete (fracpete at gmail dot com)

import os


def add_node(doc, parent, name, value=None):
    """
    Adds a node to the DOM document.

    :param doc: the DOM document
    :type doc: minidom.Document
    :param parent: the parent node to add the new node to
    :type parent: minidom.Element
    :param name: the name of the node
    :type name: str
    :param value: the text value, ignored if None
    :type value: str
    :return: the generated node
    :rtype: minidom.Element
    """

    node = doc.createElement(name)
    parent.appendChild(node)
    if value is not None:
        text = doc.createTextNode(value)
        node.appendChild(text)

    return node


def output_xml(doc, xml_path, dry_run=False, overwrite=False, logger=None):
    """
    Outputs the XML document. Can throw an exception if writing fails.

    :param doc: the XML document to output
    :param xml_path: the file to (potentially) write to
    :type xml_path: str
    :param dry_run: whether this is just a test run
    :type dry_run: bool
    :param overwrite: whether to overwrite existing files
    :type overwrite: bool
    :param logger: the logger instance to use for outputting logging information
    :return: whether a file was generated
    :rtype: bool
    """
    xml_str = doc.toprettyxml(indent="  ")
    if dry_run:
        print(xml_str)
        return False
    else:
        if os.path.exists(xml_path) and not overwrite:
            logger.info(".nfo file already exists, skipping: %s" % xml_path)
            return False
        else:
            if logger is not None:
                logger.info("Writing .nfo file: %s" % xml_path)
            with open(xml_path, "w") as xml_file:
                xml_file.write(xml_str)
            return True
