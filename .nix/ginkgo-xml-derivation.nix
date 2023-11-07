{ lib
, stdenv
, python311
, python311Packages
, doxygen
, graphviz
, cmake
, texlive
, font-manager
, perl
}:

stdenv.mkDerivation {
  pname = "masp-ginkgo-xml";
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
    graphviz
    texlive.combined.scheme-small
    font-manager
    perl
  ];

  cmakeFlags = [
    "-DBUILD_SHARED_LIBS=OFF"
    "-DGINKGO_WITH_CCACHE=OFF"
    "-DGINKGO_BUILD_TESTS=OFF"
    "-DGINKGO_BUILD_EXAMPLES=OFF"
    "-DGINKGO_BUILD_BENCHMARKS=OFF"
    "-DGINKGO_BUILD_REFERENCE=OFF"
    "-DGINKGO_BUILD_OMP=OFF"
    "-DGINKGO_BUILD_MPI=OFF"
    "-DGINKGO_BUILD_DOC=ON"
  ];

  patches = [
	  ./ginkgo-xml-doc.patch
  ];

  buildPhase = ''
    make usr
  '';

  installPhase = ''
    mkdir -p $out
    mv doc/usr/xml $out/xml
  '';
}
