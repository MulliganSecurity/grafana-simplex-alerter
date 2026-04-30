{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    snowfall-lib = {
      url = "github:snowfallorg/lib";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        nixpkgs.follows = "nixpkgs";
      };
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
        nixpkgs.follows = "nixpkgs";
      };
    };

    fb-observlib.url = "github:ForgottenBeast/observlib";

    simplex = {
      url = "github:simplex-chat/simplex-chat/v6.4.11";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    simplexmq-src = {
      url = "github:simplex-chat/simplexmq/v6.4.4";
      flake = false;
    };

    haskell-nix = {
      url = "github:input-output-hk/haskell.nix/armv7a";
    };
  };

  outputs =
    inputs:

    inputs.snowfall-lib.mkFlake {
      inherit inputs;
      src = ./.;
      snowfall = {
        root = ./nix;
        namespace = "simplex-alerter";
      };

      alias = {
        shells.default = "dev";
        packages.default = "simplex-alerter";
      };
    };

}
