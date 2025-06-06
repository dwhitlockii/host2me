import subprocess
import sys

def run_step(cmd, desc):
    print(f"\n[STEP] {desc}...")
    result = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        print(f"[ERROR] Step failed: {desc}")
        sys.exit(result.returncode)

if __name__ == "__main__":
    run_step(["run_foundational_scrape.py"], "Foundational Scrape (raw candidates)")
    run_step(["run_directory_scrape.py"], "Directory Scrape (HostAdvice/WHTop)")
    run_step(["scoring_pass.py"], "Scoring Pass (modular scoring)")
    run_step(["export_results.py"], "Export Results (final Excel/CSV)")
    print("\n[PIPELINE] All steps completed. Check the output/ directory for results.") 