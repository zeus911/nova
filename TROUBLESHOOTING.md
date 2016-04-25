# Common Instalation Issues

## `ImportError: No module named _markerlib`

Run `easy_install Distribute`

## Exception installing pycrypto

    env "CFLAGS=-I/usr/local/include -L/usr/local/lib" pip install pycrypto

## Creating a new CF stack (different name that service name) and nova cannot deploy

Ensure Docker image is the name of your nova.yml service_name (i.e. Using sbt-native-packager `packageName in Docker`)
