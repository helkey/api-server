
# Parking Garage
This is a docker-based service for operating a parking garage ticketing service. This is an HTTP-based API for
- deciding if cars can be parked within the garage (that is, there is enough space to hold the additional car),
- calculating the cost of cars leaving the garage, and
- keeping status of the available space as cars enter/exit the garage.

## Description
This solution is designed to support highly concurrent connections, by separating out most of the functions in thread-safe
code, and making the non-thread-safe code as simple and fast as possible. 

The shared object uses a simple three-array lookup to allocate all of the parking spaces, with the Python
Global Interpreter Lock (GIL) used to restrict shared data access. All of the floor/row/space conversion/checking 
is in thread-safe code.

## Further Work
In order to make this approach handle higher load than the present implemention, one of the steps would make to 
the main shared computation faster by writing this small section of code in Cython or C. 
Also the three-array lookup (for the three types of vehicles) could be broken up into three separate data objects, 
which could also approximately triple the maximum number of connections.

## Build
The application is packaged as a [Docker app](https://stackabuse.com/dockerizing-python-applications/).
```
FROM ubuntu:16.04
MAINTAINER Roger Helkey "roger@helkey.org"
RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev
WORKDIR /
COPY ./server.py /
COPY ./garage.py /
ENTRYPOINT [ "python3" ]
CMD [ "server.py" ]
```

```sh
docker build -t garage:latest .
docker run --name garageapp -p 8080:8080 garage:latest
```

## Testing
The function `garage_test.py` tests most of the functionality of the garage operation,
and demonstrates key error detection and handling. Some key additional tests are indicated
in comments, but not implemented.

## Logging
Due to time constraints, logging has been sadly neglected in this demonstration.
