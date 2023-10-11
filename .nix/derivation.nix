{ lib
, stdenvNoCC
, python310
, python310Packages
}:

stdenvNoCC.mkDerivation {
  pname = "masp";
  version = "0.0.0";

  src = ./..;

  nativeBuildInputs = [
    python310
  ];

  buildPhase = ''
  '';

  installPhase = ''
    mkdir -p $out/bin
    mkdir -p $out/tmpl
    cp $src/src/dispatch.py $out/bin
    cp $src/src/wip/make_rst.py $out/bin
    cp -r $src/src/wip/class.rst.tmpl $out/tmpl/
  '';
}
