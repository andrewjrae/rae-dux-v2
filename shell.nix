{ pkgs ? import <nixpkgs> {} }:

with pkgs;

mkShell {
  buildInputs = [
    nodejs
    kicad
  ];
  shellHook = ''
    npm install
  '';
}
