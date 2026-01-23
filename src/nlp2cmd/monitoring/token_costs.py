"""
Token cost estimation utilities for NLP2CMD.

Converts resource metrics to LLM token equivalents for cost comparison.
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TokenCostEstimate:
    """Token cost estimation based on resource consumption."""
    
    # Resource metrics
    time_ms: float
    cpu_percent: float
    memory_mb: float
    energy_mj: float
    
    # Token equivalents
    input_tokens_estimate: int
    output_tokens_estimate: int
    total_tokens_estimate: int
    
    # Cost estimates (USD)
    estimated_cost_usd: float
    
    # Model comparison
    equivalent_model_tier: str  # "tiny", "small", "medium", "large"
    
    # Efficiency metrics
    tokens_per_millisecond: float
    tokens_per_mj: float


class TokenCostEstimator:
    """Converts resource metrics to token equivalents."""
    
    # Reference: GPT-4 Turbo pricing (as of 2024)
    # Input: $0.01 per 1K tokens, Output: $0.03 per 1K tokens
    # Average: ~100 tokens per second for complex reasoning
    
    MODEL_REFERENCE = {
        "tiny": {  # GPT-3.5 Turbo level
            "tokens_per_second": 150,
            "cost_per_1k_tokens": 0.002,  # Average input+output
            "energy_per_1k_tokens": 0.5,  # mJ
        },
        "small": {  # GPT-4 level
            "tokens_per_second": 80,
            "cost_per_1k_tokens": 0.02,
            "energy_per_1k_tokens": 2.0,
        },
        "medium": {  # GPT-4 Turbo level
            "tokens_per_second": 120,
            "cost_per_1k_tokens": 0.015,
            "energy_per_1k_tokens": 1.5,
        },
        "large": {  # Claude 3 Opus level
            "tokens_per_second": 60,
            "cost_per_1k_tokens": 0.075,
            "energy_per_1k_tokens": 5.0,
        }
    }
    
    def __init__(self):
        self.base_cpu_cost_per_ms = 0.000001  # $1 per second of CPU time
        self.base_memory_cost_per_mb_ms = 0.00000001  # $0.01 per GB-second
    
    def estimate_from_metrics(
        self, 
        time_ms: float, 
        cpu_percent: float, 
        memory_mb: float, 
        energy_mj: Optional[float] = None
    ) -> TokenCostEstimate:
        """Estimate token cost from resource metrics."""
        
        # Convert to seconds for calculations
        time_seconds = time_ms / 1000.0
        
        # Calculate resource-based token estimates
        cpu_tokens = self._estimate_tokens_from_cpu(time_seconds, cpu_percent)
        memory_tokens = self._estimate_tokens_from_memory(time_seconds, memory_mb)
        
        # Use energy if available, otherwise estimate from CPU+memory
        if energy_mj is not None:
            energy_tokens = self._estimate_tokens_from_energy(energy_mj)
            # Weight the estimates (energy is most reliable)
            total_tokens = int(0.5 * energy_tokens + 0.3 * cpu_tokens + 0.2 * memory_tokens)
        else:
            total_tokens = int(0.6 * cpu_tokens + 0.4 * memory_tokens)
        
        # Split into input/output (typical ratio 70:30 for generation tasks)
        input_tokens = int(total_tokens * 0.7)
        output_tokens = int(total_tokens * 0.3)
        
        # Determine model tier based on performance characteristics
        model_tier = self._determine_model_tier(time_ms, cpu_percent, memory_mb)
        model_ref = self.MODEL_REFERENCE[model_tier]
        
        # Calculate cost
        estimated_cost_usd = (total_tokens / 1000.0) * model_ref["cost_per_1k_tokens"]
        
        # Calculate efficiency metrics
        tokens_per_ms = total_tokens / time_ms if time_ms > 0 else 0
        tokens_per_mj = total_tokens / energy_mj if energy_mj and energy_mj > 0 else 0
        
        return TokenCostEstimate(
            time_ms=time_ms,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            energy_mj=energy_mj or 0.0,
            input_tokens_estimate=input_tokens,
            output_tokens_estimate=output_tokens,
            total_tokens_estimate=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
            equivalent_model_tier=model_tier,
            tokens_per_millisecond=tokens_per_ms,
            tokens_per_mj=tokens_per_mj,
        )
    
    def _estimate_tokens_from_cpu(self, time_seconds: float, cpu_percent: float) -> int:
        """Estimate tokens based on CPU usage."""
        # Assume 1 CPU core can process ~100 tokens per second at 100% usage
        cpu_cores_used = cpu_percent / 100.0
        tokens_per_second = 100 * cpu_cores_used
        return int(tokens_per_second * time_seconds)
    
    def _estimate_tokens_from_memory(self, time_seconds: float, memory_mb: float) -> int:
        """Estimate tokens based on memory usage."""
        # Assume 1GB memory can hold context for ~50K tokens
        # Memory usage indicates model size and context window
        memory_gb = memory_mb / 1024.0
        context_tokens = int(50000 * memory_gb)
        
        # Adjust for processing time (longer time = more processing)
        time_factor = min(time_seconds / 1.0, 5.0)  # Cap at 5x factor
        return int(context_tokens * time_factor * 0.1)  # Scale down for estimation
    
    def _estimate_tokens_from_energy(self, energy_mj: float) -> int:
        """Estimate tokens based on energy consumption."""
        # Use reference energy per 1K tokens
        # Assume medium model as baseline
        energy_per_1k = self.MODEL_REFERENCE["medium"]["energy_per_1k_tokens"]
        return int((energy_mj / energy_per_1k) * 1000)
    
    def _determine_model_tier(self, time_ms: float, cpu_percent: float, memory_mb: float) -> str:
        """Determine equivalent model tier based on resource usage."""
        
        # Calculate resource scores
        time_score = min(time_ms / 10.0, 10.0)  # 10ms = score 1
        cpu_score = cpu_percent / 100.0
        memory_score = memory_mb / 1000.0  # 1GB = score 1
        
        # Combined score
        total_score = (time_score * 0.4 + cpu_score * 0.3 + memory_score * 0.3)
        
        if total_score < 0.5:
            return "tiny"
        elif total_score < 1.5:
            return "small"
        elif total_score < 3.0:
            return "medium"
        else:
            return "large"
    
    def format_estimate(self, estimate: TokenCostEstimate) -> str:
        """Format token cost estimate for display."""
        
        lines = [
            f"🤖 Token Estimate: {estimate.total_tokens_estimate:,} tokens",
            f"   Input: {estimate.input_tokens_estimate:,} | Output: {estimate.output_tokens_estimate:,}",
            f"   Cost: ${estimate.estimated_cost_usd:.6f}",
            f"   Model Tier: {estimate.equivalent_model_tier}",
            f"   Efficiency: {estimate.tokens_per_millisecond:.1f} tokens/ms"
        ]
        
        if estimate.energy_mj > 0:
            lines.append(f"   Energy: {estimate.tokens_per_mj:.0f} tokens/mJ")
        
        return " | ".join(lines)


# Global estimator instance
_estimator = TokenCostEstimator()


def estimate_token_cost(
    time_ms: float, 
    cpu_percent: float, 
    memory_mb: float, 
    energy_mj: Optional[float] = None
) -> TokenCostEstimate:
    """Convenient function for token cost estimation."""
    return _estimator.estimate_from_metrics(time_ms, cpu_percent, memory_mb, energy_mj)


def format_token_estimate(estimate: TokenCostEstimate) -> str:
    """Format token cost estimate for display."""
    return _estimator.format_estimate(estimate)


def parse_metrics_string(metrics_str: str) -> Dict[str, float]:
    """Parse metrics string like '⏱️ Time: 2.6ms | 💻 CPU: 0.0% | 🧠 RAM: 53.5MB (0.1%) | ⚡ Energy: 0.022mJ'"""
    
    metrics = {}
    
    # Parse time
    if "Time:" in metrics_str:
        time_part = metrics_str.split("Time:")[1].split("ms")[0].strip()
        try:
            metrics["time_ms"] = float(time_part)
        except:
            pass
    
    # Parse CPU
    if "CPU:" in metrics_str:
        cpu_part = metrics_str.split("CPU:")[1].split("%")[0].strip()
        try:
            metrics["cpu_percent"] = float(cpu_part)
        except:
            pass
    
    # Parse RAM
    if "RAM:" in metrics_str:
        ram_part = metrics_str.split("RAM:")[1].split("MB")[0].strip()
        try:
            metrics["memory_mb"] = float(ram_part)
        except:
            pass
    
    # Parse Energy
    if "Energy:" in metrics_str:
        energy_part = metrics_str.split("Energy:")[1].strip()
        if "mJ" in energy_part:
            energy_value = energy_part.split("mJ")[0].strip()
            try:
                metrics["energy_mj"] = float(energy_value)
            except:
                pass
        elif "J" in energy_part:
            energy_value = energy_part.split("J")[0].strip()
            try:
                metrics["energy_mj"] = float(energy_value) * 1000  # Convert J to mJ
            except:
                pass
    
    return metrics
