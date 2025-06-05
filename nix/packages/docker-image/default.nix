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
in
pkgs.dockerTools.buildImage {
    name = "simplex-alerter";
    tag = "latest";
    copyToRoot = pkgs.buildEnv {
        name = "image-root";
        paths = [ env ];
        pathsToLink = [ "/bin" ];
    };
    config = {
        ExposedPorts."7898" = {};
        EntryPoint = ["${pkgs.${namespace}.simplex-alerter}/bin/simplex-alerter" ];
    };
}
