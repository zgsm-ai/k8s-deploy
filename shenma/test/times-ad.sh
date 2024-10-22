#!/bin/sh

FILES=`ls testdata/*.*`
PORTS=(32326 32329)

echo FILES: $FILES
echo PORTS: $PORTS

for file in $FILES; do
  if [[ -f "$file" ]]; then
    echo $file
    for port in "${PORTS[@]}"; do
      echo sh completion-ad.sh $port $file
      time sh completion-ad.sh $port $file
    done
  fi
done
