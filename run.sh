#!/bin/sh
python /home/evgenii/plants_final/capture.py &
pid1=$!
python /home/evgenii/plants_final/server.py &
pid2=$!
python /home/evgenii/plants_final/weather_checker.py &
pid3=$!

wait $pid1 $pid2 $pid3

