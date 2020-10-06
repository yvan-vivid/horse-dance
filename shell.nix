{ pkgs ? import <nixpkgs> {} }:
with pkgs; mkShell {
  buildInputs = [
    python38
    python38Packages.python_magic
    python38Packages.poetry
    python38Packages.pylint
    python38Packages.mypy
  ];
}
