import logging

from pulpcore.plugin.models import RepositoryVersion
from pulp_npm.app.models import NpmRepository, Package 

log = logging.getLogger(__name__)

def publish(repository_pk, package_pk):
    repository = NpmRepository.objects.get(pk=repository_pk)

    # create new repository version and add package
    with repository.new_version() as new_version:
        new_version.add_content(Package.objects.filter(pk=package_pk))

