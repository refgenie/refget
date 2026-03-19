#!/bin/bash
# env/mutagen-setup.sh — Start mutagen sync for this project and its dependencies

if [ -z "$SYNC_REMOTE" ]; then
  echo "SYNC_REMOTE is not set. Set it in your env file to enable sync."
  echo "Example: export SYNC_REMOTE=user@host:/path/to/project"
  exit 0
fi

if [ -z "$PROJECT_NAME" ]; then
  PROJECT_NAME=$(basename "$PWD")
fi

# Sync the project itself
mutagen sync create \
  --name="${PROJECT_NAME}-pipeline" \
  --ignore=__pycache__ \
  --ignore="*.pyc" \
  --ignore="*.log" \
  --ignore=.git \
  . "$SYNC_REMOTE"

echo "Sync started: ${PROJECT_NAME}-pipeline → $SYNC_REMOTE"

# Sync dependencies for deployment
if [ -n "$DEPLOY_HOST" ] && [ -n "$DEPLOY_DIR" ]; then
  # gtars — local source synced to remote deploy dir
  GTARS_LOCAL="$HOME/Dropbox/workspaces/intervals/repos/gtars"
  if [ -d "$GTARS_LOCAL" ]; then
    mutagen sync create \
      --name="deploy-gtars" \
      --ignore=target \
      --ignore=__pycache__ \
      --ignore="*.pyc" \
      --ignore=.git \
      "$GTARS_LOCAL" "${DEPLOY_HOST}:${DEPLOY_DIR}/gtars"
    echo "Sync started: deploy-gtars → ${DEPLOY_HOST}:${DEPLOY_DIR}/gtars"
  else
    echo "Warning: $GTARS_LOCAL not found, skipping gtars sync"
  fi

  # refget — local source synced to remote deploy dir
  REFGET_LOCAL="$HOME/Dropbox/workspaces/refgenie/repos/refget"
  if [ -d "$REFGET_LOCAL" ]; then
    mutagen sync create \
      --name="deploy-refget" \
      --ignore=__pycache__ \
      --ignore="*.pyc" \
      --ignore=.git \
      "$REFGET_LOCAL" "${DEPLOY_HOST}:${DEPLOY_DIR}/refget"
    echo "Sync started: deploy-refget → ${DEPLOY_HOST}:${DEPLOY_DIR}/refget"
  else
    echo "Warning: $REFGET_LOCAL not found, skipping refget sync"
  fi
fi
