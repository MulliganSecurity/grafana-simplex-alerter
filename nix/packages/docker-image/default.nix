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

  # Get simplex-chat from upstream flake (v6.4.10)
  simplex-chat = inputs.simplex-chat.packages.${pkgs.system}."exe:simplex-chat";

  # Python alerter virtualenv
  alerter = common.pythonSet.mkVirtualEnv common.package_name common.workspace.deps.default;

  # Runtime dependencies needed by simplex-chat
  runtimeDeps = with pkgs; [
    zlib        # libz
    openssl     # openssl
    gmp         # gmp
    glibc       # C runtime
  ];

in
pkgs.dockerTools.buildImage {
  name = "simplex-alerter";
  tag = "latest";

  # Building from scratch (no Ubuntu base)
  copyToRoot = pkgs.buildEnv {
    name = "image-root";
    paths = [
      alerter
      simplex-chat
      # Include runtime dependencies and basic utilities
      pkgs.coreutils      # Basic utilities
      pkgs.bash           # Shell for entrypoint
    ] ++ runtimeDeps;
    pathsToLink = [ "/bin" "/lib" "/lib64" ];  # Include library paths
  };

  config = {
    ExposedPorts."7898" = { };
    Env = [
      # Set library path for runtime linking
      "LD_LIBRARY_PATH=/lib:/lib64"
    ];
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
