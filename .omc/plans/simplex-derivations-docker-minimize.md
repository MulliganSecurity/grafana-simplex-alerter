# Plan: Copy Simplex Derivations and Minimize Docker Image

**Status:** Approved
**Source:** ralplan consensus (Planner → Architect → Critic)
**Date:** 2026-04-30

---

## Decision

Copy `simplex-chat` and `simplexmq` package derivations from `../machines_conf` into this flake, unify on `inputs.simplex` (v6.4.11), and minimize the scratch Docker image by removing `bash` and `coreutils`.

## Decision Drivers

1. `machines_conf` is at simplex-chat v6.4.11; `simplex-alerter` is at v6.4.10 — copy unifies versions
2. The `simplex-chat` wrapper adds an `overrideAttrs` passthru shim for NixOS module compatibility
3. Docker image currently includes `bash` and `coreutils` which are not required by the alerter entrypoint

## Alternatives Considered

- **Keep upstream flake + copy derivations without wiring them up** — rejected: pointless if nothing references the local packages
- **Use `pkgs.simplex-alerter.simplex-chat` (snowfall namespace)** — rejected: potential evaluation ordering risk; direct `inputs.simplex` reference is safer and explicit

## Consequences

- `flake.lock` will update: `simplex-chat` entry replaced by `simplex` (v6.4.11), plus new `simplexmq-src` and `haskell-nix` entries
- `haskell-nix` adds a second nixpkgs evaluation (pinned to nixpkgs-2305) — increased eval time accepted for `simplexmq` derivation
- Docker image loses `bash` and `coreutils` — no interactive shell in container; debugging requires `docker cp` or exec into the process namespace

## Follow-ups

- Run `nix flake update simplex` when upgrading simplex-chat in the future (no longer `simplex-chat`)
- `simplexmq` package is available in the flake but not pulled into the Docker image; add it if SMP server functionality is ever needed in the container

---

## Task Flow

### Step 1: Update flake.nix inputs

Remove:
```nix
simplex-chat = {
  url = "github:simplex-chat/simplex-chat/v6.4.10";
  inputs.nixpkgs.follows = "nixpkgs";
};
```

Add:
```nix
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
```

Branch: `chore/simplex-derivations`

### Step 2: Create nix/packages/simplex-chat/default.nix

Copy verbatim from `machines_conf/packages/simplex-chat/default.nix`.
Input name is already `inputs.simplex` — no adaptation needed.

```nix
{
  inputs,
  pkgs,
  ...
}:
let
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

  meta = upstream.meta or {
    description = "SimpleX Chat - private and secure messaging client";
    homepage = "https://simplex.chat";
  };
}
```

### Step 3: Create nix/packages/simplexmq/default.nix

Copy verbatim from `machines_conf/packages/simplexmq/default.nix`.

```nix
{
  inputs,
  pkgs,
  ...
}:
let
  # Use haskell-nix's own pkgs to avoid nixpkgs version conflicts
  haskellPkgs = inputs.haskell-nix.legacyPackages.${pkgs.stdenv.hostPlatform.system};
in
haskellPkgs.haskell-nix.cabalProject {
  name = "simplexmq";
  src = inputs.simplexmq-src;
  compiler-nix-name = "ghc966";
  index-state = "2023-12-12T00:00:00Z";

  sha256map = {
    "https://github.com/simplex-chat/aeson.git"."aab7b5a14d6c5ea64c64dcaee418de1bb00dcc2b" =
      "0jz7kda8gai893vyvj96fy962ncv8dcsx71fbddyy8zrvc88jfrr";
    "https://github.com/simplex-chat/hs-socks.git"."a30cc7a79a08d8108316094f8f2f82a0c5e1ac51" =
      "0yasvnr7g91k76mjkamvzab2kvlb1g5pspjyjn2fr6v83swjhj38";
    "https://github.com/simplex-chat/direct-sqlcipher.git"."f814ee68b16a9447fbb467ccc8f29bdd3546bfd9" =
      "1ql13f4kfwkbaq7nygkxgw84213i0zm7c1a8hwvramayxl38dq5d";
    "https://github.com/simplex-chat/sqlcipher-simple.git"."a46bd361a19376c5211f1058908fc0ae6bf42446" =
      "1z0r78d8f0812kxbgsm735qf6xx8lvaz27k1a0b4a2m0sshpd5gl";
    "https://github.com/yesodweb/wai.git"."ec5e017d896a78e787a5acea62b37a4e677dec2e" =
      "1ckcpmpjfy9jiqrb52q20lj7ln4hmq9v2jk6kpkf3m68c1m9c2bx";
    "https://github.com/simplex-chat/wai.git"."2f6e5aa5f05ba9140ac99e195ee647b4f7d926b0" =
      "199g4rjdf1zp1fcw8nqdsyr1h36hmg424qqx03071jk7j00z7ay4";
  };
}
```

### Step 4: Update nix/packages/simplex-alerter/default.nix

Change line 23:
```nix
# Before
simplex-chat = inputs.simplex-chat.packages.${pkgs.system}."exe:simplex-chat";

# After
simplex-chat = inputs.simplex.packages.${pkgs.system}."exe:simplex-chat";
```

### Step 5: Update nix/packages/docker-image/default.nix

Change simplex-chat source (line 24):
```nix
# Before
simplex-chat = inputs.simplex-chat.packages.${pkgs.system}."exe:simplex-chat";

# After
simplex-chat = inputs.simplex.packages.${pkgs.system}."exe:simplex-chat";
```

Remove from `copyToRoot` paths:
```nix
pkgs.coreutils      # remove
pkgs.bash           # remove
```

Final `copyToRoot`:
```nix
copyToRoot = pkgs.buildEnv {
  name = "image-root";
  paths = [ alerter simplex-chat ] ++ runtimeDeps;
  pathsToLink = [ "/bin" "/lib" "/lib64" ];
};
```

---

## Verification

```bash
nix flake check
nix build
nix build .#docker-image
docker load < result
docker run --rm simplex-alerter:latest --help
```
