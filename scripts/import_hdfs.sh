#!/usr/bin/env bash
set -Eeuo pipefail

local_dir="${XKCD_LOCAL_RAW_DIR:?missing XKCD_LOCAL_RAW_DIR}"
hdfs_dir="${XKCD_HDFS_RAW_DIR:?missing XKCD_HDFS_RAW_DIR}"

# Proof local dir
if [[ ! -d "$local_dir" ]]; then
    echo "Error: local dir is missing: $local_dir" >&2
    exit 1
fi

# wait untill hdfs is available
ready=0

for attempt in $(seq 1 60); do
    if hdfs dfsadmin -report 2>/dev/null | \
        grep -Eq 'Live datanodes \([1-9][0-9]*\):'; then
            ready=1
            break
    fi

    echo "Waiting for NameNode/DataNode ($attempt/60) ..."
    sleep 2
done


if [[ "$ready" -ne 1 ]]; then
    echo "Error: No active DataNode found." >&2
    exit 1
fi

# create HDFS dir
hdfs dfs -mkdir -p "$hdfs_dir"

shopt -s nullglob
found=0

# Go through every local year 
for year_dir in "$local_dir"/*/; do
    year="$(basename "$year_dir")"

    # only valid years
    if [[ ! "$year" =~ ^[0-9]{4}$ ]]; then
        echo "Skipp folder: $year"
        continue
    fi

    files=("$year_dir"/*.json)

    if (( ${#files[@]} == 0 )); then
        continue
    fi

    found=1

    # create hdfs year folder
    dest="$hdfs_dir/$year"

    hdfs dfs -mkdir -p "$dest"
    # copy files to hdfs
    hdfs dfs -put -f "${files[@]}" "$dest/"
    echo "Imported ${#files[@]} Comics from $year"
done

if (( found == 0 )); then
    echo "No JSON-file found!" >&2
    exit 1
fi

echo "Finished Import"

hdfs dfs -ls "$hdfs_dir"