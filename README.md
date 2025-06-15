# How to build

## Using nix

### standalone alerter

~~~
nix build .#simplex-alerter
~~~

### docker image

~~~
nix build .#docker-image
~~~

## Using docker

~~~
docker build . -t builder
docker run --rm -v $(pwd):/src builder
docker load < simplex-alerter.tar.gz
~~~

# How to run

## Docker
- install the [simplex-chat](https://github.com/simplex-chat/simplex-chat/releases) CLI client
- create a folder for your configuration file
- start the client to initialize it and set your displayName (simplex-chat -d /mychatfolder/chatDB)
- copy your config file to a different folder (eg a read only one):
- docker run -v /mychatfolder:/simplex -v myconffolder:/alerterconfig
