"""
Kubernetes DSL Adapter for NLP2CMD.

Supports kubectl commands and YAML manifest generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import re
from nlp2cmd.utils.yaml_compat import yaml

from nlp2cmd.adapters.base import AdapterConfig, BaseDSLAdapter, SafetyPolicy


@dataclass
class KubernetesSafetyPolicy(SafetyPolicy):
    """Kubernetes-specific safety policy."""

    allowed_namespaces: list[str] = field(default_factory=lambda: ["default"])
    blocked_namespaces: list[str] = field(
        default_factory=lambda: ["kube-system", "kube-public"]
    )
    allow_delete: bool = False
    allow_exec: bool = True
    require_namespace: bool = True
    max_replicas: int = 10
    require_resource_limits: bool = True

    def check_command(self, command: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Check kubectl command against safety policy.

        Exposed for DynamicAdapter compatibility (it calls safety_policy.check_command if present).
        """
        # Check delete operations
        if " delete " in f" {command} " and not self.allow_delete:
            return {
                "allowed": False,
                "reason": "Delete operations are not allowed",
                "risk_level": "high",
            }

        # Check exec operations
        if " exec " in f" {command} " and not self.allow_exec:
            return {
                "allowed": False,
                "reason": "Exec operations are not allowed",
                "risk_level": "high",
            }

        # Check namespace restrictions
        for ns in self.blocked_namespaces:
            if f"-n {ns}" in command or f"--namespace={ns}" in command:
                return {
                    "allowed": False,
                    "reason": f"Operations in namespace '{ns}' are blocked",
                    "risk_level": "high",
                }

        # Check scale limits
        if " scale " in f" {command} " and "--replicas" in command:
            import re

            match = re.search(r"--replicas[=\s](\d+)", command)
            if match:
                replicas = int(match.group(1))
                if replicas > self.max_replicas:
                    return {
                        "allowed": False,
                        "reason": f"Replica count {replicas} exceeds limit {self.max_replicas}",
                        "risk_level": "high",
                    }

        return {"allowed": True, "requires_confirmation": False, "risk_level": "low"}


@dataclass
class ClusterContext:
    """Kubernetes cluster context."""

    context: str = "default"
    namespace: str = "default"
    resources: dict[str, list[str]] = field(default_factory=dict)


