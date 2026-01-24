#!/usr/bin/env python3
"""Intelligent command detection from natural language descriptions."""

import re
import json
import os
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict

from nlp2cmd.utils.data_files import find_data_file

@dataclass
class CommandMatch:
    """Represents a matched command with confidence."""
    command: str
    confidence: float
    keywords: List[str]
    context: str

class CommandDetector:
    """Detects shell commands from natural language descriptions."""
    
    def __init__(self):
        """Initialize the detector with keyword mappings."""
        # Action keywords -> command mappings
        self.action_mappings = {
            # File operations
            'find': {
                'keywords': ['find', 'search', 'look for', 'locate', 'list files', 'search files'],
                'patterns': [r'\bfind\b', r'\bsearch\b', r'\blook for\b', r'\blocate\b'],
                'context_keywords': ['file', 'files', 'directory', 'folder', 'pattern', 'name']
            },
            'grep': {
                'keywords': ['search', 'find text', 'search in', 'look for', 'grep', 'pattern'],
                'patterns': [r'\bsearch\b', r'\bgrep\b', r'\bfind text\b'],
                'context_keywords': ['text', 'content', 'pattern', 'string', 'word', 'file', 'files']
            },
            'sed': {
                'keywords': ['replace', 'substitute', 'change', 'modify', 'edit text'],
                'patterns': [r'\breplace\b', r'\bsubstitute\b', r'\bsed\b'],
                'context_keywords': ['text', 'file', 'pattern', 'string']
            },
            'awk': {
                'keywords': ['process', 'extract', 'parse', 'column', 'field'],
                'patterns': [r'\bawk\b', r'\bextract\b', r'\bcolumn\b'],
                'context_keywords': ['text', 'file', 'field', 'column']
            },
            'ls': {
                'keywords': ['list', 'show', 'display files', 'directory contents'],
                'patterns': [r'\blist\b', r'\bls\b', r'\bshow files\b'],
                'context_keywords': ['files', 'directory', 'folder', 'contents']
            },
            'mkdir': {
                'keywords': ['create directory', 'make directory', 'mkdir', 'new folder'],
                'patterns': [r'\bcreate.*directory\b', r'\bmake.*directory\b', r'\bmkdir\b'],
                'context_keywords': ['directory', 'folder']
            },
            'rm': {
                'keywords': ['remove', 'delete', 'rm', 'unlink'],
                'patterns': [r'\bremove\b', r'\bdelete\b', r'\brm\b'],
                'context_keywords': ['file', 'files', 'directory', 'folder']
            },
            'cp': {
                'keywords': ['copy', 'duplicate', 'cp'],
                'patterns': [r'\bcopy\b', r'\bduplicate\b', r'\bcp\b'],
                'context_keywords': ['file', 'files', 'directory', 'folder']
            },
            'mv': {
                'keywords': ['move', 'rename', 'mv'],
                'patterns': [r'\bmove\b', r'\brename\b', r'\bmv\b'],
                'context_keywords': ['file', 'files', 'directory', 'folder']
            },
            
            # Archive operations
            'tar': {
                'keywords': ['compress', 'archive', 'tar', 'bundle', 'pack'],
                'patterns': [r'\bcompress\b', r'\barchive\b', r'\btar\b', r'\bbundle\b'],
                'context_keywords': ['files', 'directory', 'folder', 'backup']
            },
            'zip': {
                'keywords': ['zip', 'compress to zip'],
                'patterns': [r'\bzip\b'],
                'context_keywords': ['files', 'folder']
            },
            'unzip': {
                'keywords': ['unzip', 'extract zip'],
                'patterns': [r'\bunzip\b', r'\bextract.*zip\b'],
                'context_keywords': ['archive', 'file']
            },
            
            # System monitoring
            'ps': {
                'keywords': ['processes', 'running processes', 'ps', 'list processes'],
                'patterns': [r'\bprocesses?\b', r'\bps\b', r'\brunning\b'],
                'context_keywords': ['process', 'running', 'list']
            },
            'top': {
                'keywords': ['monitor processes', 'top', 'process monitor'],
                'patterns': [r'\btop\b', r'\bmonitor.*process\b'],
                'context_keywords': ['process', 'monitor', 'running']
            },
            'kill': {
                'keywords': ['kill', 'terminate', 'stop process'],
                'patterns': [r'\bkill\b', r'\bterminate\b', r'\bstop.*process\b'],
                'context_keywords': ['process', 'pid', 'signal']
            },
            'df': {
                'keywords': ['disk usage', 'disk space', 'df', 'filesystem'],
                'patterns': [r'\bdisk\b', r'\bdf\b', r'\bspace\b'],
                'context_keywords': ['disk', 'space', 'filesystem', 'usage']
            },
            'du': {
                'keywords': ['disk usage', 'file size', 'directory size', 'du'],
                'patterns': [r'\bfile.*size\b', r'\bdu\b', r'\bdirectory.*size\b'],
                'context_keywords': ['size', 'disk', 'usage', 'file', 'directory']
            },
            'free': {
                'keywords': ['memory', 'ram', 'free', 'memory usage'],
                'patterns': [r'\bmemory\b', r'\bram\b', r'\bfree\b'],
                'context_keywords': ['memory', 'ram', 'usage', 'free']
            },
            'uname': {
                'keywords': ['system info', 'uname', 'kernel version'],
                'patterns': [r'\bsystem.*info\b', r'\buname\b', r'\bkernel\b'],
                'context_keywords': ['system', 'kernel', 'version', 'info']
            },
            'uptime': {
                'keywords': ['uptime', 'system uptime', 'how long'],
                'patterns': [r'\buptime\b', r'\bsystem.*uptime\b', r'\bhow long\b'],
                'context_keywords': ['uptime', 'running', 'time']
            },
            
            # Network
            'ping': {
                'keywords': ['ping', 'test connection', 'check host', 'network test'],
                'patterns': [r'\bping\b', r'\btest.*connection\b', r'\bcheck.*host\b'],
                'context_keywords': ['host', 'connection', 'network', 'test']
            },
            'curl': {
                'keywords': ['download', 'http', 'url', 'curl', 'web request'],
                'patterns': [r'\bcurl\b', r'\bdownload\b', r'\bhttp\b', r'\burl\b'],
                'context_keywords': ['url', 'http', 'download', 'web', 'request']
            },
            'wget': {
                'keywords': ['download', 'wget', 'fetch'],
                'patterns': [r'\bwget\b', r'\bdownload\b', r'\bfetch\b'],
                'context_keywords': ['url', 'download', 'file', 'web']
            },
            'netstat': {
                'keywords': ['network connections', 'netstat', 'ports', 'listening'],
                'patterns': [r'\bnetstat\b', r'\bnetwork.*connection\b', r'\bports?\b'],
                'context_keywords': ['network', 'connection', 'port', 'listening']
            },
            'ss': {
                'keywords': ['socket', 'ss', 'network statistics'],
                'patterns': [r'\bss\b', r'\bsocket\b', r'\bnetwork.*stat\b'],
                'context_keywords': ['socket', 'network', 'connection']
            },
            'ssh': {
                'keywords': ['ssh', 'remote login', 'connect to server'],
                'patterns': [r'\bssh\b', r'\bremote.*login\b', r'\bconnect.*server\b'],
                'context_keywords': ['remote', 'server', 'ssh', 'connect']
            },
            'scp': {
                'keywords': ['scp', 'remote copy', 'transfer file'],
                'patterns': [r'\bscp\b', r'\bremote.*copy\b', r'\btransfer.*file\b'],
                'context_keywords': ['remote', 'copy', 'transfer', 'file']
            },
            
            # Development
            'git': {
                'keywords': ['git', 'version control', 'commit', 'push', 'pull', 'clone', 'status'],
                'patterns': [r'\bgit\b', r'\bcommit\b', r'\bpush\b', r'\bpull\b', r'\bclone\b', r'\bstatus\b'],
                'context_keywords': ['repository', 'branch', 'code', 'version']
            },
            'docker': {
                'keywords': ['docker', 'container', 'image', 'docker run'],
                'patterns': [r'\bdocker\b', r'\bcontainer\b', r'\bimage\b'],
                'context_keywords': ['container', 'image', 'docker', 'run']
            },
            'kubectl': {
                'keywords': ['kubernetes', 'kubectl', 'k8s', 'pod', 'deployment'],
                'patterns': [r'\bkubectl\b', r'\bkubernetes\b', r'\bk8s\b', r'\bpod\b'],
                'context_keywords': ['kubernetes', 'pod', 'deployment', 'cluster']
            },
            'make': {
                'keywords': ['make', 'build', 'compile'],
                'patterns': [r'\bmake\b', r'\bbuild\b', r'\bcompile\b'],
                'context_keywords': ['build', 'compile', 'makefile']
            },
            'gcc': {
                'keywords': ['gcc', 'compile c', 'gcc compile'],
                'patterns': [r'\bgcc\b', r'\bcompile.*c\b'],
                'context_keywords': ['compile', 'c', 'source']
            },
            'python': {
                'keywords': ['python', 'run python', 'python script'],
                'patterns': [r'\bpython\b', r'\brun.*python\b'],
                'context_keywords': ['python', 'script', 'run']
            },
            'npm': {
                'keywords': ['npm', 'node', 'install package'],
                'patterns': [r'\bnpm\b', r'\bnode\b', r'\binstall.*package\b'],
                'context_keywords': ['npm', 'node', 'package', 'install']
            },
        }
        
        # Context weights for different keyword types
        self.context_weights = {
            'action_keyword': 0.6,
            'context_keyword': 0.3,
            'pattern_match': 0.8,
            'exact_command': 1.0
        }

        loaded = self._load_config_from_json()
        if loaded is not None:
            action_mappings = loaded.get("action_mappings")
            if isinstance(action_mappings, dict) and action_mappings:
                self.action_mappings = action_mappings

            context_weights = loaded.get("context_weights")
            if isinstance(context_weights, dict) and context_weights:
                # Merge into defaults to avoid KeyError if config is partial
                self.context_weights.update(context_weights)

    def _load_config_from_json(self) -> Optional[Dict[str, Dict]]:
        p = find_data_file(
            explicit_path=os.environ.get("NLP2CMD_COMMAND_DETECTOR_FILE"),
            default_filename="command_detector.json",
        )
        if not p:
            return None
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(payload, dict):
            return None

        raw_action_mappings = payload.get("action_mappings")
        raw_context_weights = payload.get("context_weights")

        loaded_action_mappings: Dict[str, Dict[str, List[str]]] = {}
        if isinstance(raw_action_mappings, dict):
            for cmd, info in raw_action_mappings.items():
                if not isinstance(cmd, str) or not cmd.strip():
                    continue
                if not isinstance(info, dict):
                    continue

                keywords = info.get("keywords")
                patterns = info.get("patterns")
                context_keywords = info.get("context_keywords")
                if not isinstance(keywords, list) or not isinstance(patterns, list) or not isinstance(context_keywords, list):
                    continue

                clean_keywords = [x for x in keywords if isinstance(x, str) and x.strip()]
                clean_patterns = [x for x in patterns if isinstance(x, str) and x.strip()]
                clean_context = [x for x in context_keywords if isinstance(x, str) and x.strip()]
                if not clean_keywords and not clean_patterns and not clean_context:
                    continue

                loaded_action_mappings[cmd.strip()] = {
                    "keywords": clean_keywords,
                    "patterns": clean_patterns,
                    "context_keywords": clean_context,
                }

        loaded_context_weights: Dict[str, float] = {}
        if isinstance(raw_context_weights, dict):
            for k, v in raw_context_weights.items():
                if not isinstance(k, str) or not k.strip():
                    continue
                if isinstance(v, (int, float)):
                    loaded_context_weights[k.strip()] = float(v)

        if not loaded_action_mappings and not loaded_context_weights:
            return None

        return {
            "action_mappings": loaded_action_mappings,
            "context_weights": loaded_context_weights,
        }
    
    def detect_command(self, query: str, top_k: int = 3) -> List[CommandMatch]:
        """
        Detect the most likely commands from a natural language query.
        
        Args:
            query: Natural language description
            top_k: Number of top matches to return
            
        Returns:
            List of CommandMatch objects sorted by confidence
        """
        query_lower = query.lower()
        matches = []
        
        for command, info in self.action_mappings.items():
            confidence = 0.0
            matched_keywords = []
            
            # Check for exact command name
            if command in query_lower:
                confidence += self.context_weights['exact_command']
                matched_keywords.append(command)
            
            # Check pattern matches
            for pattern in info['patterns']:
                if re.search(pattern, query_lower):
                    confidence += self.context_weights['pattern_match']
                    matched_keywords.append(pattern)
            
            # Check action keywords
            for keyword in info['keywords']:
                if keyword in query_lower:
                    confidence += self.context_weights['action_keyword'] * len(keyword.split())
                    matched_keywords.append(keyword)
            
            # Check context keywords
            context_matches = sum(1 for kw in info['context_keywords'] if kw in query_lower)
            if context_matches > 0:
                confidence += self.context_weights['context_keyword'] * context_matches
                matched_keywords.extend([kw for kw in info['context_keywords'] if kw in query_lower])
            
            # Normalize confidence
            if confidence > 0:
                # Additional boost for multiple keyword matches
                if len(matched_keywords) > 1:
                    confidence *= 1.2
                
                # Cap at 1.0
                confidence = min(confidence, 1.0)
                
                matches.append(CommandMatch(
                    command=command,
                    confidence=confidence,
                    keywords=list(set(matched_keywords)),
                    context=self._extract_context(query, command)
                ))
        
        # Sort by confidence and return top_k
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches[:top_k]
    
    def _extract_context(self, query: str, command: str) -> str:
        """Extract relevant context for the command."""
        # Simple context extraction - in real system, could use NLP
        context_words = []
        
        # Extract file paths
        paths = re.findall(r'[/][^\s]*', query)
        if paths:
            context_words.extend(paths)
        
        # Extract file extensions
        extensions = re.findall(r'\.\w+\b', query)
        if extensions:
            context_words.extend(extensions)
        
        # Extract sizes
        sizes = re.findall(r'\d+[KMGT]?B?', query)
        if sizes:
            context_words.extend(sizes)
        
        # Extract hosts/URLs
        hosts = re.findall(r'[\w.-]+\.(?:com|org|net|gov|edu|io|local)', query)
        if hosts:
            context_words.extend(hosts)
        
        return ' '.join(context_words[:5])  # Limit context length


def test_command_detector():
    """Test the command detector with various queries."""
    detector = CommandDetector()
    
    test_cases = [
        "Find files larger than 100MB",
        "Search for TODO in Python files",
        "Compress logs directory",
        "Copy file to backup",
        "Move old files to archive",
        "Remove temporary files",
        "Show running processes",
        "Check disk usage",
        "Check memory usage",
        "Show system uptime",
        "Test connection to google.com",
        "Download file from URL",
        "Check network connections",
        "Check git status",
        "List Docker containers",
        "Check Kubernetes pods",
    ]
    
    print("Command Detection Test Results")
    print("=" * 60)
    
    for query in test_cases:
        print(f"\nQuery: {query}")
        matches = detector.detect_command(query, top_k=3)
        
        for i, match in enumerate(matches, 1):
            status = "✓" if match.confidence > 0.7 else "⚠" if match.confidence > 0.4 else "✗"
            print(f"  {i}. {status} {match.command} (confidence: {match.confidence:.2f})")
            if match.context:
                print(f"     Context: {match.context}")


if __name__ == "__main__":
    test_command_detector()
