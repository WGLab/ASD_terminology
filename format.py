import argparse, sys
from processing.clamp import format_clamp_output
from processing.ctakes import format_ctakes_output
from processing.metamap import format_metamap_output_and_generate_labels

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Format the output of CLAMP, cTAKES, or MetaMap for subsequent NER analysis.')
    parser.add_argument('tool', help='Either CLAMP, cTAKES, or MetaMap.')
    parser.add_argument('input_dir', help='The path to the directory containing the CLAMP, cTAKES, or MetaMap output.')
    parser.add_argument('output_dir', help='The path to the directory where a file will be created with the formatted output.')
    parser.add_argument('text_dir', help='The path to the directory where the original texts (input into CLAMP/cTAKES/MetaMap) are located.')
    parser.add_argument('-p', '--print-every', type=int, help='Interval reprsenting number of files after which to continuously print progress.')
    parser.add_argument('-c', '--cui2tui', help='File with CUI to TUI mapping (required for CLAMP). Each row of the file should be in the format "CUI\tTUI"')
    parser.add_argument('-b', '--bm-file', help='File with benchmark terms used to generate true labels from MetaMap output.')
    parser.add_argument('-m', '--metamap-add', help='Additional MetaMap files to be processed.')
    args = parser.parse_args()

    tool = args.tool.lower().strip()
    if tool == 'clamp':
        print('Processing CLAMP output...')
        if not args.cui2tui:
            print('-c --cui2tui argument required when processing CLAMP.')
            sys.exit(1)
        # assumes CLAMP output in output_dir end with .txt and corresponding texts in text_dir also end with .txt
        format_clamp_output(args.input_dir, args.output_dir, args.text_dir, args.cui2tui, args.print_every)
    
    elif tool == 'ctakes':
        print('Processing cTAKES output...')
        # assume cTAKES output in output_dir ends with .csv and corresponding texts in text_dir end with .txt
        format_ctakes_output(args.input_dir, args.output_dir, args.text_dir, args.print_every)

    elif tool == 'metamap':
        print('Processing MetaMap output...')
        if not args.bm_file:
            print('-b --bm-file argument required when processing MetaMap.')
            sys.exit(1)
        format_metamap_output_and_generate_labels(args.input_dir, args.output_dir, args.text_dir, args.bm_file, args.metamap_add, print_every=args.print_every)

    else:
        print("'tool' must be one of 'clamp', 'ctakes', or 'metamap'.", file=sys.stderr)
        sys.exit(1)
