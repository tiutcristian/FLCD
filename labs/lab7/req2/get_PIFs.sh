#!/bin/bash

FLCD_BASE_PATH="$(cd $(dirname $0)/../.. && pwd)"
LAB7_PATH="${FLCD_BASE_PATH}/lab7"
LAB3_PATH="${FLCD_BASE_PATH}/lab3"
OUTPUT_DIR_BASE_PATH="${LAB3_PATH}/output"

cd ${LAB3_PATH}
./run_scanner.sh prog1.txt
./run_scanner.sh prog2.txt

cp ${OUTPUT_DIR_BASE_PATH}_prog1/pif.txt ${LAB7_PATH}/req2/prog1_PIF.txt
cp ${OUTPUT_DIR_BASE_PATH}_prog2/pif.txt ${LAB7_PATH}/req2/prog2_PIF.txt

./cleanup.sh