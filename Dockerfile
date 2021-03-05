# Automation Dockerfile

FROM python:3.7.4
MAINTAINER zhonghua2040@163.com

# set default shell
SHELL ["/bin/bash", "-c"]

# set login user
USER root

# expose container port
EXPOSE 5000/tcp 5001/tcp 5002/tcp

# set param variables
ARG Project

# set environment variables
ENV Project ${Project:-GastepoApiAutomation}

# set workdir
WORKDIR /Automation/$Project

# copy and extract jdk8
ADD ./Docker/jdk8.gz /software/jdk8

# copy and extract nodejs
ADD ./Docker/nodejs.xz /software/nodejs

# copy and extract allure plugin
ADD ./Docker/allure.tgz /software/allure

# copy project to workdir
COPY ./Gastepo .

# set PATH environment
RUN echo -e "JAVA_HOME=/software/jdk8/jdk1.8.0_211\nJRE_HOME=\$JAVA_HOME/jre\nCLASSPATH=.:\$JAVA_HOME/lib:\$JRE_HOME/lib\nPATH=$PATH:\$JAVA_HOME/bin:\$JRE_HOME/bin:/software/nodejs/node-v12.18.1-linux-x64/bin:/software/allure/package/bin" >> /etc/profile \
	&& source /etc/profile \
	&& echo $PATH

# link nodejs and sync localtime
RUN ln -s /software/nodejs/node-v12.18.1-linux-x64 /usr/bin/node \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo 'Asia/Shanghai' >/etc/timezone

# install python dependency packages
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# move automation shell and change mode
RUN mv ./Docker/start.sh . \
    && chmod 777 start.sh

# execute automation shell
CMD ["./start.sh"]
