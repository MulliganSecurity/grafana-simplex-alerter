{
  # Snowfall Lib provides a customized `lib` instance with access to your flake's library
  # as well as the libraries available from your flake's inputs.
  lib,
  # You also have access to your flake's inputs.
  inputs,

  # The namespace used for your flake, defaulting to "internal" if not set.

  # All other arguments come from NixPkgs. You can use `pkgs` to pull packages or helpers
  # programmatically or you may add the named attributes as arguments here.
  pkgs,
  namespace,
  ...
}:

let
  common = import ./../../uv_setup.nix {
    inherit inputs lib pkgs;
    package_name = namespace;
  };
  env = common.pythonSet.mkVirtualEnv common.package_name common.workspace.deps.default;
  simplex-chat = pkgs.stdenv.mkDerivation rec {
    name = "simplex-chat";
    version = "v6.3.4";
    src = pkgs.fetchurl {
      url = "https://github.com/simplex-chat/simplex-chat/releases/download/${version}/simplex-chat-ubuntu-24_04-x86-64";
      hash = "sha256-8A2jqRaRYy7okGDD8Q8Gx7ZttxXhcSDsFRKvvdbyZHc=";
    };
    dontBuild = true;
    dontUnpack = true;
    installPhase = "mkdir -p $out/bin; cp $src $out/bin/simplex-chat; chmod +x $out/bin/simplex-chat";
  };
  ubuntu = pkgs.dockerTools.pullImage {
    imageName = "ubuntu";
    imageDigest = "sha256:b59d21599a2b151e23eea5f6602f4af4d7d31c4e236d22bf0b62b86d2e386b8f";
    finalImageName = "ubuntu";
    sha256 = "sha256-YdbJusA6R6SRxpoMZzQI/F0XoIw2cQKlz4FMvbAHGoA=";
  };
  alerter = common.pythonSet.mkVirtualEnv common.package_name common.workspace.deps.default;

in
pkgs.dockerTools.buildImage {
  name = "simplex-alerter";
  tag = "latest";
  fromImage = ubuntu;
  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [
      alerter
      simplex-chat
    ];
    pathsToLink = [ "/bin" ];
  };
  config = {
    ExposedPorts."7898" = { };
    EntryPoint = [
      "/bin/simplex-alerter"
      "-b"
      "0.0.0.0:7898"
      "-c"
      "/alerterconfig/config.yml"
      "-e"
      "127.0.0.1:7897"
    ];
  };
}
