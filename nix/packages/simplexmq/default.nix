{
  inputs,
  pkgs,
  ...
}:

let
  # Use haskell-nix's own pkgs to avoid nixpkgs version conflicts
  # Note: Uses its own pinned nixpkgs-2305, not our nixpkgs
  haskellPkgs = inputs.haskell-nix.legacyPackages.${pkgs.stdenv.hostPlatform.system};
in
# Build simplexmq from source with Haskell.nix
# Includes SHA256 hashes for all source-repository-package dependencies
# to ensure reproducibility and supply chain traceability
haskellPkgs.haskell-nix.cabalProject {
  name = "simplexmq";
  src = inputs.simplexmq-src;
  compiler-nix-name = "ghc966";
  index-state = "2023-12-12T00:00:00Z";

  # SHA256 hashes for source-repository-package dependencies
  # Source: https://github.com/simplex-chat/simplex-chat/blob/v6.4.10/scripts/nix/sha256map.nix
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
