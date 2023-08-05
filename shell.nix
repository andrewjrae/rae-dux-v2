{ pkgs ? import <nixpkgs> {} }:

with pkgs;

mkShell {
  buildInputs = [
    nodejs
    kicad-small
  ];
  shellHook = ''
    npm install
  '';
}
