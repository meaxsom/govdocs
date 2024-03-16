#!/bin/bash

source .env/vars.sh

theWebPort=$WEB_PORT
theDBPort=$DB_PORT
theWorkDirectory=$WORK_DIR
theDataDirectory=$DATA_DIR

while getopts ":m:p:d:w:" opt; do
	case $opt in
		m ) theMount=$OPTARG 
			;;
		d ) theDBPort=$OPTARG
			;;
		p ) theWebPort=$OPTARG
			;;
		w ) theWorkDirectory=$OPTARG
			;;
		\? ) echo 'usage args'
			 exit 1
			 ;;
    	: ) echo "Invalid option: $OPTARG requires an argument" 1>&2
      		;;	
      esac
done

shift $(($OPTIND - 1))

theCommand=$1
theName=$2

if [ "$theCommand" = "start" ]; then
	docker run -d --name=$theName -p "$theWebPort:7474" -p "$theDBPort:7687" -v "$theDataDirectory:/data:Z" -v "$theWorkDirectory:/workspaces/govdocs:Z" --env NEO4J_AUTH=neo4j/neo4j_test neo4j:latest
elif [ "$theCommand" = "stop" ]; then
	docker container stop $theName
	docker container rm $theName
elif [ "$theCommand" = "sh" ]; then
	docker exec -it $theName bash
elif [ "$theCommand" = "log" ]; then
	docker logs $(sudo docker ps -aq --filter name=index.js) $theName
elif [ "$theCommand" = "build" ]; then
	docker build -t neo4j:latest .
else
	echo "command $theCommand not supported"
fi
