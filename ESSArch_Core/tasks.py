import os, urllib

from django.conf import settings

from ESSArch_Core.util import (
    alg_from_str,
)

from ESSArch_Core.essxml.Generator.xmlGenerator import XMLGenerator
from ESSArch_Core.WorkflowEngine.models import (
    ProcessStep,
    ProcessTask,
)
from ESSArch_Core.WorkflowEngine.dbtask import DBTask
from ESSArch_Core.util import (
    getSchemas,
    get_value_from_path,
    remove_prefix,
)

from fido.fido import Fido
from lxml import etree


class CalculateChecksum(DBTask):
    def run(self, filename=None, block_size=65536, algorithm='SHA-256'):
        """
        Calculates the checksum for the given file, one chunk at a time

        Args:
            filename: The filename to calculate checksum for
            block_size: The size of the chunk to calculate
            algorithm: The algorithm to use

        Returns:
            The hexadecimal digest of the checksum
        """

        hash_val = alg_from_str(algorithm)()

        with open(filename, 'r') as f:
            while True:
                data = f.read(block_size)
                if data:
                    hash_val.update(data)
                else:
                    break

        self.set_progress(100, total=100)
        return hash_val.hexdigest()

    def undo(self, filename=None, block_size=65536, algorithm='SHA-256'):
        pass

    def event_outcome_success(self, filename=None, block_size=65536, algorithm='SHA-256'):
        return "Created checksum for %s with %s" % (filename, algorithm)


class IdentifyFileFormat(DBTask):
    def handle_matches(self, fullname, matches, delta_t, matchtype=''):
        f, sigName = matches[-1]
        self.lastFmt = f.find('name').text

    def run(self, filename=None):
        """
        Identifies the format of the file using the fido library

        Args:
            filename: The filename to identify

        Returns:
            The format of the file
        """

        self.fid = Fido()
        self.fid.handle_matches = self.handle_matches
        self.fid.identify_file(filename)

        self.set_progress(100, total=100)

        return self.lastFmt

    def undo(self, filename=None):
        pass

    def event_outcome_success(self, filename=None, block_size=65536, algorithm='SHA-256'):
        return "Identified foramt of %s" % filename


class GenerateXML(DBTask):
    def run(self, info={}, filesToCreate={}, folderToParse=None, algorithm='SHA-256'):
        """
        Generates the XML using the specified data and folder, and adds the XML
        to the specified files
        """

        generator = XMLGenerator(
            filesToCreate, info
        )

        generator.generate(
            folderToParse=folderToParse, algorithm=algorithm,
            ip=self.taskobj.information_package
        )

        self.set_progress(100, total=100)

    def undo(self, info={}, filesToCreate={}, folderToParse=None, algorithm='SHA-256'):
        for f, template in filesToCreate.iteritems():
            os.remove(f)

    def event_outcome_success(self, info={}, filesToCreate={}, folderToParse=None, algorithm='SHA-256'):
        return "Generated %s" % ", ".join(filesToCreate.keys())


class InsertXML(DBTask):
    """
    Inserts XML to the specifed file
    """

    def run(self, filename=None, elementToAppendTo=None, spec={}, info={}, index=None):
        generator = XMLGenerator()

        generator.insert(filename, elementToAppendTo, spec, info=info, index=index)

        self.set_progress(100, total=100)

    def undo(self, filename=None, elementToAppendTo=None, spec={}, info={}, index=None):
        pass

    def event_outcome_success(self, filename=None, elementToAppendTo=None, spec={}, info={}, index=None):
        return "Inserted XML to element %s in %s" % (elementToAppendTo, filename)


