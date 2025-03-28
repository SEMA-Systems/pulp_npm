import base64
import uuid

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.files.base import ContentFile
from django.db import transaction
from drf_spectacular.utils import extend_schema

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from pulpcore.plugin import viewsets as core
from pulpcore.plugin.actions import ModifyRepositoryActionMixin
from pulpcore.plugin.models import Artifact, ContentArtifact, PulpTemporaryFile
from pulpcore.plugin.serializers import (
    AsyncOperationResponseSerializer,
    RepositorySyncURLSerializer,
)
from pulpcore.plugin.tasking import dispatch

from . import models, serializers, tasks


def get_auth_token(request):
    """
    Retrieve npm authentication token.
    """

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, Response({"error": "Missing or invalid Authorization header"}, status=status.HTTP_401_UNAUTHORIZED)

    token_str = auth_header.split(' ')[1]
    try:
        token = models.AuthToken.objects.get(token=token_str)
        return token, None
    except models.AuthToken.DoesNotExist:
        return None, Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)


class PackageFilter(core.ContentFilter):
    """
    FilterSet for Package.
    """

    class Meta:
        model = models.Package
        fields = {"name": ["exact", "in"]}


class PackageViewSet(core.SingleArtifactContentUploadViewSet):
    """
    A ViewSet for Package.

    Define endpoint name which will appear in the API endpoint for this content type.
    For example::
        http://pulp.example.com/pulp/api/v3/content/npm/units/

    Also specify queryset and serializer for Package.
    """

    endpoint_name = "packages"
    queryset = models.Package.objects.all()
    serializer_class = serializers.PackageSerializer
    filterset_class = PackageFilter
    authentication_classes = []
    permission_classes = []

    @transaction.atomic
    def create(self, request, reponame=None, packagename=None, *args, **kwargs):
        """
        Handle npm package upload.
        """

        # check authorization
        token, error = get_auth_token(request)
        if error:
            return error

        # extract request data
        name = request.data['name']
        version = request.data['dist-tags']['latest']
        repository = models.NpmRepository.objects.get(name=reponame)
        attachment_name, attachment = next(iter(request.data.get('_attachments', {}).items()))
        binary_data = base64.b64decode(attachment['data'])
        file = ContentFile(binary_data, name=f"{uuid.uuid4().hex[:8]}-{name}")

        # find existing package
        package = models.Package.objects.filter(name=name, version=version).first()

        if not package:
            # create and save artifact
            temp_file = PulpTemporaryFile(file=file)
            artifact = Artifact.from_pulp_temporary_file(temp_file)
            artifact.save()

            # prepare data for validation
            data = {
                "name": name,
                "version": version,
                "relative_path": f"{name}/-/{attachment_name}",
                "artifact": str(artifact.pk)
            }

            # validate data
            serializer = serializers.PackageSerializer(data=data)
            serializer.is_valid(raise_exception=False)

            # create and save package
            package = models.Package(
                name=name,
                version=version,
            )
            package.save()

            # create and save content artifact
            ContentArtifact.objects.create(
                content=package,
                artifact=artifact,
                relative_path=package.relative_path,
            )

        # add package to repository
        result = dispatch(
            tasks.publish,
            kwargs={"repository_pk": repository.pk, "package_pk": package.pk},
            exclusive_resources=[repository, package],
        )

        return core.OperationPostponedResponse(result, request)


class NpmRemoteViewSet(core.RemoteViewSet):
    """
    A ViewSet for NpmRemote.

    Similar to the PackageViewSet above, define endpoint_name,
    queryset and serializer, at a minimum.
    """

    endpoint_name = "npm"
    queryset = models.NpmRemote.objects.all()
    serializer_class = serializers.NpmRemoteSerializer


class NpmRepositoryViewSet(core.RepositoryViewSet, ModifyRepositoryActionMixin):
    """
    A ViewSet for NpmRepository.

    Similar to the PackageViewSet above, define endpoint_name,
    queryset and serializer, at a minimum.
    """

    endpoint_name = "npm"
    queryset = models.NpmRepository.objects.all()
    serializer_class = serializers.NpmRepositorySerializer

    # This decorator is necessary since a sync operation is asyncrounous and returns
    # the id and href of the sync task.
    @extend_schema(
        description="Trigger an asynchronous task to sync content.",
        summary="Sync from remote",
        responses={202: AsyncOperationResponseSerializer},
    )
    @action(detail=True, methods=["post"], serializer_class=RepositorySyncURLSerializer)
    def sync(self, request, pk):
        """
        Dispatches a sync task.
        """
        repository = self.get_object()
        serializer = RepositorySyncURLSerializer(
            data=request.data, context={"request": request, "repository_pk": pk}
        )
        serializer.is_valid(raise_exception=True)
        remote = serializer.validated_data.get("remote", repository.remote)

        result = dispatch(
            tasks.synchronize,
            kwargs={"remote_pk": remote.pk, "repository_pk": repository.pk},
            exclusive_resources=[repository],
            shared_resources=[remote],
        )
        return core.OperationPostponedResponse(result, request)


class NpmRepositoryVersionViewSet(core.RepositoryVersionViewSet):
    """
    A ViewSet for a NpmRepositoryVersion represents a single Npm repository version.
    """

    parent_viewset = NpmRepositoryViewSet


class NpmDistributionViewSet(core.DistributionViewSet):
    """
    ViewSet for NPM Distributions.
    """

    endpoint_name = "npm"
    queryset = models.NpmDistribution.objects.all()
    serializer_class = serializers.NpmDistributionSerializer


class NpmUserLoginView(APIView):
    """
    ViewSet for NPM login.
    """

    authentication_classes = []
    permission_classes = []

    def put(self, request, reponame, username, *args, **kwargs):
        """
        Handle npm user login.
        """

        serializer = serializers.LoginSerializer(data=request.data)
        if serializer.is_valid():
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                # Associate login with repository
                try:
                    repository = models.NpmRepository.objects.get(name=reponame)

                    # Generate login token
                    token, created = models.AuthToken.objects.get_or_create(user=user)
                    if not created:
                        token.save()

                    return Response({"token": token.token}, status=status.HTTP_200_OK)
                except models.NpmRepository.DoesNotExist:
                    return Response({"error": "Repository not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)