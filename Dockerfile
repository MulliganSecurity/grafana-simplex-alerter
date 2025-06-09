FROM nixos/nix

ENV NIX_CONFIG='experimental-features = nix-command flakes'

WORKDIR /src

CMD nix build .\#docker-image
