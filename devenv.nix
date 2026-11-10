# @autorun
{pkgs, ...}:
{

  dotenv.disableHint = true;

  # Python packages come from nixpkgs (not pip) so they're pinned by devenv.lock
  languages.python = {
    enable = true;
    package = pkgs.python313.withPackages (ps: [
      ps.openpyxl
      ps.selenium
      ps.pytest
      ps.python-dotenv
    ]);
  };

  packages = [
    pkgs.firefox
    pkgs.geckodriver
  ];


  scripts.run.exec = ''
    python ./src/main.py
  '';
}
