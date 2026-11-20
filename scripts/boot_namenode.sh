#!/usr/bin/env bash
set -Eeuo pipefail

name_dir=/tmp/hadoop-root/dfs/name

if [[ ! -f "$name_dir/current/VERSION" ]]; then
    # Never format an existing or partially initialized namespace.
    if [[ -n "$(find "$name_dir" -mindepth 1 -print -quit)" ]]; then
        echo "Error: NameNode directory is not empty but has no current/VERSION; refusing to format." >&2
        exit 1
    fi
    echo "Initializing empty NameNode volume..."
    hdfs namenode -format -nonInteractive
fi

exec hdfs namenode
