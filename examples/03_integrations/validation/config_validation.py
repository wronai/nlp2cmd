#!/usr/bin/env python3
"""
Example: Configuration File Validation

Demonstrates validation and repair of various configuration files:
- Dockerfile
- docker-compose.yml
- Kubernetes manifests
- GitHub Actions workflows
- .env files

Shows how to use SchemaRegistry for automated config validation.
"""

from nlp2cmd import SchemaRegistry


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(result: dict, title: str = "Result"):
    """Print validation result."""
    status = "✅ Valid" if result.get("valid") else "❌ Invalid"
    print(f"{title}: {status}")
    
    if result.get("errors"):
        print("  Errors:")
        for error in result["errors"]:
            print(f"    • {error}")
    
    if result.get("warnings"):
        print("  Warnings:")
        for warning in result["warnings"]:
            print(f"    ⚠️  {warning}")


def main():
    print_section("Configuration File Validation Demo")
    
    registry = SchemaRegistry()
    
    # =========================================================================
    # Dockerfile Validation
    # =========================================================================
    print_section("1. Dockerfile Validation")
    
    # Valid Dockerfile
    valid_dockerfile = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]
"""
    
    print("Valid Dockerfile:")
    print("-" * 40)
    result = registry.validate(valid_dockerfile, "dockerfile")
    print_result(result)
    
    # Dockerfile with issues
    problematic_dockerfile = """FROM python
RUN apt-get install python3-dev
COPY . /app
WORKDIR /app
"""
    
    print("\nDockerfile with issues:")
    print("-" * 40)
    result = registry.validate(problematic_dockerfile, "dockerfile")
    print_result(result)
    
    # =========================================================================
    # Docker Compose Validation
    # =========================================================================
    print_section("2. Docker Compose Validation")
    
    valid_compose = """version: '3.8'
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    restart: unless-stopped
  
  api:
    build: ./api
    environment:
      - DATABASE_URL=postgres://db:5432/app
    depends_on:
      - db
  
  db:
    image: postgres:15
    volumes:
      - db_data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: secret

volumes:
  db_data:
"""
    
    print("Valid docker-compose.yml:")
    print("-" * 40)
    result = registry.validate(valid_compose, "docker-compose")
    print_result(result)
    
    # Compose with old version
    old_compose = """version: '2'
services:
  web:
    image: nginx
"""
    
    print("\ndocker-compose.yml with old version:")
    print("-" * 40)
    result = registry.validate(old_compose, "docker-compose")
    print_result(result)
    
    # =========================================================================
    # Kubernetes Manifest Validation
    # =========================================================================
    print_section("3. Kubernetes Deployment Validation")
    
    valid_k8s = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
  template:
    metadata:
      labels:
        app: api-server
    spec:
      containers:
        - name: api
          image: myapp/api:v1.2.3
          ports:
            - containerPort: 8000
          resources:
            limits:
              memory: "512Mi"
              cpu: "500m"
            requests:
              memory: "256Mi"
              cpu: "250m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
"""
    
    print("Valid Kubernetes Deployment:")
    print("-" * 40)
    result = registry.validate(valid_k8s, "kubernetes-deployment")
    print_result(result)
    
    # K8s manifest without replicas
    incomplete_k8s = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  selector:
    matchLabels:
      app: web
  template:
    spec:
      containers:
        - name: web
          image: nginx
"""
    
    print("\nIncomplete Kubernetes Deployment:")
    print("-" * 40)
    result = registry.validate(incomplete_k8s, "kubernetes-deployment")
    print_result(result)
    
    # =========================================================================
    # GitHub Actions Workflow Validation
    # =========================================================================
    print_section("4. GitHub Actions Workflow Validation")
    
    valid_workflow = """name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: ./deploy.sh
"""
    
    print("Valid GitHub Actions Workflow:")
    print("-" * 40)
    result = registry.validate(valid_workflow, "github-workflow")
    print_result(result)
    
    # Workflow without runs-on
    invalid_workflow = """name: CI
on: push
jobs:
  test:
    steps:
      - run: echo "test"
"""
    
    print("\nWorkflow missing runs-on:")
    print("-" * 40)
    result = registry.validate(invalid_workflow, "github-workflow")
    print_result(result)
    
    # =========================================================================
    # Environment File Validation
    # =========================================================================
    print_section("5. Environment File Validation")
    
    valid_env = """# Database configuration
DATABASE_URL=postgres://localhost:5432/myapp
DATABASE_POOL_SIZE=10

# API Keys
API_KEY="sk-1234567890"
SECRET_KEY='very-secret-key'

# Feature flags
DEBUG=true
LOG_LEVEL=info
"""
    
    print("Valid .env file:")
    print("-" * 40)
    result = registry.validate(valid_env, "env-file")
    print_result(result)
    
    # Env file with issues
    problematic_env = """database_url=postgres://localhost:5432/myapp
api_key="unclosed quote
VALID_VAR=value
invalid line without equals
"""
    
    print("\n.env file with issues:")
    print("-" * 40)
    result = registry.validate(problematic_env, "env-file")
    print_result(result)
    
    # =========================================================================
    # Auto-Repair Demo
    # =========================================================================
    print_section("6. Auto-Repair Demo")
    
    compose_to_fix = """version: '2'
services:
  web:
    image: nginx
"""
    
    print("Original docker-compose.yml:")
    print("-" * 40)
    print(compose_to_fix)
    
    print("\nAttempting repair...")
    repair_result = registry.repair(compose_to_fix, "docker-compose", auto_fix=True)
    
    print("\nRepair Result:")
    if repair_result.get("changes"):
        print("  Changes made:")
        for change in repair_result["changes"]:
            print(f"    • {change}")
    
    if repair_result.get("content"):
        print("\nRepaired content:")
        print("-" * 40)
        print(repair_result["content"])
    
    # =========================================================================
    # Summary
    # =========================================================================
    print_section("Summary")
    
    print("Available schemas:")
    for name in sorted(registry.schemas.keys()):
        schema = registry.schemas[name]
        print(f"  • {schema.name}")
        print(f"    Extensions: {', '.join(schema.extensions[:3])}")


if __name__ == "__main__":
    main()
