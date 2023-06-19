#!/bin/bash
# to use this -->
# source ./env.sh

pyenv install -s
if [ ! -d env ]; then
    python3 -m venv env
    # shellcheck disable=SC1091
    source env/bin/activate
    env/bin/pip install --upgrade pip setuptools wheel
    env/bin/pip install -r requirements.dev.txt
    env/bin/poetry install
else
    # shellcheck disable=SC1091
    source env/bin/activate
fi


lint() {
    bash <<BASH
#!/bin/bash
set -x \\
&& black src \\
&& isort src \\
&& flake8 src \\
&& bandit -r src \\
&& pre-commit run --all --all-files \\
;
BASH
}
