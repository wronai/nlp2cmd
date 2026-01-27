#!/usr/bin/env python3
"""
NLP2CMD File Repair Example

Demonstrates configuration file validation and repair:
- Dockerfile validation and repair
- docker-compose.yml validation and repair
- Kubernetes manifest validation
- Environment file (.env) validation
"""

from pathlib import Path
import tempfile
import os

from nlp2cmd.schemas import SchemaRegistry


def create_sample_files(tmpdir: Path) -> dict[str, Path]:
    """Create sample files for testing."""
    files = {}

    # Dockerfile with issues
    dockerfile = tmpdir / "Dockerfile"
    dockerfile.write_text("""FROM python
WORKDIR /app
RUN apt-get update
RUN apt-get install python3-pip
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD python app.py
""")
    files["dockerfile"] = dockerfile

    # docker-compose.yml with issues
    compose = tmpdir / "docker-compose.yml"
    compose.write_text("""version: '2'
services:
  web:
    image: nginx
    ports:
      - 8080:80
  db:
    image: postgres
    environment:
      POSTGRES_PASSWORD: secret
""")
    files["compose"] = compose

    # Kubernetes deployment with issues
    k8s = tmpdir / "deployment.yaml"
    k8s.write_text("""apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx
""")
    files["kubernetes"] = k8s

    # .env file with issues
    env = tmpdir / ".env"
    env.write_text("""database_url=postgres://localhost:5432/db
secret_key=mysecretkey
DEBUG=true
api_endpoint=https://api.example.com
""")
    files["env"] = env

    # GitHub workflow with issues
    workflow_dir = tmpdir / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    workflow = workflow_dir / "ci.yml"
    workflow.write_text("""name: CI
on: push
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest
""")
    files["workflow"] = workflow

    return files


def validate_file(registry: SchemaRegistry, path: Path, schema_name: str) -> None:
    """Validate a file and print results."""
    content = path.read_text()

    print(f"\n📄 File: {path.name}")
    print(f"   Schema: {schema_name}")
    print("   " + "-" * 50)

    result = registry.validate(content, schema_name)

    if result["valid"]:
        print("   ✅ Valid")
    else:
        print("   ❌ Invalid")

    if result["errors"]:
        print("   Errors:")
        for error in result["errors"]:
            print(f"      - {error}")

    if result["warnings"]:
        print("   Warnings:")
        for warning in result["warnings"]:
            print(f"      ⚠️  {warning}")


def repair_file(
    registry: SchemaRegistry,
    path: Path,
    schema_name: str,
    auto_fix: bool = True
) -> None:
    """Repair a file and show changes."""
    content = path.read_text()

    print(f"\n🔧 Repairing: {path.name}")
    print("   " + "-" * 50)

    result = registry.repair(content, schema_name, auto_fix=auto_fix)

    if result["repaired"]:
        print("   ✅ File repaired")

        for change in result["changes"]:
            change_type = change.get("type", "unknown")
            reason = change.get("reason", "")

            if change_type == "fixed":
                print(f"   🔧 Fixed: {reason}")
                if "original" in change:
                    print(f"      Before: {change['original'][:50]}...")
                if "fixed" in change:
                    print(f"      After:  {change['fixed'][:50]}...")
            elif change_type == "warning":
                print(f"   ⚠️  Warning: {reason}")
            elif change_type == "missing":
                print(f"   ➕ Added: {reason}")

        # Save repaired content
        if auto_fix:
            backup_path = path.with_suffix(path.suffix + ".bak")
            path.rename(backup_path)
            path.write_text(result["content"])
            print(f"\n   💾 Saved repaired file (backup: {backup_path.name})")
    else:
        print("   ℹ️  No repairs needed or not possible")

        for change in result.get("changes", []):
            if change.get("type") == "warning":
                print(f"   ⚠️  {change.get('reason', '')}")


def main():
    print("=" * 70)
    print("NLP2CMD File Repair Example")
    print("=" * 70)

    registry = SchemaRegistry()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create sample files
        print("\n📁 Creating sample files with intentional issues...")
        files = create_sample_files(tmpdir)

        # SECTION 1: Dockerfile
        print("\n" + "=" * 70)
        print("1. DOCKERFILE VALIDATION AND REPAIR")
        print("=" * 70)

        print("\n📋 Original content:")
        print("-" * 40)
        print(files["dockerfile"].read_text())

        validate_file(registry, files["dockerfile"], "dockerfile")
        repair_file(registry, files["dockerfile"], "dockerfile")

        print("\n📋 After repair:")
        print("-" * 40)
        print(files["dockerfile"].read_text())

        # SECTION 2: Docker Compose
        print("\n" + "=" * 70)
        print("2. DOCKER-COMPOSE VALIDATION AND REPAIR")
        print("=" * 70)

        print("\n📋 Original content:")
        print("-" * 40)
        print(files["compose"].read_text())

        validate_file(registry, files["compose"], "docker-compose")
        repair_file(registry, files["compose"], "docker-compose")

        # SECTION 3: Kubernetes
        print("\n" + "=" * 70)
        print("3. KUBERNETES MANIFEST VALIDATION")
        print("=" * 70)

        print("\n📋 Original content:")
        print("-" * 40)
        print(files["kubernetes"].read_text())

        validate_file(registry, files["kubernetes"], "kubernetes-deployment")
        repair_file(registry, files["kubernetes"], "kubernetes-deployment")

        # SECTION 4: Environment File
        print("\n" + "=" * 70)
        print("4. ENVIRONMENT FILE (.env) VALIDATION")
        print("=" * 70)

        print("\n📋 Original content:")
        print("-" * 40)
        print(files["env"].read_text())

        validate_file(registry, files["env"], "env-file")
        repair_file(registry, files["env"], "env-file")

        # SECTION 5: GitHub Workflow
        print("\n" + "=" * 70)
        print("5. GITHUB WORKFLOW VALIDATION")
        print("=" * 70)

        print("\n📋 Original content:")
        print("-" * 40)
        print(files["workflow"].read_text())

        validate_file(registry, files["workflow"], "github-workflow")
        repair_file(registry, files["workflow"], "github-workflow")

        # SECTION 6: Format Detection
        print("\n" + "=" * 70)
        print("6. AUTOMATIC FORMAT DETECTION")
        print("=" * 70)

        print("\n🔍 Detecting file formats:")
        for name, path in files.items():
            if path.exists():
                detected = registry.detect_format(path)
                if detected:
                    print(f"   {path.name}: {detected.name}")
                else:
                    print(f"   {path.name}: Unknown format")

        # SECTION 7: Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)

        print("""
The SchemaRegistry provides:

✅ Validation for multiple configuration formats:
   - Dockerfile
   - docker-compose.yml
   - Kubernetes manifests
   - GitHub Actions workflows
   - .env files

✅ Automatic repair with:
   - Pattern-based fixes (regex)
   - Structure-based fixes (YAML/JSON paths)
   - Backup creation

✅ Format detection:
   - By filename
   - By content analysis

Usage in your code:
    from nlp2cmd import SchemaRegistry

    registry = SchemaRegistry()

    # Validate
    result = registry.validate(content, "docker-compose")

    # Repair
    repaired = registry.repair(content, "dockerfile", auto_fix=True)
""")


if __name__ == "__main__":
    main()
