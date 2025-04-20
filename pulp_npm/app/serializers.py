from gettext import gettext as _
from rest_framework import serializers

from pulpcore.plugin import models as core_models
from pulpcore.plugin import serializers as core_serializers

from . import models


class PackageSerializer(core_serializers.SingleArtifactContentUploadSerializer):
    """
    Serializer for NPM Packages.
    """

    name = serializers.CharField()
    version = serializers.CharField()
    relative_path = serializers.CharField()
    dependencies = serializers.JSONField()

    class Meta:
        fields = core_serializers.SingleArtifactContentUploadSerializer.Meta.fields + (
            "name",
            "version",
            "relative_path",
            "dependencies",
        )
        model = models.Package


class NpmRemoteSerializer(core_serializers.RemoteSerializer):
    """
    A Serializer for NpmRemote.

    Add any new fields if defined on NpmRemote.
    Similar to the example above, in PackageSerializer.
    Additional validators can be added to the parent validators list

    For example::

    class Meta:
        validators = core_serializers.RemoteSerializer.Meta.validators + [myValidator1, ...]

    By default the 'policy' field in core_serializers.RemoteSerializer only validates the choice
    'immediate'. To add on-demand support for more 'policy' options, e.g. 'streamed' or 'on_demand',
    re-define the 'policy' option as follows::

    """

    policy = serializers.ChoiceField(
        help_text="The policy to use when downloading content. The possible values include: "
        "'immediate', 'on_demand', and 'streamed'. 'immediate' is the default.",
        choices=core_models.Remote.POLICY_CHOICES,
        required=False,
    )

    class Meta:
        fields = core_serializers.RemoteSerializer.Meta.fields
        model = models.NpmRemote


class NpmRepositorySerializer(core_serializers.RepositorySerializer):
    """
    A Serializer for NpmRepository.

    Add any new fields if defined on NpmRepository.
    Similar to the example above, in PackageSerializer.
    Additional validators can be added to the parent validators list

    For example::

    class Meta:
        validators = core_serializers.RepositorySerializer.Meta.validators + [myValidator1, ...]
    """

    class Meta:
        fields = core_serializers.RepositorySerializer.Meta.fields
        model = models.NpmRepository


class NpmRepositorySyncSerializer(core_serializers.RepositorySyncURLSerializer):
    """
    A Serializer for NpmRepositorySync.

    Extends RepositorySyncURLSerializer to add the 'sync_deps' field for controlling dependency sync.
    Default is False.

    Example::

        class Meta:
            validators = core_serializers.RepositorySyncURLSerializer.Meta.validators + [myCustomValidator, ...]
    """

    sync_deps = serializers.BooleanField(default=False, required=False)


class NpmDistributionSerializer(core_serializers.DistributionSerializer):
    """
    Serializer for NPM Distributions.
    """

    remote = core_serializers.DetailRelatedField(
        required=False,
        help_text=_("Remote that can be used to fetch content when using pull-through caching."),
        view_name_pattern=r"remotes(-.*/.*)?-detail",
        queryset=core_models.Remote.objects.all(),
        allow_null=True,
    )

    class Meta:
        fields = core_serializers.DistributionSerializer.Meta.fields + ("remote",)
        model = models.NpmDistribution


class LoginSerializer(serializers.Serializer):
    """
    Serializer for NPM Login.
    """

    name = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100)
    email = serializers.EmailField()