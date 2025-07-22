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
  nixos = pkgs.dockerTools.pullImage {
    imageName = "nixos/nix";
    imageDigest = "sha256:8c144c6c37184fe03fd7fed740c6eeb2ecfd801d6e34a6aba4e38f1c8d10de3e";
    finalImageName = "nixos/nix";
    sha256 = "sha256-WeFkiLfv+UX+ZNJYjO2TGHb357xJFP7zBcmVn/jVNXQ=";
  };


in
pkgs.dockerTools.buildImage {
  name = "simplex-alerter";
  tag = "latest";
  fromImage = nixos;
  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [
      pkgs.${namespace}.simplex-alerter
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
