{ pkgs ? import <nixpkgs> {} }:

with pkgs;

let
  # Using local kicad with tests disabled because ngspice is still causing
  # issues (and debug=true enables assertions which causes issues)
  custom-kicad = kicad.override {
    stable = false;
    with3d = false;
    srcs = {
      kicad = fetchFromGitHub {
        owner = "andrewjrae";
        repo = "kicad-mirror";
        rev = "17ad4b73c4f1d7e6cd9916e116693dcc31b09850";
        sha256 = "bKg5xIPc6ITHvW6/HpJT9eMlrae0ZiPpPpPXfLKneZ8=";
      };
    };
  };
  custom-python3 = python3.override {
    packageOverrides = self: super: {
      kicad = super.toPythonModule(custom-kicad.src);
    };
  };
  custom-python3-with-kicad = custom-python3.withPackages(
    ps: [ps.kicad]
  );
  freerouting = callPackage ./nix/freerouting {};
in
mkShell {
  name = "keeb-utils";
  buildInputs = [
    nodejs
    custom-kicad
    custom-python3-with-kicad
    freerouting
  ];
  shellHook = ''
    npm install
  '';
}
