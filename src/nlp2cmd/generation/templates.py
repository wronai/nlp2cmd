"""
Iteration 3: Template-Based Generation.

Generate DSL commands from templates using detected intent and entities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TemplateResult:
    """Result of template generation."""
    
    command: str
    template_used: str
    entities_used: dict[str, Any]
    missing_entities: list[str]
    success: bool


class TemplateGenerator:
    """
    Generate DSL commands from templates.
    
    Uses predefined templates filled with extracted entities.
    Falls back to sensible defaults when entities are missing.
    
    Example:
        generator = TemplateGenerator()
        result = generator.generate(
            domain='sql',
            intent='select',
            entities={'table': 'users', 'columns': ['id', 'name']}
        )
        # result.command == "SELECT id, name FROM users;"
    """
    
    SQL_TEMPLATES: dict[str, str] = {
        'select': "SELECT {columns} FROM {table}{where}{order}{limit};",
        'select_all': "SELECT * FROM {table}{where}{order}{limit};",
        'insert': "INSERT INTO {table} ({columns}) VALUES ({values});",
        'update': "UPDATE {table} SET {set_clause}{where};",
        'delete': "DELETE FROM {table}{where};",
        'aggregate': "SELECT {aggregations} FROM {table}{where}{group}{order};",
        'count': "SELECT COUNT(*) FROM {table}{where};",
    }
    
    SHELL_TEMPLATES: dict[str, str] = {
        'find': "find {path} {type_flag} {name_flag} {size_flag} {time_flag}",
        'find_simple': "find {path} -name '{pattern}'",
        'list': "ls -la {path}",
        'list_recursive': "ls -laR {path}",
        'grep': "grep -r '{pattern}' {path}",
        'grep_file': "grep '{pattern}' {file}",
        'process_list': "ps aux | grep {process_name}",
        'process_top': "ps aux --sort=-%{metric} | head -n {limit}",
        'disk_usage': "df -h {path}",
        'dir_size': "du -sh {path}",
        'copy': "cp {flags} {source} {destination}",
        'move': "mv {source} {destination}",
        'remove': "rm {flags} {target}",
        'archive_tar': "tar -czvf {archive} {source}",
        'extract_tar': "tar -xzvf {archive} {destination}",
        'archive_zip': "zip -r {archive} {source}",
        'extract_zip': "unzip {archive} -d {destination}",
    }
    
    DOCKER_TEMPLATES: dict[str, str] = {
        'list': "docker ps {flags}",
        'list_all': "docker ps -a",
        'images': "docker images {flags}",
        'run': "docker run {flags} {image} {command}",
        'run_detached': "docker run -d {ports} {volumes} {env} --name {name} {image}",
        'stop': "docker stop {container}",
        'start': "docker start {container}",
        'restart': "docker restart {container}",
        'logs': "docker logs {flags} {container}",
        'logs_tail': "docker logs --tail {limit} {follow} {container}",
        'exec': "docker exec -it {container} {command}",
        'exec_bash': "docker exec -it {container} /bin/bash",
        'build': "docker build -t {tag} {context}",
        'pull': "docker pull {image}",
        'push': "docker push {image}",
        'rm': "docker rm {flags} {container}",
        'rmi': "docker rmi {flags} {image}",
        'prune': "docker system prune {flags}",
        'compose_up': "docker-compose up {flags}",
        'compose_down': "docker-compose down {flags}",
        'inspect': "docker inspect {target}",
        'stats': "docker stats {container}",
    }
    
    KUBERNETES_TEMPLATES: dict[str, str] = {
        'get': "kubectl get {resource} {name} {namespace} {selector} {output}",
        'get_all': "kubectl get {resource} -A {output}",
        'describe': "kubectl describe {resource} {name} {namespace}",
        'apply': "kubectl apply -f {file} {namespace}",
        'delete': "kubectl delete {resource} {name} {namespace} {selector}",
        'scale': "kubectl scale {resource}/{name} --replicas={replicas} {namespace}",
        'logs': "kubectl logs {pod} {container} {namespace} {follow} --tail={tail}",
        'logs_simple': "kubectl logs {pod} {namespace} --tail={tail}",
        'exec': "kubectl exec -it {pod} {container} {namespace} -- {command}",
        'exec_bash': "kubectl exec -it {pod} {namespace} -- /bin/bash",
        'port_forward': "kubectl port-forward {resource} {ports} {namespace}",
        'rollout_status': "kubectl rollout status {resource}/{name} {namespace}",
        'rollout_restart': "kubectl rollout restart {resource}/{name} {namespace}",
        'top_pods': "kubectl top pods {namespace}",
        'top_nodes': "kubectl top nodes",
        'config_view': "kubectl config view",
        'config_context': "kubectl config use-context {context}",
    }
    
    def __init__(
        self,
        custom_templates: Optional[dict[str, dict[str, str]]] = None,
    ):
        """
        Initialize template generator.
        
        Args:
            custom_templates: Additional templates per domain
        """
        self.templates: dict[str, dict[str, str]] = {
            'sql': self.SQL_TEMPLATES.copy(),
            'shell': self.SHELL_TEMPLATES.copy(),
            'docker': self.DOCKER_TEMPLATES.copy(),
            'kubernetes': self.KUBERNETES_TEMPLATES.copy(),
        }
        
        if custom_templates:
            for domain, domain_templates in custom_templates.items():
                if domain not in self.templates:
                    self.templates[domain] = {}
                self.templates[domain].update(domain_templates)
    
    def generate(
        self,
        domain: str,
        intent: str,
        entities: dict[str, Any],
    ) -> TemplateResult:
        """
        Generate DSL command from template.
        
        Args:
            domain: Target domain (sql, shell, docker, kubernetes)
            intent: Intent (select, find, run, get, etc.)
            entities: Extracted entities
            
        Returns:
            TemplateResult with generated command
        """
        # Get template
        domain_templates = self.templates.get(domain, {})
        template = domain_templates.get(intent)
        
        if not template:
            # Try to find alternative template
            template = self._find_alternative_template(domain, intent, entities)
        
        if not template:
            return TemplateResult(
                command=f"# Unknown: {domain}/{intent}",
                template_used="",
                entities_used=entities,
                missing_entities=[],
                success=False,
            )
        
        # Prepare entities with defaults
        prepared = self._prepare_entities(domain, intent, entities)
        
        # Fill template
        try:
            command = self._fill_template(template, prepared)
            command = self._clean_command(command)
            
            return TemplateResult(
                command=command,
                template_used=template,
                entities_used=prepared,
                missing_entities=self._find_missing(template, prepared),
                success=True,
            )
        except Exception as e:
            return TemplateResult(
                command=f"# Error: {e}",
                template_used=template,
                entities_used=entities,
                missing_entities=[],
                success=False,
            )
    
    def _find_alternative_template(
        self,
        domain: str,
        intent: str,
        entities: dict[str, Any],
    ) -> Optional[str]:
        """Find alternative template based on intent mapping."""
        intent_aliases: dict[str, dict[str, str]] = {
            'sql': {
                'data_retrieval': 'select',
                'query': 'select',
                'fetch': 'select',
                'aggregation': 'aggregate',
            },
            'shell': {
                'file_search': 'find',
                'search': 'find',
                'file_operation': 'list',
                'process': 'process_list',
                'process_monitoring': 'process_top',
                'disk': 'disk_usage',
                'archive': 'archive_tar',
            },
            'docker': {
                'container_list': 'list',
                'container_management': 'list',
                'image_list': 'images',
            },
            'kubernetes': {
                'list': 'get',
                'show': 'get',
                'view': 'get',
            },
        }
        
        domain_aliases = intent_aliases.get(domain, {})
        aliased_intent = domain_aliases.get(intent)
        
        if aliased_intent:
            return self.templates.get(domain, {}).get(aliased_intent)
        
        return None
    
    def _prepare_entities(
        self,
        domain: str,
        intent: str,
        entities: dict[str, Any],
    ) -> dict[str, Any]:
        """Prepare entities with defaults and formatting."""
        result = entities.copy()
        
        if domain == 'sql':
            result = self._prepare_sql_entities(intent, result)
        elif domain == 'shell':
            result = self._prepare_shell_entities(intent, result)
        elif domain == 'docker':
            result = self._prepare_docker_entities(intent, result)
        elif domain == 'kubernetes':
            result = self._prepare_kubernetes_entities(intent, result)
        
        return result
    
    def _prepare_sql_entities(self, intent: str, entities: dict[str, Any]) -> dict[str, Any]:
        """Prepare SQL entities."""
        result = entities.copy()
        
        # Columns
        columns = entities.get('columns', ['*'])
        if isinstance(columns, list):
            result['columns'] = ', '.join(columns)
        elif columns:
            result['columns'] = columns
        else:
            result['columns'] = '*'
        
        # Table default
        result.setdefault('table', 'unknown_table')
        
        # WHERE clause
        filters = entities.get('filters', [])
        if filters:
            where_parts = []
            for f in filters:
                field = f.get('field', '')
                op = f.get('operator', '=')
                value = f.get('value', '')
                if isinstance(value, str):
                    value = f"'{value}'"
                where_parts.append(f"{field} {op} {value}")
            result['where'] = f"\nWHERE {' AND '.join(where_parts)}"
        else:
            result['where'] = ''
        
        # ORDER BY
        ordering = entities.get('ordering', [])
        if ordering:
            order_parts = []
            for o in ordering:
                if isinstance(o, dict):
                    order_parts.append(f"{o.get('field', '')} {o.get('direction', 'ASC')}")
                else:
                    order_parts.append(str(o))
            result['order'] = f"\nORDER BY {', '.join(order_parts)}"
        else:
            result['order'] = ''
        
        # LIMIT
        limit = entities.get('limit')
        if limit:
            result['limit'] = f"\nLIMIT {limit}"
        else:
            result['limit'] = ''
        
        # GROUP BY
        grouping = entities.get('grouping', [])
        if grouping:
            result['group'] = f"\nGROUP BY {', '.join(grouping)}"
        else:
            result['group'] = ''
        
        # Aggregations
        aggregations = entities.get('aggregations', [])
        if aggregations:
            agg_parts = []
            for agg in aggregations:
                func = agg.get('function', 'COUNT')
                field = agg.get('field', '*')
                agg_parts.append(f"{func}({field})")
            result['aggregations'] = ', '.join(agg_parts)
        else:
            result['aggregations'] = 'COUNT(*)'
        
        # SET clause for UPDATE
        values = entities.get('values', {})
        if values:
            set_parts = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" 
                        for k, v in values.items()]
            result['set_clause'] = ', '.join(set_parts)
        else:
            result['set_clause'] = ''
        
        return result
    
    def _prepare_shell_entities(self, intent: str, entities: dict[str, Any]) -> dict[str, Any]:
        """Prepare shell entities."""
        result = entities.copy()
        
        # Path default
        result.setdefault('path', '.')
        
        # Pattern
        pattern = entities.get('pattern', entities.get('file_pattern'))
        if pattern:
            if not pattern.startswith('*'):
                pattern = f"*.{pattern}"
            result['pattern'] = pattern
        else:
            result['pattern'] = '*'
        
        # Find flags
        result['type_flag'] = ''
        if entities.get('target') == 'files':
            result['type_flag'] = '-type f'
        elif entities.get('target') == 'directories':
            result['type_flag'] = '-type d'
        
        result['name_flag'] = f"-name '{result['pattern']}'" if result['pattern'] != '*' else ''
        
        # Size flag
        size = entities.get('size')
        if size and isinstance(size, dict):
            val = size.get('value', 0)
            unit = size.get('unit', 'M')
            result['size_flag'] = f"-size +{val}{unit[0]}"
        else:
            result['size_flag'] = ''
        
        # Time flag
        age = entities.get('age')
        if age and isinstance(age, dict):
            val = age.get('value', 0)
            result['time_flag'] = f"-mtime +{val}"
        else:
            result['time_flag'] = ''
        
        # Process monitoring
        result.setdefault('metric', 'mem')
        result.setdefault('limit', '10')
        result.setdefault('process_name', '')
        
        # Archive
        result.setdefault('archive', 'archive.tar.gz')
        result.setdefault('source', '.')
        result.setdefault('destination', '.')
        
        # Copy/move
        result.setdefault('flags', '')
        result.setdefault('target', '')
        result.setdefault('file', '')
        
        return result
    
    def _prepare_docker_entities(self, intent: str, entities: dict[str, Any]) -> dict[str, Any]:
        """Prepare Docker entities."""
        result = entities.copy()
        
        # Flags default
        result.setdefault('flags', '')
        # Normalize flags extracted from regex (single flag or list)
        flags = result.get('flags')
        if isinstance(flags, list):
            result['flags'] = ' '.join(flags)
        
        # Container/image
        result.setdefault('container', '')
        result.setdefault('image', '')
        result.setdefault('name', 'mycontainer')
        
        # Ports
        ports = entities.get('port')
        if ports:
            if isinstance(ports, dict):
                result['ports'] = f"-p {ports.get('host', 8080)}:{ports.get('container', 80)}"
            else:
                result['ports'] = f"-p {ports}"
        else:
            result['ports'] = ''
        
        # Volumes
        volume = entities.get('volume')
        if volume:
            if isinstance(volume, dict):
                result['volumes'] = f"-v {volume.get('host', '.')}:{volume.get('container', '/app')}"
            else:
                result['volumes'] = f"-v {volume}"
        else:
            result['volumes'] = ''
        
        # Environment
        env = entities.get('env_var')
        if env:
            if isinstance(env, dict):
                result['env'] = f"-e {env.get('name', 'VAR')}={env.get('value', '')}"
            else:
                result['env'] = f"-e {env}"
        else:
            result['env'] = ''
        
        # Logs
        result.setdefault('limit', '100')
        result['follow'] = '-f' if entities.get('follow') else ''
        
        # Command
        result.setdefault('command', '')
        result.setdefault('tag', 'latest')
        result.setdefault('context', '.')
        result.setdefault('target', '')
        
        return result
    
    def _prepare_kubernetes_entities(self, intent: str, entities: dict[str, Any]) -> dict[str, Any]:
        """Prepare Kubernetes entities."""
        result = entities.copy()
        
        # Resource type
        result.setdefault('resource', entities.get('resource_type', 'pods'))
        
        # Name
        name = entities.get('resource_name', entities.get('name', ''))
        result['name'] = name
        
        # Namespace
        ns = entities.get('namespace')
        result['namespace'] = f"-n {ns}" if ns else ''
        
        # Selector
        selector = entities.get('selector')
        result['selector'] = f"-l {selector}" if selector else ''
        
        # Output format
        output = entities.get('output')
        result['output'] = f"-o {output}" if output else ''
        
        # Scale
        result.setdefault('replicas', '1')
        
        # Logs
        result.setdefault('pod', entities.get('pod_name', ''))
        result.setdefault('tail', '100')
        result['follow'] = '-f' if entities.get('follow') else ''
        result['container'] = f"-c {entities.get('container_name')}" if entities.get('container_name') else ''
        
        # Exec
        result.setdefault('command', '/bin/bash')
        
        # Port forward
        ports = entities.get('ports')
        if ports:
            result['ports'] = ports
        else:
            result['ports'] = '8080:80'
        
        # File
        result.setdefault('file', '')
        
        # Context
        result.setdefault('context', '')
        
        return result
    
    def _fill_template(self, template: str, entities: dict[str, Any]) -> str:
        """Fill template with entities."""
        result = template
        
        for key, value in entities.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value) if value else '')
        
        return result
    
    def _clean_command(self, command: str) -> str:
        """Clean up generated command."""
        # Remove multiple spaces
        import re
        command = re.sub(r'\s+', ' ', command)
        
        # Remove trailing/leading spaces
        command = command.strip()
        
        # Remove empty flags
        command = re.sub(r'\s+-[a-zA-Z]+\s+(?=-|$)', ' ', command)
        
        # Clean up again
        command = re.sub(r'\s+', ' ', command)
        
        return command.strip()
    
    def _find_missing(self, template: str, entities: dict[str, Any]) -> list[str]:
        """Find missing entities in template."""
        import re
        placeholders = re.findall(r'\{(\w+)\}', template)
        return [p for p in placeholders if p not in entities or not entities[p]]
    
    def add_template(self, domain: str, intent: str, template: str) -> None:
        """
        Add custom template.
        
        Args:
            domain: Domain name
            intent: Intent name
            template: Template string with {placeholders}
        """
        if domain not in self.templates:
            self.templates[domain] = {}
        self.templates[domain][intent] = template
    
    def get_template(self, domain: str, intent: str) -> Optional[str]:
        """Get template for domain/intent."""
        return self.templates.get(domain, {}).get(intent)
    
    def list_templates(self, domain: str) -> list[str]:
        """List available templates for domain."""
        return list(self.templates.get(domain, {}).keys())
