import argparse, os, sys
import pandas as pd
from datetime import datetime

# function for filtering predictions
def filter_pred(pred_df_temp, filter_out_file=None, filter_tuis=None, clamp_problem=False):
    
    pred_df_temp = pred_df_temp.dropna(subset=["CUI"]) # keep only terms with CUI
    pred_df_temp = pred_df_temp[(pred_df_temp["CUI"].str.len() == 8) & (pred_df_temp["CUI"].str[0] == 'C')] # valid CUI only
    pred_df_temp =  pred_df_temp[(pred_df_temp["TUI"].isin(filter_tuis)) | (pred_df_temp["CUI"]=='C0018817')] # C0018817 is atrial septal defect
    
    # remove non-ASD specific terms (i.e. commorbidities)
    autism_comorbid = set(pd.read_csv(filter_out_file)["CUI"])
    pred_df_temp = pred_df_temp[~(pred_df_temp["CUI"].isin(autism_comorbid))]

    # only keep CLAMP predictions with a Semantic of 'problem'
    if clamp_problem:
        pred_df_temp = pred_df_temp[pred_df_temp["Semantic"]=="problem"]
        
    pred_df = pred_df_temp
    return pred_df


def calculate_statistics(pred_df, true_df):
    # drop duplicate predictions on same entity span
    pred_df = pred_df.drop_duplicates(subset=["paper", "Start", "End"]).sort_values(by=["paper", "Start", "End"])
    true_df = true_df.drop_duplicates(subset=["paper", "Start", "End"]).sort_values(by=["paper", "Start", "End"])

    # get true positives from predictions
    match_idx = []
    idx_t = 0
    idx_p = 0
    while idx_t < len(true_df) and idx_p < len(pred_df):
        row_t = true_df.iloc[idx_t,:]
        s_t = row_t['Start']
        e_t = row_t['End']
        row_p = pred_df.iloc[idx_p,:]
        s_p = row_p['Start']
        e_p = row_p['End']
        if row_t['paper'] < row_p['paper']:
            idx_t += 1
            continue
        elif row_t['paper'] > row_p['paper']:
            idx_p += 1
            continue
        if e_p < s_t:
            idx_p += 1
        elif e_t < s_p:
            idx_t += 1
        else:
            match_idx.append(row_p.name)
            idx_p += 1

    match_grouped = pred_df[pred_df.index.isin(match_idx)].merge(true_df, on=["paper"], how="outer")
    match_grouped = match_grouped.rename(columns={"Start_x": "Start_pred", "End_x": "End_pred", "Start_y": "Start_label", "End_y": "End_label", "Entity_x": "Entity_pred", "Entity_y": "Entity_label"})
    match_grouped = match_grouped.fillna("NA")
    
    # count overlaps
    temp = match_grouped[(match_grouped["Start_pred"] != "NA") & (match_grouped["Start_label"] != "NA")]
    temp = temp[((temp["Start_pred"] >= temp["Start_label"]) & (temp["Start_pred"] <= temp["End_label"])) | ((temp["Start_label"] >= temp["Start_pred"]) & (temp["Start_label"] <= temp["End_pred"]))]   
    true_pos_df = temp
    num_true_pos = len(temp.drop_duplicates(["paper", "Start_label", "End_label"])) # only count max one pred per label
    num_label_pos = len(true_df)
    num_pred_pos = len(pred_df)

    print("Number of true positives =", num_true_pos)
    print("Number of positive labels =", num_label_pos)
    print("Number of positive predictions =", num_pred_pos)
    print()
    precision = num_true_pos/num_pred_pos
    recall = num_true_pos/num_label_pos
    print("Precision =", precision)
    print("Recall =", recall)
    print("F-Measure =", (2 * precision * recall) / (precision + recall))
    
    return true_pos_df, pred_df, true_df


