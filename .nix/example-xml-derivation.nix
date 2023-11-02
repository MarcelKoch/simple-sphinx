{ lib
, stdenvNoCC
, python311
, python311Packages
, doxygen
, target_src ? { outPath = ./../example; }
}:

stdenvNoCC.mkDerivation {
  pname = "masp-example-xml";
  version = "0.0.0";

  src = target_src;

  nativeBuildInputs = [
    python311
    python311Packages.frozendict
    python311Packages.sphinx
    python311Packages.sphinx-rtd-theme
    doxygen
  ];

  buildPhase = ''
    # C++ API generation
    doxygen Doxyfile_cpp
  '';

  installPhase = ''
    mkdir -p $out
    mv doxygen/xml $out/xml
  '';
}
