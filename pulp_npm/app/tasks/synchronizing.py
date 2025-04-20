from gettext import gettext as _
import json
import logging
import requests

from pulpcore.plugin.models import Artifact, Remote, Repository
from pulpcore.plugin.stages import (
    DeclarativeArtifact,
    DeclarativeContent,
    DeclarativeVersion,
    Stage,
)

from pulp_npm.app.models import Package, NpmRemote


log = logging.getLogger(__name__)


def synchronize(remote_pk, repository_pk, mirror=False, sync_deps=False):
    """
    Sync content from the remote repository.

    Create a new version of the repository that is synchronized with the remote.

    Args:
        remote_pk (str): The remote PK.
        repository_pk (str): The repository PK.
        mirror (bool): True for mirror mode, False for additive.
        sync_deps (bool): If True, dependencies are also synced. Defaults to False.

    Raises:
        ValueError: If the remote does not specify a URL to sync

    """
    remote = NpmRemote.objects.get(pk=remote_pk)
    repository = Repository.objects.get(pk=repository_pk)

    if not remote.url:
        raise ValueError(_("A remote must have a url specified to synchronize."))

    # Interpret policy to download Artifacts or not
    deferred_download = remote.policy != Remote.IMMEDIATE
    first_stage = NpmFirstStage(remote, deferred_download, sync_deps=sync_deps)
    return DeclarativeVersion(first_stage, repository, mirror=mirror).create()


class NpmFirstStage(Stage):
    """
    The first stage of a pulp_npm sync pipeline.
    """

    def __init__(self, remote, deferred_download, sync_deps=False):
        """
        The first stage of a pulp_npm sync pipeline.

        Args:
            remote (FileRemote): The remote data to be used when syncing
            deferred_download (bool): if True the downloading will not happen now. If False, it will
                happen immediately.
            sync_deps (bool): If True, dependencies are also synced. Defaults to False.

        """
        super().__init__()
        self.remote = remote
        self.deferred_download = deferred_download
        self.sync_deps = sync_deps

    async def run(self):
        """
        Build and emit `DeclarativeContent` from the Manifest data.

        Args:
            in_q (asyncio.Queue): Unused because the first stage doesn't read from an input queue.
            out_q (asyncio.Queue): The out_q to send `DeclarativeContent` objects to

        """
        downloader = self.remote.get_downloader(url=self.remote.url)
        result = await downloader.run()
        data = self.get_json_data(result.path)

        to_process = []
        pkgs = []

        if "versions" in data:
            to_process.extend(list(data["versions"].values()))
        else:
            to_process.extend([data])

        while to_process:
            pkg = to_process.pop()

            name = pkg["name"]
            version = pkg["version"]

            # add package to pkgs if it does not yet exist
            pkg_list_name_version = {(pkg['name'], pkg['version']) for pkg in pkgs}
            if (name, version) not in pkg_list_name_version:
                pkgs.append(pkg)

            if self.sync_deps and "dependencies" in pkg:
                for dependency in pkg["dependencies"]:

                    # skip dependency if it already exists in pkgs
                    pkg_list_name = {name for name, _ in pkg_list_name_version}
                    if dependency in pkg_list_name:
                        continue

                    next_url = self.remote.url.replace(data["name"], dependency).replace(data.get("version", ""), "")
                    downloader = self.remote.get_downloader(url=next_url)
                    result = await downloader.run()
                    dep_data = self.get_json_data(result.path)

                    if "versions" in dep_data:
                        deps = list(dep_data["versions"].values())
                    else:
                        deps = [dep_data]

                    # add dependency to process list if it does not yet exist
                    to_process_list_names = {(pkg['name']) for pkg in to_process}
                    if dependency not in to_process_list_names:
                        to_process.extend(deps)

        for pkg in pkgs:
            dependencies = pkg.get("dependencies", {})
            package = Package(name=pkg["name"], version=pkg["version"], dependencies=dependencies)
            artifact = Artifact()
            url = pkg["dist"]["tarball"]

            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                da = DeclarativeArtifact(
                    artifact=artifact,
                    url=url,
                    relative_path=f"{pkg['name']}/-/{url.split('/')[-1]}",
                    remote=self.remote,
                    deferred_download=self.deferred_download,
                )
                dc = DeclarativeContent(content=package, d_artifacts=[da])
                await self.put(dc)

    def get_json_data(self, path):
        """
        Parse the metadata for npm Content type.

        Args:
            path: Path to the metadata file
        """
        with open(path) as fd:
            return json.load(fd)
