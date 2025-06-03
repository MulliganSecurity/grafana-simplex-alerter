# Use an official Nix image as the base
FROM nixos/nix

# Enable flakes and experimental features
ENV NIX_CONFIG 'experimental-features = nix-command flakes'

# Copy the flake repo into the image
COPY . /app
WORKDIR /app

# Build the default package
RUN nix build .#defaultPackage.x86_64-linux

# Set the default command to run the built binary
CMD ["./result/bin/simplex-alerter"]
