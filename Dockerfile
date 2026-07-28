FROM nixos/nix

ENV NIX_CONFIG='experimental-features = nix-command flakes'

RUN git config --global --add safe.directory /src

WORKDIR /src

CMD nix build .\#docker-image && cp result simplex-alerter.tar.gz
