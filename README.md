# Batch-ipsae
Run a batch of ipsae using the code from the Dunbrack lab https://github.com/DunbrackLab/IPSAE


Key Features:

Automatic Structure Detection: Scans your out_dir/predictions/ folder to find all PAE (.npz) and CIF file pairs
Batch Processing: Runs ipsae.py on each structure automatically

Results Collation: Combines all results into organized CSV files

Multiple Output Formats: Creates separate CSVs for different interaction types

Usage:
python run_ipsae_batch.py /path/to/your/out_dir /path/to/ipsae.py --pae_cutoff 15 --dist_cutoff 15

Output Files:
The script will generate several CSV files:

ipsae_results_A_to_B.csv - All A→B chain interactions
ipsae_results_B_to_A.csv - All B→A chain interactions
ipsae_results_asym.csv - All asymmetric interactions
ipsae_results_max.csv - All max-type interactions
ipsae_results_complete.csv - All results combined

Additional Features:

Progress tracking: Shows which structures are being processed
Error handling: Continues processing even if individual structures fail
Metadata: Adds columns for input name, source files for easy tracking
Flexible cutoffs: Customizable PAE and distance cutoffs
Cleanup: Removes temporary files automatically

Command Line Options:

--pae_cutoff: PAE cutoff value (default: 15)
--dist_cutoff: Distance cutoff value (default: 15)
--output_prefix: Prefix for output CSV files (default: "ipsae_results")

The script will automatically find all your predicted structures based on the Boltz output format you described and process them systematically. Each row in the final CSVs will represent one structure's interaction data, organized by the interaction type as you requested.
