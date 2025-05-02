# Genetic Variants Viewer

A simple web application to display genetic variant data from a CSV or JSON file using the DataTables library. Includes a Python script to parse ClinVar VCF files into the required format using `cyvcf2`.

## Features

*   **Interactive Table:** Uses DataTables for searching, sorting, pagination, and exporting (CSV, Excel, PDF, Print, Copy).
*   **Dynamic Data Loading:** Can load data from a local JavaScript array or fetch a CSV/JSON file.
*   **Dynamic Columns:** Table headers (`gene`, `variantId`, etc.) are configurable.
*   **Expandable Details:** Click '+' icon to view all fields for a variant in a child row.
*   **ClinVar Links:** Automatically links ClinVar IDs to the NCBI ClinVar website.
*   **dbSNP Links:** Automatically links Variant IDs (if they start with 'rs') to dbSNP.
*   **NCBI Genome Browser Links:** Provides a direct link to view the variant's location on the NCBI Genome Browser (GRCh38).
*   **Responsive Design:** Table adapts to different screen sizes.
*   **VCF Parser:** Python script (`parse_clinvar_vcf.py`) using `cyvcf2` to efficiently parse ClinVar VCF files (.vcf.gz) into CSV or JSON format suitable for the web app.
*   **Makefile:** Simple automation for downloading the latest ClinVar VCF and parsing it.

## Prerequisites

*   **Web Browser:** Any modern web browser (Chrome, Firefox, Safari, Edge).
*   **Python:** Python 3.6+ for the parsing script.
*   **pip:** Python package installer.
*   **cyvcf2:** Python library for VCF parsing (`pip install cyvcf2`).
*   **(Optional) Make:** For using the `Makefile` automation (common on Linux/macOS; can be installed on Windows).
*   **(Optional) wget or curl:** For the `Makefile` download target (common on Linux/macOS; can be installed on Windows).

## Setup

1.  **Clone or Download:** Get the project files (HTML, Python script, Makefile).
2.  **Install Python Dependency:**
    ```bash
    pip install cyvcf2
    ```

## Usage

### 1. Prepare Data (using Makefile - Recommended)

The `Makefile` automates downloading the ClinVar VCF (GRCh38) and parsing it.

*   **Download VCF:** (Downloads `clinvar_grch38.vcf.gz` - ~1GB, takes time)
    ```bash
    make download
    ```
*   **Parse VCF:** (Assumes `clinvar_grch38.vcf.gz` exists; creates `variants.csv` and `variants.json`)
    ```bash
    make parse
    ```
    *You can parse with a limit for testing:*
    ```bash
    make parse ARGS="--limit 1000"
    ```
*   **Download & Parse:**
    ```bash
    make all
    ```
*   **Clean Up:** (Removes downloaded VCF and generated CSV/JSON)
    ```bash
    make clean
    ```

### 2. Prepare Data (Manual Python Script)

Alternatively, run the Python script directly:

1.  **Download ClinVar VCF:** Manually download the VCF file (e.g., `clinvar_grch38.vcf.gz`) from the [NCBI ClinVar FTP site](https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/).
2.  **Run the Parser:**
    ```bash
    # Output CSV (default filename used by HTML)
    python parse_clinvar_vcf.py path/to/clinvar_grch38.vcf.gz --csv variants.csv

    # Output JSON
    python parse_clinvar_vcf.py path/to/clinvar_grch38.vcf.gz --json variants.json

    # Output both with a limit
    python parse_clinvar_vcf.py path/to/clinvar_grch38.vcf.gz --csv variants.csv --json variants.json --limit 5000
    ```

### 3. View the Web Application

1.  **Ensure Data File Exists:** Make sure you have the data file (e.g., `variants.csv`) in the same directory as the HTML file (`index.html` or your chosen name).
2.  **Configure HTML:** Edit the HTML file and find the `config` object within the `<script>` tag:
    *   Set `useCsvData: true` if you want to load `variants.csv`.
    *   Set `useCsvData: false` to use the hardcoded sample data in `dataFromJs`.
    *   (If using JSON): You would need to modify the `fetch` logic slightly to parse JSON instead of using PapaParse for CSV. The current setup defaults to CSV loading when `useCsvData` is true.
    *   Verify `csvFilePath: 'variants.csv'` matches your filename.
    *   Adjust `mainTableKeys` if your CSV has different headers or you want different columns displayed initially.
3.  **Open HTML:** Open the HTML file in your web browser.

## Configuration (HTML/JavaScript)

The primary configuration is within the `<script>` block in the HTML file:

*   `config.useCsvData`: `true` to load CSV, `false` for internal JS data.
*   `config.csvFilePath`: Path to the CSV file (relative to the HTML).
*   `config.mainTableKeys`: Array of keys (CSV headers/JS object keys) to display as main table columns. Order matters. Case-insensitive matching is used.
*   `config.showMainKeysInChildRow`: `true` to repeat main column data in the expandable details, `false` to hide them.
*   `config.genomeBrowserBaseUrl`, `config.genomeAssembly`: Settings for the NCBI Genome Browser links.

## Data Source

The default data source targeted by the Makefile and parser is the **ClinVar VCF for GRCh38**.

*   **URL:** `https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/clinvar.vcf.gz` (Subject to change by NCBI)
*   **Parser Fields:** The script extracts key fields like Chromosome, Position, ID (rsID), Ref/Alt Alleles, Gene Info, ClinVar Allele ID, Clinical Significance, Review Status, Disease Name, Variant Type, Origin. More fields can be added by modifying `parse_vcf_info` and `format_record` in `parse_clinvar_vcf.py`.

## Notes

*   The ClinVar VCF file is large (~1GB compressed), downloading and parsing will take time.
*   The parser currently takes the first rsID found if multiple are listed in the VCF `ID` field.
*   The parser primarily focuses on the first `ALT` allele for simplicity when formatting output. VCF records can be complex (multiple ALTs, structural variants), and this script provides a baseline interpretation.# variant_table
