FROM nixos/nix

ENV NIX_CONFIG='experimental-features = nix-command flakes'

COPY . /app
WORKDIR /app

RUN nix build

ENTRYPOINT ["/app/result/bin/simplex-alerter"]
