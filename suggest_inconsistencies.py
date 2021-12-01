from Transitive_closure import compute_closure
from collections import defaultdict
import csv
import copy
import time
import spacy
import sys

from tqdm import tqdm, trange

closure_concept_dict = {}  #key = con id, value = Concept instance (which includes ancestors)


# class to represent existing relations, non-relations or missing relations
class Relation:
    def __init__(self, rel_string, child, parent):
        self.rel_string = rel_string
        self.child = child  # a concept object
        self.parent = parent # a concept object
        #self.pattern = None # used to store pattern that was used to obtain missing relation

    def __hash__(self):
        return hash((self.rel_string, self.child.id, self.parent.id))

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Relation):
            return self.rel_string == other.rel_string and self.child == other.child and self.parent == other.parent
        return False

    def __str__(self):
        return self.child.id_label + ' ** ' + self.rel_string + ' ** ' + self.parent.id_label


# class to represent a lexical pattern
class Pattern:
    def __init__(self, pattern_string):
        self.pattern_string = pattern_string
        self.exhibiting_relations = {}  # key =rel_string, value = set of Relation objects

    def __hash__(self):
        return hash(self.pattern_string)

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Pattern):
            return self.pattern_string == other.pattern_string
        return False

    def add_exhibiting_relation(self, rel_string, child, parent): # child and parent should be Concept objects
        if rel_string not in self.exhibiting_relations:
            self.exhibiting_relations[rel_string] = set()
        self.exhibiting_relations[rel_string].add(Relation(rel_string, child, parent))


# class to represent a difference pattern
class DifferencePattern:
    def __init__(self, difference_pattern_string):
        self.difference_pattern_string = difference_pattern_string
        self.exhibiting_relation_pairs = {}  # key =rel_string, value = set of two-Relation tuples. The two relations are examples for the replacement

    def __hash__(self):
        return hash(self.difference_pattern_string)

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, DifferencePattern):
            return self.difference_pattern_string == other.difference_pattern_string
        return False

    def add_exhibiting_relation_pair(self, rel_string, child1, parent1, child2, parent2): # child1, parent1, child2, parent2 should be Concept objects
        if rel_string not in self.exhibiting_relation_pairs:
            self.exhibiting_relation_pairs[rel_string] = set()
        self.exhibiting_relation_pairs[rel_string].add((Relation(rel_string, child1, parent1), Relation(rel_string, child2, parent2)))


def tokenize_by_space(input_str):
    return input_str.strip().split(' ')


def replace_words_in_sequence_by_token(seq, word_set_to_replace, elem_repString_dict, token_prefix):
    seq_updated = []
    for i, word in enumerate(seq):
        if word in word_set_to_replace:
            if word not in elem_repString_dict:
                rep_string = token_prefix + str(i) + '##'
                elem_repString_dict[word] = rep_string
            else:
                rep_string = elem_repString_dict[word]
            seq_updated.append(rep_string)
        else:
            seq_updated.append(word)
    return seq_updated


# generate a lexical pattern from a given concept-pair
def get_pattern_from_concept_pair(con1, con2):
    con1_seq = con1.get_sequence_of_words()
    con2_seq = con2.get_sequence_of_words()
    common_words = con1.get_set_of_words().intersection(con2.get_set_of_words())

    if len(common_words)==0:
        return None

    elem_repString = {}

    con1_seq_updated = replace_words_in_sequence_by_token(con1_seq, common_words, elem_repString, '##E')
    con2_seq_updated = replace_words_in_sequence_by_token(con2_seq, common_words, elem_repString, '##E')

    #return ' '.join(con1_seq_updated) + ' ******** ' + ' '.join(con2_seq_updated) + ' $$$$$$$$ ' + ' '.join(con1.pos_tags) + ' ******** ' + ' '.join(con2.pos_tags)
    return ' '.join(con1_seq_updated) + ' <'+' '.join(con1.pos_tags)+'> ' + ' ******** ' + ' '.join(con2_seq_updated) + ' <'+' '.join(con2.pos_tags)+'> '


# generates lexical patterns from all concept pairs with existing relations
def generate_patterns_existing_rels():
    pattern_dict = {}  # key = pattern_string, value = Pattern object

    print('Generating lexical patterns from existing relations..')
    for con in closure_concept_dict.values():
        for rel, ancs in con.ancestors.items():
            for anc_id in ancs:
                anc = closure_concept_dict[anc_id]
                pattern_string = get_pattern_from_concept_pair(con, anc)
                if pattern_string is None:  # the concepts have no common words
                    continue
                if pattern_string not in pattern_dict:
                    pattern_dict[pattern_string] = Pattern(pattern_string)
                pattern_dict[pattern_string].add_exhibiting_relation(rel, con, anc)

    return pattern_dict


