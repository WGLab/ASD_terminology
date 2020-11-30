import csv, os
import pandas as pd
import spacy

def get_CUI(x):
    # get and format CUI
    if pd.isna(x):
        return x
    else:
        return x.split()[0].strip()


def extract_entity(full_text, row):
    ent = full_text[row['Start']:row['End']].strip()
    return ent


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


def format_clamp_output(input_dir, output_dir, text_dir, cui2tui, print_every=None):
    nlp = spacy.load("en_core_web_sm")

    # format CLAMP output/predictions in csv format where one row is one NER prediction
    empty_text_files = []
    empty_input_files = []
    with open(os.path.join(output_dir, "clamp_preds.csv"), "w") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        header = ['Start', 'End', 'CUI', 'Entity', 'paper', 'Entity_lower', 'Sentence_pred']
        csv_writer.writerow(header)
        
        clamp_files = [filename for filename in os.listdir(input_dir) if filename.endswith(".txt")]
        for idx, filename in enumerate(clamp_files):

            if print_every != None and idx % print_every == 0:
                print(idx, filename)
                
            if is_file_empty(text_dir, filename):
                empty_text_files.append(filename)
                continue
                
            # ignore empty files
            if is_file_empty(input_dir, filename):
                empty_input_files.append(filename)
                continue

            with open(os.path.join(text_dir, filename)) as f:
                full_text = f.read()
                doc = nlp(full_text)

            df = pd.read_csv(os.path.join(input_dir, filename), sep="\t", quoting=3)
            df["paper"] = filename
            df["Entity"] = list(df.apply(lambda row: extract_entity(full_text, row), axis=1))
            df["Entity_lower"] = df["Entity"].str.lower()
            df["Sentence_pred"] = df.apply(lambda row: extract_sentence(doc.sents, row), axis=1)
            df = df[['Start', 'End', 'CUI', 'Entity', 'paper', 'Entity_lower', 'Sentence_pred']] # these are the only columns needed (+TUI)
            df = df[~(df["paper"].isnull())]
            df = df.drop_duplicates(["Start", "End", "paper", "CUI"])

            for _, row in df.iterrows():
                csv_writer.writerow(list(row))

    # additional formatting

    # format CUI
    pred_df_temp = pd.read_csv(os.path.join(output_dir, "clamp_preds.csv"))
    pred_df_temp["CUI"] = pred_df_temp["CUI"].apply(lambda x: get_CUI(x)) # get CUI

    # map CUI to TUI
    cui_to_tui_df = pd.read_csv(cui2tui, sep="\t", header = None)
    cui_to_tui_df.columns = ["CUI", "TUI"]
    pred_df_temp = pred_df_temp.merge(cui_to_tui_df, on="CUI", how="left")

    pred_df_temp.to_csv(os.path.join(output_dir, "clamp_preds.csv"), index=False)

    print('Done processing CLAMP output.')
    print('Empty text files:')
    print(empty_text_files)
    print('Empty CLAMP output files:')
    print(empty_input_files)
