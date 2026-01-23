#!/usr/bin/env python3
"""
NLP2CMD Kubernetes Example

Demonstrates natural language to kubectl command transformation
and manifest generation with safety policies.
"""

from pathlib import Path

from app2schema import extract_appspec_to_file
from nlp2cmd import NLP2CMD
from nlp2cmd.adapters import AppSpecAdapter
from nlp2cmd.adapters.kubernetes import KubernetesSafetyPolicy


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

    # app2schema -> build appspec for kubectl CLI
    appspec_path = Path("./generated_kubectl_appspec.json")
    extract_appspec_to_file("kubectl", appspec_path, source_type="shell", merge=True)

    adapter = AppSpecAdapter(appspec_path=appspec_path, safety_policy=safety_policy)
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

        ir = nlp.transform_ir(cmd)

        print(f"Action: {ir.action_id}")
        print(f"\nGenerated command:")
        print(f"   $ {ir.dsl}")

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
        try:
            ir = nlp.transform_ir(cmd)
            print(f"Generated: {ir.dsl}")
        except Exception as e:
            print(f"❌ Blocked: {e}")


if __name__ == "__main__":
    main()
