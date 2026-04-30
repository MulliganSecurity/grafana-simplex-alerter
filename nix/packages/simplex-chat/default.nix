{
  # Snowfall Lib provides a customized `lib` instance with access to your flake's library
  # as well as the libraries available from your flake's inputs.
  # You also have access to your flake's inputs.
  inputs,
  pkgs,
  ...
}:

let
  # Get the upstream simplex-chat package from the simplex flake
  upstream = inputs.simplex.packages.${pkgs.stdenv.hostPlatform.system}."exe:simplex-chat";
in
pkgs.stdenv.mkDerivation {
  pname = "simplex-chat";
  version = upstream.version or "unknown";

  dontUnpack = true;
  dontBuild = true;

  installPhase = ''
    mkdir -p $out/bin
    ln -s ${upstream}/bin/simplex-chat $out/bin/simplex-chat
  '';

  # Support overrideAttrs with default-launch-options for module compatibility
  # This maintains compatibility with modules/nixos/simplex/default.nix
  passthru = {
    inherit upstream;
    overrideAttrs =
      f:
      let
        attrs = f { };
        launch-opts = attrs.default-launch-options or "";
      in
      if launch-opts == "" then
        upstream
      else
        pkgs.writeShellScriptBin "simplex-chat" ''
          exec ${upstream}/bin/simplex-chat ${launch-opts} "$@"
        '';
  };

  meta =
    upstream.meta or {
      description = "SimpleX Chat - private and secure messaging client";
      homepage = "https://simplex.chat";
    };
}
