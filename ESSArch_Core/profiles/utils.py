import os

from django.utils.timezone import localtime

from ESSArch_Core.configuration.models import Parameter
from ESSArch_Core.util import find_destination


profile_types = [
    "Transfer Project",
    "Content Type",
    "Data Selection",
    "Authority Information",
    "Archival Description",
    "Import",
    "Submit Description",
    "SIP",
    "AIC Description",
    "AIP",
    "AIP Description",
    "DIP",
    "Workflow",
    "Preservation Metadata",
    "Event",
    "Validation",
    "Transformation",
]

def fill_specification_data(data={}, sa=None, ip=None):
    if sa:
        data['_SA_ID'] = str(sa.pk)
        data['_SA_NAME'] = sa.name

    if ip:
        if not sa and ip.submission_agreement is not None:
            sa = ip.submission_agreement
            data['_SA_ID'] = str(sa.pk)
            data['_SA_NAME'] = sa.name

        data['_OBJID'] = ip.object_identifier_value
        data['_OBJUUID'] = str(ip.pk)
        data['_OBJLABEL'] = ip.label
        data['_OBJPATH'] = ip.object_path
        data['_STARTDATE'] = localtime(ip.start_date)
        data['_ENDDATE'] = localtime(ip.end_date)
        data['_INFORMATIONCLASS'] = ip.information_class

        data['_CONTENT_METS_PATH'] = ip.content_mets_path
        data['_CONTENT_METS_CREATE_DATE'] = localtime(ip.content_mets_create_date)
        data['_CONTENT_METS_SIZE'] = ip.content_mets_size
        data['_CONTENT_METS_DIGEST_ALGORITHM'] = ip.get_content_mets_digest_algorithm_display()
        data['_CONTENT_METS_DIGEST'] = ip.content_mets_digest

        data['_PACKAGE_METS_PATH'] = ip.package_mets_path
        data['_PACKAGE_METS_CREATE_DATE'] = localtime(ip.package_mets_create_date)
        data['_PACKAGE_METS_SIZE'] = ip.package_mets_size
        data['_PACKAGE_METS_DIGEST_ALGORITHM'] = ip.get_package_mets_digest_algorithm_display()
        data['_PACKAGE_METS_DIGEST'] = ip.package_mets_digest

        if ip.get_package_type_display() in ['SIP', 'AIP']:
            ip_profile = ip.get_profile(ip.get_package_type_display().lower())
            premis_dir, premis_file = find_destination("preservation_description_file", ip_profile.structure)
            if premis_dir is None or premis_file is None:
                return None
            data['_PREMIS_PATH'] = os.path.join(ip.object_path, premis_dir, premis_file)

        try:
            # do we have a transfer project profile?
            ip.get_profile('transfer_project')
        except AttributeError:
            container = 'TAR'
        else:
            container = ip.get_container_format()

        data['_IP_CONTAINER_FORMAT'] = container.upper()

        if ip.policy is not None:
            data['_POLICYUUID'] = ip.policy.pk
            data['_POLICYID'] = ip.policy.policy_id
            data['_POLICYNAME'] = ip.policy.policy_name
        else:
            try:
                # do we have a transfer project profile?
                ip.get_profile('transfer_project')
            except AttributeError:
                pass
            else:
                transfer_project_data = ip.get_profile_data('transfer_project')
                data['_POLICYUUID'] = transfer_project_data.get('archive_policy_uuid')
                data['_POLICYID'] = transfer_project_data.get('archive_policy_id')
                data['_POLICYNAME'] = transfer_project_data.get('archive_policy_name')


        if ip.archivist_organization:
            data['_IP_ARCHIVIST_ORGANIZATION'] = ip.archivist_organization.name

        if ip.archival_institution:
            data['_IP_ARCHIVAL_INSTITUTION'] = ip.archival_institution.name

        if ip.archival_type:
            data['_IP_ARCHIVAL_TYPE'] = ip.archival_type.name

        if ip.archival_location:
            data['_IP_ARCHIVAL_LOCATION'] = ip.archival_location.name

        profile_ids = zip([x.lower().replace(' ', '_') for x in profile_types], ["_PROFILE_" + x.upper().replace(' ', '_') + "_ID" for x in profile_types])

        for (profile_type, key) in profile_ids:
            try:
                data[key] = str(ip.get_profile(profile_type).pk)
            except AttributeError:
                pass

    for p in Parameter.objects.iterator():
        data['_PARAMETER_%s' % p.entity.upper()] = p.value

    return data
