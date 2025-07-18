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
  simplex-chat = pkgs.stdenv.mkDerivation {
    name = "simplex-chat";
    version = "v6.3.4";
    src = pkgs.fetchurl {
      url = "https://github.com/simplex-chat/simplex-chat/releases/download/v6.3.4/simplex-chat-ubuntu-24_04-x86-64";
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
  start_services = pkgs.writeScriptBin "start-script.sh" ''
    /bin/simplex-chat -y -p 7897 -d /alerterconfig/chatDB &
    sleep 60
    /bin/simplex-alerter -b 0.0.0.0:7898 -c /alerterconfig/config.yml -e 127.0.0.1:7897 '';

in
pkgs.dockerTools.buildImage {
  name = "simplex-alerter";
  tag = "latest";
  fromImage = ubuntu;
  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [
      pkgs.${namespace}.simplex-alerter
      simplex-chat
      start_services
    ];
    pathsToLink = [ "/bin" ];
  };
  config = {
    ExposedPorts."7898" = { };
    EntryPoint = [
      "bash"
      "start-script.sh"
    ];
  };
}
