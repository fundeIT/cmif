#!/bin/sh

# xargs options
#   -t : show output commands
#   -n : number of arguments
# curl options
#   -C : continue 
#   -s : silent mode
#   -S : display message in case of error on silent mode
#   -O : use the same filename from origin
xargs -tn 1 curl -C - -SO --output-dir ./sources < urls.txt

cd sources
for f in *.zip
do
    unzip $f
    # rm -f $f
done
cd ..

cat sources/*2019*csv | sed 's/Persona Natural/N/' | sed 's/Persona Jurídica/J/' > sources/tmp.txt
cp sources/tmp.txt sources/*2019*csv
