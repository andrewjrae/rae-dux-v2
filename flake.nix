{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    cq-flake.url = "github:vinszent/cq-flake";
  };

  outputs = { self, nixpkgs, flake-utils, cq-flake }:
    let
      systems = [ "x86_64-linux" ];
    in
      flake-utils.lib.eachSystem systems (system:
        let
          pkgs = import nixpkgs { inherit system; };
          cq-pkgs = cq-flake.packages.${system};
        in
        {
          devShells.default = import ./nix/shell.nix { inherit pkgs cq-pkgs; };
        }
      );
}
