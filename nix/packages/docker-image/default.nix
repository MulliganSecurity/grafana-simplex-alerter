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
    version = "v6.4.6";
    src = pkgs.fetchurl {
      url = "https://github.com/simplex-chat/simplex-chat/releases/download/${version}/simplex-chat-ubuntu-24_04-x86_64";
      hash = "sha256-r/I4i25tOrSATSenOhuAbEkBjvQs6LPu/DKWK63JRlw=";
    };
    dontBuild = true;
    dontUnpack = true;
    installPhase = "mkdir -p $out/bin; cp $src $out/bin/simplex-chat; chmod +x $out/bin/simplex-chat";
  };
  ubuntu = pkgs.dockerTools.pullImage {
    imageName = "ubuntu";
    imageDigest = "sha256:9b61739164b58f2263067bd3ab31c7746ded4cade1f9d708e6f1b047b408a470";
    finalImageName = "ubuntu";
    sha256 = "sha256-PvB8IMmuvwewsnQYjcfGB8eaAkYqf8aaIJyQ66XgJ+M=";
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
