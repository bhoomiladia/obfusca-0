from pathlib import Path
import shutil
import os
import sys
import json

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from run_advanced_obfuscation import AdvancedObfuscationPipeline

def find_latest_ll_file(work_dir: Path) -> str:
    """Find the latest LLVM IR file in the working directory"""
    # List all LL files in work_dir
    ll_files = list(work_dir.glob("*.ll"))
    
    # Also check current directory (backend) in case files were created there
    current_dir = Path.cwd()
    if current_dir != work_dir:
        current_ll_files = list(current_dir.glob("*.ll"))
        ll_files.extend(current_ll_files)
    
    if not ll_files:
        return None
    
    # Try to find pass_7.ll specifically (final pass)
    for ll_file in ll_files:
        if ll_file.name == "pass_7.ll":
            return str(ll_file)
    
    # If pass_7.ll doesn't exist, find the highest numbered pass file
    def get_pass_number(ll_file):
        try:
            return int(ll_file.stem.split('_')[1])
        except:
            return -1
    
    # Sort by pass number and get the highest
    sorted_ll_files = sorted(ll_files, key=get_pass_number)
    latest_ll = sorted_ll_files[-1] if sorted_ll_files else None
    
    if latest_ll:
        return str(latest_ll)
    
    return None

def obfuscate_code(input_file_path: str, selected_techniques: list = None) -> dict:
    """
    Run the obfuscation pipeline on a given file.
    Returns paths to final report, exe, and llvm files.
    """
    if selected_techniques is None:
        selected_techniques = []
    
    input_path = Path(input_file_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file_path}")

    # Use backend directory as work directory
    backend_dir = Path(__file__).parent
    work_dir = backend_dir / "temp_work"
    work_dir.mkdir(exist_ok=True)
    
    output_exe = work_dir / f"{input_path.stem}_obfuscated.exe"

    # Copy user file into working dir
    local_input = work_dir / input_path.name
    shutil.copy2(input_path, local_input)

    print(f"Starting obfuscation pipeline with techniques: {selected_techniques}")

    # Run obfuscation pipeline
    try:
        # Change to backend directory to run the pipeline
        original_cwd = os.getcwd()
        os.chdir(backend_dir)
        
        pipeline = AdvancedObfuscationPipeline(str(local_input), str(output_exe))
        # Pass selected techniques to the pipeline
        success = pipeline.run_advanced_obfuscation(selected_techniques)

        # Change back to original directory
        os.chdir(original_cwd)

        if not success:
            raise RuntimeError("Obfuscation pipeline failed")

        # Collect results
        result = {
            "exe": str(output_exe) if output_exe.exists() else None,
            "report": str(backend_dir / "report.json") if (backend_dir / "report.json").exists() else None,
            "llvm_ir": find_latest_ll_file(work_dir),
            "advanced_report": str(backend_dir / "advanced_obfuscation_report.json") if (backend_dir / "advanced_obfuscation_report.json").exists() else None
        }

        # Read metrics from report if available
        if result['report'] and Path(result['report']).exists():
            try:
                with open(result['report'], 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                result["metrics"] = report_data.get("metrics", {})
                result["summary"] = report_data.get("summary", {})
            except Exception as e:
                print(f"Could not read report: {e}")

        print(f"Obfuscation completed: {result['exe']}")

        return result

    except Exception as e:
        # Change back to original directory on error
        if 'original_cwd' in locals():
            os.chdir(original_cwd)
        raise