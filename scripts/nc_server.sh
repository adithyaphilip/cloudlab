#! /bin/bash
for i in $(seq 1 $1);
do 
nc -l $(( 6000 + $i )) > /dev/null &
done
