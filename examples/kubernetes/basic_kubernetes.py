#!/usr/bin/env python3
"""
NLP2CMD Kubernetes Example

Demonstrates natural language to kubectl command transformation
and manifest generation with safety policies.
"""

from nlp2cmd import NLP2CMD
from nlp2cmd.adapters import KubernetesAdapter, KubernetesSafetyPolicy


def main():
    # Configure safety policy
    safety_policy = KubernetesSafetyPolicy(
        allowed_namespaces=["default", "staging", "development"],
        blocked_namespaces=["kube-system", "kube-public", "production"],
        allow_delete=False,
        allow_exec=True,
        require_namespace=True,
        max_replicas=10,
        require_resource_limits=True,
    )

    # Create adapter
    adapter = KubernetesAdapter(
        cluster_context={
            "context": "minikube",
            "namespace": "default",
        },
        safety_policy=safety_policy,
    )

    nlp = NLP2CMD(adapter=adapter)

    # Example commands
    commands = [
        "Show all pods in default namespace",
        "Get deployments with wide output",
        "Scale nginx deployment to 3 replicas",
        "Show logs for nginx pod with follow",
        "Describe the web service",
        "Get pods with label app=backend",
        "Port forward web service to 8080",
        "Restart nginx deployment",
    ]

    print("=" * 60)
    print("NLP2CMD Kubernetes Examples")
    print("=" * 60)

    for cmd in commands:
        print(f"\n📝 Request: {cmd}")
        print("-" * 40)

        result = nlp.transform(cmd)

        print(f"Status: {result.status.value}")
        print(f"Confidence: {result.confidence:.0%}")
        print(f"\nGenerated command:")
        print(f"   $ {result.command}")

        if result.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")

    # Manifest generation
    print("\n" + "=" * 60)
    print("Manifest Generation")
    print("=" * 60)

    # Generate Deployment
    deployment_spec = {
        "kind": "Deployment",
        "name": "web",
        "namespace": "default",
        "image": "nginx:alpine",
        "replicas": 3,
        "port": 80,
        "labels": {"app": "web", "tier": "frontend"},
        "resources": {
            "requests": {"memory": "128Mi", "cpu": "100m"},
            "limits": {"memory": "256Mi", "cpu": "200m"},
        },
    }

    print("\nDeployment Manifest:")
    print("-" * 40)
    print(adapter.generate_manifest(deployment_spec))

    # Generate Service
    service_spec = {
        "kind": "Service",
        "name": "web",
        "namespace": "default",
        "port": 80,
        "target_port": 80,
        "type": "ClusterIP",
        "selector": {"app": "web"},
    }

    print("\nService Manifest:")
    print("-" * 40)
    print(adapter.generate_manifest(service_spec))

    # Generate Ingress
    ingress_spec = {
        "kind": "Ingress",
        "name": "web-ingress",
        "namespace": "default",
        "host": "web.example.com",
        "service_name": "web",
        "service_port": 80,
        "tls": True,
    }

    print("\nIngress Manifest:")
    print("-" * 40)
    print(adapter.generate_manifest(ingress_spec))

    # Safety policy demo
    print("\n" + "=" * 60)
    print("Safety Policy Demo")
    print("=" * 60)

    blocked_commands = [
        "Delete all pods in production",
        "Scale deployment to 100 replicas",
        "Get pods in kube-system namespace",
    ]

    for cmd in blocked_commands:
        print(f"\n📝 Request: {cmd}")
        result = nlp.transform(cmd)
        print(f"Status: {result.status.value}")

        if not result.is_success:
            print(f"❌ Blocked: {result.errors[0] if result.errors else 'Safety violation'}")


if __name__ == "__main__":
    main()
