#!/usr/bin/env python3
"""
NLP2CMD Kubernetes Example

Demonstrates natural language to kubectl command transformation
and manifest generation with safety policies.
"""

from pathlib import Path

from app2schema import extract_schema_to_file
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters.dynamic import DynamicAdapter
from nlp2cmd.adapters.kubernetes import KubernetesSafetyPolicy
from nlp2cmd.core import RuleBasedBackend


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

    # app2schema -> build dynamic schema export for kubectl CLI
    export_path = Path("./generated_kubectl_dynamic_schema.json")
    try:
        extract_schema_to_file("kubectl", export_path, source_type="shell", merge=True)
    except Exception as e:
        print(f"Failed to extract schema for kubectl: {e}")
        return

    adapter = DynamicAdapter(
        config={"custom_options": {"load_common_commands": False}},
        safety_policy=safety_policy,
    )
    adapter.register_schema_source(str(export_path), source_type="auto")

    nlp = NLP2CMD(
        adapter=adapter,
        nlp_backend=RuleBasedBackend(rules={}, config={"dsl": "kubernetes"}),
    )

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

    # Safety policy demo
    print("\n" + "=" * 60)
    print("Safety Policy Demo")
    print("=" * 60)

    blocked_commands = [
        "Delete all pods in production",
        "Scale deployment to 100 replicas",
        "Get pods in kube-system namespace",
    ]

    dangerous_commands = [
        "kubectl delete pods -n production --all",
        "kubectl scale deployment nginx --replicas=100 -n default",
        "kubectl get pods -n kube-system",
    ]

    for cmd in dangerous_commands:
        print(f"\n📝 Command: {cmd}")
        safety = adapter.check_safety(cmd)
        if not safety.get("allowed", True):
            print(f"❌ Blocked: {safety.get('reason', 'Blocked by safety policy')}")
        else:
            print("✅ Allowed")


if __name__ == "__main__":
    main()
