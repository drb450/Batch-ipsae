#!/usr/bin/env python3
"""
Batch runner for ipsae.py on Boltz output structures.
Collates results into separate CSV files for A→B, B→A, and max interaction types.
"""

import os
import sys
import subprocess
import pandas as pd
import glob
from pathlib import Path
import argparse

def find_boltz_structures(out_dir):
    """
    Find all PAE and CIF file pairs in the Boltz output directory.
    
    Args:
        out_dir (str): Path to Boltz output directory
        
    Returns:
        list: List of tuples containing (pae_file, cif_file, input_name)
    """
    predictions_dir = os.path.join(out_dir, "predictions")
    
    if not os.path.exists(predictions_dir):
        print(f"Error: Predictions directory not found at {predictions_dir}")
        return []
    
    structure_pairs = []
    
    # Iterate through each input folder in predictions
    for input_folder in os.listdir(predictions_dir):
        input_path = os.path.join(predictions_dir, input_folder)
        
        if not os.path.isdir(input_path):
            continue
            
        print(f"Processing folder: {input_folder}")
        
        # Find all PAE files in this folder
        pae_files = glob.glob(os.path.join(input_path, f"pae_{input_folder}_model_*.npz"))
        
        for pae_file in pae_files:
            # Extract model number from PAE filename
            pae_basename = os.path.basename(pae_file)
            model_part = pae_basename.replace(f"pae_{input_folder}_", "").replace(".npz", "")
            
            # Find corresponding CIF file
            cif_file = os.path.join(input_path, f"{input_folder}_{model_part}.cif")
            
            if os.path.exists(cif_file):
                structure_pairs.append((pae_file, cif_file, input_folder))
                print(f"  Found pair: {os.path.basename(pae_file)} + {os.path.basename(cif_file)}")
            else:
                print(f"  Warning: CIF file not found for {pae_basename}")
    
    return structure_pairs

