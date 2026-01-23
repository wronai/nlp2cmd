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
        'remove_all': "find . -name '*.{extension}' -delete",
        'create_dir': "mkdir {directory}",
        'create_file': "touch {file}",
        'rename': "mv {old_name} {new_name}",
        'show_size': "du -h {file_path}",
        'archive_tar': "tar -czvf {archive} {source}",
        'extract_tar': "tar -xzvf {archive} {destination}",
        'archive_zip': "zip -r {archive} {source}",
        'extract_zip': "unzip {archive} -d {destination}",
        # Polish-specific templates
        'file_search': "find {path} -name '*.{extension}' -type f",
        'file_content': "cat {file_path}",
        'file_tail': "tail -{lines} {file_path}",
        'file_size': "du -h {file_path}",
        'file_rename': "mv {old_name} {new_name}",
        'file_delete_all': "find . -name '*.{extension}' -delete",
        'dir_create': "mkdir {directory}",
        'process_monitor': "top -n 1",
        'process_memory': "ps aux --sort=-%mem | head -10",
        'process_cpu': "ps aux --sort=-%cpu | head -10",
        'process_tree': "pstree",
        'process_user': "ps aux | grep {user}",
        'process_zombie': "ps aux | awk '{print $8}' | grep -v '^\\[' | sort | uniq -c",
        'system_monitor': "htop",
        'network_ping': "ping -c 4 {host}",
        'network_port': "netstat -tuln | grep LISTEN",
        'network_lsof': "lsof -i :{port}",
        'network_ip': "ip addr show",
        'network_config': "ifconfig -a",
        'network_scan': "nmap -sn 192.168.1.0/24",
        'network_speed': "curl -o /dev/null -s -w '%{time_total}' http://speedtest.net",
        'network_connections': "ss -tulpn",
        'disk_health': "fsck -n /dev/sda1",
        'disk_defrag': "defrag /dev/sda1",
        'backup_create': "tar -czf backup.tar.gz {source}",
        'backup_copy': "rsync -av {source} {destination}",
        'backup_restore': "tar -xzf backup.tar.gz {file}",
        'backup_integrity': "md5sum {file}",
        'backup_status': "ls -la {path}",
        'backup_cleanup': "find {path} -mtime +7 -delete",
        'backup_size': "du -sh {file}",
        'backup_schedule': "crontab -l",
        'system_update': "apt update && apt upgrade -y",
        'system_clean': "rm -rf /tmp/*",
        'system_logs': "tail -n 50 /var/log/syslog",
        'system_cron': "systemctl status cron",
        'dev_test': "pytest tests/",
        'dev_build_maven': "mvn clean install",
        'dev_install_npm': "npm install",
        'dev_server': "python manage.py runserver",
        'dev_version_node': "node --version",
        'dev_lint': "pylint src/",
        'dev_logs': "tail -f app.log",
        'dev_debug': "python -m pdb script.py",
        'dev_clean': "rm -rf __pycache__",
        'dev_docs': "sphinx-build -b html docs/",
        'security_who': "who",
        'security_last': "last -n 10",
        'security_permissions': "ls -la {file_path}",
        'security_suid': "find / -perm -4000 -type f",
        'security_firewall': "iptables -L",
        'security_logs': "tail -n 100 /var/log/auth.log",
        'security_suspicious': "ps aux | grep -v '\\['",
        'security_packages': "dpkg -l | grep -i security",
        'security_users': "cat /etc/passwd",
        'process_kill': "kill -9 {pid}",
        'process_background': "nohup {command} &",
        'process_script': "./{script}",
        'service_start': "systemctl start {service}",
        'service_stop': "systemctl stop {service}",
        'service_restart': "systemctl restart {service}",
        'service_status': "systemctl status {service}",
        'text_search_errors': "grep -i error {file}",
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
            alternative_template = self._find_alternative_template(domain, intent, entities)
            if alternative_template:
                template = domain_templates.get(alternative_template)
        
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
        """Find alternative template based on intent mapping and context."""
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
        
        # Special handling for shell file_operation - context-aware template selection
        if domain == 'shell' and intent == 'file_operation':
            # Check entities to determine the specific operation
            text_lower = str(entities.get('text', '')).lower()
            
            if 'wszystkie' in text_lower or 'all' in text_lower:
                return 'remove_all'  # For "usuń wszystkie pliki"
            elif 'katalog' in text_lower or 'directory' in text_lower or 'utwórz' in text_lower:
                return 'create_dir'  # For creating directories
            elif 'zmień nazwę' in text_lower or 'rename' in text_lower:
                return 'rename'  # For renaming files
            elif 'rozmiar' in text_lower or 'size' in text_lower:
                return 'show_size'  # For checking file size
            elif 'skopiuj' in text_lower or 'copy' in text_lower:
                return 'copy'  # For copying files
            elif 'przenieś' in text_lower or 'move' in text_lower:
                return 'move'  # For moving files
            elif 'usuń' in text_lower or 'delete' in text_lower or 'remove' in text_lower:
                return 'remove'  # For deleting files
            else:
                return 'list'  # Default fallback
        
        # Standard intent mapping
        domain_aliases = intent_aliases.get(domain, {})
        return domain_aliases.get(intent)
    
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
        
        # Polish-specific defaults
        if intent == 'file_search':
            result.setdefault('extension', entities.get('file_pattern', entities.get('extension', 'py')))
            result.setdefault('path', '.')
        elif intent == 'file_content':
            result.setdefault('file_path', entities.get('target', ''))
        elif intent == 'file_tail':
            result.setdefault('lines', '10')
            result.setdefault('file_path', entities.get('target', ''))
        elif intent == 'file_size':
            result.setdefault('file_path', entities.get('target', ''))
        elif intent == 'file_rename':
            result.setdefault('old_name', entities.get('old_name', ''))
            result.setdefault('new_name', entities.get('new_name', ''))
        elif intent == 'file_delete_all':
            result.setdefault('extension', entities.get('file_pattern', entities.get('extension', 'tmp')))
        elif intent == 'dir_create':
            result.setdefault('directory', entities.get('target', ''))
        elif intent == 'remove_all':
            result.setdefault('extension', entities.get('file_pattern', entities.get('extension', 'tmp')))
        elif intent == 'file_operation':
            # Handle file_operation context-aware
            text_lower = str(entities.get('text', '')).lower()
            if 'wszystkie' in text_lower or 'all' in text_lower:
                result.setdefault('extension', entities.get('file_pattern', entities.get('extension', 'tmp')))
            elif 'katalog' in text_lower or 'directory' in text_lower or 'utwórz' in text_lower:
                result.setdefault('directory', entities.get('target', ''))
            elif 'zmień nazwę' in text_lower or 'rename' in text_lower:
                result.setdefault('old_name', entities.get('old_name', ''))
                result.setdefault('new_name', entities.get('new_name', ''))
            elif 'rozmiar' in text_lower or 'size' in text_lower:
                result.setdefault('file_path', entities.get('target', ''))
            elif 'skopiuj' in text_lower or 'copy' in text_lower:
                result.setdefault('source', entities.get('source', '.'))
                result.setdefault('destination', entities.get('destination', '.'))
            elif 'przenieś' in text_lower or 'move' in text_lower:
                result.setdefault('source', entities.get('source', '.'))
                result.setdefault('destination', entities.get('destination', '.'))
            elif 'usuń' in text_lower or 'delete' in text_lower or 'remove' in text_lower:
                result.setdefault('target', entities.get('target', ''))
            else:
                result.setdefault('target', entities.get('target', ''))
        elif intent == 'process_monitor':
            pass  # Uses top -n 1
        elif intent == 'process_memory':
            pass  # Uses ps aux --sort=-%mem | head -10
        elif intent == 'process_cpu':
            pass  # Uses ps aux --sort=-%cpu | head -10
        elif intent == 'process_tree':
            pass  # Uses pstree
        elif intent == 'process_user':
            result.setdefault('user', 'tom')
        elif intent == 'process_zombie':
            pass  # Uses ps aux | awk command
        elif intent == 'system_monitor':
            pass  # Uses htop
        elif intent == 'network_ping':
            result.setdefault('host', 'google.com')
        elif intent == 'network_port':
            pass  # Uses netstat -tuln | grep LISTEN
        elif intent == 'network_lsof':
            result.setdefault('port', '8080')
        elif intent == 'network_ip':
            pass  # Uses ip addr show
        elif intent == 'network_config':
            pass  # Uses ifconfig -a
        elif intent == 'network_scan':
            pass  # Uses nmap -sn 192.168.1.0/24
        elif intent == 'network_speed':
            pass  # Uses curl command
        elif intent == 'network_connections':
            pass  # Uses ss -tulpn
        elif intent == 'disk_health':
            pass  # Uses fsck -n /dev/sda1
        elif intent == 'disk_defrag':
            pass  # Uses defrag /dev/sda1
        elif intent == 'backup_create':
            result.setdefault('source', entities.get('target', '.'))
        elif intent == 'backup_copy':
            result.setdefault('source', entities.get('source', '.'))
            result.setdefault('destination', entities.get('destination', '.'))
        elif intent == 'backup_restore':
            result.setdefault('file', entities.get('target', ''))
        elif intent == 'backup_integrity':
            result.setdefault('file', entities.get('target', 'backup.tar.gz'))
        elif intent == 'backup_status':
            result.setdefault('path', entities.get('path', '/backup'))
        elif intent == 'backup_cleanup':
            result.setdefault('path', entities.get('path', '/backup'))
        elif intent == 'backup_size':
            result.setdefault('file', entities.get('target', 'backup.tar.gz'))
        elif intent == 'backup_schedule':
            pass  # Uses crontab -l
        elif intent == 'system_update':
            pass  # Uses apt update && apt upgrade -y
        elif intent == 'system_clean':
            pass  # Uses rm -rf /tmp/*
        elif intent == 'system_logs':
            pass  # Uses tail -n 50 /var/log/syslog
        elif intent == 'system_cron':
            pass  # Uses systemctl status cron
        elif intent == 'dev_test':
            pass  # Uses pytest tests/
        elif intent == 'dev_build_maven':
            pass  # Uses mvn clean install
        elif intent == 'dev_install_npm':
            pass  # Uses npm install
        elif intent == 'dev_server':
            pass  # Uses python manage.py runserver
        elif intent == 'dev_version_node':
            pass  # Uses node --version
        elif intent == 'dev_lint':
            result.setdefault('path', 'src')
        elif intent == 'dev_logs':
            result.setdefault('file', 'app.log')
        elif intent == 'dev_debug':
            result.setdefault('script', 'script.py')
        elif intent == 'dev_clean':
            pass  # Uses rm -rf __pycache__
        elif intent == 'dev_docs':
            result.setdefault('path', 'docs')
        elif intent == 'security_who':
            pass  # Uses who
        elif intent == 'security_last':
            pass  # Uses last -n 10
        elif intent == 'security_permissions':
            result.setdefault('file_path', entities.get('file_path', 'config.conf'))
        elif intent == 'security_suid':
            pass  # Uses find / -perm -4000 -type f
        elif intent == 'security_firewall':
            pass  # Uses iptables -L
        elif intent == 'security_logs':
            pass  # Uses tail -n 100 /var/log/auth.log
        elif intent == 'security_suspicious':
            pass  # Uses ps aux | grep -v '\['
        elif intent == 'security_packages':
            pass  # Uses dpkg -l | grep -i security
        elif intent == 'security_users':
            pass  # Uses cat /etc/passwd
        elif intent == 'process_kill':
            result.setdefault('pid', 'PID')
        elif intent == 'process_background':
            result.setdefault('command', 'python script.py')
        elif intent == 'process_script':
            result.setdefault('script', entities.get('target', 'script.sh'))
        elif intent == 'service_start':
            result.setdefault('service', entities.get('service', 'nginx'))
        elif intent == 'service_stop':
            result.setdefault('service', entities.get('service', 'nginx'))
        elif intent == 'service_restart':
            result.setdefault('service', entities.get('service', 'apache2'))
        elif intent == 'service_status':
            result.setdefault('service', entities.get('service', 'docker'))
        elif intent == 'text_search_errors':
            result.setdefault('file', '/var/log/syslog')
        
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
