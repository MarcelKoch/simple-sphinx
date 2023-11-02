{ lib
, stdenvNoCC
, python311
, python311Packages
, doxygen
, cmake
, masp
}:

stdenvNoCC.mkDerivation {
  pname = "masp-sphinx-ginkgo";
  version = "0.0.0";

  src = builtins.fetchGit {
    url = "https://github.com/ginkgo-project/ginkgo";
    ref = "develop";
  };

  nativeBuildInputs = [
    cmake
    python311
    python311Packages.frozendict
    python311Packages.sphinx
    python311Packages.sphinx-rtd-theme
    doxygen
    masp
  ];

  configurePhase = ''

  '';

  buildPhase = ''
    # C++ API generation
    doxygen Doxyfile_cpp
    python3 ${masp.outPath}/bin/dispatch.py > cpp_map.json
    # Ensure file tree exists in source
    mkdir -p source/cpp_api
    # C++ and C template generation
    python3 ${masp.outPath}/bin/make_rst.py --title="C++" -t ${masp.outPath}/tmpl -m cpp_map.json -o source/cpp_api
    make html
  '';

  installPhase = ''
    mkdir -p $out $out/rst $out/json
    mv build/html $out/html
    mv source/cpp_api $out/rst/cpp_api
    mv doxygen/xml $out/xml
    mv cpp_map.json $out/json/
  '';
}
