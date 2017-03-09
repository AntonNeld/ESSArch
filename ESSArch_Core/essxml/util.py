"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Core
    Copyright (C) 2005-2017 ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
"""

from __future__ import absolute_import

import os

from lxml import etree

from ESSArch_Core.util import get_value_from_path

XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"


def get_agent(el, ROLE=None, OTHERROLE=None, TYPE=None, OTHERTYPE=None):
    s = ".//*[local-name()='agent']"

    if ROLE:
        s += "[@ROLE='%s']" % ROLE

    if OTHERROLE:
        s += "[@OTHERROLE='%s']" % OTHERROLE

    if TYPE:
        s += "[@TYPE='%s']" % TYPE

    if OTHERTYPE:
        s += "[@OTHERTYPE='%s']" % OTHERTYPE

    try:
        first = el.xpath(s)[0]
    except IndexError:
        return None

    return {
        'name': first.xpath("*[local-name()='name']")[0].text,
        'notes': [note.text for note in first.xpath("*[local-name()='note']")]
    }


def get_altrecordid(el, TYPE):
    try:
        return el.xpath(".//*[local-name()='altRecordID'][@TYPE='%s']" % TYPE)[0].text
    except IndexError:
        return None


def get_objectpath(el):
    try:
        e = el.xpath('.//*[local-name()="%s"]' % "FLocat")[0]
        if e is not None:
            return get_value_from_path(e, "@href").split('file:///')[1]
    except IndexError:
        return None


def parse_submit_description(xmlfile, srcdir=''):
    ip = {}
    doc = etree.parse(xmlfile)
    root = doc.getroot()

    try:
        ip['id'] = root.get('OBJID').split(':')[1]
    except:
        ip['id'] = root.get('OBJID')

    ip['label'] = root.get('LABEL')
    ip['create_date'] = root.find("{*}metsHdr").get('CREATEDATE')

    objpath = get_objectpath(root)

    if objpath:
        ip['object_path'] = os.path.join(srcdir, objpath)
        ip['object_size'] = os.stat(ip['object_path']).st_size

    ip['start_date'] = get_altrecordid(root, TYPE='STARTDATE'),
    ip['end_date'] = get_altrecordid(root, TYPE='ENDDATE'),

    try:
        ip['archivist_organization'] = get_agent(root, ROLE='ARCHIVIST', TYPE='ORGANIZATION')['name']
    except TypeError:
        pass

    try:
        ip['creator_organization'] = get_agent(root, ROLE='CREATOR', TYPE='ORGANIZATION')['name']
    except TypeError:
        pass

    try:
        ip['submitter_organization'] = get_agent(root, ROLE='OTHER', OTHERROLE='SUBMITTER', TYPE='ORGANIZATION')['name']
    except TypeError:
        pass

    try:
        ip['submitter_individual'] = get_agent(root, ROLE='OTHER', OTHERROLE='SUBMITTER', TYPE='INDIVIDUAL')['name']
    except TypeError:
        pass

    try:
        ip['producer_organization'] = get_agent(root, ROLE='OTHER', OTHERROLE='PRODUCER', TYPE='ORGANIZATION')['name']
    except TypeError:
        pass

    try:
        ip['producer_individual'] = get_agent(root, ROLE='OTHER', OTHERROLE='PRODUCER', TYPE='INDIVIDUAL')['name']
    except TypeError:
        pass

    try:
        ip['ipowner_organization'] = get_agent(root, ROLE='IPOWNER', TYPE='ORGANIZATION')['name']
    except TypeError:
        pass

    try:
        ip['preservation_organization'] = get_agent(root, ROLE='PRESERVATION', TYPE='ORGANIZATION')['name']
    except TypeError:
        pass

    try:
        ip['system_name'] = get_agent(root, ROLE='ARCHIVIST', TYPE='OTHER', OTHERTYPE='SOFTWARE')['name']
    except TypeError:
        pass

    try:
        ip['system_version'] = get_agent(root, ROLE='ARCHIVIST', TYPE='OTHER', OTHERTYPE='SOFTWARE')['notes'][0],
    except TypeError:
        pass

    try:
        ip['system_type'] = get_agent(root, ROLE='ARCHIVIST', TYPE='OTHER', OTHERTYPE='SOFTWARE')['notes'][1],
    except TypeError:
        pass

    return ip