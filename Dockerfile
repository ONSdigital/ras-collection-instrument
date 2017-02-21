FROM openjdk
MAINTAINER David Carboni

WORKDIR /app
ADD build/libs/*.jar .
ENV server.port 8080

ENTRYPOINT java -Xdebug -Xrunjdwp:server=y,transport=dt_socket,address=8000,suspend=n -jar ./*.jar