class AppendEvents(DBTask):
    def run(self, filename="", events={}):
        generator = XMLGenerator()
        template = {
            "-name": "event",
            "-min": 1,
            "-max": 1,
            "-allowEmpty": 1,
            "-namespace": "premis",
            "-children": [
                {
                    "-name": "eventIdentifier",
                    "-min": 1,
                    "-max": 1,
                    "-allowEmpty": 1,
                    "-namespace": "premis",
                    "-children": [
                        {
                            "-name": "eventIdentifierType",
                            "-min": 1,
                            "-max": 1,
                            "-namespace": "premis",
                            "#content": [{"var": "eventIdentifierType"}]
                        }, {
                            "-name": "eventIdentifierValue",
                            "-min": 1,
                            "-max": 1,
                            "-allowEmpty": 1,
                            "-namespace": "premis",
                            "#content": [{"var": "eventIdentifierValue"}]
                        },
                    ]
                },
                {
                    "-name": "eventType",
                    "-min": 1,
                    "-max": 1,
                    "-allowEmpty": 1,
                    "-namespace": "premis",
                    "#content": [{"var": "eventType"}]
                },
                {
                    "-name": "eventDateTime",
                    "-min": 1,
                    "-max": 1,
                    "-allowEmpty": 1,
                    "-namespace": "premis",
                    "#content": [{"var": "eventDateTime"}]
                },
                {
                    "-name": "eventDetailInformation",
                    "-namespace": "premis",
                    "-children": [
                        {
                            "-name": "eventDetail",
                            "-min": 1,
                            "-max": 1,
                            "-allowEmpty": 1,
                            "-namespace": "premis",
                            "#content": [{"var": "eventDetail"}]
                        },
                    ]
                },
                {
                    "-name": "eventOutcomeInformation",
                    "-min": 1,
                    "-max": 1,
                    "-allowEmpty": 1,
                    "-namespace": "premis",
                    "-children": [
                        {
                            "-name": "eventOutcome",
                            "-min": 1,
                            "-max": 1,
                            "-allowEmpty": 1,
                            "-namespace": "premis",
                            "#content": [{"var": "eventOutcome"}]
                        },
                        {
                            "-name": "eventOutcomeDetail",
                            "-min": 1,
                            "-max": 1,
                            "-allowEmpty": 1,
                            "-namespace": "premis",
                            "-children": [
                                {
                                    "-name": "eventOutcomeDetailNote",
                                    "-min": 1,
                                    "-max": 1,
                                    "-allowEmpty": 1,
                                    "-namespace": "premis",
                                    "#content": [{"var": "eventOutcomeDetailNote"}]
                                },
                            ]
                        },
                    ]
                },
                {
                    "-name": "linkingAgentIdentifier",
                    "-min": 1,
                    "-max": 1,
                    "-allowEmpty": 1,
                    "-namespace": "premis",
                    "-children": [
                        {
                            "-name": "linkingAgentIdentifierType",
                            "-min": 1,
                            "-max": 1,
                            "-namespace": "premis",
                            "#content": [{"var": "linkingAgentIdentifierType"}]
                        },
                        {
                            "-name": "linkingAgentIdentifierValue",
                            "-min": 1,
                            "-max": 1,
                            "-allowEmpty": 1,
                            "-namespace": "premis",
                            "#content": [{"var": "linkingAgentIdentifierValue"}]
                        },
                    ]
                },
                {
                    "-name": "linkingObjectIdentifier",
                    "-min": 1,
                    "-max": 1,
                    "-allowEmpty": 1,
                    "-namespace": "premis",
                    "-children": [
                        {
                            "-name": "linkingObjectIdentifierType",
                            "-min": 1,
                            "-max": 1,
                            "-namespace": "premis",
                            "#content": [{"var": "linkingObjectIdentifierType"}]
                        },
                        {
                            "-name": "linkingObjectIdentifierValue",
                            "-min": 1,
                            "-max": 1,
                            "-allowEmpty": 1,
                            "-namespace": "premis",
                            "#content": [{"var": "linkingObjectIdentifierValue"}]
                        },
                    ]
                },
            ]
        }

        if not events:
            events = self.taskobj.information_package.events.all()

        events = events.order_by(
            'eventDateTime'
        )

        for event in events:
            data = {
                "eventIdentifierType": "SE/RA",
                "eventIdentifierValue": str(event.id),
                "eventType": str(event.eventType.eventType),
                "eventDateTime": str(event.eventDateTime),
                "eventDetail": event.eventType.eventDetail,
                "eventOutcome": str(event.eventOutcome),
                "eventOutcomeDetailNote": event.eventOutcomeDetailNote,
                "linkingAgentIdentifierType": "SE/RA",
                "linkingAgentIdentifierValue": event.linkingAgentIdentifierValue,
                "linkingObjectIdentifierType": "SE/RA",
                "linkingObjectIdentifierValue": str(event.linkingObjectIdentifierValue.ObjectIdentifierValue),
            }

            generator.insert(filename, "premis", template, data)

        self.set_progress(100, total=100)

    def undo(self, filename="", events={}):
        pass

    def event_outcome_success(self, filename="", events={}):
        return "Appended events to %s" % filename


class CopySchemas(DBTask):
    def findDestination(self, dirname, structure, path=''):
        for content in structure:
            if content['name'] == dirname and content['type'] == 'folder':
                return os.path.join(path, dirname)
            elif content['type'] == 'dir':
                rec = self.findDestination(
                    dirname, content['children'], os.path.join(path, content['name'])
                )
                if rec: return rec

    def createSrcAndDst(self, schema, root, structure):
        src = schema['location']
        fname = os.path.basename(src.rstrip("/"))
        dst = os.path.join(
            root,
            self.findDestination(schema['preservation_location'], structure),
            fname
        )

        return src, dst

    def run(self, schema={}, root=None, structure=None):
        """
        Copies the schema to a specified location
        """

        src, dst = self.createSrcAndDst(schema, root, structure)
        urllib.urlretrieve(src, dst)

        self.set_progress(100, total=100)

    def undo(self, schema={}, root=None, structure=None):
        pass

    def event_outcome_success(self, schema={}, root=None, structure=None):
        src, dst = self.createSrcAndDst(schema, root, structure)
        return "Copied schemas from %s to %s" % src, dst


