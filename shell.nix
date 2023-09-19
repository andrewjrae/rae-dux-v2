{ pkgs ? import <nixpkgs> {} }:

with pkgs;

mkShell {
  buildInputs = [
    nodejs
    kicad-small
    (python3.withPackages(ps: with ps; [kicad]))
  ];
  shellHook = ''
    npm install
  '';
}
