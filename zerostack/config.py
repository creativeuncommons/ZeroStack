"""
ZeroStack Enterprise Configuration & Rule Registry
==================================================
Provides declarative enterprise configuration with sensible production defaults,
environment variable overrides, and custom PII sensitivity rule binding.

Zero external dependencies: 100% Python standard library.
"""

import os
import sys
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from pathlib import Path

# Add parent directory for submodule ecosystem loader
PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ecosystem_loader import zeroleak


@dataclass
class EnterpriseConfig:
    """Enterprise-grade configuration for the ZeroStack pipeline."""
    app_name: str = "ZeroStackEnterpriseAgent"
    storage_dir: Optional[str] = None
    trace_dir: Optional[str] = None
    default_top_k_tools: int = 5
    enable_bm25_pruning: bool = True
    enable_toolpacks: bool = False
    enable_wal_journal: bool = True
    enable_otlp_tracing: bool = True
    max_durable_steps: int = 50
    custom_rules: List[zeroleak.CustomEntityRule] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "EnterpriseConfig":
        """Loads configuration from environment variables with ZEROSTACK_* prefix."""
        storage_dir = os.environ.get("ZEROSTACK_STORAGE_DIR")
        trace_dir = os.environ.get("ZEROSTACK_TRACE_DIR")
        app_name = os.environ.get("ZEROSTACK_APP_NAME", "ZeroStackEnterpriseAgent")
        top_k = int(os.environ.get("ZEROSTACK_TOP_K_TOOLS", "5"))
        enable_pruning = os.environ.get("ZEROSTACK_ENABLE_PRUNING", "true").lower() in ("1", "true", "yes")

        return cls(
            app_name=app_name,
            storage_dir=storage_dir,
            trace_dir=trace_dir,
            default_top_k_tools=top_k,
            enable_bm25_pruning=enable_pruning
        )

    def add_custom_rule(
        self,
        name: str,
        pattern: str,
        priority: int = 50,
        entropy_threshold: Optional[float] = None,
        description: str = ""
    ) -> "EnterpriseConfig":
        """Registers a novel organization-specific sensitivity rule."""
        rule = zeroleak.CustomEntityRule(
            name=name,
            pattern=pattern,
            priority=priority,
            entropy_threshold=entropy_threshold,
            description=description
        )
        self.custom_rules.append(rule)
        return self
