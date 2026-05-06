#!/bin/bash
# ==========================================
# Nurse Mate: Version Control Setup Script
# Run this script to establish local Git version control,
# ignore sensitive/compiled files, and create an Agile branching strategy.
# ==========================================

set -euo pipefail

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is not installed or not available on PATH." >&2
  echo "Install Git and rerun this script." >&2
  exit 1
fi

echo "[1/5] Checking repository state..."
if [ -d .git ]; then
  echo "Existing Git repository found. Using current repository."
else
  echo "[1/5] Initializing new Git repository..."
  git init
fi

echo "[2/5] Creating .gitignore file..."
cat > .gitignore <<'EOT'
# Python artifacts
__pycache__/
*.pyc
*.pyo
*.pyd

# Test artifacts
.pytest_cache/
.coverage
htmlcov/

# Environments
venv/
env/
.env

# IDE artifacts
.vscode/
.idea/
EOT

echo "[3/5] Staging files..."
git add .

echo "[4/5] Creating initial commit if needed..."
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "Existing commit history detected. Skipping initial commit."
else
  git commit -m "feat: Initial commit of Nurse Mate project and test suite"
fi

echo "[5/5] Ensuring workflow branches exist..."
branches=(
  feature/emr-fhir-integration
  feature/nlp-voice-assistant
  feature/task-manager
  release/v1.0.0-beta
)
for branch in "${branches[@]}"; do
  if git show-ref --verify --quiet "refs/heads/$branch"; then
    echo "Branch '$branch' already exists."
  else
    git branch "$branch"
    echo "Created branch '$branch'."
  fi
done

echo "✅ Version control setup complete."
echo "Current branch status:"
git status
if git branch -a >/dev/null 2>&1; then
  echo "Available branches:"
  git branch -a
fi