#!/bin/sh

FILES=`ls testdata/*.*`
PORTS=(32320 32321 32324)

echo FILES: $FILES
echo PORTS: $PORTS

for file in $FILES; do
  if [[ -f "$file" ]]; then
    echo $file
    for port in "${PORTS[@]}"; do
      echo sh completion-ad.sh -p $port -f $file
      time sh completion-ad.sh -p $port -f $file
    done
  fi
done
