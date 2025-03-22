from django.urls import path
from .viewsets import NpmUserLoginView, PackageViewSet

urlpatterns = [
    # NPM user login endpoint
    path('pulp/api/v3/npm/cli/<str:reponame>/-/user/org.couchdb.user:<str:username>', NpmUserLoginView.as_view(), name='npm-user-login'),

    # NPM package upload endpoint
    path('pulp/api/v3/npm/cli/<str:reponame>/<str:packagename>/', PackageViewSet.as_view(({'put': 'create'})), name='npm-package-upload'),
]