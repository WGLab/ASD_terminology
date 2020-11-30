import csv, os
import pandas as pd
import spacy

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


def format_ctakes_output(input_dir, output_dir, text_dir, print_every=None):
    nlp = spacy.load("en_core_web_sm")

    # format cTAKES output/predictions in csv format where one row is one NER prediction
    empty_input_files = []
    empty_text_files = []
    with open(os.path.join(output_dir, "ctakes_preds.csv"), "w") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
        header = ['Start', 'End', 'CUI', 'Entity', 'paper', 'Entity_lower', 'Sentence_pred', 'TUI']
        csv_writer.writerow(header)
        
        ctakes_files = [filename for filename in os.listdir(input_dir) if filename.endswith(".csv")]
        for idx, filename in enumerate(ctakes_files):

            if print_every != None and idx % print_every == 0:
                print(idx, filename)

            input_filename = filename.replace(".csv", ".txt")
                
            # ignore empty files
            if is_file_empty(text_dir, input_filename):
                empty_text_files.append(input_filename)
                continue
            
            if is_file_empty(input_dir, filename):
                empty_input_files.append(filename)
                continue

            with open(os.path.join(text_dir, input_filename)) as f:
                plain_text = f.read()     
                doc = nlp(plain_text)
                
            df = pd.read_csv(os.path.join(input_dir, filename))
            df["paper"] = filename.replace(".csv", ".txt")
            df = df.rename(columns={"cui":"CUI", "tui":"TUI", "pos_start":"Start", "pos_end":"End"})
            df["Entity"] = df.apply(lambda row: plain_text[row['Start']:row['End']].strip(), axis=1)
            df["Entity_lower"] = df["Entity"].str.lower()
            df["Sentence_pred"] = df.apply(lambda row: extract_sentence(doc.sents, row), axis=1)
            df = df[['Start', 'End', 'CUI', 'Entity', 'paper', 'Entity_lower', 'Sentence_pred', 'TUI']] # these are the only columns needed
            df = df[~(df["paper"].isnull())]
            df = df.drop_duplicates(["Start", "End", "paper", "CUI"])

            for _, row in df.iterrows():
                csv_writer.writerow(list(row))

    print('Done processing cTAKES output.')
    print('Empty text files:')
    print(empty_text_files)
    print('Empty cTAKES output files:')
    print(empty_input_files)