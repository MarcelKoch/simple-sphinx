{ pkgs ? import <nixpkgs> {}
}:

let

in rec {
  masp = pkgs.callPackage .nix/derivation.nix {};
  masp-sphinx-example = pkgs.callPackage .nix/docs-derivation.nix {
    inherit masp;
  };
}
