{ pkgs ? import <nixpkgs> {}
}:

let
in rec {
  masp = pkgs.callPackage .nix/derivation.nix {};

  masp-example-xml = pkgs.callPackage .nix/example-xml-derivation.nix {};
  
  masp-ginkgo-xml = pkgs.callPackage .nix/ginkgo-xml-derivation.nix {
    
  };

  masp-sphinx-example = pkgs.callPackage .nix/docs-derivation.nix {
    inherit masp;
    masp-xml = masp-example-xml;
  };

  masp-sphinx-ginkgo = pkgs.callPackage .nix/docs-derivation.nix {
    inherit masp;
    masp-xml = masp-ginkgo-xml;
    pname = "masp-sphinx-ginkgo";
  };

}
