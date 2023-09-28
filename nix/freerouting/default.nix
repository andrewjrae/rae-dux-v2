let
  pkgs = import <nixpkgs> {};
in
{ stdenv ? pkgs.stdenv,
  fetchurl ? pkgs.fetchurl,
  makeWrapper ? pkgs.makeWrapper,
  jre ? pkgs.jdk17
}:

stdenv.mkDerivation rec {
  name = "freerouting";
  version = "1.7.0";

  src = fetchurl {
    url = "https://github.com/freerouting/freerouting/releases/download/v${version}/${name}-${version}.jar";
    sha256 = "5sXbM3kqAPmXmbERO7n14VdnMfiFsGnaiFBSBSj3748=";
  };

  dontUnpack = true;

  nativeBuildInputs = [ makeWrapper ];

  installPhase = ''
    mkdir -pv $out/share/java $out/bin
    cp ${src} $out/share/java/${name}-${version}.jar

    makeWrapper ${jre}/bin/java $out/bin/freerouting \
      --add-flags "-jar $out/share/java/${name}-${version}.jar"
  '';
}
