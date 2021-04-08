#!/usr/bin/env bash
# Description: Auto-build docker container
# Developer: yuzhonghua
# Date: 2020-08-11 14:20

dockerfile_exists=`ls -a | grep Dockerfile`
image_exists=`docker images -a | grep automation/gastepo`
container_exists=`docker ps -a | grep gastepo`
function run_container() {
    if [[ -z "$container_exists" ]];then
        echo "Now create docker container named gastepo..."
        docker create --name gastepo -p 5000:5000 -v /Users/mayer/Software/Docker/Automation/gastepo/config:/Automation/Gastepo/Config -v /Users/mayer/Software/Docker/Automation/gastepo/data:/Automation/Gastepo/TestSuite/TestCase automation/gastepo
        if [[ -n $(docker ps -a | grep gastepo) ]];then
            echo "[Success]: docker container named gastepo has been created successfully!"
            echo "Now start docker container named gastepo..."
            docker start -ai gastepo
        else
            echo "[Failure]: docker container gastepo created failure, please try again!"
        fi
    else
        echo "[Attention]: docker container named gastepo has been existed!"
        echo "Now stop docker container named gastepo..."
        docker stop gastepo
        echo "[Success]: docker container stopped!"
        echo "Now start docker container named gastepo..."
        docker start -ai gastepo
    fi
}

if [[ -z "$image_exists" ]];then
    echo "docker image automation/gastepo is not exist, Now will try to build it..."
    if [[ -z "$dockerfile_exists" ]];then
        echo "[Warning]: Dockerfile is not found on current directory, Please check it first!"
        exit 0
    else
        docker build -f Dockerfile -t automation/gastepo .
        if [[ -n $(docker images -a | grep automation/gastepo) ]];then
            echo "[Success]: docker image automation/gastepo has been built successfully!"
            run_container
        else
            echo "[Failure]: docker image automation/gastepo build failure, please try again!"
        fi
    fi
else
   run_container
fi