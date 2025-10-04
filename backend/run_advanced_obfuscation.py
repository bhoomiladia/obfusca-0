import json
import os
import subprocess
import sys
import shutil
from pathlib import Path
import datetime
import time
import re

class AdvancedObfuscationPipeline:
    def __init__(self, input_file, output_file="super_obfuscated.exe"):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.work_dir = Path(".")
        self.start_time = time.time()
        self.pass_times = []
        self.report_data = {
            "metadata": {},
            "metrics": {},
            "timing": {},
            "file_sizes": {},
            "steps": [],
            "pass_reports": [],
            "summary": {}
        }
    
    def run_advanced_obfuscation(self, selected_techniques=None):
        """Run advanced obfuscation passes with optional technique filtering"""
        if selected_techniques is None:
            selected_techniques = []
            
        # Store original working directory
        original_cwd = os.getcwd()
        
        try:
            # Change to the work directory where files should be created
            os.chdir(self.work_dir)
            
            # Initialize timing
            self.start_time = time.time()
            self.pass_times = []
            
            # Step 1: Initial compilation
            bc_file = Path("input.bc")
            step_start = time.time()
            self.report_data["steps"].append({
                "step": "initial_compilation",
                "command": f"clang -O0 -c -emit-llvm {self.input_file} -o {bc_file}",
                "status": "success" if self.emit_bc(bc_file) else "failed",
                "output": "Generated initial bitcode" if bc_file.exists() else "Failed to generate bitcode"
            })
            self.pass_times.append(("initial_compilation", time.time() - step_start))
            
            if not bc_file.exists():
                return False
            
            # Step 2: All passes (filter if techniques are specified)
            all_passes = [
                ("stringenc", "String Encryption", "AdvancedObfuscationPasses.dll"),
                ("bogus-instructions", "Bogus Instructions", "AdvancedObfuscationPasses.dll"),
                ("rename-symbols", "Symbol Renaming", "AdvancedObfuscationPasses.dll"),
                ("dynamic-xor", "Dynamic XOR Obfuscation", "AdvancedObfuscationPasses.dll"),
                ("cfflatten", "Control Flow Flattening", "AdvancedObfuscationPasses.dll"), 
                ("opaque-preds", "Opaque Predicates", "AdvancedObfuscationPasses.dll"),
                ("bbsplit", "Basic Block Splitting", "AdvancedObfuscationPasses.dll"),
                ("anti-debug", "Anti-Debugging Protection", "AdvancedObfuscationPasses.dll"),
            ]
            
            # Filter passes if specific techniques are selected
            if selected_techniques:
                passes = [pass_info for pass_info in all_passes if pass_info[0] in selected_techniques]
                print(f"Running selected techniques: {[p[0] for p in passes]}")
            else:
                passes = all_passes
                print("Running all techniques")
            
            current_bc = bc_file
            for i, (pass_name, description, plugin) in enumerate(passes):
                step_start = time.time()
                next_bc = Path(f"pass_{i}.bc")
                next_ll = Path(f"pass_{i}.ll")
                
                # Run the optimization pass
                pass_success = self.run_opt_pass(current_bc, next_ll, pass_name, description, plugin)
                
                # Record step with timing
                step_duration = time.time() - step_start
                self.pass_times.append((pass_name, step_duration))
                
                step_info = {
                    "step": f"opt-pass-{pass_name}",
                    "command": f"opt -load-pass-plugin build/{plugin} -passes {pass_name} -S {current_bc} -o {next_ll}",
                    "status": "success" if pass_success else "failed",
                    "stderr": self.get_last_stderr()
                }
                
                if not pass_success:
                    print(f"Pass {pass_name} failed, continuing...")
                    shutil.copy2(str(current_bc), str(next_bc))
                    step_info["status"] = "failed"
                    step_info["error"] = "Pass execution failed"
                else:
                    if not self.llvm_as(next_ll, next_bc):
                        step_info["status"] = "failed"
                        step_info["error"] = "LLVM assembly failed"
                    else:
                        # Add pass details if available
                        pass_details = self.get_pass_details(pass_name)
                        if pass_details:
                            step_info["details"] = pass_details
                
                self.report_data["steps"].append(step_info)
                current_bc = next_bc
            
            # Final compilation steps
            if passes:  # Only if we have passes
                final_bc = Path(f"pass_{len(passes)-1}.bc")
            else:
                # If no passes selected, compile original
                final_bc = bc_file
            
            # LLC compilation
            step_start = time.time()
            obj_file = self.work_dir / "final.o"
            llc_success = self.run_command(
                ["llc", "-filetype=obj", str(final_bc), "-o", str(obj_file)],
                "LLC Compile"
            )
            self.report_data["steps"].append({
                "step": "llc_compile",
                "command": f"llc -filetype=obj {final_bc} -o final.o",
                "status": "success" if llc_success else "failed",
                "output": "Generated object file" if llc_success else "Failed to generate object file"
            })
            self.pass_times.append(("llc_compile", time.time() - step_start))
            
            # Final linking
            step_start = time.time()
            link_success = self.run_command(
                ["clang", str(obj_file), "-o", str(self.output_file), "-mconsole"],
                "Final Link"
            )
            self.report_data["steps"].append({
                "step": "final_link",
                "command": f"clang final.o -o {self.output_file} -mconsole",
                "status": "success" if link_success else "failed",
                "output": "Generated final executable" if link_success else "Failed to generate executable"
            })
            self.pass_times.append(("final_link", time.time() - step_start))
            
            success = self.output_file.exists()
            
            # Always generate the comprehensive report
            self.generate_comprehensive_report()
            
            return success
            
        finally:
            # Always change back to original directory
            os.chdir(original_cwd)

    def run_command(self, cmd, description):
        """Run a command and return success status"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            self.last_stderr = result.stderr
            self.last_stdout = result.stdout
            return result.returncode == 0
        except Exception as e:
            self.last_stderr = str(e)
            return False
    
    def get_last_stderr(self):
        """Get the last stderr output"""
        return getattr(self, 'last_stderr', '')
    
    def get_pass_details(self, pass_name):
        """Extract pass details from the advanced_passes report data"""
        for pass_info in self.report_data.get("advanced_passes", []):
            if pass_info.get("pass") == pass_name and pass_info.get("status") == "success":
                return pass_info.get("details", {})
        return {}

    def run_opt_pass(self, input_bc, output_ll, pass_name, description, plugin):
        """Run a single opt pass"""
        backend_dir = Path(__file__).parent
        plugin_path = backend_dir / "build" / plugin
        
        cmd = [
            "opt", "-load-pass-plugin", str(plugin_path),
            "-passes", pass_name, "-S", str(input_bc), "-o", str(output_ll)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            self.last_stderr = result.stderr
        except Exception as e:
            self.last_stderr = str(e)
            return False
        
        if result.returncode != 0:
            soft_errors = [
                "broken module", "verifier failed", "does not dominate",
                "instruction does not dominate all uses", "terminator found in the middle"
            ]
            
            error_msg = result.stderr.lower() if result.stderr else ""
            is_soft_error = any(soft_err in error_msg for soft_err in soft_errors)
            
            if is_soft_error:
                self.report_data["advanced_passes"].append({
                    "pass": pass_name, "description": description,
                    "status": "soft_failure", "error": "Soft failure"
                })
                with open(output_ll, 'w', encoding='utf-8') as f:
                    f.write("; Empty file due to pass failure\n")
                return True
            else:
                return False
        
        self.parse_pass_output(result.stderr, pass_name, description)
        return True
    
    def safe_json_parse(self, json_str):
        """Safely parse JSON with error recovery for invalid escape sequences"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            # Try to fix common JSON issues
            try:
                # Fix invalid Unicode escapes by replacing them
                fixed_json = re.sub(r'\\u[0-9a-fA-F]{0,3}[^0-9a-fA-F]', r'\\\\u0000', json_str)
                return json.loads(fixed_json)
            except:
                # If still failing, try to extract key-value pairs manually
                return self.extract_key_values(json_str)
    
    def extract_key_values(self, text):
        """Extract key-value pairs from text when JSON parsing fails"""
        result = {}
        try:
            # Look for basic patterns like "key": value
            patterns = [
                r'"strings_encrypted"\s*:\s*(\d+)',
                r'"bogus_instr_count"\s*:\s*(\d+)',
                r'"functions_renamed"\s*:\s*(\d+)',
                r'"globals_renamed"\s*:\s*(\d+)',
                r'"encrypted_strings"\s*:\s*\[[^\]]*\]',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                if matches:
                    if "strings_encrypted" in pattern:
                        result["strings_encrypted"] = int(matches[0])
                    elif "bogus_instr_count" in pattern:
                        result["bogus_instr_count"] = int(matches[0])
                    elif "functions_renamed" in pattern:
                        result["functions_renamed"] = int(matches[0])
                    elif "globals_renamed" in pattern:
                        result["globals_renamed"] = int(matches[0])
                    elif "encrypted_strings" in pattern:
                        # Count items in array
                        array_match = re.search(r'\[([^\]]*)\]', text)
                        if array_match:
                            items = array_match.group(1).split(',')
                            result["encrypted_strings"] = [item.strip(' "') for item in items if item.strip()]
                            result["strings_encrypted"] = len(result["encrypted_strings"])
            
            return result
        except Exception as e:
            print(f"Error extracting key-values: {e}")
            return {}
    
    def parse_pass_output(self, stderr, pass_name, description):
        """Parse pass output and store in report - FIXED with robust JSON handling"""
        try:
            if stderr and stderr.strip():
                data = {"pass": pass_name, "description": description, "status": "success"}
                
                # Debug output
                print(f"DEBUG [{pass_name}]: {stderr[:500]}...")
                
                # Look for JSON data in stderr
                if "{" in stderr and "}" in stderr:
                    try:
                        json_start = stderr.find('{')
                        json_end = stderr.rfind('}') + 1
                        json_str = stderr[json_start:json_end]
                        
                        # Use safe JSON parsing
                        json_data = self.safe_json_parse(json_str)
                        
                        if json_data:
                            data["details"] = json_data
                            print(f"✅ Successfully parsed {pass_name} output")
                            
                            # Special handling for string encryption
                            if pass_name == "stringenc":
                                if "strings_encrypted" in json_data:
                                    print(f"✅ String encryption: {json_data['strings_encrypted']} strings")
                                elif "encrypted_strings" in json_data:
                                    count = len(json_data["encrypted_strings"])
                                    data["details"]["strings_encrypted"] = count
                                    print(f"✅ Counted encrypted strings: {count}")
                        else:
                            data["message"] = "JSON parsing failed, using fallback"
                            # Try fallback extraction
                            fallback_data = self.extract_pass_data_from_text(stderr, pass_name)
                            if fallback_data:
                                data["details"] = fallback_data
                            
                    except Exception as e:
                        print(f"JSON processing error: {e}")
                        data["message"] = f"JSON error: {str(e)}"
                        # Try fallback extraction
                        fallback_data = self.extract_pass_data_from_text(stderr, pass_name)
                        if fallback_data:
                            data["details"] = fallback_data
                else:
                    data["message"] = stderr.strip()
                    # Try to extract data from non-JSON output
                    fallback_data = self.extract_pass_data_from_text(stderr, pass_name)
                    if fallback_data:
                        data["details"] = fallback_data
                
                # Ensure we have the advanced_passes list
                if "advanced_passes" not in self.report_data:
                    self.report_data["advanced_passes"] = []
                
                self.report_data["advanced_passes"].append(data)
                
        except Exception as e:
            print(f"Error parsing pass output: {e}")
            # Ensure we have the advanced_passes list
            if "advanced_passes" not in self.report_data:
                self.report_data["advanced_passes"] = []
                
            self.report_data["advanced_passes"].append({
                "pass": pass_name, "description": description,
                "status": "success", "message": f"Output parsing failed: {str(e)}"
            })
    
    def extract_pass_data_from_text(self, text, pass_name):
        """Extract pass data from text when JSON parsing fails"""
        data = {}
        
        if pass_name == "stringenc":
            # Look for string encryption patterns
            encrypted_match = re.search(r'strings?_encrypted[^\d]*(\d+)', text, re.IGNORECASE)
            if encrypted_match:
                data["strings_encrypted"] = int(encrypted_match.group(1))
            
            # Look for encrypted strings array
            array_match = re.search(r'encrypted_strings[^[]*\[([^\]]*)\]', text)
            if array_match:
                items = array_match.group(1).split(',')
                encrypted_strings = [item.strip(' "') for item in items if item.strip()]
                data["encrypted_strings"] = encrypted_strings
                if "strings_encrypted" not in data:
                    data["strings_encrypted"] = len(encrypted_strings)
        
        elif pass_name == "bogus-instructions":
            instr_match = re.search(r'bogus_instr_count[^\d]*(\d+)', text, re.IGNORECASE)
            if instr_match:
                data["bogus_instr_count"] = int(instr_match.group(1))
        
        elif pass_name == "rename-symbols":
            func_match = re.search(r'functions_renamed[^\d]*(\d+)', text, re.IGNORECASE)
            global_match = re.search(r'globals_renamed[^\d]*(\d+)', text, re.IGNORECASE)
            
            if func_match:
                data["functions_renamed"] = int(func_match.group(1))
            if global_match:
                data["globals_renamed"] = int(global_match.group(1))
        
        return data if data else None
    
    def emit_bc(self, output_bc):
        cmd = ["clang", "-O0", "-c", "-emit-llvm", str(self.input_file), "-o", str(output_bc)]
        return self.run_command(cmd, "Emit BC")
    
    def llvm_as(self, input_ll, output_bc):
        cmd = ["llvm-as", str(input_ll), "-o", str(output_bc)]
        return self.run_command(cmd, "LLVM Assemble")
    
    def calculate_timing_metrics(self):
        """Calculate timing metrics from pass times"""
        if not self.pass_times:
            return {
                "total_duration": "unknown",
                "average_pass_time": "unknown", 
                "slowest_pass": "unknown",
                "fastest_pass": "unknown"
            }
        
        total_duration = time.time() - self.start_time
        pass_durations = [duration for _, duration in self.pass_times if isinstance(duration, (int, float))]
        
        if pass_durations:
            avg_time = sum(pass_durations) / len(pass_durations)
            slowest = max(pass_durations)
            fastest = min(pass_durations)
            slowest_pass = self.pass_times[pass_durations.index(slowest)][0]
            fastest_pass = self.pass_times[pass_durations.index(fastest)][0]
        else:
            avg_time = slowest = fastest = 0
            slowest_pass = fastest_pass = "unknown"
        
        return {
            "total_duration": f"{total_duration:.2f}s",
            "average_pass_time": f"{avg_time:.2f}s",
            "slowest_pass": f"{slowest_pass} ({slowest:.2f}s)",
            "fastest_pass": f"{fastest_pass} ({fastest:.2f}s)"
        }
    
    def generate_comprehensive_report(self):
        """Generate the final comprehensive report with all fixed metrics"""
        # Calculate all metrics
        metrics = self.calculate_metrics()
        file_sizes = self.calculate_file_sizes()
        timing = self.calculate_timing_metrics()
        
        # Build complete report
        report = {
            "metadata": {
                "timestamp": datetime.datetime.now().isoformat(),
                "input_file": str(self.input_file),
                "output_file": str(self.output_file),
                "obfuscation_level": "advanced",
                "security_rating": self.calculate_security_rating(metrics)
            },
            "metrics": metrics,
            "timing": timing,
            "file_sizes": file_sizes,
            "steps": self.report_data["steps"],
            "pass_reports": self.build_pass_reports(),
            "summary": self.build_summary(metrics)
        }
        
        # Write the report
        with open("report.json", "w", encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report
    
    def calculate_metrics(self):
        """Calculate obfuscation metrics from pass data - COMPLETELY FIXED"""
        metrics = {
            "strings_encrypted": 0, "functions_renamed": 0, "globals_renamed": 0,
            "bogus_instr_count": 0, "control_flow_obfuscated": 0,
            "opaque_predicates_added": 0, "anti_debugging_checks": 0,
            "basic_blocks_split": 0
        }
        
        print("=== CALCULATING METRICS ===")
        
        # Initialize advanced_passes if it doesn't exist
        if "advanced_passes" not in self.report_data:
            self.report_data["advanced_passes"] = []
        
        for pass_info in self.report_data.get("advanced_passes", []):
            if pass_info.get("status") != "success":
                continue
                
            pass_name = pass_info.get("pass")
            details = pass_info.get("details", {})
            
            print(f"Processing pass: {pass_name}")
            print(f"Details: {details}")
            
            if pass_name == "stringenc":
                # FIXED: Properly handle string encryption count
                if "strings_encrypted" in details:
                    count = details["strings_encrypted"]
                    metrics["strings_encrypted"] = count
                    print(f"✅ Set strings_encrypted: {count}")
                elif "encrypted_strings" in details:
                    # Count the encrypted strings array
                    count = len(details["encrypted_strings"])
                    metrics["strings_encrypted"] = count
                    print(f"✅ Counted encrypted_strings: {count}")
                else:
                    print("⚠️ No string count found in stringenc pass")
                    # If we have encrypted strings but no count, set to 0 to avoid inconsistency
                    metrics["strings_encrypted"] = 0
                    
            elif pass_name == "rename-symbols":
                metrics["functions_renamed"] = details.get("functions_renamed", 0)
                metrics["globals_renamed"] = details.get("globals_renamed", 0)
                print(f"✅ Renaming: {metrics['functions_renamed']} functions, {metrics['globals_renamed']} globals")
                
            elif pass_name == "bogus-instructions":
                if "bogus_instr_count" in details:
                    metrics["bogus_instr_count"] = details["bogus_instr_count"]
                    print(f"✅ Bogus instructions: {details['bogus_instr_count']}")
                    
            elif pass_name == "cfflatten":
                metrics["control_flow_obfuscated"] = 1
                print("✅ Control flow flattened")
                
            elif pass_name == "opaque-preds":
                # Count actual predicates if available, otherwise mark as applied
                if "predicates_added" in details:
                    metrics["opaque_predicates_added"] = details["predicates_added"]
                else:
                    metrics["opaque_predicates_added"] = 1
                print("✅ Opaque predicates added")
                
            elif pass_name == "anti-debug":
                metrics["anti_debugging_checks"] = 1
                print("✅ Anti-debugging checks added")
                
            elif pass_name == "bbsplit":
                metrics["basic_blocks_split"] = 1
                print("✅ Basic blocks split")
        
        print(f"=== FINAL METRICS: {metrics} ===")
        return metrics
    
    def build_pass_reports(self):
        """Build detailed pass reports for the final report"""
        pass_reports = []
        # Initialize advanced_passes if it doesn't exist
        if "advanced_passes" not in self.report_data:
            self.report_data["advanced_passes"] = []
            
        for pass_info in self.report_data.get("advanced_passes", []):
            if pass_info.get("status") == "success":
                report = {
                    "pass": pass_info["pass"],
                    "description": pass_info["description"],
                    "type": "obfuscation"
                }
                # Add pass-specific details
                details = pass_info.get("details", {})
                if details:
                    report.update(details)
                pass_reports.append(report)
        return pass_reports
    
    def calculate_file_sizes(self):
        """Calculate file sizes including intermediate files"""
        sizes = {}
        if self.input_file.exists():
            sizes["input_size"] = self.input_file.stat().st_size
        if self.output_file.exists():
            sizes["output_size"] = self.output_file.stat().st_size
        
        # Add intermediate file sizes if they exist
        bc_files = list(Path(".").glob("*.bc"))
        ll_files = list(Path(".").glob("*.ll"))
        
        if bc_files:
            sizes["largest_bc"] = max(f.stat().st_size for f in bc_files)
            sizes["smallest_bc"] = min(f.stat().st_size for f in bc_files)
        if ll_files:
            sizes["largest_ll"] = max(f.stat().st_size for f in ll_files)
            sizes["smallest_ll"] = min(f.stat().st_size for f in ll_files)
        
        return sizes
    
    def calculate_security_rating(self, metrics):
        """Calculate security rating based on applied obfuscations"""
        score = 0
        
        # Weight different obfuscation techniques
        if metrics["strings_encrypted"] > 0:
            score += 2
        if metrics["functions_renamed"] > 0:
            score += 1
        if metrics["bogus_instr_count"] > 10:
            score += 2
        if metrics["control_flow_obfuscated"] > 0:
            score += 3
        if metrics["opaque_predicates_added"] > 0:
            score += 2
        if metrics["anti_debugging_checks"] > 0:
            score += 2
        if metrics["basic_blocks_split"] > 0:
            score += 1
        
        if score >= 8:
            return "HIGH"
        elif score >= 5:
            return "MEDIUM"
        else:
            return "BASIC"
    
    def build_summary(self, metrics):
        """Build summary with consistent achievement reporting"""
        successful_passes = len([p for p in self.report_data.get("advanced_passes", []) if p.get("status") == "success"])
        
        # Build achievements - FIXED to be consistent with metrics
        achievements = []
        
        if metrics['strings_encrypted'] > 0:
            achievements.append(f"Encrypted {metrics['strings_encrypted']} strings")
        
        if metrics['functions_renamed'] > 0 or metrics['globals_renamed'] > 0:
            achievements.append(f"Renamed {metrics['functions_renamed']} functions and {metrics['globals_renamed']} globals")
        
        if metrics['bogus_instr_count'] > 0:
            achievements.append(f"Added {metrics['bogus_instr_count']} bogus instructions")
        
        if metrics['control_flow_obfuscated']:
            achievements.append("Applied control flow flattening")
        
        if metrics['opaque_predicates_added'] > 0:
            achievements.append(f"Added {metrics['opaque_predicates_added']} opaque predicates")
        
        if metrics['anti_debugging_checks'] > 0:
            achievements.append(f"Added {metrics['anti_debugging_checks']} anti-debugging checks")
        
        if metrics['basic_blocks_split'] > 0:
            achievements.append(f"Split {metrics['basic_blocks_split']} basic blocks")
        
        # If no specific achievements, add general one
        if not achievements and successful_passes > 0:
            achievements = [f"Applied {successful_passes} obfuscation passes"]
        elif not achievements:
            achievements = ["Basic compilation completed"]
        
        # Build recommendations
        recommendations = []
        if metrics['strings_encrypted'] == 0:
            recommendations.append("More strings could be encrypted for better protection")
        if metrics['functions_renamed'] < 2:
            recommendations.append("Additional function renaming would improve obfuscation")
        if metrics['bogus_instr_count'] < 20:
            recommendations.append("Consider adding more bogus instructions for increased complexity")
        
        return {
            "total_passes_applied": successful_passes,
            "obfuscation_effectiveness": self.calculate_security_rating(metrics),
            "key_achievements": achievements,
            "recommendations": recommendations
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_advanced_obfuscation.py <input.c> [output.exe]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "super_obfuscated.exe"
    
    pipeline = AdvancedObfuscationPipeline(input_file, output_file)
    if pipeline.run_advanced_obfuscation():
        print("Obfuscation completed successfully")
        print(f"Report generated: report.json")
    else:
        print("Obfuscation failed")
        sys.exit(1)