def difference_pattern(con1, con2):
    con1_seq = con1.get_sequence_of_words()
    con2_seq = con2.get_sequence_of_words()
    con1_con2_diff = con1.get_set_of_words().difference(con2.get_set_of_words())
    con2_con1_diff = con2.get_set_of_words().difference(con1.get_set_of_words())

    con1_elem_repString = {}
    con1_seq_updated = replace_words_in_sequence_by_token(con1_seq, con1_con2_diff, con1_elem_repString, '##L')
    con2_seq_updated = replace_words_in_sequence_by_token(con2_seq, con2_con1_diff, con1_elem_repString, '##R')

    return ' '.join(con1_seq_updated) + ' <' + ' '.join(con1.pos_tags) + '> ' + ' ******** ' + ' '.join(con2_seq_updated) + ' <' + ' '.join(con2.pos_tags) + '> '


def generate_difference_patterns(pattern_dict):
    if pattern_dict == None:
        pattern_dict = generate_patterns_existing_rels(None)

    difference_patterns = {}  # key = (string), value = ReplacementPattern object

    print('Generating difference patterns from existing relation pairs...')
    for pattern_string, pat_obj in pattern_dict.items():
        for rel_string, rel_obj_set in pat_obj.exhibiting_relations.items():
            for rel_obj_1 in rel_obj_set:
                difference_pat_1 = difference_pattern(rel_obj_1.child, rel_obj_1.parent)

                for rel_obj_2 in rel_obj_set:
                    if rel_obj_1 == rel_obj_2:
                        continue

                    difference_pat_2 = difference_pattern(rel_obj_2.child, rel_obj_2.parent)
                    difference_pat = difference_pat_1 + ' -------- ' + difference_pat_2

                    if difference_pat not in difference_patterns:
                        diff_pat_obj = DifferencePattern(difference_pat)
                        difference_patterns[difference_pat] = diff_pat_obj

                    diff_pat_obj = difference_patterns[difference_pat]
                    diff_pat_obj.add_exhibiting_relation_pair(rel_string, rel_obj_1.child, rel_obj_1.parent, rel_obj_2.child, rel_obj_2.parent)

        # print('Num replacement candidates: ', len(replacement_candidates))
        # if len(difference_patterns) > 1000000:
        #     break

    return difference_patterns


