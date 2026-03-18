#!/bin/bash
# Push refget stores to S3 via Rivanna.
#
# Clears stale GPG socket, connects with agent forwarding, decrypts
# credentials, and runs aws s3 sync.
#
# Usage (from laptop):
#   source env/remote-hpc.env
#   bash src/push_to_s3.sh vgp
#   bash src/push_to_s3.sh ref
#   bash src/push_to_s3.sh pangenome
#   bash src/push_to_s3.sh all
#   bash src/push_to_s3.sh vgp --dry-run

set -euo pipefail

STORE=${1:-all}
DRYRUN_FLAG="${2:-}"

: "${VGP_STORE_PATH:?Set VGP_STORE_PATH in env}"
: "${REF_STORE_PATH:?Set REF_STORE_PATH in env}"
: "${PANGENOME_STORE_PATH:?Set PANGENOME_STORE_PATH in env}"
: "${VGP_S3_PATH:?Set VGP_S3_PATH in env}"
: "${REF_S3_PATH:?Set REF_S3_PATH in env}"
: "${PANGENOME_S3_PATH:?Set PANGENOME_S3_PATH in env}"

# Clear stale GPG socket, then connect with forwarding
ssh riva1 "rm -f /run/user/\$(id -u)/gnupg/S.gpg-agent"

ssh riva1_gpg "
  source /etc/profile.d/modules.sh
  module load awscli

  export AWS_ACCESS_KEY_ID=\$(pass databio/refgenie/s3_access_key_id)
  export AWS_SECRET_ACCESS_KEY=\$(pass databio/refgenie/s3_secret_access_key)

  if [ \"$STORE\" = \"vgp\" ] || [ \"$STORE\" = \"all\" ]; then
    echo 'Pushing VGP store to $VGP_S3_PATH ...'
    aws s3 sync '$VGP_STORE_PATH' '$VGP_S3_PATH' $DRYRUN_FLAG
    echo 'VGP push complete.'
  fi

  if [ \"$STORE\" = \"ref\" ] || [ \"$STORE\" = \"all\" ]; then
    echo 'Pushing ref store to $REF_S3_PATH ...'
    aws s3 sync '$REF_STORE_PATH' '$REF_S3_PATH' $DRYRUN_FLAG
    echo 'Ref push complete.'
  fi

  if [ \"$STORE\" = \"pangenome\" ] || [ \"$STORE\" = \"all\" ]; then
    echo 'Pushing pangenome store to $PANGENOME_S3_PATH ...'
    aws s3 sync '$PANGENOME_STORE_PATH' '$PANGENOME_S3_PATH' $DRYRUN_FLAG
    echo 'Pangenome push complete.'
  fi

  echo 'Done!'
"
