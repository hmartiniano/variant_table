# Makefile for ClinVar VCF Download and Parsing

# --- Variables ---
# Tool Configuration
PYTHON = python3 # Use python3 or python
WGET = wget
# CURL = curl -L # Uncomment if you prefer curl

# File/URL Configuration
# Use GRCh38 VCF URL from NCBI FTP
VCF_URL = https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz
VCF_GZ_FILE = clinvar_grch38.vcf.gz
PARSER_SCRIPT = parse_clinvar_vcf.py
OUTPUT_CSV = variants.csv
OUTPUT_JSON = variants.json

# Default arguments for the parser script (can be overridden)
# Example: ARGS="--limit 1000" make parse
ARGS =

# --- Targets ---

# Default target: download and parse
all: download parse

# Download the ClinVar VCF file
download:
	@echo "--- Downloading ClinVar VCF (GRCh38) from $(VCF_URL) ---"
	@echo "    (This may take a while...)"
	$(WGET) -O $(VCF_GZ_FILE) $(VCF_URL)
# Alternative using curl:
#	$(CURL) -o $(VCF_GZ_FILE) $(VCF_URL)
	@echo "--- Download complete: $(VCF_GZ_FILE) ---"

# Parse the downloaded VCF file into CSV and JSON
parse: $(VCF_GZ_FILE) $(PARSER_SCRIPT)
	@echo "--- Parsing $(VCF_GZ_FILE) using $(PARSER_SCRIPT) ---"
	$(PYTHON) $(PARSER_SCRIPT) $(VCF_GZ_FILE) --csv $(OUTPUT_CSV) --json $(OUTPUT_JSON) $(ARGS)
	@echo "--- Parsing complete. Output: $(OUTPUT_CSV), $(OUTPUT_JSON) ---"

# Clean up downloaded and generated files
clean:
	@echo "--- Cleaning up generated files ---"
	rm -f $(VCF_GZ_FILE) $(OUTPUT_CSV) $(OUTPUT_JSON)
	@echo "--- Cleanup complete ---"

# Declare targets that are not files
.PHONY: all download parse clean
