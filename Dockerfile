FROM openjdk
MAINTAINER David Carboni

WORKDIR /app
ADD build/libs/*.jar .

CMD java -jar ./*.jar
