#!/bin/bash
source ~/anaconda3/bin/activate
search_dir=..
for entry in "$search_dir"/neat*.y*
do
  echo "$entry"
  neat run --config $entry
done
