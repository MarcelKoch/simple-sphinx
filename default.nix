{ pkgs ? import <nixpkgs> {}
}:

let
in rec {
  masp = pkgs.callPackage .nix/derivation.nix {};
  masp-sphinx-example = pkgs.callPackage .nix/docs-derivation.nix {
    inherit masp;
  };

  masp-sphinx-ginkgo = pkgs.callPackage .nix/ginkgo-docs-derivation.nix {
    inherit masp;
  };
}
