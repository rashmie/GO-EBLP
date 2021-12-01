# Gene-Ontology-auditing-evidence-based-lexical-patterns
An evidence-based lexical pattern approach for quality assurance of Gene Ontology relations

## About
 Python implementation of an approach to automatically audit relationships in the Gene Ontology (GO). The paper can be found at:

## Requirements
 Pandas, spaCy, and tqdm is required to run this code.

 ## Inputs
 Takes four inputs (examples are given in the "inputs" folder):
 
 (1) labels file: A text file with each line containing a GO id and a name delimitted by a tab.
 
 (2) relations file: A text file with each line containing a direct GO relation. The source and target concept IDs are delimitted by tab.

 (3) part-of-speech file: A csv file containing part-of-speech tags of each GO concept name. The format of the file is as follows.

 	Column 1: Sequence number
 	Column 2: GO concept ID
 	Column 3: GO concept label
 	Column 4: part-of-speech tags of the label. These are delimitted by '|'

 (4) output file: a csv file containing the potential inconsistencies identified. The format of the output file is as follows.
	Column 1: Descendant
	Column 2: Relation
	Column 3: Ancestor
	Column 4: Lexical Pattern
	Column 5: Number of existing relations with the lexical pattern
	Column 6: Example existing relation with the lexical pattern
	Column 7: Difference pattern
	Column 8: Number of relation-pairs exhibiting the difference pattern
	Column 9: Example relation 1 for difference pattern
	Column 10: Example relation 2 for difference pattern


## How to run
`python suggest_inconsistencies.py <labels file> <relations file> <part-of-speech file> <output file>`


## Part-of-speech-tags
 part-of-speech tags file can be obtained by the 'Part_of_speech_tagging.py' script. Run the following to obtain this file.

 `python Part_of_speech_tagging.py <labels file> <part-of-speech file>`