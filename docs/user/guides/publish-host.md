# Publish and Host

Users can populate their repositories with content from self-published npm packages.

## Create repository
```bash
curl -X POST $BASE_ADDR/pulp/api/v3/repositories/npm/npm/ -d '{"name": "foo"}' -H 'Content-Type: application/json'
```

## Create distribution

To host a repository, (which makes it consumable by a package manager),
users create a distribution which will serve the associated repository 
at `/pulp/content/{distribution.base_path}`:

```bash
curl -X POST $BASE_ADDR/pulp/api/v3/distributions/npm/npm/ -d '{"name": "foo", "base_path": "npm/foo", "repository": "$REPO_HREF"}' -H 'Content-Type: application/json'
```

## Publish NPM package
Login to repository (legacy login only):
  ```bash
  npm login --registry=$BASE_ADDR/pulp/api/v3/npm/cli/foo/
  ```

Publish NPM package:
  ```bash
  npm publish --registry=$BASE_ADDR/pulp/api/v3/npm/cli/foo/
  ```

## Install NPM package
  ```bash
  npm install --registry $BASE_ADDR/pulp/content/npm/foo $PKG_NAME
  ```