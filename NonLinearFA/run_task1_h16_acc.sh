#!/bin/bash

while IFS=, read size h trace interest lr;
do
	echo --n="$size" --hidden="$h" --trace_type="$trace" --intrst="$interest" --lr="$lr" --env="gridWorld"
	python drl_data.py --n="$size" --hidden="$h" --trace_type="$trace" --intrst="$interest" --lr="$lr" --env="gridWorld" --episodes=150 --t_seeds=20
done < task1_h16_acc.txt