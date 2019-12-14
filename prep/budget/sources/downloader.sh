#!/bin/sh

EP="estructura_presupuestaria.zip"
curl -o $EP "http://www.transparenciafiscal.gob.sv/downloads/zip/700-DINAFI-CT-2019-2002.zip"
unzip -f $EP
rm $EP