def run_ipsae(ipsae_script_path, pae_file, cif_file, pae_cutoff, dist_cutoff):
    """
    Run ipsae.py on a single structure pair.
    
    Args:
        ipsae_script_path (str): Path to ipsae.py script
        pae_file (str): Path to PAE NPZ file
        cif_file (str): Path to CIF file
        pae_cutoff (float): PAE cutoff value
        dist_cutoff (float): Distance cutoff value
        
    Returns:
        str or None: Path to the generated .txt file, or None if failed
    """
    try:
        # Run ipsae.py
        cmd = [
            "python", ipsae_script_path,
            pae_file, cif_file,
            str(pae_cutoff), str(dist_cutoff)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Determine the expected output .txt file name
        cif_basename = os.path.splitext(os.path.basename(cif_file))[0]
        output_txt = f"{cif_basename}_{pae_cutoff}_{dist_cutoff}.txt"
        
        # Check if the file was created in the current directory or same directory as CIF
        current_dir_output = output_txt
        cif_dir_output = os.path.join(os.path.dirname(cif_file), output_txt)
        
        if os.path.exists(current_dir_output):
            return current_dir_output
        elif os.path.exists(cif_dir_output):
            return cif_dir_output
        else:
            print(f"Warning: Expected output file not found: {output_txt}")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Error running ipsae.py: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

def parse_ipsae_output(txt_file):
    """
    Parse the ipsae output .txt file.
    
    Args:
        txt_file (str): Path to the .txt file
        
    Returns:
        pd.DataFrame or None: Parsed data as DataFrame, or None if failed
    """
    try:
        # Read the file, assuming it's tab or space delimited
        df = pd.read_csv(txt_file, delim_whitespace=True)
        return df
    except Exception as e:
        print(f"Error parsing {txt_file}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Batch run ipsae.py on Boltz output structures")
    parser.add_argument("out_dir", help="Path to Boltz output directory")
    parser.add_argument("ipsae_script", help="Path to ipsae.py script")
    parser.add_argument("--pae_cutoff", type=float, default=15.0, help="PAE cutoff value (default: 15)")
    parser.add_argument("--dist_cutoff", type=float, default=15.0, help="Distance cutoff value (default: 15)")
    parser.add_argument("--output_prefix", default="ipsae_results", help="Prefix for output CSV files")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.out_dir):
        print(f"Error: Output directory not found: {args.out_dir}")
        sys.exit(1)
        
    if not os.path.exists(args.ipsae_script):
        print(f"Error: ipsae.py script not found: {args.ipsae_script}")
        sys.exit(1)
    
    # Find all structure pairs
    print("Finding Boltz structure pairs...")
    structure_pairs = find_boltz_structures(args.out_dir)
    
    if not structure_pairs:
        print("No structure pairs found!")
        sys.exit(1)
    
    print(f"Found {len(structure_pairs)} structure pairs to process")
    
    # Initialize lists to collect results
    all_results = []
    
    # Process each structure pair
    for i, (pae_file, cif_file, input_name) in enumerate(structure_pairs, 1):
        print(f"\n=== Processing {i}/{len(structure_pairs)}: {input_name} ===")
        
        # Run ipsae.py
        output_txt = run_ipsae(args.ipsae_script, pae_file, cif_file, 
                              args.pae_cutoff, args.dist_cutoff)
        
        if output_txt:
            # Parse the results
            df = parse_ipsae_output(output_txt)
            
            if df is not None and not df.empty:
                # Add metadata columns
                df['input_name'] = input_name
                df['pae_file'] = os.path.basename(pae_file)
                df['cif_file'] = os.path.basename(cif_file)
                
                all_results.append(df)
                print(f"  Successfully processed: {len(df)} rows")
                
                # Clean up the temporary output file if it's in current directory
                if os.path.exists(output_txt) and os.path.dirname(output_txt) == "":
                    try:
                        os.remove(output_txt)
                    except:
                        pass
            else:
                print(f"  Failed to parse results from {output_txt}")
        else:
            print(f"  Failed to generate ipsae output")
    
    # Combine all results
    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        print(f"\nCombined {len(combined_df)} total rows from {len(all_results)} structures")
        
        # Separate by interaction type and save to CSV
        interaction_types = ['asym', 'max']  # Based on your example, looks like A->B and B->A are both 'asym'
        
        # Check what Type values actually exist
        if 'Type' in combined_df.columns:
            actual_types = combined_df['Type'].unique()
            print(f"Found interaction types: {list(actual_types)}")
            
            # Save separate CSV for each type
            for interaction_type in actual_types:
                type_df = combined_df[combined_df['Type'] == interaction_type].copy()
                
                if not type_df.empty:
                    output_file = f"{args.output_prefix}_{interaction_type}.csv"
                    type_df.to_csv(output_file, index=False)
                    print(f"Saved {len(type_df)} rows to {output_file}")
            
            # Also save A->B and B->A separately if we have Chn1 and Chn2 columns
            if 'Chn1' in combined_df.columns and 'Chn2' in combined_df.columns:
                # A->B interactions
                ab_df = combined_df[(combined_df['Chn1'] == 'A') & (combined_df['Chn2'] == 'B')].copy()
                if not ab_df.empty:
                    ab_file = f"{args.output_prefix}_A_to_B.csv"
                    ab_df.to_csv(ab_file, index=False)
                    print(f"Saved {len(ab_df)} A→B interactions to {ab_file}")
                
                # B->A interactions
                ba_df = combined_df[(combined_df['Chn1'] == 'B') & (combined_df['Chn2'] == 'A')].copy()
                if not ba_df.empty:
                    ba_file = f"{args.output_prefix}_B_to_A.csv"
                    ba_df.to_csv(ba_file, index=False)
                    print(f"Saved {len(ba_df)} B→A interactions to {ba_file}")
        
        # Save complete results
        complete_file = f"{args.output_prefix}_complete.csv"
        combined_df.to_csv(complete_file, index=False)
        print(f"Saved complete results ({len(combined_df)} rows) to {complete_file}")
        
    else:
        print("No results to save!")

if __name__ == "__main__":
    main()
