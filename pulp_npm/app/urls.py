from django.urls import path, re_path
from .viewsets import NpmUserLoginView, PackageViewSet

urlpatterns = [
    # NPM user login endpoint
    path(
        'pulp/api/v3/npm/cli/<str:reponame>/-/user/org.couchdb.user:<str:username>',
        NpmUserLoginView.as_view(),
        name='npm-user-login',
    ),

    # NPM scoped/unscoped package upload
    re_path(
        r'^pulp/api/v3/npm/cli/(?P<reponame>[^/]+)/(?P<packagename>.+)/$',
        PackageViewSet.as_view({'put': 'create'}),
        name='npm-package-upload',
    ),
]