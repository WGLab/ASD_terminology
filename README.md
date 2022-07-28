# ASD_terminology

The following pipeline was used for the NER analysis. The files are provided so you can reproduce the results by downloading the [CLAMP, cTAKES, and MetaMap formatted prediction data here](https://drive.google.com/file/d/1eCLLxvbCbwZ0ewGfNITa_GyZkNf8-f_9/view?usp=sharing) and jumping to step 3) or 4). Use `python3 format.py --help` and `python3 results.py --help` to get more information.

### 1) Label benchmark (BM) terms 
------

**Label full-texts**  
`python3 processing/label_bm.py 'pubmed_fulltexts_544' 'BM_labelled/full_text_labels_formatted.csv' 'BM_terms.csv' -p 10`

**Label abstracts**  
`python3 processing/label_bm.py 'pubmed_abstracts_20408' 'BM_labelled/abstract_labels_formatted.csv' 'BM_terms.csv' -p 500`


### 2) Format raw CLAMP, cTAKES, and MetaMap output  
------

**Format CLAMP**  
`python3 format.py clamp 'clamp/clamp_output_full_text' 'clamp/clamp_results_full_text' pubmed_fulltexts_544 -p 10 -c clamp_cui_to_tui_map.txt`
`python3 format.py clamp 'clamp/clamp_output_abstract' 'clamp/clamp_results_abstract' pubmed_abstracts_20408 -p 500 -c clamp_cui_to_tui_map.txt`

**Format cTAKES**   
`python3 format.py ctakes 'ctakes/ctakes_output_full_text' 'ctakes/ctakes_results_full_text' pubmed_fulltexts_544 -p 10`
`python3 format.py ctakes 'ctakes/ctakes_output_abstract' 'ctakes/ctakes_results_abstract' pubmed_abstracts_20408 -p 500`

**Format MetaMap**  
`python3 format.py metamap 'metamap/metamap_output_full_text' 'metamap/metamap_results_full_text' 'metamap/metamap_full_text' -b 'BM_terms_formatted.csv' -m 'metamap/metamap_tables' -p 10`
`python3 format.py metamap 'metamap/metamap_output_abstract' 'metamap/metamap_results_abstract' 'metamap/metamap_abstract' -b 'BM_terms_formatted.csv' -p 500`


### 3) Compute results and generate true positive, false positive, and false negative lists  
------

### CLAMP results  

**Full-text without filter**  
`python3 results.py clamp 'clamp/clamp_results_full_text/clamp_preds.csv' 'BM_labelled/full_text_labels_formatted.csv' 'statistics/clamp_statistics_fulltext.txt' 'clamp/clamp_results_full_text'`

**Full-text filtered**  
`python3 results.py clamp 'clamp/clamp_results_full_text/clamp_preds.csv' 'BM_labelled/full_text_labels_formatted.csv' 'statistics/filtered_clamp_statistics_fulltext.txt' 'clamp/clamp_results_full_text' -f -r 'asd_psychiatric_commorbidities.csv'`

**Abstract without filter**  
`python3 results.py clamp 'clamp/clamp_results_abstract/clamp_preds.csv' 'BM_labelled/abstract_labels_formatted.csv' 'statistics/clamp_statistics_abstract.txt' 'clamp/clamp_results_abstract'`

**Abstract filtered**  
`python3 results.py clamp 'clamp/clamp_results_abstract/clamp_preds.csv' 'BM_labelled/abstract_labels_formatted.csv' 'statistics/filtered_clamp_statistics_abstract.txt' 'clamp/clamp_results_abstract' -f -r 'asd_psychiatric_commorbidities.csv'`


### cTAKES results

**Full-text without filter**  
`python3 results.py ctakes 'ctakes/ctakes_results_full_text/ctakes_preds.csv' 'BM_labelled/full_text_labels_formatted.csv' 'statistics/ctakes_statistics_fulltext.txt' 'ctakes/ctakes_results_full_text'`

**Full-text filtered**  
`python3 results.py ctakes 'ctakes/ctakes_results_full_text/ctakes_preds.csv' 'BM_labelled/full_text_labels_formatted.csv' 'statistics/filtered_ctakes_statistics_fulltext.txt' 'ctakes/ctakes_results_full_text' -f -r 'asd_psychiatric_commorbidities.csv'`

**Abstract without filter**  
`python3 results.py ctakes 'ctakes/ctakes_results_abstract/ctakes_preds.csv' 'BM_labelled/abstract_labels_formatted.csv' 'statistics/ctakes_statistics_abstract.txt' 'ctakes/ctakes_results_abstract'`

**Abstract filtered**   
`python3 results.py ctakes 'ctakes/ctakes_results_abstract/ctakes_preds.csv' 'BM_labelled/abstract_labels_formatted.csv' 'statistics/filtered_ctakes_statistics_abstract.txt' 'ctakes/ctakes_results_abstract' -f -r 'asd_psychiatric_commorbidities.csv'`


### MetaMap results

**Full-text without filter**  
`python3 results.py metamap 'metamap/metamap_results_full_text/metamap_preds.csv' 'metamap/metamap_results_full_text/metamap_labels.csv' 'statistics/metamap_statistics_fulltext.txt' 'metamap/metamap_results_full_text'`

**Full-text filtered**  
`python3 results.py metamap 'metamap/metamap_results_full_text/metamap_preds.csv' 'metamap/metamap_results_full_text/metamap_labels.csv' 'statistics/filtered_metamap_statistics_fulltext.txt' 'metamap/metamap_results_full_text' -f -r 'asd_psychiatric_commorbidities.csv'`

**Abstract without filter**  
`python3 results.py metamap 'metamap/metamap_results_abstract/metamap_preds.csv' 'metamap/metamap_results_abstract/metamap_labels.csv' 'statistics/metamap_statistics_abstract.txt' 'metamap/metamap_results_abstract'`

**Abstract filtered**  
`python3 results.py metamap 'metamap/metamap_results_abstract/metamap_preds.csv' 'metamap/metamap_results_abstract/metamap_labels.csv' 'statistics/filtered_metamap_statistics_abstract.txt' 'metamap/metamap_results_abstract' -f -r 'asd_psychiatric_commorbidities.csv'`


### 4) Plot figures and generate tables 
------

**Figure 1**  
`generate_figures_NER_comparison.ipynb`

**Supplemental Figure 1**  
`analyze_BM_terms_in_texts.ipynb`

**Supplemental Figure 2 and Supplemental Table 3**  
`false_positive_analysis.ipynb`

**Supplemental Tables 4 and 5**  
`true_positive_analysis.ipynb`

### REFERENCE
Please cite the following paper:

Peng, J., Zhao, M., Havrilla, J. et al. Natural language processing (NLP) tools in extracting biomedical concepts from research articles: a case study on autism spectrum disorder. **BMC Med Inform Decis Mak** 20, 322 (2020). https://doi.org/10.1186/s12911-020-01352-2
