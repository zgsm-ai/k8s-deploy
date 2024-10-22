#!/bin/sh

FILES=`ls testdata/*.*`

echo FILES: $FILES

for file in $FILES; do
  if [[ -f "$file" ]]; then
    echo sh completion-faux.sh $file
    time sh completion-faux.sh $file
  fi
done
