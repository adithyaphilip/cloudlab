#! /bin/bash

for i in $(seq 1 $1)
do python3 python_send.py $2 $(( 6000+$i )) &
done
