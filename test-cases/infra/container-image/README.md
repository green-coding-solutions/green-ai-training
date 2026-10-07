# Prompt

Optimize this Dockerfile according to Green Coding Rules

# Expected Output

- Use a slim base image (`python:3.12-slim`) instead of the full `python:3.12` image
- Remove packages the app doesn't need at runtime (`build-essential`, `git`, `curl`, `vim`). If something must be compiled, do it in a separate build stage (multi-stage build) and copy only the result
- Don't install development tools (`pytest`, `black`, `mypy`, `ipython`) into the production image
- Copy `requirements.txt` and install dependencies before copying the rest of the source, so the dependency layer is cached and not rebuilt on every code change
- Use `pip install --no-cache-dir` and clean up apt lists (`rm -rf /var/lib/apt/lists/*`) to keep layers small
- Add a `.dockerignore` (e.g. `.git`, `__pycache__`, `.venv`, tests) so the build context and image stay small
- Expected energy saving when running this file 1.000 times
