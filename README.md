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
~~~
docker run -p 127.0.0.1:7898:7898 -v /my/alerter/data:/alerterconfig --rm simplex-alerter 
~~~

# Tip the dev

85DnG7JvsRCT5FJXKkFstm75Pysani2Q1LMftG4sVLkTWEDqnDcHRqiTYEKzSx1FPvYeJkfXqD7uiXhNxgbYWWij1iyt7rd
