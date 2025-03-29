# Synchronize Repository

Users can populate their repositories with content from an external sources by syncing
their repository.

## Create repository
```bash
curl -X POST $BASE_ADDR/pulp/api/v3/repositories/npm/npm/ -d '{"name": "foo"}' -H 'Content-Type: application/json'
```

## Create remote
```bash
curl -X POST $BASE_ADDR/pulp/api/v3/remotes/npm/npm/ -d '{"name": "react-0.5.2", "url": "https://registry.npmjs.org/react/0.5.2"}' -H 'Content-Type: application/json'
```

## Sync repository

Use the remote object to kick off a synchronize task by specifying the repository to
sync with. You are telling pulp to fetch content from the remote and add to the repository:

```bash
curl -X POST $BASE_ADDR/$REPO_HREF/sync/ -d '{"remote": "$REMOTE_HREF"}' -H 'Content-Type: application/json'
```

## Create distribution
  ```bash
  curl -X POST $BASE_ADDR/pulp/api/v3/distributions/npm/npm/ -d '{"name": "foo", "base_path": "npm/foo", "repository": "$REPO_HREF"}' -H 'Content-Type: application/json'
  ```

## Install NPM package
  ```bash
  npm install --registry $BASE_ADDR/pulp/content/npm/foo react@0.5.2
  ```