class ValidateFiles(DBTask):

    def run(self, ip=None, xmlfile=None, validate_fileformat=True, validate_integrity=True, rootdir=None):
        if rootdir is None:
            rootdir = ip.ObjectPath

        doc = etree.ElementTree(file=xmlfile)

        step = ProcessStep.objects.create(
            name="Validate Files",
            parallel=True,
            parent_step=self.taskobj.processstep
        )

        if any([validate_fileformat, validate_integrity]):
            for elname, props in settings.FILE_ELEMENTS.iteritems():
                for f in doc.xpath('.//*[local-name()="%s"]' % elname):
                    fpath = get_value_from_path(f, props["path"])

                    if fpath:
                        fpath = remove_prefix(fpath, props.get("pathprefix", ""))

                    fformat = get_value_from_path(f, props.get("format"))
                    checksum = get_value_from_path(f, props.get("checksum"))
                    algorithm = get_value_from_path(f, props.get("checksumtype"))

                    if validate_fileformat and fformat is not None:
                        step.tasks.add(ProcessTask.objects.create(
                            name="ESSArch_Core.tasks.ValidateFileFormat",
                            params={
                                "filename": os.path.join(rootdir, fpath),
                                "fileformat": fformat,
                            },
                            information_package=ip
                        ))

                    if validate_integrity and checksum is not None:
                        step.tasks.add(ProcessTask.objects.create(
                            name="ESSArch_Core.tasks.ValidateIntegrity",
                            params={
                                "filename": os.path.join(rootdir, fpath),
                                "checksum": checksum,
                                "algorithm": algorithm,
                            },
                            information_package=ip
                        ))

        self.set_progress(100, total=100)

        return step.run()

    def undo(self, ip=None, xmlfile=None, validate_fileformat=True, validate_integrity=True, rootdir=None):
        pass

    def event_outcome_success(self, ip, xmlfile, validate_fileformat=True, validate_integrity=True, rootdir=None):
        return "Validated files in %s" % xmlfile


class ValidateFileFormat(DBTask):
    def run(self, filename=None, fileformat=None):
        """
        Validates the format of the given file
        """
        t = ProcessTask(
            name="ESSArch_Core.tasks.IdentifyFileFormat",
            params={
                "filename": filename,
            },
            information_package=self.taskobj.information_package
        )

        res = t.run_eagerly()

        assert res == fileformat, "fileformat for %s is not valid" % filename
        self.set_progress(100, total=100)

    def undo(self, filename=None, fileformat=None):
        pass

    def event_outcome_success(self, filename=None, fileformat=None):
        return "Validated format of %s to be %s" % (filename, fileformat)


class ValidateIntegrity(DBTask):
    def run(self, filename=None, checksum=None, block_size=65536, algorithm='SHA-256'):
        """
        Validates the integrity(checksum) for the given file
        """

        t = ProcessTask(
            name="ESSArch_Core.tasks.CalculateChecksum",
            params={
                "filename": filename,
                "block_size": block_size,
                "algorithm": algorithm
            },
            information_package=self.taskobj.information_package
        )

        digest = t.run_eagerly()

        assert digest == checksum, "checksum for %s is not valid (%s != %s)" % (filename, digest, checksum)
        self.set_progress(100, total=100)

    def undo(self, filename=None,checksum=None,  block_size=65536, algorithm='SHA-256'):
        pass

    def event_outcome_success(self, filename=None, checksum=None, block_size=65536, algorithm='SHA-256'):
        return "Validated integrity of %s against %s with %s" % (filename, checksum, algorithm)


class ValidateXMLFile(DBTask):
    def run(self, xml_filename=None, schema_filename=None):
        """
        Validates (using LXML) an XML file using a specified schema file
        """

        doc = etree.ElementTree(file=xml_filename)

        if schema_filename:
            xmlschema = etree.XMLSchema(etree.parse(schema_filename))
        else:
            xmlschema = getSchemas(doc=doc)

        xmlschema.assertValid(doc)
        self.set_progress(100, total=100)

    def undo(self, xml_filename=None, schema_filename=None):
        pass

    def event_outcome_success(self, xml_filename=None, schema_filename=None):
        return "Validated %s against schema" % xml_filename


class UpdateIPStatus(DBTask):
    def run(self, ip=None, status=None):
        ip.State = status
        ip.save()
        self.set_progress(100, total=100)

    def undo(self, ip=None, status=None):
        pass

    def event_outcome_success(self, ip=None, status=None):
        return "Updated status of %s" % (ip.pk)
