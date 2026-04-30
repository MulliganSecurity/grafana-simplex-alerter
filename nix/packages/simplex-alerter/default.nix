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
  simplex-chat = inputs.simplex.packages.${pkgs.system}."exe:simplex-chat";

  externalDeps = [
    simplex-chat
  ];

in
(common.pythonSet.mkVirtualEnv common.package_name common.workspace.deps.default).overrideAttrs
  (old: {
    nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ pkgs.makeWrapper ];
    buildInputs = (old.buildInputs or [ ]) ++ externalDeps;

    postFixup =
      (old.postFixup or "")
      + ''
        for exe in $out/bin/*; do
          if [[ -f "$exe" && -x "$exe" ]]; then
            wrapProgram "$exe" \
              --prefix PATH : ${lib.makeBinPath externalDeps}
          fi
        done
      '';
  }

  )
