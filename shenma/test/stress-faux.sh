#!/bin/sh

FILES=`ls testdata/*.*`

echo FILES: $FILES

for file in $FILES; do
  if [[ -f "$file" ]]; then
    for i in {1..10}
    do
      echo sh completion-faux.sh $file
      sh completion-faux.sh $file &
    done
  fi
done

wait
