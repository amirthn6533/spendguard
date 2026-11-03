"""
Command Line Interface (CLI) for SpendGuard.
"""

import argparse
import sys
from .pricing import MODEL_PRICING, calculate_cost
from .core import SpendGuard, BudgetExceededError


def main():
    parser = argparse.ArgumentParser(
        description="SpendGuard - High-Precision Token Budget & Cost Guard for LLM Applications",
        prog="spendguard",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: cost
    cost_parser = subparsers.add_parser("cost", help="Calculate exact USD cost for prompt and completion tokens")
    cost_parser.add_argument("--model", "-m", required=True, help="LLM model identifier (e.g. gpt-4o, o3-mini, claude-3-5-sonnet)")
    cost_parser.add_argument("--prompt", "-p", type=int, default=1000, help="Prompt tokens count")
    cost_parser.add_argument("--completion", "-c", type=int, default=500, help="Completion tokens count")

    # Command: models
    subparsers.add_parser("models", help="List all supported models and pricing rates")

    # Command: demo
    subparsers.add_parser("demo", help="Run interactive simulation of budget enforcement & precision clamping")

    args = parser.parse_args()

    if args.command == "cost":
        cost = calculate_cost(args.model, args.prompt, args.completion)
        print("\n=== SpendGuard Cost Estimate ===")
        print(f"  Model             : {args.model}")
        print(f"  Prompt Tokens     : {args.prompt:,}")
        print(f"  Completion Tokens : {args.completion:,}")
        print(f"  Total Cost        : ${cost:.6f} USD\n")

    elif args.command == "models":
        print("\n=== Supported Built-in Models & Rates (per 1M tokens) ===\n")
        print(f"{'Model':<35} {'Prompt ($/1M)':<18} {'Completion ($/1M)':<18}")
        print("-" * 72)
        for model, (p, c) in MODEL_PRICING.items():
            print(f"{model:<35} ${p:<17.2f} ${c:<17.2f}")
        print("")

    elif args.command == "demo":
        print("\n=== Running SpendGuard Budget Simulation ===")
        guard = SpendGuard(global_budget=0.05)  # $0.05 budget
        account = guard.get_account("production_app")

        print(f"  Initial Spend: ${account.spend:.6f}")
        for i in range(1, 6):
            try:
                # simulate gpt-4o queries: 2000 prompt, 1000 completion = ~$0.015
                cost = calculate_cost("gpt-4o", 2000, 1000)
                account.record_usage(cost, tokens=3000)
                print(f"  Query {i}: +${cost:.6f} -> Current Spend: ${account.spend:.6f} [OK]")
            except BudgetExceededError as e:
                print(f"  Query {i}: [BLOCKED] {e}")
                break

        print("\n  Testing Spend Reset (decrementing without float underflow):")
        account.reset_spend(decrement_by=0.015)
        print(f"  Spend after decrement: ${account.spend:.6f} (Guaranteed non-negative)\n")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
