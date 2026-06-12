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

  simplex-chat = inputs.simplex.packages.${pkgs.system}."exe:simplex-chat";

  alerter = common.pythonSet.mkVirtualEnv common.package_name common.workspace.deps.default;

in
pkgs.dockerTools.buildLayeredImage {
  name = "simplex-alerter";
  tag = "latest";

  # Full Nix store closure is included as layers — simplex-chat finds its
  # exact haskell.nix bootstrap glibc/gmp at their hardcoded store paths.
  contents = [ alerter simplex-chat pkgs.dockerTools.fakeNss ];

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
