FROM nixos/nix

ENV NIX_CONFIG='experimental-features = nix-command flakes'

RUN git config --global --add safe.directory /src
RUN printf 'substituters = https://cache.nixos.org https://cache.iog.io\ntrusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY= hydra.iohk.io:f/Ea+s+dFdN+3Y/G+FDgSq+a5NEWhJGzdjvKNGv0/EQ=\n' >> /etc/nix/nix.conf

WORKDIR /src

CMD nix build .\#docker-image && cp result simplex-alerter.tar.gz
