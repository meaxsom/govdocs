FROM neo4j:5.17.0-bullseye

RUN apt update
RUN apt-get update
RUN apt-get -y install git
RUN apt-get -y install python3
RUN apt-get -y install python3-pip
RUN pip3 install boto3
RUN pip3 install neo4j
RUN pip3 install python-dotenv
RUN pip3 install typeid-python

#RUN groupadd -g 10001 webmaster
#RUN useradd -u 3004 -g 10001 prog
#RUN chmod a+rwx /var/lib/neo4j/import

COPY conf/neo4j.conf /var/lib/neo4j/conf

COPY bin/bootstrap.sh /etc/bootstrap.sh
RUN chown root:root /etc/bootstrap.sh && \
    chmod 777 /etc/bootstrap.sh

RUN mkdir -p /workspaces/govdocs

EXPOSE 7474
EXPOSE 7687

ENV NEO4J_AUTH=neo4j/neo4j_test

# Set the bootstrap script on container run
ENV BOOTSTRAP /etc/bootstrap.sh
ENTRYPOINT ["/etc/bootstrap.sh"]
