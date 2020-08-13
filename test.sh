#!/bin/bash

for file in test_data/*.lsp; do
    echo ===================================================
    echo $file:
    cat $file
    echo ---------------------------------------------------
    cat $file.output
    echo ----
	python mini_lisp.py $file
	echo ---------------------------------------------------
	read -p "Press Enter to continue...."
done
