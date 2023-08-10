#!/bin/sh
python /home/evgenii/plants_final/capture.py &
pid1=$!
python /home/evgenii/plants_final/server.py &
pid2=$!

wait $pid1 $pid2

