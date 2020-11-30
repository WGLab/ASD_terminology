import argparse, csv, os
import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Format the output of CLAMP, cTAKES, or MetaMap for subsequent NER analysis.')
    parser.add_argument('text_dir', help='The path to the directory where the original texts to be labelled are located.')
    parser.add_argument('output', help='The path to the file where the labels will be saved as a .csv file.')
    parser.add_argument('bm_file', help='File with benchmark terms used to generate labels.')
    parser.add_argument('-p', '--print-every', type=int, help='Interval reprsenting number of files after which to continuously print progress.')
    args = parser.parse_args()

    nlp = spacy.load("en_core_web_sm")
    # read in BM ASD terms and create BM set (all lowercase)
    BM_df = pd.read_csv(args.bm_file)
    BM_df["TEXT"] = BM_df["TEXT"].str.strip().str.lower()
    autism_terms = set(BM_df["TEXT"])
    print(f"There are {len(autism_terms)} autism terms")

    # create spaCy Phrase Matcher (used for labelling BM terms)
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(text) for text in autism_terms]
    matcher.add("AutismTerms", None, *patterns)

    # label BM terms and write the results to the csv file where one row is a label/match
    with open(args.output, "w") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(["Entity", "Entity_lower", "paper", "Start", "End", "Sentence"]) # header
        for idx, filename in enumerate(os.listdir(args.text_dir)):

            if filename.endswith(".txt"):
                path = os.path.join(args.text_dir, filename)

                if args.print_every != None and idx % args.print_every == 0:
                    print(idx, filename)

                # tag entities in abstract
                with open(path, "r") as f:
                    data = f.read()
                
                doc = nlp(data)
                matches = matcher(doc)
                spans = []

                for match_id, start, end in matches:
                    span = doc[start:end]
                    spans.append(span)

                # use longest BM term match
                filtered = spacy.util.filter_spans(spans)

                for span in filtered:
                    row = [span.text, span.text.lower().strip(), filename, span.start_char, span.end_char, span.sent.text]
                    csv_writer.writerow(row)

    # additional formatting
    labels_df = pd.read_csv(os.path.join(args.output))

    # read in BM ASD terms and add TUI
    BM_df = pd.read_csv(args.bm_file)
    BM_df.rename(columns={"CUI": "CUI_original"}, inplace=True)
    BM_df["NEGATED"] = BM_df["CUI_original"].apply(lambda x: str(x)[0] == "-")
    BM_df["CUI"] = BM_df["CUI_original"].apply(lambda x: str(x).replace("-", ""))
    BM_cui_to_tui_df = pd.read_csv("tui_list_BM.txt", sep="\t", index_col=0, header=None).reset_index()
    BM_cui_to_tui_df.columns = ["CUI", "TUI"]
    BM_df = BM_df.merge(BM_cui_to_tui_df, how="left")
    BM_df["TEXT"] = BM_df["TEXT"].str.strip().str.lower()
    BM_df = BM_df.drop_duplicates() 

    # merge labels with BM term information
    labels_df = labels_df.merge(BM_df, left_on="Entity_lower", right_on="TEXT", how="left")

    # clean-up
    labels_df = labels_df.replace({'Entity_lower': {"asperger 's": "asperger's"}})
    labels_df = labels_df.replace({'Entity': {"asperger 's": "asperger's"}})
    labels_df = labels_df.replace({'Entity': {"Asperger 's": "Asperger's"}})

    # case-sensitive for ASD and ASDs
    labels_df = labels_df[~((labels_df["Entity_lower"]=="asds")&(labels_df["Entity"]!="ASDs"))]
    labels_df = labels_df[~((labels_df["Entity_lower"]=="asd")&(labels_df["Entity"]!="ASD"))]
    labels_df = labels_df.drop_duplicates(["paper", "Start", "End", "CUI"])

    labels_df.to_csv(args.output, index=False)
