# Pull-Through Cache

The pull-through cache feature allows Pulp to act as a cache for any package from a remote source.

## Create remote
  ```bash
  curl -X POST $BASE_ADDR/pulp/api/v3/remotes/npm/npm/ -d '{"name": "foo", "url": "http://some.url/somewhere/"}' -H 'Content-Type: application/json'
  ```

## Create distribution
  ```bash
  curl -X POST $BASE_ADDR/pulp/api/v3/distributions/npm/npm/ -d '{"name": "foo", "base_path": "npm/foo", "remote": "$REMOTE_HREF"}' -H 'Content-Type: application/json'
  ```

## Install NPM package
  ```bash
  npm install --registry $BASE_ADDR/pulp/content/npm/foo react@19.0.0
  ```
