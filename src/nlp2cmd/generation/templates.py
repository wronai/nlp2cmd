"""
Iteration 3: Template-Based Generation.

Generate DSL commands from templates using detected intent and entities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
import getpass
import json
import os
import re
from pathlib import Path

from nlp2cmd.utils.data_files import find_data_files


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
        'select_distinct': "SELECT DISTINCT {columns} FROM {table}{where}{order}{limit};",
        'insert': "INSERT INTO {table} ({columns}) VALUES ({values});",
        'insert_multiple': "INSERT INTO {table} ({columns}) VALUES {values};",
        'update': "UPDATE {table} SET {set_clause}{where};",
        'delete': "DELETE FROM {table}{where};",
        'truncate': "TRUNCATE TABLE {table};",
        'aggregate': "SELECT {aggregations} FROM {table}{where}{group}{order};",
        'count': "SELECT COUNT(*) FROM {table}{where};",
        'count_distinct': "SELECT COUNT(DISTINCT {column}) FROM {table}{where};",
        'sum': "SELECT SUM({column}) FROM {table}{where};",
        'avg': "SELECT AVG({column}) FROM {table}{where};",
        'min_max': "SELECT MIN({column}), MAX({column}) FROM {table}{where};",
        # Joins
        'join': "SELECT {columns} FROM {table1} {join_type} JOIN {table2} ON {condition}{where}{order}{limit};",
        'inner_join': "SELECT {columns} FROM {table1} INNER JOIN {table2} ON {table1}.{key1} = {table2}.{key2}{where};",
        'left_join': "SELECT {columns} FROM {table1} LEFT JOIN {table2} ON {table1}.{key1} = {table2}.{key2}{where};",
        'right_join': "SELECT {columns} FROM {table1} RIGHT JOIN {table2} ON {table1}.{key1} = {table2}.{key2}{where};",
        'full_join': "SELECT {columns} FROM {table1} FULL OUTER JOIN {table2} ON {table1}.{key1} = {table2}.{key2}{where};",
        # Subqueries
        'subquery_in': "SELECT {columns} FROM {table} WHERE {column} IN (SELECT {subcolumn} FROM {subtable}{subwhere});",
        'subquery_exists': "SELECT {columns} FROM {table} WHERE EXISTS (SELECT 1 FROM {subtable} WHERE {condition});",
        # DDL
        'create_table': "CREATE TABLE {table} ({columns});",
        'create_table_if_not_exists': "CREATE TABLE IF NOT EXISTS {table} ({columns});",
        'drop_table': "DROP TABLE {table};",
        'drop_table_if_exists': "DROP TABLE IF EXISTS {table};",
        'alter_add_column': "ALTER TABLE {table} ADD COLUMN {column} {datatype};",
        'alter_drop_column': "ALTER TABLE {table} DROP COLUMN {column};",
        'alter_rename_column': "ALTER TABLE {table} RENAME COLUMN {old_name} TO {new_name};",
        'alter_modify_column': "ALTER TABLE {table} MODIFY COLUMN {column} {datatype};",
        # Indexes
        'create_index': "CREATE INDEX {index_name} ON {table} ({columns});",
        'create_unique_index': "CREATE UNIQUE INDEX {index_name} ON {table} ({columns});",
        'drop_index': "DROP INDEX {index_name};",
        # Views
        'create_view': "CREATE VIEW {view_name} AS SELECT {columns} FROM {table}{where};",
        'drop_view': "DROP VIEW {view_name};",
        # Window functions
        'window_row_number': "SELECT {columns}, ROW_NUMBER() OVER ({partition} ORDER BY {order_column}) AS row_num FROM {table};",
        'window_rank': "SELECT {columns}, RANK() OVER ({partition} ORDER BY {order_column}) AS rank FROM {table};",
        'window_lag': "SELECT {columns}, LAG({column}, {offset}) OVER ({partition} ORDER BY {order_column}) AS prev_val FROM {table};",
        'window_lead': "SELECT {columns}, LEAD({column}, {offset}) OVER ({partition} ORDER BY {order_column}) AS next_val FROM {table};",
        # CTEs
        'cte': "WITH {cte_name} AS (SELECT {cte_columns} FROM {cte_table}{cte_where}) SELECT {columns} FROM {cte_name}{where};",
        # Transactions
        'begin': "BEGIN;",
        'commit': "COMMIT;",
        'rollback': "ROLLBACK;",
        # Utility
        'describe': "DESCRIBE {table};",
        'show_tables': "SHOW TABLES;",
        'show_databases': "SHOW DATABASES;",
        'use_database': "USE {database};",
        'explain': "EXPLAIN {query};",
    }
    
    SHELL_TEMPLATES: dict[str, str] = {
        'file_operation': "sudo apt-get install {package}",
        'find': "find {path} {type_flag} {name_flag} {size_flag} {time_flag} {exec_flag}",
        'find_simple': "find {path} -name '{pattern}'",
        'count_files': "find '{path}' -maxdepth 1 -mindepth 1 -type f {name_flag_count} | wc -l",
        'count_dirs': "find '{path}' -maxdepth 1 -mindepth 1 -type d {name_flag_count} | wc -l",
        'list': "ls -la {path}",
        'list_recursive': "ls -laR {path}",
        'list_user_directories': "ls -la {path}",
        'list_dirs': "find {path} -maxdepth 1 -type d",
        'grep': "grep -r '{pattern}' {path}",
        'search': "grep -r '{pattern}' {path}",
        'grep_file': "grep '{pattern}' {file}",
        'process': "ps aux",
        'list_processes': "ps aux",
        'process_list': "ps aux | grep {process_name}",
        'process_top': "ps aux --sort=-%{metric} | head -n {limit}",
        'disk_usage': "df -h {path}",
        'dir_size': "du -sh {path}",
        'copy': "cp {flags} {source} {destination}",
        'move': "mv {source} {destination}",
        'remove': "rm {flags} {target}",
        'remove_all': "find . -name '*.{extension}' -delete",
        'create_dir': "mkdir {directory}",
        'copy_file': "cp {source} {destination}",
        'move_file': "mv {source} {destination}",
        'delete_file': "rm {file}",
        'create_directory': "mkdir {directory}",
        'create_file': "touch {file}",
        'rename': "mv {old_name} {new_name}",
        'show_size': "du -h {file_path}",
        'process_kill': "kill -9 {pid}",
        'process_monitor': "top",
        'process_find': "ps aux | grep {process_name}",
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
        'system_start': "sudo systemctl start {service}",
        'system_restart': "sudo systemctl restart {service}",
        'system_shutdown': "sudo systemctl shutdown -h now",
        'system_reboot': "sudo reboot",
        'run_application': "{application}",
        'npm_start': "npm start",
        'run_python': "python {script}",
        'start_server': "{server_command}",
        'service_start': "sudo systemctl start {service}",
        'service_stop': "sudo systemctl stop {service}",
        'service_restart': "sudo systemctl restart {service}",
        'system_monitor': "htop",
        'network_ping': "ping -c 4 {host}",
        'network_port': "netstat -tuln | grep LISTEN",
        'network_lsof': "lsof -i :{port}",
        'network_ip': "ip addr show",
        'network_config': "ifconfig -a",
        'network_scan': "nmap -sn {cidr}",
        'network_speed': "curl -o /dev/null -s -w '%{time_total}' {url}",
        'network_connections': "ss -tulpn",
        'disk_health': "fsck -n {device}",
        'disk_defrag': "defrag {device}",
        'backup_create': "tar -czf backup.tar.gz {source}",
        'backup_copy': "rsync -av {source} {destination}",
        'backup_restore': "tar -xzf backup.tar.gz {file}",
        'backup_integrity': "md5sum {file}",
        'backup_status': "ls -la {path}",
        'backup_cleanup': "find {path} -mtime +7 -delete",
        'backup_size': "du -sh {file}",
        'backup_schedule': "crontab -l",
        'system_update': "apt list --upgradable 2>/dev/null | grep -v 'WARNING:' || sudo apt update && sudo apt upgrade -y",
        'system_maintenance': "apt list --upgradable 2>/dev/null | grep -v 'WARNING:' || sudo apt update && sudo apt upgrade -y",
        'system_clean': "rm -rf /tmp/*",
        'system_logs': "tail -n 50 {file}",
        'system_cron': "systemctl status cron",
        'dev_test': "pytest tests/",
        'dev_build_maven': "mvn clean install",
        'dev_install_npm': "npm install",
        'dev_server': "python manage.py runserver",
        'dev_version_node': "node --version",
        'dev_lint': "pylint src/",
        'dev_logs': "tail -f {file}",
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
        'git_status': "git status",
        'git_branch': "git branch --show-current",
        'git_log': "git log --oneline -n {limit}",
        # Browser/URL opening (cross-platform)
        'open_url': "xdg-open '{url}'",
        'open_browser': "xdg-open '{url}'",
        'browse': "xdg-open '{url}'",
        'search_web': "xdg-open 'https://www.google.com/search?q={query}'",
        # Text processing
        'text_head': "head -n {lines} {file}",
        'text_tail': "tail -n {lines} {file}",
        'text_tail_follow': "tail -f {file}",
        'text_wc': "wc {flags} {file}",
        'text_wc_lines': "wc -l {file}",
        'text_wc_words': "wc -w {file}",
        'text_sort': "sort {flags} {file}",
        'text_sort_reverse': "sort -r {file}",
        'text_sort_numeric': "sort -n {file}",
        'text_uniq': "sort {file} | uniq",
        'text_uniq_count': "sort {file} | uniq -c",
        'text_cut': "cut -d'{delimiter}' -f{field} {file}",
        'text_awk': "awk '{print ${field}}' {file}",
        'text_awk_pattern': "awk '/{pattern}/ {print}' {file}",
        'text_sed': "sed 's/{pattern}/{replacement}/g' {file}",
        'text_sed_inplace': "sed -i 's/{pattern}/{replacement}/g' {file}",
        'text_tr': "tr '{from_chars}' '{to_chars}'",
        'text_tr_lower': "tr '[:upper:]' '[:lower:]'",
        'text_tr_upper': "tr '[:lower:]' '[:upper:]'",
        'text_diff': "diff {file1} {file2}",
        'text_diff_unified': "diff -u {file1} {file2}",
        'text_cat': "cat {file}",
        'text_cat_number': "cat -n {file}",
        'text_less': "less {file}",
        # Permissions
        'perm_chmod': "chmod {mode} {path}",
        'perm_chmod_recursive': "chmod -R {mode} {path}",
        'perm_chmod_exec': "chmod +x {path}",
        'perm_chown': "chown {owner}:{group} {path}",
        'perm_chown_recursive': "chown -R {owner}:{group} {path}",
        # Users
        'user_whoami': "whoami",
        'user_id': "id {user}",
        'user_list': "cat /etc/passwd | cut -d: -f1",
        'user_groups': "groups {user}",
        # SSH/SCP
        'ssh_connect': "ssh {user}@{host}",
        'ssh_connect_port': "ssh -p {port} {user}@{host}",
        'ssh_copy': "scp {source} {user}@{host}:{destination}",
        'ssh_copy_recursive': "scp -r {source} {user}@{host}:{destination}",
        'ssh_keygen': "ssh-keygen -t {type} -b {bits} -C '{comment}'",
        'ssh_keygen_default': "ssh-keygen -t ed25519",
        # Environment
        'env_show': "printenv",
        'env_show_var': "echo ${variable}",
        'env_export': "export {variable}={value}",
        'env_path': "echo $PATH",
        # Cron
        'cron_list': "crontab -l",
        'cron_edit': "crontab -e",
        'cron_remove': "crontab -r",
        # System info
        'sys_uname': "uname -a",
        'sys_uptime': "uptime",
        'sys_hostname': "hostname",
        'sys_date': "date",
        'sys_date_format': "date '+{format}'",
        'sys_cal': "cal",
        'sys_cal_year': "cal {year}",
        'sys_free': "free -h",
        'sys_lscpu': "lscpu",
        'sys_lsblk': "lsblk",
        'sys_mount': "mount | column -t",
        'sys_dmesg': "dmesg | tail -n {lines}",
        # History
        'history': "history | tail -n {lines}",
        'history_search': "history | grep '{pattern}'",
        # Aliases
        'alias_list': "alias",
        'alias_set': "alias {name}='{command}'",
        # Watch
        'watch': "watch -n {interval} '{command}'",
        'watch_default': "watch -n 2 '{command}'",
        # Download
        'download_wget': "wget {url}",
        'download_wget_output': "wget -O {output} {url}",
        'download_curl': "curl -O {url}",
        'download_curl_output': "curl -o {output} {url}",
        'download_curl_api': "curl -X {method} -H 'Content-Type: application/json' {url}",
        # JSON
        'json_jq': "jq '{filter}' {file}",
        'json_jq_pretty': "cat {file} | jq .",
        'json_jq_keys': "jq 'keys' {file}",
        # Xargs
        'xargs': "xargs -I {} {command}",
        'xargs_parallel': "xargs -P {jobs} -I {} {command}",
    }
    
    DOCKER_TEMPLATES: dict[str, str] = {
        'list': "docker ps {flags}",
        'list_all': "docker ps -a",
        'images': "docker images {flags}",
        'images_all': "docker images -a",
        'run': "docker run {flags} {ports} {image} {command}",
        'run_detached': "docker run -d {ports} {volumes} {env} --name {name} {image}",
        'stop': "docker stop {container}",
        'start': "docker start {container}",
        'restart': "docker restart {container}",
        'docker_run': "docker run {image}",
        'docker_stop': "docker stop {container}",
        'docker_build': "docker build -t {tag} {context}",
        'docker_compose_up': "docker-compose up -d",
        'docker_compose_down': "docker-compose down",
        'logs': "docker logs {flags} {container}",
        'logs_tail': "docker logs --tail {limit} {follow} {container}",
        'exec': "docker exec -it {container} {command}",
        'exec_bash': "docker exec -it {container} /bin/bash",
        'build': "docker build -t {tag} {context}",
        'build_no_cache': "docker build --no-cache -t {tag} {context}",
        'pull': "docker pull {image}",
        'push': "docker push {image}",
        'tag': "docker tag {source} {target}",
        'rm': "docker rm {flags} {container}",
        'rmi': "docker rmi {flags} {image}",
        'prune': "docker system prune {flags}",
        'prune_all': "docker system prune -a -f",
        'inspect': "docker inspect {target}",
        'inspect_format': "docker inspect --format '{{{{json .{field}}}}}' {target}",
        'stats': "docker stats {container}",
        'stats_all': "docker stats --no-stream",
        'network_list': "docker network ls",
        'network_create': "docker network create {name}",
        'network_inspect': "docker network inspect {name}",
        'network_rm': "docker network rm {name}",
        'volume_list': "docker volume ls",
        'volume_create': "docker volume create {name}",
        'volume_inspect': "docker volume inspect {name}",
        'volume_rm': "docker volume rm {name}",
        'cp_to': "docker cp {source} {container}:{destination}",
        'cp_from': "docker cp {container}:{source} {destination}",
        'diff': "docker diff {container}",
        'history': "docker history {image}",
        'save': "docker save -o {output} {image}",
        'load': "docker load -i {input}",
        'compose_up': "docker-compose up -d",
        'compose_up_build': "docker-compose up -d --build",
        'compose_down': "docker-compose down",
        'compose_down_volumes': "docker-compose down -v",
        'compose_ps': "docker-compose ps",
        'compose_logs': "docker-compose logs {flags} {service}",
        'compose_build': "docker-compose build {service}",
        'compose_restart': "docker-compose restart {service}",
        'compose_exec': "docker-compose exec {service} {command}",
        'compose_pull': "docker-compose pull",
        'compose_config': "docker-compose config",
    }
    
    KUBERNETES_TEMPLATES: dict[str, str] = {
        'get': "kubectl get {resource} {name} {namespace} {selector} {output}",
        'get_all': "kubectl get {resource} -A {output}",
        'describe': "kubectl describe {resource} {name} {namespace}",
        'apply': "kubectl apply -f {file} {namespace}",
        'apply_recursive': "kubectl apply -R -f {directory} {namespace}",
        'delete': "kubectl delete {resource} {name} {namespace} {selector}",
        'delete_force': "kubectl delete {resource} {name} {namespace} --force --grace-period=0",
        'create': "kubectl create {resource} {name} --image={image} {namespace}",
        'scale': "kubectl scale {resource}/{name} --replicas={replicas} {namespace}",
        'logs': "kubectl logs {pod} {container} {namespace} {follow} --tail={tail}",
        'logs_simple': "kubectl logs {pod} {namespace} --tail={tail}",
        'logs_previous': "kubectl logs {pod} {namespace} --previous",
        'exec': "kubectl exec -it {pod} {container} {namespace} -- {command}",
        'exec_bash': "kubectl exec -it {pod} {namespace} -- /bin/bash",
        'port_forward': "kubectl port-forward {resource} {ports} {namespace}",
        'rollout': "kubectl rollout status {resource}/{name} {namespace}",
        'rollout_status': "kubectl rollout status {resource}/{name} {namespace}",
        'rollout_restart': "kubectl rollout restart {resource}/{name} {namespace}",
        'rollout_history': "kubectl rollout history {resource}/{name} {namespace}",
        'rollout_undo': "kubectl rollout undo {resource}/{name} {namespace}",
        'rollout_pause': "kubectl rollout pause {resource}/{name} {namespace}",
        'rollout_resume': "kubectl rollout resume {resource}/{name} {namespace}",
        'top_pods': "kubectl top pods {namespace}",
        'top_nodes': "kubectl top nodes",
        'config_view': "kubectl config view",
        'config_context': "kubectl config use-context {context}",
        'config_current': "kubectl config current-context",
        'events': "kubectl get events {namespace} --sort-by='.lastTimestamp'",
        'events_watch': "kubectl get events {namespace} -w",
        'configmap_get': "kubectl get configmap {name} {namespace} {output}",
        'configmap_create': "kubectl create configmap {name} --from-file={file} {namespace}",
        'configmap_create_literal': "kubectl create configmap {name} --from-literal={key}={value} {namespace}",
        'configmap_delete': "kubectl delete configmap {name} {namespace}",
        'secret_get': "kubectl get secret {name} {namespace} {output}",
        'secret_decode': "kubectl get secret {name} {namespace} -o jsonpath='{{.data.{key}}}' | base64 -d",
        'secret_create': "kubectl create secret generic {name} --from-literal={key}={value} {namespace}",
        'secret_create_file': "kubectl create secret generic {name} --from-file={file} {namespace}",
        'secret_delete': "kubectl delete secret {name} {namespace}",
        'namespace_list': "kubectl get namespaces",
        'namespace_create': "kubectl create namespace {name}",
        'namespace_delete': "kubectl delete namespace {name}",
        'cluster_info': "kubectl cluster-info",
        'api_resources': "kubectl api-resources",
        'explain': "kubectl explain {resource}",
        'run_pod': "kubectl run {name} --image={image} {namespace} --restart=Never",
        'create_deployment': "kubectl create deployment {name} --image={image} {namespace}",
        'expose': "kubectl expose {resource} {name} --port={port} --target-port={target_port} {namespace}",
        'annotate': "kubectl annotate {resource} {name} {annotation} {namespace}",
        'label': "kubectl label {resource} {name} {label} {namespace}",
        'cordon': "kubectl cordon {node}",
        'uncordon': "kubectl uncordon {node}",
        'drain': "kubectl drain {node} --ignore-daemonsets --delete-emptydir-data",
        'taint': "kubectl taint nodes {node} {taint}",
    }
    
    BROWSER_TEMPLATES: dict[str, str] = {
        'web_action': "# Browser action: {action} on {target}",
        'navigate': "xdg-open '{url}'",
        'click': "# Click: {element}",
        'fill_form': "# Fill form: {form_data}",
        'google_search': "xdg-open 'https://www.google.com/search?q={query}'",
        'github_search': "xdg-open 'https://github.com/search?q={query}'",
        'amazon_search': "xdg-open 'https://www.amazon.com/s?k={query}'",
    }
    
    GIT_TEMPLATES: dict[str, str] = {
        'status': "git status",
        'status_short': "git status -s",
        'log': "git log --oneline -n {limit}",
        'log_graph': "git log --oneline --graph --all -n {limit}",
        'log_author': "git log --author='{author}' --oneline -n {limit}",
        'diff': "git diff {file}",
        'diff_staged': "git diff --staged",
        'diff_commit': "git diff {commit1} {commit2}",
        'branch': "git branch",
        'branch_all': "git branch -a",
        'branch_create': "git branch {name}",
        'branch_delete': "git branch -d {name}",
        'branch_delete_force': "git branch -D {name}",
        'checkout': "git checkout {branch}",
        'checkout_create': "git checkout -b {branch}",
        'checkout_file': "git checkout -- {file}",
        'switch': "git switch {branch}",
        'switch_create': "git switch -c {branch}",
        'pull': "git pull {remote} {branch}",
        'pull_rebase': "git pull --rebase {remote} {branch}",
        'push': "git push {remote} {branch}",
        'push_force': "git push --force-with-lease {remote} {branch}",
        'push_tags': "git push --tags",
        'push_set_upstream': "git push -u {remote} {branch}",
        'commit': "git commit -m '{message}'",
        'commit_amend': "git commit --amend",
        'commit_all': "git commit -am '{message}'",
        'add': "git add {file}",
        'add_all': "git add -A",
        'add_patch': "git add -p {file}",
        'stash': "git stash",
        'stash_message': "git stash push -m '{message}'",
        'stash_list': "git stash list",
        'stash_pop': "git stash pop",
        'stash_apply': "git stash apply {stash}",
        'stash_drop': "git stash drop {stash}",
        'merge': "git merge {branch}",
        'merge_no_ff': "git merge --no-ff {branch}",
        'merge_abort': "git merge --abort",
        'rebase': "git rebase {branch}",
        'rebase_interactive': "git rebase -i {commit}",
        'rebase_abort': "git rebase --abort",
        'rebase_continue': "git rebase --continue",
        'reset': "git reset {commit}",
        'reset_soft': "git reset --soft {commit}",
        'reset_hard': "git reset --hard {commit}",
        'reset_file': "git reset HEAD {file}",
        'revert': "git revert {commit}",
        'clone': "git clone {url}",
        'clone_shallow': "git clone --depth 1 {url}",
        'clone_branch': "git clone -b {branch} {url}",
        'remote': "git remote -v",
        'remote_add': "git remote add {name} {url}",
        'remote_remove': "git remote remove {name}",
        'remote_set_url': "git remote set-url {name} {url}",
        'fetch': "git fetch {remote}",
        'fetch_all': "git fetch --all",
        'fetch_prune': "git fetch --prune",
        'tag': "git tag",
        'tag_create': "git tag {name}",
        'tag_annotated': "git tag -a {name} -m '{message}'",
        'tag_delete': "git tag -d {name}",
        'tag_push': "git push {remote} {name}",
        'blame': "git blame {file}",
        'show': "git show {commit}",
        'show_file': "git show {commit}:{file}",
        'cherry_pick': "git cherry-pick {commit}",
        'cherry_pick_no_commit': "git cherry-pick -n {commit}",
        'clean': "git clean -fd",
        'clean_dry': "git clean -fdn",
        'reflog': "git reflog -n {limit}",
        'bisect_start': "git bisect start",
        'bisect_good': "git bisect good {commit}",
        'bisect_bad': "git bisect bad {commit}",
        'bisect_reset': "git bisect reset",
        'worktree_list': "git worktree list",
        'worktree_add': "git worktree add {path} {branch}",
        'submodule_init': "git submodule init",
        'submodule_update': "git submodule update --init --recursive",
        'config_list': "git config --list",
        'config_get': "git config {key}",
        'config_set': "git config {scope} {key} '{value}'",
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
            'git': self.GIT_TEMPLATES.copy(),
            'browser': self.BROWSER_TEMPLATES.copy(),
        }

        self.defaults: dict[str, Any] = {}
        self._defaults_loaded = False
        self._templates_loaded = False
        self._load_defaults_from_json()
        self._load_templates_from_json()

        strict = str(os.environ.get("NLP2CMD_STRICT_CONFIG") or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "y",
            "on",
        }
        if strict:
            if not self._defaults_loaded:
                raise FileNotFoundError(
                    "Template defaults not loaded. Expected defaults.json to be available in the package "
                    "data dir or user config dir, or set NLP2CMD_DEFAULTS_FILE."
                )
            if not self._templates_loaded:
                raise FileNotFoundError(
                    "Templates not loaded. Expected templates.json to be available in the package data dir "
                    "or user config dir, or set NLP2CMD_TEMPLATES_FILE."
                )
        
        if custom_templates:
            for domain, domain_templates in custom_templates.items():
                if domain not in self.templates:
                    self.templates[domain] = {}
                self.templates[domain].update(domain_templates)

    def _load_defaults_from_json(self) -> None:
        for p in find_data_files(
            explicit_path=os.environ.get("NLP2CMD_DEFAULTS_FILE"),
            default_filename="defaults.json",
        ):
            try:
                payload = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(payload, dict):
                self._defaults_loaded = True
                self.defaults.update(payload)

    def _load_templates_from_json(self) -> None:
        for p in find_data_files(
            explicit_path=os.environ.get("NLP2CMD_TEMPLATES_FILE"),
            default_filename="templates.json",
        ):
            try:
                payload = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue

            self._templates_loaded = True

            # Expected format: {"shell": {"intent": "template"}, "docker": {...}, ...}
            for domain, templates in payload.items():
                if not isinstance(domain, str) or not domain:
                    continue
                if not isinstance(templates, dict):
                    continue

                bucket = self.templates.setdefault(domain, {})
                for intent, template in templates.items():
                    if isinstance(intent, str) and intent and isinstance(template, str) and template:
                        bucket[intent] = template

    def _get_default(self, key: str, fallback: Any) -> Any:
        if key in self.defaults:
            v = self.defaults.get(key)
            return v if v is not None and v != "" else fallback
        return fallback
    
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
        # Normalize some domain buckets from patterns.json to domains we can generate.
        # We only have templates for high-level domains like: shell/sql/docker/kubernetes.
        normalized_domain = domain
        normalized_intent = intent
        normalized_entities = dict(entities or {})

        if normalized_domain == "shell_utilities":
            # Treat shell utilities as shell commands.
            normalized_domain = "shell"
            # We generally don't have dedicated templates for every utility.
            # Fallback to running the utility directly.
            if normalized_intent not in self.templates.get("shell", {}):
                normalized_entities.setdefault("application", normalized_intent)
                normalized_intent = "run_application"

        # Some detectors emit utility-like domains that still map to shell commands.
        effective_domain = domain
        if domain not in self.templates:
            if domain in {"utility", "networking_ext", "hardware_info", "data_processing"}:
                effective_domain = "shell"

        # Get template
        domain_templates = self.templates.get(effective_domain, {})
        template = domain_templates.get(intent)
        
        # Special case: for shell domain with list intent, always check for alternatives
        if normalized_domain == 'shell' and normalized_intent == 'list':
            alternative_template = self._find_alternative_template(
                normalized_domain,
                normalized_intent,
                normalized_entities,
            )
            if alternative_template and alternative_template != normalized_intent:
                template = domain_templates.get(alternative_template)
        # Special case: shell file_operation should always map based on text context
        elif normalized_domain == 'shell' and normalized_intent == 'file_operation':
            alternative_template = self._find_alternative_template(
                normalized_domain,
                normalized_intent,
                normalized_entities,
            )
            if alternative_template and alternative_template != normalized_intent:
                template = domain_templates.get(alternative_template)
        elif not template:
            # Try to find alternative template
            alternative_template = self._find_alternative_template(effective_domain, intent, entities)
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
        prepared = self._prepare_entities(effective_domain, intent, entities)
        
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
                'network': 'network_ip',
            },
            'docker': {
                'container_list': 'list',
                'container_management': 'list',
                'image_list': 'images',
                'remove': 'rm',
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
        
        # Special handling for list intent when target is directories
        if domain == 'shell' and intent == 'list' and entities.get('target') == 'directories':
            return 'list_dirs'
        
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
                    direction = str(o.get('direction', 'ASC') or 'ASC').upper()
                    if direction not in {'ASC', 'DESC'}:
                        direction = 'ASC'
                    order_parts.append(f"{o.get('field', '')} {direction}")
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
        elif entities.get('aggregation'):
            func = str(entities.get('aggregation') or 'count').upper()
            col = '*'
            cols = entities.get('columns')
            if isinstance(cols, list) and cols:
                col = str(cols[0])
            elif isinstance(cols, str) and cols:
                col = cols
            if func == 'AVG':
                result['aggregations'] = f"AVG({col})"
            elif func == 'SUM':
                result['aggregations'] = f"SUM({col})"
            elif func == 'MIN':
                result['aggregations'] = f"MIN({col})"
            elif func == 'MAX':
                result['aggregations'] = f"MAX({col})"
            else:
                result['aggregations'] = f"COUNT({col})"
        else:
            result['aggregations'] = 'COUNT(*)'

        if intent == 'select' and (entities.get('aggregation') or aggregations):
            result['columns'] = result.get('aggregations', result.get('columns', '*'))
        
        # SET clause for UPDATE
        values = entities.get('values', {})
        if values:
            set_parts = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" 
                        for k, v in values.items()]
            result['set_clause'] = ', '.join(set_parts)
        else:
            result['set_clause'] = ''
        
        return result

    def _get_user_home_dir(self, username: str) -> str:
        if os.name != "posix":
            return f"~{username}"

        if username == "root":
            return "/root"

        try:
            import pwd  # noqa: WPS433

            return pwd.getpwnam(username).pw_dir
        except Exception:
            return f"/home/{username}"

    def _apply_shell_path_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
        if 'user' in entities and entities['user'] == 'current':
            result.setdefault('path', '~')
        elif 'username' in entities:
            username = entities['username']
            if username == 'root':
                result['path'] = '/root'
            elif username.lower() in ['folders', 'użytkownika', 'usera', 'user', 'użytkownik']:
                result['path'] = '~'
            else:
                result['path'] = self._get_user_home_dir(str(username))
        else:
            text_lower = str(entities.get('text') or '').lower()
            if any(word in text_lower for word in ['usera', 'użytkownika', 'user', 'użytkownik']):
                if intent == 'list':
                    result['path'] = '~'
                else:
                    result.setdefault('path', '.')
            else:
                result.setdefault('path', '.')

    def _apply_shell_pattern_defaults(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        pattern = entities.get('pattern', entities.get('file_pattern'))
        if pattern:
            if not pattern.startswith('*'):
                pattern = f"*.{pattern}"
            result['pattern'] = pattern
        else:
            result['pattern'] = '*'

        if result.get('pattern') and result.get('pattern') != '*':
            result['name_flag_count'] = f"-name '{result['pattern']}'"
        else:
            result['name_flag_count'] = ''

    def _apply_shell_find_flags(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
        target = self._infer_shell_find_target(intent, entities)
        result['type_flag'] = self._build_shell_find_type_flag(target)
        result['name_flag'] = self._build_shell_find_name_flag(result.get('pattern', '*'))
        result['exec_flag'] = self._build_shell_find_exec_flag(intent, entities)
        result['size_flag'] = self._build_shell_find_size_flag(entities)
        result['time_flag'] = self._build_shell_find_time_flag(entities)

    def _infer_shell_find_target(self, intent: str, entities: dict[str, Any]) -> str:
        target = entities.get('target')
        if not target and intent == 'find':
            text_lower = str(entities.get('text') or '').lower()
            if any(x in text_lower for x in ('pliki', 'files', 'file ')):
                return 'files'
            if any(x in text_lower for x in ('katalogi', 'directories', 'folder', 'folders')):
                return 'directories'
        return str(target or '')

    def _build_shell_find_type_flag(self, target: str) -> str:
        if target == 'files':
            return '-type f'
        if target == 'directories':
            return '-type d'
        return ''

    def _build_shell_find_name_flag(self, pattern: str) -> str:
        return f"-name '{pattern}'" if pattern and pattern != '*' else ''

    def _build_shell_find_exec_flag(self, intent: str, entities: dict[str, Any]) -> str:
        if intent != 'find':
            return ''
        text_lower = str(entities.get('text') or '').lower()
        if any(x in text_lower for x in ('wyświetl', 'wyswietl', 'lista', 'listę', 'liste', 'list')):
            return '-ls'
        return ''

    def _build_shell_find_size_flag(self, entities: dict[str, Any]) -> str:
        size = entities.get('size')
        text = str(entities.get('text', ''))
        size_operator = str(entities.get('size_operator') or entities.get('operator') or '>')
        if "mniejsz" in text.lower() or "smaller" in text.lower():
            size_operator = '<'
        elif "większ" in text.lower() or "larger" in text.lower() or "bigger" in text.lower():
            size_operator = '>'

        if size and isinstance(size, dict):
            val = size.get('value', 0)
            unit = str(size.get('unit', 'M') or 'M').upper()
            sign = '+' if size_operator in {'>', '>='} else '-' if size_operator in {'<', '<='} else ''
            return f"-size {sign}{val}{unit[0]}"
        if isinstance(size, str) and size.strip():
            m = re.match(r"^(\d+)\s*([a-zA-Z]+)$", size.strip())
            if m:
                sign = '+' if size_operator in {'>', '>='} else '-' if size_operator in {'<', '<='} else ''
                return f"-size {sign}{m.group(1)}{m.group(2).upper()}"
        return ''

    def _build_shell_find_time_flag(self, entities: dict[str, Any]) -> str:
        age = entities.get('age')
        if age and isinstance(age, dict):
            val = age.get('value', 0)
            text = str(entities.get('text', ''))
            time_operator = '+'
            if "ostatnich" in text.lower() or "ostatnie" in text.lower() or "last" in text.lower() or "recent" in text.lower():
                time_operator = '-'
            elif "starsze" in text.lower() or "older" in text.lower():
                time_operator = '+'
            return f"-mtime {time_operator}{val}"
        return ''

    def _apply_shell_common_defaults(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('metric', 'mem')
        result.setdefault('limit', '10')
        result.setdefault('process_name', '')

        result.setdefault('archive', 'archive.tar.gz')
        result.setdefault('source', '.')
        result.setdefault('destination', '.')

        result.setdefault('flags', '')
        result.setdefault('target', '')
        result.setdefault('file', '')

    def _apply_shell_text_processing_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
        self._apply_shell_text_tail_defaults(intent, entities, result)
        self._apply_shell_text_cat_defaults(intent, entities, result)
        self._apply_shell_json_defaults(intent, entities, result)
        self._apply_shell_text_wc_defaults(intent, entities, result)

    def _apply_shell_file_default(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        if result.get('file'):
            return
        result['file'] = (
            entities.get('file')
            or entities.get('path')
            or entities.get('target')
            or entities.get('filename', '')
        )

    def _apply_shell_text_tail_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
        if intent not in {'text_tail', 'text_head', 'text_tail_follow'}:
            return
        result.setdefault('lines', str(entities.get('lines', entities.get('limit', '10'))))

        self._apply_shell_file_default(entities, result)
        if not result.get('file'):
            result['file'] = 'app.log'

        text_lower = str(entities.get('text') or '').lower()
        if not result.get('lines') or str(result.get('lines')) == '10':
            m = re.search(r"\b(\d{1,4})\s*(?:lini\w*|line\w*)\b", text_lower)
            if m:
                result['lines'] = m.group(1)

    def _apply_shell_text_cat_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
        if intent not in {'text_cat', 'text_cat_number'}:
            return
        self._apply_shell_file_default(entities, result)

    def _apply_shell_json_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
        if intent not in {'json_jq', 'json_jq_pretty', 'json_jq_keys'}:
            return
        self._apply_shell_file_default(entities, result)
        if not result.get('filter'):
            result['filter'] = '.'

    def _apply_shell_text_wc_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
        if intent not in {'text_wc', 'text_wc_lines', 'text_wc_words'}:
            return
        self._apply_shell_file_default(entities, result)
        if not result.get('file'):
            result['file'] = 'app.log'

        if intent == 'text_wc_lines':
            result.setdefault('flags', '-l')
            return
        if intent == 'text_wc_words':
            result.setdefault('flags', '-w')
            return

        if not result.get('flags'):
            text_lower = str(entities.get('text') or '').lower()
            if any(x in text_lower for x in ('linie', 'linijek', 'lines')):
                result['flags'] = '-l'
            elif any(x in text_lower for x in ('słow', 'slow', 'words')):
                result['flags'] = '-w'

    def _shell_intent_file_search(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('extension', entities.get('file_pattern', entities.get('extension', 'py')))
        result.setdefault('path', '.')

    def _shell_intent_file_content(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('file_path', entities.get('target', ''))

    def _shell_intent_file_tail(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('lines', '10')
        result.setdefault('file_path', entities.get('target', ''))

    def _shell_intent_file_size(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('file_path', entities.get('target', ''))

    def _shell_intent_file_rename(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('old_name', entities.get('old_name', ''))
        result.setdefault('new_name', entities.get('new_name', ''))

    def _shell_intent_file_delete_all(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('extension', entities.get('file_pattern', entities.get('extension', 'tmp')))

    def _shell_intent_dir_create(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('directory', entities.get('target', ''))

    def _shell_intent_remove_all(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('extension', entities.get('file_pattern', entities.get('extension', 'tmp')))

    def _shell_intent_file_operation(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        text_lower = str(entities.get('text', '')).lower()
        handlers = (
            (self._shell_file_op_is_all, self._shell_file_op_all),
            (self._shell_file_op_is_directory, self._shell_file_op_directory),
            (self._shell_file_op_is_rename, self._shell_file_op_rename),
            (self._shell_file_op_is_size, self._shell_file_op_size),
            (self._shell_file_op_is_copy, self._shell_file_op_copy),
            (self._shell_file_op_is_move, self._shell_file_op_move),
            (self._shell_file_op_is_delete, self._shell_file_op_delete),
        )
        for predicate, handler in handlers:
            if predicate(text_lower):
                handler(entities, result)
                return
        self._shell_file_op_default(entities, result)

    def _shell_file_op_is_all(self, text_lower: str) -> bool:
        return 'wszystkie' in text_lower or 'all' in text_lower

    def _shell_file_op_is_directory(self, text_lower: str) -> bool:
        return 'katalog' in text_lower or 'directory' in text_lower or 'utwórz' in text_lower

    def _shell_file_op_is_rename(self, text_lower: str) -> bool:
        return 'zmień nazwę' in text_lower or 'rename' in text_lower

    def _shell_file_op_is_size(self, text_lower: str) -> bool:
        return 'rozmiar' in text_lower or 'size' in text_lower

    def _shell_file_op_is_copy(self, text_lower: str) -> bool:
        return 'skopiuj' in text_lower or 'copy' in text_lower

    def _shell_file_op_is_move(self, text_lower: str) -> bool:
        return 'przenieś' in text_lower or 'move' in text_lower

    def _shell_file_op_is_delete(self, text_lower: str) -> bool:
        return 'usuń' in text_lower or 'delete' in text_lower or 'remove' in text_lower

    def _shell_file_op_all(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('extension', entities.get('file_pattern', entities.get('extension', 'tmp')))

    def _shell_file_op_directory(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('directory', entities.get('target', ''))

    def _shell_file_op_rename(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('old_name', entities.get('old_name', ''))
        result.setdefault('new_name', entities.get('new_name', ''))

    def _shell_file_op_size(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('file_path', entities.get('target', ''))

    def _shell_file_op_copy(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('source', entities.get('source', '.'))
        result.setdefault('destination', entities.get('destination', '.'))

    def _shell_file_op_move(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('source', entities.get('source', '.'))
        result.setdefault('destination', entities.get('destination', '.'))

    def _shell_file_op_delete(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('target', entities.get('target', ''))

    def _shell_file_op_default(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('target', entities.get('target', ''))

    def _shell_intent_process_user(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('user', self._get_default('shell.user', os.environ.get('USER') or getpass.getuser()))

    def _shell_intent_network_ping(self, result: dict[str, Any]) -> None:
        result.setdefault('host', self._get_default('shell.ping_host', os.environ.get('NLP2CMD_DEFAULT_PING_HOST') or 'google.com'))

    def _shell_intent_network_lsof(self, result: dict[str, Any]) -> None:
        result.setdefault('port', self._get_default('shell.default_port', os.environ.get('NLP2CMD_DEFAULT_PORT') or '8080'))

    def _shell_intent_network_scan(self, result: dict[str, Any]) -> None:
        result.setdefault('cidr', self._get_default('shell.scan_cidr', os.environ.get('NLP2CMD_DEFAULT_SCAN_CIDR') or '192.168.1.0/24'))

    def _shell_intent_network_speed(self, result: dict[str, Any]) -> None:
        result.setdefault('url', self._get_default('shell.speedtest_url', os.environ.get('NLP2CMD_DEFAULT_SPEEDTEST_URL') or 'http://speedtest.net'))

    def _shell_intent_disk_device(self, result: dict[str, Any]) -> None:
        result.setdefault('device', self._get_default('shell.disk_device', os.environ.get('NLP2CMD_DEFAULT_DISK_DEVICE') or '/dev/sda1'))

    def _shell_intent_backup_create(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('source', entities.get('target', '.'))

    def _shell_intent_backup_copy(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('source', entities.get('source', '.'))
        result.setdefault('destination', entities.get('destination', '.'))

    def _shell_intent_backup_restore(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('file', entities.get('target', ''))

    def _shell_intent_backup_integrity(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault(
            'file',
            entities.get(
                'target',
                self._get_default('shell.backup_archive', os.environ.get('NLP2CMD_DEFAULT_BACKUP_ARCHIVE') or 'backup.tar.gz'),
            ),
        )

    def _shell_intent_backup_path(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('path', entities.get('path', self._get_default('shell.backup_path', os.environ.get('NLP2CMD_DEFAULT_BACKUP_PATH') or './backup')))

    def _shell_intent_backup_size(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault(
            'file',
            entities.get(
                'target',
                self._get_default('shell.backup_archive', os.environ.get('NLP2CMD_DEFAULT_BACKUP_ARCHIVE') or 'backup.tar.gz'),
            ),
        )

    def _shell_intent_system_logs(self, result: dict[str, Any]) -> None:
        result.setdefault('file', self._get_default('shell.system_log_file', os.environ.get('NLP2CMD_DEFAULT_SYSTEM_LOG_FILE') or '/var/log/syslog'))

    def _shell_intent_dev_lint(self, result: dict[str, Any]) -> None:
        result.setdefault('path', 'src')

    def _shell_intent_dev_logs(self, result: dict[str, Any]) -> None:
        result.setdefault('file', self._get_default('shell.dev_log_file', os.environ.get('NLP2CMD_DEFAULT_DEV_LOG_FILE') or 'app.log'))

    def _shell_intent_dev_debug(self, result: dict[str, Any]) -> None:
        result.setdefault('script', self._get_default('shell.debug_script', os.environ.get('NLP2CMD_DEFAULT_DEBUG_SCRIPT') or 'script.py'))

    def _shell_intent_dev_docs(self, result: dict[str, Any]) -> None:
        result.setdefault('path', 'docs')

    def _shell_intent_security_permissions(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('file_path', entities.get('file_path', 'config.conf'))

    def _shell_intent_process_kill(self, result: dict[str, Any]) -> None:
        result.setdefault('pid', 'PID')

    def _shell_intent_process_background(self, result: dict[str, Any]) -> None:
        result.setdefault('command', 'python script.py')

    def _shell_intent_process_script(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('script', entities.get('target', 'script.sh'))

    def _shell_intent_service(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        result.setdefault('service', entities.get('service', self._get_default('shell.default_service', os.environ.get('NLP2CMD_DEFAULT_SERVICE') or 'nginx')))

    def _shell_intent_text_search_errors(self, result: dict[str, Any]) -> None:
        result.setdefault('file', self._get_default('shell.system_log_file', os.environ.get('NLP2CMD_DEFAULT_SYSTEM_LOG_FILE') or '/var/log/syslog'))

    def _shell_intent_open_url(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        url = entities.get('url', '')
        if url and not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        result['url'] = url or self._get_default('shell.default_url', os.environ.get('NLP2CMD_DEFAULT_URL') or 'https://google.com')

    def _shell_intent_search_web(self, entities: dict[str, Any], result: dict[str, Any]) -> None:
        query = entities.get('query', '')
        if not query:
            text = entities.get('text', '')
            match = re.search(r'(?:wyszukaj|search|szukaj|google)\s+(.+?)(?:\s+w\s+|\s*$)', text, re.IGNORECASE)
            if match:
                query = match.group(1).strip()
        result['query'] = query or 'nlp2cmd'

    def _apply_shell_backup_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> bool:
        backup_handlers = {
            'backup_create': self._shell_intent_backup_create,
            'backup_copy': self._shell_intent_backup_copy,
            'backup_restore': self._shell_intent_backup_restore,
            'backup_integrity': self._shell_intent_backup_integrity,
            'backup_status': self._shell_intent_backup_path,
            'backup_cleanup': self._shell_intent_backup_path,
            'backup_size': self._shell_intent_backup_size,
        }

        handler = backup_handlers.get(intent)
        if handler is None:
            return False
        handler(entities, result)
        return True

    def _apply_shell_system_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> bool:
        system_handlers = {
            'system_logs': lambda e, r: self._shell_intent_system_logs(r),
        }

        handler = system_handlers.get(intent)
        if handler is None:
            return False
        handler(entities, result)
        return True

    def _apply_shell_dev_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> bool:
        dev_handlers = {
            'dev_lint': lambda e, r: self._shell_intent_dev_lint(r),
            'dev_logs': lambda e, r: self._shell_intent_dev_logs(r),
            'dev_debug': lambda e, r: self._shell_intent_dev_debug(r),
            'dev_docs': lambda e, r: self._shell_intent_dev_docs(r),
        }

        handler = dev_handlers.get(intent)
        if handler is None:
            return False
        handler(entities, result)
        return True

    def _apply_shell_security_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> bool:
        security_handlers = {
            'security_permissions': self._shell_intent_security_permissions,
        }

        handler = security_handlers.get(intent)
        if handler is None:
            return False
        handler(entities, result)
        return True

    def _apply_shell_text_search_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> bool:
        text_handlers = {
            'text_search_errors': lambda e, r: self._shell_intent_text_search_errors(r),
        }

        handler = text_handlers.get(intent)
        if handler is None:
            return False
        handler(entities, result)
        return True

    def _apply_shell_network_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> bool:
        network_handlers = {
            'network_ping': lambda e, r: self._shell_intent_network_ping(r),
            'network_lsof': lambda e, r: self._shell_intent_network_lsof(r),
            'network_scan': lambda e, r: self._shell_intent_network_scan(r),
            'network_speed': lambda e, r: self._shell_intent_network_speed(r),
        }

        handler = network_handlers.get(intent)
        if handler is None:
            return False
        handler(entities, result)
        return True

    def _apply_shell_disk_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> bool:
        disk_handlers = {
            'disk_health': lambda e, r: self._shell_intent_disk_device(r),
            'disk_defrag': lambda e, r: self._shell_intent_disk_device(r),
        }

        handler = disk_handlers.get(intent)
        if handler is None:
            return False
        handler(entities, result)
        return True

    def _apply_shell_process_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> bool:
        process_handlers = {
            'process_user': self._shell_intent_process_user,
            'process_kill': lambda e, r: self._shell_intent_process_kill(r),
            'process_background': lambda e, r: self._shell_intent_process_background(r),
            'process_script': self._shell_intent_process_script,
        }

        handler = process_handlers.get(intent)
        if handler is None:
            return False
        handler(entities, result)
        return True

    def _apply_shell_service_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> bool:
        service_intents = {
            'service_start': self._shell_intent_service,
            'service_stop': self._shell_intent_service,
            'service_restart': self._shell_intent_service,
            'service_status': self._shell_intent_service,
        }

        handler = service_intents.get(intent)
        if handler is None:
            return False
        handler(entities, result)
        return True

    def _apply_shell_browser_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> bool:
        if intent in ('open_url', 'open_browser', 'browse'):
            self._shell_intent_open_url(entities, result)
            return True

        browser_handlers = {
            'search_web': self._shell_intent_search_web,
        }

        handler = browser_handlers.get(intent)
        if handler is None:
            return False
        handler(entities, result)
        return True

    def _apply_shell_intent_specific_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
        file_handlers: dict[str, Any] = {
            'file_search': self._shell_intent_file_search,
            'file_content': self._shell_intent_file_content,
            'file_tail': self._shell_intent_file_tail,
            'file_size': self._shell_intent_file_size,
            'file_rename': self._shell_intent_file_rename,
            'file_delete_all': self._shell_intent_file_delete_all,
            'dir_create': self._shell_intent_dir_create,
            'remove_all': self._shell_intent_remove_all,
            'file_operation': self._shell_intent_file_operation,
        }

        handler = file_handlers.get(intent)
        if handler is not None:
            handler(entities, result)
            return

        category_handlers = (
            self._apply_shell_backup_defaults,
            self._apply_shell_system_defaults,
            self._apply_shell_dev_defaults,
            self._apply_shell_security_defaults,
            self._apply_shell_text_search_defaults,
            self._apply_shell_network_defaults,
            self._apply_shell_disk_defaults,
            self._apply_shell_process_defaults,
            self._apply_shell_service_defaults,
            self._apply_shell_browser_defaults,
        )

        for handler_func in category_handlers:
            if handler_func(intent, entities, result):
                return

    def _prepare_shell_entities(self, intent: str, entities: dict[str, Any]) -> dict[str, Any]:
        """Prepare shell entities."""
        result = entities.copy()

        self._apply_shell_path_defaults(intent, entities, result)
        self._apply_shell_pattern_defaults(entities, result)
        self._apply_shell_find_flags(intent, entities, result)
        self._apply_shell_common_defaults(entities, result)
        self._apply_shell_text_processing_defaults(intent, entities, result)
        self._apply_shell_intent_specific_defaults(intent, entities, result)
        
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
        tail_lines = entities.get('tail_lines')
        if intent == 'logs' and tail_lines and not result.get('flags'):
            result['flags'] = f"--tail {tail_lines}"
        
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
        default_resource = 'deployment' if isinstance(intent, str) and intent.startswith('rollout') else 'pods'
        result.setdefault('resource', entities.get('resource_type', default_resource))
        
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
        replica_count = entities.get('replica_count')
        if replica_count is not None and str(replica_count).strip():
            result['replicas'] = str(replica_count).strip()
        else:
            result.setdefault('replicas', '1')
        
        # Logs
        pod_name = entities.get('pod_name') or entities.get('name') or entities.get('resource_name') or ''
        if pod_name:
            result['pod'] = str(pod_name)
        else:
            result.setdefault('pod', '')

        tail_lines = entities.get('tail_lines')
        if tail_lines is not None and str(tail_lines).strip():
            result['tail'] = str(tail_lines).strip()
        else:
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
        
        # Remove empty flags (only remove standalone flags, not flags with values)
        # This regex removes flags like "-flag " but keeps "-flag value"
        command = re.sub(r'\s+-[a-zA-Z]+\s+$', ' ', command)
        command = re.sub(r'\s+-[a-zA-Z]+\s+(?=-[a-zA-Z])', ' ', command)
        
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
    
    def list_templates(self, domain: Optional[str] = None):
        """List available templates.

        Backwards compatible behavior:
        - If domain is provided: returns list[str] of intents for that domain
        - If domain is None: returns dict[str, list[str]] for all domains
        """
        if domain is None:
            return {d: list(intents.keys()) for d, intents in self.templates.items()}
        return list(self.templates.get(domain, {}).keys())
