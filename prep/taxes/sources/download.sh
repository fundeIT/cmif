#!/bin/sh

wget -ci urls.txt

for f in *.zip
do
    unzip $f
done
