import logging

from pulpcore.plugin.models import RepositoryVersion
from pulp_npm.app.models import NpmDistribution, NpmRepository, Package 

log = logging.getLogger(__name__)

def publish(repository_pk, package_pk):
    repository = NpmRepository.objects.get(pk=repository_pk)
    distribution = NpmDistribution.objects.get(repository=repository)

    # create new repository version
    with repository.new_version(base_version=repository.latest_version()) as new_version:
        new_version.add_content(Package.objects.filter(pk=package_pk))

    # switch distribution to new version
    distribution.repository_version = new_version
    distribution.save()
