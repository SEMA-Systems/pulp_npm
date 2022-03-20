#!/bin/bash

# WARNING: DO NOT EDIT!
#
# This file was generated by plugin_template, and is managed by it. Please use
# './plugin-template --github pulp_npm' to update this file.
#
# For more info visit https://github.com/pulp/plugin_template

set -euv

# make sure this script runs at the repo root
cd "$(dirname "$(realpath -e "$0")")"/../../..

mkdir ~/.ssh
touch ~/.ssh/pulp-infra
chmod 600 ~/.ssh/pulp-infra
echo "$PULP_DOCS_KEY" > ~/.ssh/pulp-infra

echo "docs.pulpproject.org,8.43.85.236 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBGXG+8vjSQvnAkq33i0XWgpSrbco3rRqNZr0SfVeiqFI7RN/VznwXMioDDhc+hQtgVhd6TYBOrV07IMcKj+FAzg=" >> /home/runner/.ssh/known_hosts
chmod 644 /home/runner/.ssh/known_hosts

pip3 install packaging

export PYTHONUNBUFFERED=1
export DJANGO_SETTINGS_MODULE=pulpcore.app.settings
export PULP_SETTINGS=$PWD/.ci/ansible/settings/settings.py
export WORKSPACE=$PWD

eval "$(ssh-agent -s)" #start the ssh agent
ssh-add ~/.ssh/pulp-infra

python3 .github/workflows/scripts/docs-publisher.py --build-type $1 --branch $2

if [[ "$GITHUB_WORKFLOW" == "Npm changelog update" ]]; then
  # Do not build bindings docs on changelog update
  exit
fi

# Building python bindings
export PULP_URL="${PULP_URL:-https://pulp}"
VERSION=$(http $PULP_URL/pulp/api/v3/status/ | jq --arg plugin npm --arg legacy_plugin pulp_npm -r '.versions[] | select(.component == $plugin or .component == $legacy_plugin) | .version')
cd ../pulp-openapi-generator
rm -rf pulp_npm-client
./generate.sh pulp_npm python $VERSION
cd pulp_npm-client

# Adding mkdocs
find ./docs/* -exec sed -i 's/README//g' {} \;
cp README.md docs/index.md
sed -i 's/docs\///g' docs/index.md
find ./docs/* -exec sed -i 's/\.md//g' {} \;
cat >> mkdocs.yml << DOCSYAML
---
site_name: PulpNpm Client
site_description: Npm bindings
site_author: Pulp Team
site_url: https://docs.pulpproject.org/pulp_npm_client/
repo_name: pulp/pulp_npm
repo_url: https://github.com/pulp/pulp_npm
theme: readthedocs
DOCSYAML

pip install mkdocs pymdown-extensions

# Building the bindings docs
mkdocs build

# publish to docs.pulpproject.org/pulp_npm_client
rsync -avzh site/ doc_builder_pulp_npm@docs.pulpproject.org:/var/www/docs.pulpproject.org/pulp_npm_client/

# publish to docs.pulpproject.org/pulp_npm_client/en/{release}
rsync -avzh site/ doc_builder_pulp_npm@docs.pulpproject.org:/var/www/docs.pulpproject.org/pulp_npm_client/en/"$1"
