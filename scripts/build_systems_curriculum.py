#!/usr/bin/env python3
"""
Systems Curriculum Generator & Verifier.

Builds a comprehensive multi-tier engineering dataset across:
1. Tier 1: Algorithmic Invariants & Big-O Complexity
2. Tier 2: High-Level System Design (HLD) & Distributed Systems
3. Tier 3: Low-Level Design (LLD), Concurrency & Architecture Paradigms
4. Tier 4: Landmark Systems Research Paper Derivations
5. Tier 5: Hybrid & Heterogeneous Systems

Validates 100% of samples through AST syntax parsing and sandbox unit testing.

Author: Nilesh Chakraborty / AGY Swarm Systems
"""

import os
import sys
import json
import random

# Ensure workspace root is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from curriculum.expander import expand_curriculum
from curriculum.variations import generate_domain_variations
from curriculum.verifier import verify_all_samples

def main():
    print("=" * 80)
    print("🏛️  BUILDING LARGE-SCALE SYSTEMS & ARCHITECTURE CURRICULUM")
    print("=" * 80)
    
    # 1. Expand base archetypes across all 5 tiers
    print("\n[Step 1/4] Generating base multi-tier systems curriculum...")
    base_samples = expand_curriculum()
    print(f"Generated {len(base_samples)} foundational archetypes.")
    
    # 2. Generate industrial domain variations
    print("\n[Step 2/4] Synthesizing domain adaptations & operational variations...")
    domain_variations = generate_domain_variations(base_samples)
    print(f"Generated {len(domain_variations)} domain-adapted variations.")
    
    all_samples = base_samples + domain_variations
    print(f"Total candidate dataset size: {len(all_samples)} high-yield samples.")
    
    # 3. Verify all samples via AST parser and sandbox execution
    print("\n[Step 3/4] Running automated AST syntax validation and unit test sandbox...")
    passed, failed, errors = verify_all_samples(all_samples)
    print(f"Verification Results: {passed} PASSED | {failed} FAILED")
    
    if failed > 0:
        print("Encountered verification errors:")
        for err in errors:
            print("  -", err)
        raise RuntimeError(f"Dataset verification failed with {failed} errors!")
        
    print("✅ All samples passed AST syntax and sandbox unit test execution!")
    
    # 4. Export training and validation splits
    print("\n[Step 4/4] Exporting verified curriculum splits...")
    out_dir = os.path.join(PROJECT_ROOT, "data/systems_curriculum")
    os.makedirs(out_dir, exist_ok=True)
    
    train_file = os.path.join(out_dir, "train.jsonl")
    valid_file = os.path.join(out_dir, "valid.jsonl")
    
    # Shuffle with fixed seed for deterministic reproducibility
    random.seed(42)
    random.shuffle(all_samples)
    
    val_size = max(4, int(len(all_samples) * 0.1))
    valid_samples = all_samples[:val_size]
    train_samples = all_samples[val_size:]
    
    with open(train_file, "w") as f:
        for s in train_samples:
            f.write(json.dumps(s) + "\n")
            
    with open(valid_file, "w") as f:
        for s in valid_samples:
            f.write(json.dumps(s) + "\n")
            
    print(f"Exported {len(train_samples)} training samples to: {train_file}")
    print(f"Exported {len(valid_samples)} validation samples to: {valid_file}")
    print(f"Total dataset size: {os.path.getsize(train_file) / 1024:.1f} KB")
    print("Curriculum build complete!")

if __name__ == "__main__":
    main()