# get true positives, false positives, and false negatives
def get_false_and_true_pos(true_pos_df, pred_df, true_df):
    
    pred_df = pred_df.drop_duplicates(subset=["paper", "Start", "End", "CUI"])
    true_df = true_df.drop_duplicates(subset=["paper", "Start", "End", "CUI"])
    
    # group overlapping entities in true pos df
    temp = pd.DataFrame(true_pos_df.groupby(by=["Entity_label", "Entity_pred"])["Start_pred"].count()).reset_index()
    grouped = pd.DataFrame(temp.groupby(by=["Entity_label"])["Start_pred"].sum()).sort_values(by="Start_pred", ascending=False)
    temp = temp.merge(grouped, on="Entity_label")
    temp.columns = ["Entity_label", "Entity_pred", "Entity_pred count", "Entity_label count"]
    temp = temp.sort_values(by=["Entity_label count", "Entity_pred count"], ascending=False)
    true_pos_grouped = temp    
    columns = ["Entity", "CUI", "TUI"]
    
    # false positives - count overlap as match
    temp = pred_df.merge(true_pos_df[["paper", "Start_pred", "End_pred"]], left_on=["paper", "Start", "End"], right_on=["paper", "Start_pred", "End_pred"], how="outer")
    
    false_pos = temp[temp["Start_pred"].isnull()].sort_values(by=["paper", "Entity"])
    false_pos_grouped = false_pos.groupby(by=columns)["Start"].count().reset_index().sort_values(by="Start", ascending=False).reset_index(drop=True)
    false_pos_grouped = false_pos_grouped.rename(columns={"Start":"count"})
    
    # false negative - count overlap as match
    temp = true_df.merge(true_pos_df[["paper", "Start_label", "End_label"]], left_on=["paper", "Start", "End"], right_on=["paper", "Start_label", "End_label"], how="outer").drop_duplicates(["paper", "Start", "End"])
    false_neg = temp[temp["Start_label"].isnull()].sort_values(by=["paper", "Entity"])
    false_neg_grouped = false_neg.groupby(by=columns)["Start"].count().reset_index().sort_values(by="Start", ascending=False).reset_index(drop=True)
    false_neg_grouped = false_neg_grouped.rename(columns={"Start":"count"})
    
    return true_pos_grouped, false_pos_grouped, false_neg_grouped, false_pos, false_neg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Get the NER results for CLAMP, cTAKES, or MetaMap.')
    parser.add_argument('tool', help='Either CLAMP, cTAKES, or MetaMap.')
    parser.add_argument('input', help='The path to the file containing the formatted CLAMP, cTAKES, or MetaMap output.')
    parser.add_argument('labels', help='The path to the file containing the benchmark labels.')
    parser.add_argument('output', help='The path to the (text) file where the NER results will be outputted.')
    parser.add_argument('output_dir', help='The path to the directory where the true positive, false positive, and false negative preidctions will be outputted.')
    parser.add_argument('-f', '--filter', action='store_true', help='Use -f --filter flag to turn on filtering of the predictions.')
    parser.add_argument('-r', '--remove', help='The path to the file containing CUI to filter out from the predictions when the -f --filter flag i used.')
    args = parser.parse_args()

    # for naming files
    if args.filter:
        if not args.remove:
            print('-r --remove argument required when using the -f --filter flag.')
            sys.exit(1)
        filtered = "filtered_"
    else:
        filtered = ""

    tool = args.tool.lower().strip()
    print(f"Calculating {tool} results...")
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("Start time =", current_time)
    labels_df = pd.read_csv(args.labels)
    pred_df = pd.read_csv(args.input)
    if args.filter:
        pred_df = filter_pred(pred_df, filter_out_file=args.remove, filter_tuis=['T033', 'T048'], clamp_problem=False)

    original_stdout = sys.stdout
    # calculate NER results and save to file
    with open(args.output, "w") as f:
        sys.stdout = f 
        print(f"{tool} results")
        true_pos_df, pred_df_temp, labels_df_temp = calculate_statistics(pred_df, labels_df)
        sys.stdout = original_stdout 
        
    with open(args.output, "r") as f:
        print(f.read())

    # get true positives, false positives, false negatives and export
    true_pos_grouped, false_pos_grouped, false_neg_grouped, false_pos, false_neg = get_false_and_true_pos(true_pos_df, pred_df, labels_df)
    true_pos_grouped.to_csv(os.path.join(args.output_dir, filtered + f"{tool}_true_positive.csv"), index=False)
    false_pos_grouped.to_csv(os.path.join(args.output_dir, filtered + f"{tool}_false_positive.csv"), index=False)
    false_neg_grouped.to_csv(os.path.join(args.output_dir, filtered + f"{tool}_false_negative.csv"), index=False)
    false_pos.to_csv(os.path.join(args.output_dir, filtered + f"{tool}_false_positive_all.csv"), index=False)
    true_pos_df.to_csv(os.path.join(args.output_dir, filtered + f"{tool}_true_positive_all.csv"), index=False)

    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("End time =", current_time)
    