import cyvcf2
import argparse
import csv
import json
import sys
import logging
from collections import OrderedDict
import gzip # Needed for writing gzipped output if desired

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper functions (parse_vcf_info, format_record) remain the same ---
# --- They process one record at a time, so they are already stream-friendly ---
def parse_vcf_info(info_dict):
    """
    Parses relevant fields from the cyvcf2 INFO dictionary-like object.
    Handles potential multiple values (tuples in cyvcf2) and missing keys.
    """
    parsed = {}

    # GENEINFO: Often 'GeneSymbol:GeneID', potentially multiple pipe-separated. cyvcf2 might return string.
    gene_info_raw = info_dict.get('GENEINFO')
    if gene_info_raw:
        # Take the first gene if multiple exist (split by '|' if necessary, then take first part before ':')
        first_gene_part = str(gene_info_raw).split('|')[0]
        parsed['gene'] = first_gene_part.split(':')[0]
    else:
        parsed['gene'] = 'N/A'

    # Clinical Significance (CLNSIG): Can be a tuple of strings or single string in cyvcf2
    clnsig_raw = info_dict.get('CLNSIG')
    if isinstance(clnsig_raw, tuple):
        parsed['clinicalSignificance'] = ', '.join(map(str, clnsig_raw))
    elif clnsig_raw:
        parsed['clinicalSignificance'] = str(clnsig_raw)
    else:
        parsed['clinicalSignificance'] = 'N/A'

    # ClinVar Allele ID (ALLELEID): Usually an integer
    parsed['clinvarAlleleId'] = info_dict.get('ALLELEID', 'N/A')

    # Review Status (CLNREVSTAT): Often a tuple of strings
    clnrevstat_raw = info_dict.get('CLNREVSTAT')
    if isinstance(clnrevstat_raw, tuple):
        parsed['reviewStatus'] = ', '.join(map(str, clnrevstat_raw))
    elif clnrevstat_raw:
         parsed['reviewStatus'] = str(clnrevstat_raw)
    else:
        parsed['reviewStatus'] = 'N/A'

    # Clinical Disease Name (CLNDN): Often a tuple of strings
    clndn_raw = info_dict.get('CLNDN')
    if isinstance(clndn_raw, tuple):
        parsed['diseaseName'] = ', '.join(map(str, clndn_raw))
    elif clndn_raw:
        parsed['diseaseName'] = str(clndn_raw)
    else:
        parsed['diseaseName'] = 'N/A'

    # Variant type (CLNVC): Usually a string
    parsed['variantType'] = info_dict.get('CLNVC', 'N/A')

    # Variant Origin (CLNORIGIN): May be useful detail
    clnorigin_raw = info_dict.get('CLNORIGIN')
    if isinstance(clnorigin_raw, tuple):
        parsed['origin'] = ', '.join(map(str, clnorigin_raw))
    elif clnorigin_raw:
        parsed['origin'] = str(clnorigin_raw)
    else:
        parsed['origin'] = 'N/A'

    return parsed


def format_record(record):
    """
    Formats a cyvcf2 Variant record into an OrderedDict suitable for output.
    Handles multi-allelic sites by processing the first ALT allele primarily.
    Uses ALLELEID as clinvarId and VCF ID as variantId (rsID).
    """
    output_record = OrderedDict() # Use OrderedDict to maintain column order easily

    output_record['chromosome'] = record.CHROM
    output_record['position'] = record.POS

    # --- POTENTIAL SWAP AREA ---
    # VCF ID Field (often rsID, can be ';'-separated, can be None)
    # THIS should go into 'variantId'
    output_record['variantId'] = record.ID.split(';')[0] if record.ID else 'N/A'

    output_record['refAllele'] = record.REF
    output_record['altAllele'] = record.ALT[0] if record.ALT else 'N/A'

    # Parse INFO fields
    info_data = parse_vcf_info(record.INFO)

    # ClinVar Allele ID (numeric ID from INFO field)
    # THIS should go into 'clinvarId'
    output_record['clinvarId'] = info_data.get('clinvarAlleleId', 'N/A') # Relies on parse_vcf_info getting 'ALLELEID'
    # --- END POTENTIAL SWAP AREA ---


    output_record['gene'] = info_data.get('gene', 'N/A')
    output_record['clinicalSignificance'] = info_data.get('clinicalSignificance', 'N/A')
    output_record['reviewStatus'] = info_data.get('reviewStatus', 'N/A')
    output_record['diseaseName'] = info_data.get('diseaseName', 'N/A')
    output_record['variantType'] = info_data.get('variantType', 'N/A')
    output_record['origin'] = info_data.get('origin', 'N/A')

    return output_record

# --- End of helper functions ---


