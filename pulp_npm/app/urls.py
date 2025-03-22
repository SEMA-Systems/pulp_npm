from django.urls import path
from .viewsets import NpmUserLoginView

urlpatterns = [
    # NPM user login endpoint
    path('pulp/api/v3/npm/cli/<str:reponame>/-/user/org.couchdb.user:<str:username>', NpmUserLoginView.as_view(), name='npm-user-login'),
]