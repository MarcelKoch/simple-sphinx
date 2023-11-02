{ lib
, stdenvNoCC
, python311
, python311Packages
}:

stdenvNoCC.mkDerivation {
  pname = "masp";
  version = "0.0.0";

  src = ./..;

  nativeBuildInputs = [
    python311
  ];

  buildPhase = ''
  '';

  installPhase = ''
    mkdir -p $out/bin
    mkdir -p $out/tmpl
    cp $src/src/dispatch.py $out/bin
    cp $src/src/wip/make_rst.py $out/bin
    cp -r $src/src/wip/*.rst.tmpl $out/tmpl/
  '';
}