def main():
    parser = argparse.ArgumentParser(
        description='Stream parse ClinVar VCF using cyvcf2 and output CSV and/or JSON Lines.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Show defaults in help
    )
    parser.add_argument('vcf_file', help='Path to the input VCF file (e.g., clinvar.vcf.gz)')
    parser.add_argument('--csv', help='Path to the output CSV file (optional)')
    parser.add_argument('--json', help='Path to the output JSON Lines file (.jsonl) (optional)')
    parser.add_argument('--limit', type=int, default=None, help='Limit processing to the first N records (optional, for testing)')
    parser.add_argument('--skip-filtered', action='store_true', help='Skip records that do not have FILTER=PASS')
    parser.add_argument('--gz', action='store_true', help='Compress output files with gzip (appends .gz to filenames)')


    args = parser.parse_args()

    if not args.csv and not args.json:
        logging.error("Error: No output format specified. Use --csv and/or --json.")
        sys.exit(1)

    # --- Prepare output files and writers ---
    csv_writer = None
    json_file = None
    output_headers = None
    csv_file_handle = None # Keep track of file handle for closing

    try:
        # Open CSV file if requested
        if args.csv:
            csv_filename = f"{args.csv}.gz" if args.gz else args.csv
            logging.info(f"Preparing CSV output to: {csv_filename}")
            # Use 'wt' for text mode with gzip, 'w' for regular text
            open_mode = 'wt' if args.gz else 'w'
            file_opener = gzip.open if args.gz else open
            # Need to keep the file handle open until the end
            csv_file_handle = file_opener(csv_filename, open_mode, newline='', encoding='utf-8')
            # We defer creating the DictWriter until we have headers

        # Open JSON Lines file if requested
        if args.json:
            json_filename = f"{args.json}.gz" if args.gz else args.json
            logging.info(f"Preparing JSON Lines output to: {json_filename}")
            open_mode = 'wt' if args.gz else 'w'
            file_opener = gzip.open if args.gz else open
            json_file = file_opener(json_filename, open_mode, encoding='utf-8')

        # --- Process VCF Stream ---
        record_count = 0
        processed_count = 0 # Count records actually written
        logging.info(f"Opening VCF file: {args.vcf_file}")
        vcf_reader = cyvcf2.VCF(args.vcf_file)

        logging.info("Streaming VCF records...")
        for record in vcf_reader:
            record_count += 1

            # Optional filtering
            if args.skip_filtered and record.FILTER and record.FILTER != 'PASS':
                continue

            # Format the current record
            try:
                formatted_record = format_record(record)
            except Exception as format_exc:
                 logging.warning(f"Skipping record {record_count} due to formatting error: {format_exc} - Record: {record.CHROM}:{record.POS}")
                 continue # Skip this record

            # --- Write to CSV (handle header on first valid record) ---
            if csv_file_handle:
                if csv_writer is None:
                    # First valid record, determine headers and create writer
                    output_headers = list(formatted_record.keys())
                    csv_writer = csv.DictWriter(csv_file_handle, fieldnames=output_headers)
                    try:
                        csv_writer.writeheader()
                    except Exception as csv_exc:
                         logging.error(f"Error writing CSV header: {csv_exc}")
                         # Optionally exit or disable further CSV writing
                         csv_file_handle.close()
                         csv_file_handle = None
                         csv_writer = None # Prevent further write attempts
                         logging.error("Disabling further CSV output.")


                if csv_writer: # Check if writer is still valid
                    try:
                        csv_writer.writerow(formatted_record)
                    except Exception as csv_exc:
                        logging.warning(f"Skipping CSV write for record {record_count} due to error: {csv_exc}")
                        # Potentially disable writer after too many errors, or just log


            # --- Write to JSON Lines ---
            if json_file:
                try:
                    json.dump(formatted_record, json_file)
                    json_file.write('\n')
                except Exception as json_exc:
                     logging.warning(f"Skipping JSON write for record {record_count} due to error: {json_exc}")
                     # Potentially disable writer after too many errors

            processed_count += 1

            # Progress logging and limit check
            if record_count % 100000 == 0: # Log less frequently for streaming
                 logging.info(f"Read {record_count} records, processed {processed_count}...")
            if args.limit and processed_count >= args.limit:
                logging.info(f"Reached processed record limit of {args.limit}.")
                break

    except FileNotFoundError:
         logging.error(f"Error: VCF file not found at {args.vcf_file}")
         sys.exit(1)
    except Exception as e:
         logging.error(f"An unexpected error occurred during VCF processing: {e}", exc_info=True)
         # Files might be partially written
    finally:
        # --- Clean up ---
        if 'vcf_reader' in locals() and vcf_reader:
            vcf_reader.close()
        if csv_file_handle:
            csv_file_handle.close()
            logging.info(f"CSV file closed.")
        if json_file:
            json_file.close()
            logging.info(f"JSON Lines file closed.")

        logging.info(f"Finished processing. Total VCF records read: {record_count}, Records processed/written: {processed_count}")
        if processed_count == 0 and record_count > 0:
             logging.warning("No records were successfully processed and written. Check filters or formatting logic.")
        elif processed_count == 0 and record_count == 0:
              logging.warning("Input VCF contained no processable records.")


if __name__ == "__main__":
    main()
