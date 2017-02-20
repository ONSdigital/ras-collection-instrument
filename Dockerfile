FROM openjdk
MAINTAINER David Carboni

WORKDIR /app
ADD build/libs/*.jar .

ENTRYPOINT java -Xdebug -Xrunjdwp:server=y,transport=dt_socket,address=8000,suspend=n -jar ./*.jar