# suggestions are made considering all non-related concept-pairs
# to suggest a missing relation, concept-pair needs to generate a lexical pattern that was generated by a related concept-pair
# difference pattern between the suggestion and the leveraged existing relation should be same as the difference pattern obtained by a pair of existing relations.
def suggest_inconsistencies(output_file):
    pattern_dict = generate_patterns_existing_rels()
    replacement_candidate_dict = generate_difference_patterns(pattern_dict)
    inconsistencies = set()
    all_concepts = list(closure_concept_dict.values())

    print('Identifying inconsistencies...')
    for i in trange(len(all_concepts)):
        #print(i)
        con1 = all_concepts[i]

        for j in range(len(all_concepts)):
            con2 = all_concepts[j]
            if con1 == con2:
                continue

            if con2.id in con1.all_ancestors or con1.id in con2.all_ancestors:  # if there exists any relation between these concept, another relation isn't predicted.
                continue

            pattern_string = get_pattern_from_concept_pair(con1, con2)

            if pattern_string is None or pattern_string not in pattern_dict:  # the pattern is not found among existing relations
                continue

            pattern_obj = pattern_dict[pattern_string]  # this returns Pattern object

            if len(pattern_obj.exhibiting_relations) > 1:  # if the pattern is observed in multiple relations, don't use it to predict missing is-a
                continue

            diff_pat_1 = difference_pattern(con1, con2)

            for rel_string, rel_exhibiting_set in pattern_obj.exhibiting_relations.items():
                if rel_string == 'is_a' and con1.root != con2.root: # don't suggest is-a relations across different top-level subhierarchies
                    continue

                for rel_exhibit in rel_exhibiting_set:
                    diff_pat_2 = difference_pattern(rel_exhibit.child, rel_exhibit.parent)
                    diff_pat = diff_pat_1 + ' -------- ' + diff_pat_2

                    if diff_pat in replacement_candidate_dict:
                        repl_pat_obj = replacement_candidate_dict[diff_pat]
                        if rel_string in repl_pat_obj.exhibiting_relation_pairs:
                            exhibit_rel_pair_sample = next(iter(repl_pat_obj.exhibiting_relation_pairs[rel_string]))
                            inconsistencies.add((con1.id_label, rel_string, con2.id_label, pattern_string,
                                             len(rel_exhibiting_set), rel_exhibit, diff_pat, len(repl_pat_obj.exhibiting_relation_pairs[rel_string]),
                                             str(exhibit_rel_pair_sample[0]), str(exhibit_rel_pair_sample[1])))
                            break

        # if len(inconsistencies)>5:
        #     break
    with open(output_file, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(('Descendant', 'Relation', 'Ancestor', 'Pattern', 'num existing relations with pattern',
                            'Example existing relations with pattern', 'Replacement pattern',
                            'num examples for replacement', 'Replacement example 1', 'Replacement example 2'))
        csvwriter.writerows(inconsistencies)

    return inconsistencies


# redundant suggestions are removed here.
def remove_redundant_relations(predictions, output_file):
    redundant_predictions = set()
    closure_concept_dict_2 = copy.deepcopy(closure_concept_dict)
    for con in closure_concept_dict_2.values():
        con.ancestors = {}
        con.all_ancestors = set()

    print('Removing redundant relation suggestions..')
    for pred1 in tqdm(predictions):
        #print('Processing prediction: ', i)
        pred1_child = pred1[0].split(' ', 1)[0]
        pred1_rel = pred1[1]
        pred1_parent = pred1[2].split(' ', 1)[0]

        closure_concept_dict_copy = copy.deepcopy(closure_concept_dict_2)

        for pred2 in predictions:   # load parent as a direct parent of child
            if pred1 == pred2:
                continue

            pred2_child = pred2[0].split(' ', 1)[0]
            pred2_rel = pred2[1]
            pred2_parent = pred2[2].split(' ', 1)[0]

            if pred2_rel in closure_concept_dict_copy[pred2_child].parents:
                closure_concept_dict_copy[pred2_child].parents[pred2_rel].add(pred2_parent)
            else:
                ances = set()
                ances.add(pred2_parent)
                closure_concept_dict_copy[pred2_child].parents[pred2_rel] = ances

        closure_concept_dict_copy[pred1_child].find_all_ancs_closure()
        # if the predicted relation exists in the computed closure which is also based on other predicted relations, then it is a redundant relation
        if (pred1_rel in closure_concept_dict_copy[pred1_child].ancestors) and (pred1_parent in closure_concept_dict_copy[pred1_child].ancestors[pred1_rel]):
            redundant_predictions.add(pred1)

    print('All predictions: ', len(predictions))
    redundant_removed = predictions.difference(redundant_predictions)
    print('After removing redundant predictions: ', len(redundant_removed))

    if output_file != None:
        with open(output_file, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(('Descendant', 'Relation', 'Ancestor', 'Pattern', 'num existing relations with pattern',
                                'Example existing relations with pattern', 'Difference pattern',
                                'num examples for replacement', 'Replacement example 1', 'Replacement example 2'))
            csvwriter.writerows(redundant_removed)

    return redundant_removed


def main():
    start_time = time.time()

    labels_file = sys.argv[1]
    relations_file = sys.argv[2]
    pos_tag_file = sys.argv[3]
    output_inconsistency_file = sys.argv[4]
    output_inconsistency_file_reduced = sys.argv[5]

    global closure_concept_dict

    #closure_concept_dict = compute_closure('inputs/GO_labels_2020_11_18.txt', 'inputs/GO_all_relations_2020_11_18.txt', 'part_of_speech_tags/part_of_speech_tags_en_core_web_rtf.csv')
    closure_concept_dict = compute_closure(labels_file, relations_file, pos_tag_file)

    print('Closure computed!')

    #predictions = suggest_inconsistencies('predictions/all_predictions_all_pairs_noCrossHierarchyRels_validReplacements_new_OO_pos_tags_neg_pos_regulates_correct_test_2.csv')
    #predictions = load_predictions('predictions/all_predictions_all_pairs_noCrossHierarchyRels_validReplacements_new_OO_pos_tags_neg_pos_regulates_correct.csv')
    #remove_redundant_relations(predictions,'predictions/all_predictions_all_pairs_noCrossHierarchyRels_validReplacements_new_OO_pos_tags_neg_pos_regulates_correct_redundantRemoved.csv')

    predictions = suggest_inconsistencies(output_inconsistency_file)
    #remove_redundant_relations(predictions, output_inconsistency_file_reduced)
    #print('Redundant suggestions removed and inconsistencies written to file!')

    end_time = (time.time() - start_time) / 60
    print("Total time: {0:.2f} mins".format(end_time))


if __name__=='__main__':
    main()