class KubernetesAdapter(BaseDSLAdapter):
    """
    Kubernetes adapter for kubectl commands and manifests.

    Transforms natural language into kubectl commands
    with support for common Kubernetes operations.
    """

    DSL_NAME = "kubernetes"
    DSL_VERSION = "1.0"

    INTENTS = {
        "get": {
            "patterns": ["pokaż", "get", "list", "wyświetl", "pobierz", "show", "show all"],
            "required_entities": ["resource_type"],
            "optional_entities": ["name", "namespace", "selector", "output"],
        },
        "describe": {
            "patterns": ["opisz", "describe", "szczegóły", "details", "show details"],
            "required_entities": ["resource_type", "name"],
            "optional_entities": ["namespace"],
        },
        "apply": {
            "patterns": ["zastosuj", "apply", "wdróż", "deploy", "create"],
            "required_entities": ["file"],
            "optional_entities": ["namespace"],
        },
        "delete": {
            "patterns": ["usuń", "delete", "remove", "remove all"],
            "required_entities": ["resource_type"],
            "optional_entities": ["name", "namespace", "selector"],
        },
        "scale": {
            "patterns": ["skaluj", "scale", "repliki", "replicas", "scale deployment"],
            "required_entities": ["resource_name", "replica_count"],
            "optional_entities": ["namespace"],
        },
        "logs": {
            "patterns": ["logi", "logs", "pokaż logi", "show logs"],
            "required_entities": ["pod_name"],
            "optional_entities": ["container", "namespace", "follow", "tail"],
        },
        "exec": {
            "patterns": ["exec", "execute", "uruchom w podzie", "wejdź"],
            "required_entities": ["pod_name", "command"],
            "optional_entities": ["container", "namespace"],
        },
        "port_forward": {
            "patterns": ["port-forward", "przekieruj port", "forward", "port forward"],
            "required_entities": ["resource", "ports"],
            "optional_entities": ["namespace"],
        },
        "rollout": {
            "patterns": ["rollout", "restart", "status wdrożenia", "restart deployment"],
            "required_entities": ["action", "resource"],
            "optional_entities": ["namespace"],
        },
        "create": {
            "patterns": ["utwórz", "create", "stwórz", "new"],
            "required_entities": ["resource_type"],
            "optional_entities": ["name", "namespace", "options"],
        },
    }

    RESOURCE_SHORTCUTS = {
        "po": "pods",
        "pod": "pods",
        "pody": "pods",  # Polish
        "podów": "pods",  # Polish genitive
        "svc": "services",
        "service": "services",
        "deploy": "deployments",
        "deployment": "deployments",
        "rs": "replicasets",
        "ds": "daemonsets",
        "sts": "statefulsets",
        "cm": "configmaps",
        "secret": "secrets",
        "ing": "ingress",
        "ns": "namespaces",
        "namespace": "namespaces",
        "przestrzeń": "namespaces",  # Polish
        "przestrzeni": "namespaces",  # Polish genitive
        "pv": "persistentvolumes",
        "pvc": "persistentvolumeclaims",
        "sa": "serviceaccounts",
        "no": "nodes",
        "node": "nodes",
        "węzły": "nodes",  # Polish
        "job": "jobs",
        "cj": "cronjobs",
    }

    def __init__(
        self,
        cluster_context: Optional[dict[str, Any]] = None,
        safety_policy: Optional[KubernetesSafetyPolicy] = None,
        config: Optional[AdapterConfig] = None,
    ):
        """
        Initialize Kubernetes adapter.

        Args:
            cluster_context: Kubernetes cluster context
            safety_policy: Kubernetes-specific safety policy
            config: Adapter configuration
        """
        super().__init__(config, safety_policy or KubernetesSafetyPolicy())
        self.cluster = self._parse_cluster_context(cluster_context or {})

    def _parse_cluster_context(self, ctx: dict[str, Any]) -> ClusterContext:
        """Parse cluster context."""
        return ClusterContext(
            context=ctx.get("context", "default"),
            namespace=ctx.get("namespace", "default"),
            resources=ctx.get("resources", {}),
        )

    def _normalize_resource(self, resource: str) -> str:
        """Normalize resource type name."""
        return self.RESOURCE_SHORTCUTS.get(resource.lower(), resource.lower())

    def generate(self, plan: dict[str, Any]) -> str:
        """Generate kubectl command from execution plan."""
        intent = plan.get("intent", "")
        entities = plan.get("entities", {})

        generators = {
            "get": self._generate_get,
            "describe": self._generate_describe,
            "apply": self._generate_apply,
            "delete": self._generate_delete,
            "scale": self._generate_scale,
            "logs": self._generate_logs,
            "exec": self._generate_exec,
            "port_forward": self._generate_port_forward,
            "rollout": self._generate_rollout,
            "create": self._generate_create,
        }

        generator = generators.get(intent)
        if generator:
            return generator(entities)

        return f"# Unknown Kubernetes intent: {intent}"

    def _generate_get(self, entities: dict[str, Any]) -> str:
        """Generate kubectl get command."""
        resource = self._normalize_resource(entities.get("resource_type", "pods"))
        name = entities.get("name", "")
        namespace = entities.get("namespace", "")
        selector = entities.get("selector", "")
        output = entities.get("output", "")
        all_namespaces = entities.get("all_namespaces", False)
        watch = entities.get("watch", False)

        parts = ["kubectl", "get", resource]

        if name:
            parts.append(name)

        if all_namespaces:
            parts.append("-A")
        elif namespace:
            parts.extend(["-n", namespace])

        if selector:
            parts.extend(["-l", selector])

        if output:
            parts.extend(["-o", output])

        if watch:
            parts.append("-w")

        return " ".join(parts)

    def _generate_describe(self, entities: dict[str, Any]) -> str:
        """Generate kubectl describe command."""
        resource = self._normalize_resource(entities.get("resource_type", "pod"))
        name = entities.get("name", "")
        namespace = entities.get("namespace", "")

        parts = ["kubectl", "describe", resource, name]

        if namespace:
            parts.extend(["-n", namespace])

        return " ".join(parts)

    def _generate_apply(self, entities: dict[str, Any]) -> str:
        """Generate kubectl apply command."""
        file = entities.get("file", "")
        namespace = entities.get("namespace", "")
        recursive = entities.get("recursive", False)
        dry_run = entities.get("dry_run", False)

        parts = ["kubectl", "apply", "-f", file]

        if namespace:
            parts.extend(["-n", namespace])

        if recursive:
            parts.append("-R")

        if dry_run:
            parts.append("--dry-run=client")

        return " ".join(parts)

    def _generate_delete(self, entities: dict[str, Any]) -> str:
        """Generate kubectl delete command."""
        resource = self._normalize_resource(entities.get("resource_type", ""))
        name = entities.get("name", "")
        namespace = entities.get("namespace", "")
        selector = entities.get("selector", "")
        force = entities.get("force", False)
        grace_period = entities.get("grace_period", "")

        parts = ["kubectl", "delete", resource]

        if name:
            parts.append(name)

        if namespace:
            parts.extend(["-n", namespace])

        if selector:
            parts.extend(["-l", selector])

        if force:
            parts.append("--force")

        if grace_period:
            parts.extend(["--grace-period", str(grace_period)])

        return " ".join(parts)

    def _generate_scale(self, entities: dict[str, Any]) -> str:
        """Generate kubectl scale command."""
        resource = entities.get("resource_name", "")
        replicas = entities.get("replica_count", 1)
        namespace = entities.get("namespace", "")

        # Determine resource type from name
        if "/" not in resource:
            resource = f"deployment/{resource}"

        parts = ["kubectl", "scale", resource, f"--replicas={replicas}"]

        if namespace:
            parts.extend(["-n", namespace])

        return " ".join(parts)

    def _generate_logs(self, entities: dict[str, Any]) -> str:
        """Generate kubectl logs command."""
        pod = entities.get("pod_name", "")
        container = entities.get("container", "")
        namespace = entities.get("namespace", "")
        follow = entities.get("follow", False)
        tail = entities.get("tail", 100)
        previous = entities.get("previous", False)
        timestamps = entities.get("timestamps", False)

        parts = ["kubectl", "logs", pod]

        if container:
            parts.extend(["-c", container])

        if namespace:
            parts.extend(["-n", namespace])

        if follow:
            parts.append("-f")

        if tail:
            parts.extend(["--tail", str(tail)])

        if previous:
            parts.append("-p")

        if timestamps:
            parts.append("--timestamps")

        return " ".join(parts)

    def _generate_exec(self, entities: dict[str, Any]) -> str:
        """Generate kubectl exec command."""
        pod = entities.get("pod_name", "")
        command = entities.get("command", "/bin/bash")
        container = entities.get("container", "")
        namespace = entities.get("namespace", "")
        interactive = entities.get("interactive", True)

        parts = ["kubectl", "exec"]

        if interactive:
            parts.append("-it")

        parts.append(pod)

        if container:
            parts.extend(["-c", container])

        if namespace:
            parts.extend(["-n", namespace])

        parts.append("--")
        parts.append(command)

        return " ".join(parts)

    def _generate_port_forward(self, entities: dict[str, Any]) -> str:
        """Generate kubectl port-forward command."""
        resource = entities.get("resource", "")
        ports = entities.get("ports", "")
        namespace = entities.get("namespace", "")
        address = entities.get("address", "")

        parts = ["kubectl", "port-forward", resource, ports]

        if namespace:
            parts.extend(["-n", namespace])

        if address:
            parts.extend(["--address", address])

        return " ".join(parts)

    def _generate_rollout(self, entities: dict[str, Any]) -> str:
        """Generate kubectl rollout command."""
        action = entities.get("action", "status")
        resource = entities.get("resource", "")
        namespace = entities.get("namespace", "")

        if "/" not in resource:
            resource = f"deployment/{resource}"

        parts = ["kubectl", "rollout", action, resource]

        if namespace:
            parts.extend(["-n", namespace])

        return " ".join(parts)

    def _generate_create(self, entities: dict[str, Any]) -> str:
        """Generate kubectl create command."""
        resource = self._normalize_resource(entities.get("resource_type", ""))
        name = entities.get("name", "")
        namespace = entities.get("namespace", "")
        options = entities.get("options", {})

        parts = ["kubectl", "create", resource, name]

        if namespace:
            parts.extend(["-n", namespace])

        # Add resource-specific options
        if resource == "secret":
            secret_type = options.get("type", "generic")
            if secret_type == "generic":
                parts.insert(3, "generic")
                for key, value in options.get("literals", {}).items():
                    parts.extend([f"--from-literal={key}={value}"])
        elif resource == "configmaps":
            for key, value in options.get("literals", {}).items():
                parts.extend([f"--from-literal={key}={value}"])

        return " ".join(parts)

    def generate_manifest(self, spec: dict[str, Any]) -> str:
        """Generate Kubernetes YAML manifest."""
        kind = spec.get("kind", "Deployment")
        name = spec.get("name", "app")
        namespace = spec.get("namespace", "default")

        generators = {
            "Deployment": self._generate_deployment_manifest,
            "Service": self._generate_service_manifest,
            "ConfigMap": self._generate_configmap_manifest,
            "Secret": self._generate_secret_manifest,
            "Ingress": self._generate_ingress_manifest,
        }

        generator = generators.get(kind)
        if generator:
            return yaml.dump(
                generator(spec),
                default_flow_style=False,
                sort_keys=False,
            )

        return f"# Unknown kind: {kind}"

    def _generate_deployment_manifest(self, spec: dict[str, Any]) -> dict:
        """Generate Deployment manifest."""
        name = spec.get("name", "app")
        namespace = spec.get("namespace", "default")
        image = spec.get("image", "nginx:latest")
        replicas = spec.get("replicas", 1)
        port = spec.get("port", 80)
        labels = spec.get("labels", {"app": name})
        resources = spec.get("resources", {})

        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": name,
                "namespace": namespace,
                "labels": labels,
            },
            "spec": {
                "replicas": replicas,
                "selector": {"matchLabels": labels},
                "template": {
                    "metadata": {"labels": labels},
                    "spec": {
                        "containers": [
                            {
                                "name": name,
                                "image": image,
                                "ports": [{"containerPort": port}],
                            }
                        ]
                    },
                },
            },
        }

        # Add resource limits if required by policy
        policy: KubernetesSafetyPolicy = self.config.safety_policy  # type: ignore
        if policy.require_resource_limits:
            manifest["spec"]["template"]["spec"]["containers"][0]["resources"] = (
                resources
                or {
                    "requests": {"memory": "128Mi", "cpu": "100m"},
                    "limits": {"memory": "256Mi", "cpu": "200m"},
                }
            )

        return manifest

    def _generate_service_manifest(self, spec: dict[str, Any]) -> dict:
        """Generate Service manifest."""
        name = spec.get("name", "app")
        namespace = spec.get("namespace", "default")
        port = spec.get("port", 80)
        target_port = spec.get("target_port", port)
        service_type = spec.get("type", "ClusterIP")
        selector = spec.get("selector", {"app": name})

        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "spec": {
                "type": service_type,
                "ports": [
                    {
                        "port": port,
                        "targetPort": target_port,
                        "protocol": "TCP",
                    }
                ],
                "selector": selector,
            },
        }

    def _generate_configmap_manifest(self, spec: dict[str, Any]) -> dict:
        """Generate ConfigMap manifest."""
        name = spec.get("name", "config")
        namespace = spec.get("namespace", "default")
        data = spec.get("data", {})

        return {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "data": data,
        }

    def _generate_secret_manifest(self, spec: dict[str, Any]) -> dict:
        """Generate Secret manifest."""
        import base64

        name = spec.get("name", "secret")
        namespace = spec.get("namespace", "default")
        data = spec.get("data", {})
        secret_type = spec.get("type", "Opaque")

        # Base64 encode values
        encoded_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                encoded_data[key] = base64.b64encode(value.encode()).decode()
            else:
                encoded_data[key] = value

        return {
            "apiVersion": "v1",
            "kind": "Secret",
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "type": secret_type,
            "data": encoded_data,
        }

    def _generate_ingress_manifest(self, spec: dict[str, Any]) -> dict:
        """Generate Ingress manifest."""
        name = spec.get("name", "ingress")
        namespace = spec.get("namespace", "default")
        host = spec.get("host", "example.com")
        service_name = spec.get("service_name", "app")
        service_port = spec.get("service_port", 80)
        tls = spec.get("tls", False)

        manifest = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": name,
                "namespace": namespace,
            },
            "spec": {
                "rules": [
                    {
                        "host": host,
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": service_name,
                                            "port": {"number": service_port},
                                        }
                                    },
                                }
                            ]
                        },
                    }
                ]
            },
        }

        if tls:
            manifest["spec"]["tls"] = [
                {
                    "hosts": [host],
                    "secretName": f"{name}-tls",
                }
            ]

        return manifest

    def validate_syntax(self, command: str) -> dict[str, Any]:
        """Validate kubectl command syntax."""
        errors = []
        warnings = []

        parts = command.split()

        if not parts or parts[0] != "kubectl":
            errors.append("Command must start with 'kubectl'")
            return {"valid": False, "errors": errors, "warnings": warnings}

        if len(parts) < 2:
            errors.append("Missing kubectl subcommand")
            return {"valid": False, "errors": errors, "warnings": warnings}

        subcommand = parts[1]
        valid_subcommands = {
            "get", "describe", "apply", "delete", "create",
            "scale", "logs", "exec", "port-forward", "rollout",
            "top", "edit", "label", "annotate", "patch",
            "config", "cluster-info", "api-resources",
        }

        if subcommand not in valid_subcommands:
            warnings.append(f"Unknown subcommand: {subcommand}")

        # Check namespace flag
        policy: KubernetesSafetyPolicy = self.config.safety_policy  # type: ignore
        if policy.require_namespace and "-n" not in command and "--namespace" not in command:
            if "-A" not in command and "--all-namespaces" not in command:
                warnings.append("Consider specifying namespace with -n")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def check_safety(self, command: str) -> dict[str, Any]:
        """Check kubectl command against safety policy."""
        policy: KubernetesSafetyPolicy = self.config.safety_policy  # type: ignore

        # Check delete operations
        if "delete" in command and not policy.allow_delete:
            return {
                "allowed": False,
                "reason": "Delete operations are not allowed",
            }

        # Check exec operations
        if "exec" in command and not policy.allow_exec:
            return {
                "allowed": False,
                "reason": "Exec operations are not allowed",
            }

        # Check namespace restrictions
        for ns in policy.blocked_namespaces:
            if f"-n {ns}" in command or f"--namespace={ns}" in command:
                return {
                    "allowed": False,
                    "reason": f"Operations in namespace '{ns}' are blocked",
                }

        # Check scale limits
        if "scale" in command and "--replicas" in command:
            import re

            match = re.search(r"--replicas[=\s](\d+)", command)
            if match:
                replicas = int(match.group(1))
                if replicas > policy.max_replicas:
                    return {
                        "allowed": False,
                        "reason": f"Replica count {replicas} exceeds limit {policy.max_replicas}",
                    }

        return {"allowed": True}
