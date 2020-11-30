import csv, os
from io import StringIO
import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
from unidecode import unidecode

def extract_sentence(sentences, row):
    ent_start = row['Start']
    for s in sentences:
        if s.start_char <= ent_start and ent_start < s.end_char:
            return s.text
    return ""


def is_file_empty(directory, filename):
    with open(os.path.join(directory, filename)) as f:
        data = f.read()        
    return data.isspace() or data == ""


def format_metamap_output_and_generate_labels(input_dir, output_dir, text_dir, bm_file, metamap_add=None, print_every=None):
    nlp = spacy.load("en_core_web_sm")
    # read in BM ASD terms and create BM set (all lowercase)
    BM_df = pd.read_csv(bm_file)
    BM_df["TEXT"] = BM_df["TEXT"].str.strip().str.lower()
    autism_terms = set(BM_df["TEXT"])
    
    # create spaCy Phrase Matcher (used for labelling BM terms)
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(text) for text in autism_terms]
    matcher.add("AutismTerms", None, *patterns)

    # arrange files so they are processed in order (MetaMap splits up text if too long)
    metamap_files = os.listdir(input_dir)
    metamap_files = [f for f in metamap_files if ".txt" in f]
    if metamap_files[0].count("_") == 1:
        metamap_files = sorted(metamap_files, key = lambda x: (x.split("_")[0], int(x.split("_")[1])))
    else:
        metamap_files = sorted(metamap_files, key = lambda x: (x.split("_")[0], int(x.split("_")[1]), int(x.split("_")[2])))

    # format cTAKES output/predictions in csv format where one row is one NER prediction

    # output files
    labels_file = open(os.path.join(output_dir, "metamap_labels.csv"), "w")
    preds_file = open(os.path.join(output_dir, "metamap_preds.csv"), "w")

    labels_csv_writer = csv.writer(labels_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    labels_csv_writer.writerow(["Entity", "Entity_lower", "paper", "Start", "End", "Sentence"])

    preds_csv_writer = csv.writer(preds_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    metamap_columns = ["id", "MappingScore", "CandidateCUI", "CandidateMatched", "SemType", "StartPos", "Length", "Negated", "CandidateScore", "MatchedWords"]
    metamap_columns_formatted = ['Start', 'End', 'CUI', 'Entity', 'paper', 'Sentence_pred', 'SemType']
    preds_csv_writer.writerow(metamap_columns_formatted)

    # metamap formatting
    header = "id	MappingScore	CandidateCUI	CandidateMatched	SemType	StartPos	Length	Negated	CandidateScore	MatchedWords\n"
    papers_analyzed = []
    full_text = ""
    empty_metamap_output = []
    for filename in metamap_files:
        paper = filename.split("_")[0]

        # new paper
        if paper not in papers_analyzed:

            # label last paper for BM terms
            if len(papers_analyzed) > 0:

                full_text = unidecode(full_text)

                with open(os.path.join(text_dir, papers_analyzed[-1]), "w") as f:
                    f.write(full_text)

                # analyze previous paper and label BM terms with spaCy
                doc = nlp(full_text)
                matches = matcher(doc)
                spans = []

                for match_id, start, end in matches:
                    span = doc[start:end]
                    spans.append(span)

                filtered = spacy.util.filter_spans(spans) # use longest match

                for span in filtered:
                    row = [span.text, span.text.lower().strip(), papers_analyzed[-1], span.start_char, span.end_char, span.sent.text]
                    labels_csv_writer.writerow(row)

            idx = len(papers_analyzed)
            if print_every != None and idx % print_every == 0:
                print(idx, filename)

            full_text = ""
            papers_analyzed.append(paper)


        if is_file_empty(input_dir, filename): # ignore empty file
            empty_metamap_output.append(filename)
            continue

        with open(os.path.join(input_dir, filename), "r") as f:
            data = f.read()

        if header not in data:
            print(filename, "has no header")

        splits = data.split(header)

        # this part contains the pmid and utterances
        info = splits[0].split("\n")
        pmid = ""
        utterance = False
        start_idx = len(full_text)

        for line in info:
            if "PMID: " in line:
                pmid_found = line.replace("PMID: ", "")
                pmid_found = pmid_found.split("_")[0]

                # check if pmid matches paper
                if pmid_found != paper:
                    raise Exception("PMID doesn't match paper:", line)
                else:
                    pmid = pmid_found

            if utterance:
                full_text = full_text + line

            if "UttText:" in line:
                utterance = True
            else:
                utterance = False

        full_text = full_text + " "

        # no terms detected
        if len(splits) < 2:
            continue

        doc = nlp(full_text)

        temp = pd.read_csv(StringIO(splits[1]), sep="\t", header=None) 
        temp.columns = metamap_columns
        temp["paper"] = paper
        temp = temp.rename(columns={"StartPos": "Start", "CandidateCUI":"CUI"})
        temp["Start"] = temp["Start"] + start_idx
        temp["End"] = temp["Start"] + temp["Length"]
        temp["Entity"] = temp.apply(lambda row: full_text[row['Start']:row['End']].strip(), axis=1)
        temp["Sentence_pred"] = temp.apply(lambda row: extract_sentence(doc.sents, row), axis=1)
        temp = temp[['Start', 'End', 'CUI', 'Entity', 'paper', 'Sentence_pred', 'SemType']] # these are the only columns needed

        for _, row in temp.iterrows():
            preds_csv_writer.writerow(list(row))


        # analyze previous paper
        full_text = unidecode(full_text)

        with open(os.path.join(text_dir, papers_analyzed[-1]), "w") as f:
            f.write(full_text)

        doc = nlp(full_text)
        matches = matcher(doc)
        spans = []

        for match_id, start, end in matches:
            span = doc[start:end]
            spans.append(span)

        filtered = spacy.util.filter_spans(spans) # use longest match

        for span in filtered:
            row = [span.text, span.text.lower().strip(), papers_analyzed[-1], span.start_char, span.end_char, span.sent.text]
            labels_csv_writer.writerow(row)

    
    # tables need to be analyzed separately because MetaMap had problems processing them
    if metamap_add:
        metamap_tables = os.listdir(metamap_add)
        metamap_tables = [f for f in metamap_tables if ".txt" in f]
        metamap_tables = sorted(metamap_tables, key = lambda x: (x.split("_")[0], int(x.split("_")[1]),))
        for filename in metamap_tables:
            paper = filename.split("_")[0]
            with open(os.path.join(metamap_add, filename)) as f:
                full_text = f.read()
            full_text = unidecode(full_text)

            doc = nlp(full_text)
            matches = matcher(doc)
            spans = []

            for match_id, start, end in matches:
                span = doc[start:end]
                spans.append(span)

            filtered = spacy.util.filter_spans(spans) # use longest match

            for span in filtered:
                row = [span.text, span.text.lower().strip(), paper, span.start_char, span.end_char, span.sent.text]
                labels_csv_writer.writerow(row)


    labels_file.close()
    preds_file.close()

    # additional formatting of labels
    labels_df_temp = pd.read_csv(os.path.join(output_dir, "metamap_labels.csv"))

    # read in BM ASD terms
    BM_df = pd.read_csv(bm_file)

    # merge labels with BM term information
    labels_df_temp = labels_df_temp.merge(BM_df, left_on="Entity_lower", right_on="TEXT", how="left")

    # clean-up
    labels_df_temp = labels_df_temp.replace({'Entity_lower': {"asperger 's": "asperger's"}})
    labels_df_temp = labels_df_temp.replace({'Entity': {"asperger 's": "asperger's"}})
    labels_df_temp = labels_df_temp.replace({'Entity': {"Asperger 's": "Asperger's"}})

    # case-sensitive for ASD and ASDs
    labels_df_temp = labels_df_temp[~((labels_df_temp["Entity_lower"]=="asds")&(labels_df_temp["Entity"]!="ASDs"))]
    labels_df_temp = labels_df_temp[~((labels_df_temp["Entity_lower"]=="asd")&(labels_df_temp["Entity"]!="ASD"))]
    labels_df_temp.to_csv(os.path.join(output_dir, "metamap_labels.csv"), index=False)

    # additional formatting of predictions
    pred_df_temp = pd.read_csv(os.path.join(output_dir, "metamap_preds.csv"))
    pred_df_temp = pred_df_temp[~((pred_df_temp["Entity"]=="Body")&(pred_df_temp["Start"]==5))] # filter out Body separator in text
    pred_df_temp = pred_df_temp[~(pred_df_temp["paper"].isnull())]
    pred_df_temp = pred_df_temp.drop_duplicates(["Start", "End", "paper", "CUI"])
    pred_df_temp["Entity_lower"] = pred_df_temp["Entity"].str.lower()

    # add TUI to predictions
    semantic_types_df = pd.read_csv("SemanticTypes_2018AB.txt", sep="|", header=None)
    semantic_types_df.columns = ["SemType", "TUI", "SemType_long"]
    pred_df_temp = pred_df_temp.merge(semantic_types_df, how="left", on="SemType")
    pred_df_temp = pred_df_temp[['Start', 'End', 'CUI', 'Entity', 'paper', 'Entity_lower', 'Sentence_pred', 'TUI']]
    pred_df_temp.to_csv(os.path.join(output_dir, "metamap_preds.csv"), index=False)

    print('Done processing MetaMap output.')
    print('Empty MetaMap output files:')
    print(empty_metamap_output)
