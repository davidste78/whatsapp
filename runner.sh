#!/bin/bash
errors=-1
localCounter=0
globalCounter=0
while true; do
    	OUTPUT=$(ps x |grep -v grep |grep -c "stack")
	theTime=$(date +"%T")
	theDate=$(date +"%D")

    	if [ "${OUTPUT}" -eq "1" ]; then
		n=$((globalCounter%12))
        	if [ $n = 0 ]; then
        		echo $theDate $theTime "Process is running errors = $errors count = $localCounter globalCount = $globalCounter"
		fi
    	else
        	echo $theDate $theTime "Process is not running."
        	python yowsup/payChat/payChatAgent/stack.py &
        	let errors=errors+1
        	let localCounter=0
    	fi

    	sleep 5
    	let localCounter=localCounter+1
    	let globalCounter=globalCounter+1
done


