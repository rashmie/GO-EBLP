## Transitive closure considering the combination of different types of relations in GO

import csv

concept_dict = None #key = con id, value = Concept instance

class Concept:
    def __init__(self, id, label):
        self.id = id
        self.label = label
        self.id_label = id+' '+label
        self.parents = {}   #dict: key=relation, value=parents
        self.ancestors = {} #dict: key=relation, value=ancestors
        self.all_ancestors = set()  # all ancestors connected by any relation
        self.root = None
        self.noun_chunks = None
        self.sequence_of_words = None
        self.set_of_words = None
        self.pos_tags = None # each element here corresponds to an element of sequence_of_words


    def __hash__(self):
        return hash(self.id)


    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, Concept):
            return self.id == other.id
        return False


    def get_sequence_of_words(self):
        if self.sequence_of_words is None:
            self.sequence_of_words = self.label.strip().split(' ')
        return self.sequence_of_words


    def get_set_of_words(self):
        if self.set_of_words is None:
            self.set_of_words = set(self.get_sequence_of_words())
        return self.set_of_words


    def is_a_ancestors(self):
        if 'is_a' in self.ancestors:
            return self.ancestors['is_a']

        isa_ancs = set()
        if 'is_a' in self.parents:
            isa_ancs.update(self.parents['is_a'])
            for isa_anc in self.parents['is_a']:
                isa_ancs.update(concept_dict[isa_anc].is_a_ancestors())

        self.ancestors['is_a'] = isa_ancs
        return self.ancestors['is_a']


    def part_of_ancestors(self):
        if 'part_of' in self.ancestors:   #if ancestors has been previously computed
            return self.ancestors['part_of']

        partof_ancs = set()

        if 'is_a' in self.parents:
            for isa_anc in self.parents['is_a']:
                partof_ancs.update(concept_dict[isa_anc].part_of_ancestors())   # part-of ancestors of is-a ancestors

        if 'part_of' in self.parents:
            partof_ancs.update(self.parents['part_of'])  # part of parents
            for partof_anc in self.parents['part_of']:
                partof_ancs.update(concept_dict[partof_anc].part_of_ancestors())   #partof ancestors of partof parents
                partof_ancs.update(concept_dict[partof_anc].is_a_ancestors())  # isa ancestors of partof parents

        self.ancestors['part_of'] = partof_ancs
        return partof_ancs


    def has_part_ancestors(self):
        if 'has_part' in self.ancestors:   #if ancestors has been previously computed
            return self.ancestors['has_part']

        haspart_ancs = set()

        if 'is_a' in self.parents:
            for isa_anc in self.parents['is_a']:
                haspart_ancs.update(concept_dict[isa_anc].has_part_ancestors())

        if 'has_part' in self.parents:
            haspart_ancs.update(self.parents['has_part'])  # haspart of parents
            for haspart_anc in self.parents['has_part']:
                haspart_ancs.update(concept_dict[haspart_anc].has_part_ancestors())   #haspart ancestors of haspart parents
                haspart_ancs.update(concept_dict[haspart_anc].is_a_ancestors())   #isa ancestors of haspart parents

        self.ancestors['has_part'] = haspart_ancs
        return haspart_ancs

    def regulates_ancestors(self):
        if 'regulates' in self.ancestors:   #if ancestors has been previously computed
            return self.ancestors['regulates']

        regulates_ancs = set()

        if 'is_a' in self.parents:
            for isa_anc in self.parents['is_a']:
                regulates_ancs.update(concept_dict[isa_anc].regulates_ancestors())

        if 'regulates' in self.parents:
            regulates_ancs.update(self.parents['regulates'])  # regulates of parents
            for regulates_anc in self.parents['regulates']:
                regulates_ancs.update(concept_dict[regulates_anc].is_a_ancestors())  # isa ancestors of regulates parents

        self.ancestors['regulates'] = regulates_ancs
        return regulates_ancs


    def negatively_regulates_ancestors(self):
        if 'negatively_regulates' in self.ancestors:   #if ancestors has been previously computed
            return self.ancestors['negatively_regulates']

        negatively_regulates_ancs = set()

        if 'is_a' in self.parents:
            for isa_anc in self.parents['is_a']:
                negatively_regulates_ancs.update(concept_dict[isa_anc].negatively_regulates_ancestors())        # negatively_regulates ancestors of is_a parents

        if 'negatively_regulates' in self.parents:
            negatively_regulates_ancs.update(self.parents['negatively_regulates'])  # direct relation
            for neg_regulates_anc in self.parents['negatively_regulates']:
                negatively_regulates_ancs.update(concept_dict[neg_regulates_anc].is_a_ancestors())  # isa ancestors of negatively_regulates parents

        self.ancestors['negatively_regulates'] = negatively_regulates_ancs
        return negatively_regulates_ancs


    def positively_regulates_ancestors(self):
        if 'positively_regulates' in self.ancestors:   #if ancestors has been previously computed
            return self.ancestors['positively_regulates']

        positively_regulates_ancs = set()

        if 'is_a' in self.parents:
            for isa_anc in self.parents['is_a']:
                positively_regulates_ancs.update(concept_dict[isa_anc].positively_regulates_ancestors())        # positively_regulates ancestors of is-a parents

        if 'positively_regulates' in self.parents:
            positively_regulates_ancs.update(self.parents['positively_regulates'])  # direct relation
            for pos_regulates_anc in self.parents['positively_regulates']:
                positively_regulates_ancs.update(concept_dict[pos_regulates_anc].positively_regulates_ancestors())  # positively_regulates ancestors of positively_regulates parents
                positively_regulates_ancs.update(concept_dict[pos_regulates_anc].is_a_ancestors())  # isa ancestors of positively_regulates parents

        neg_reg_ancs = self.negatively_regulates_ancestors()

        for neg_reg_anc in neg_reg_ancs:
            positively_regulates_ancs.update(concept_dict[neg_reg_anc].negatively_regulates_ancestors())    # negatively_regulates ancestors of negatively_regulates parents. Based on OWL file and relation ontology, this property chain holds

        self.ancestors['positively_regulates'] = positively_regulates_ancs

        return positively_regulates_ancs


    def find_all_ancs_closure(self):
        self.is_a_ancestors()
        self.part_of_ancestors()
        self.has_part_ancestors()
        self.regulates_ancestors()
        self.negatively_regulates_ancestors()
        self.positively_regulates_ancestors()

    def find_all_ancs(self):
        for rel, ancs in self.ancestors.items():
            self.all_ancestors.update(ancs)

    def find_root(self):
        if self.root is not None:
            return self.root
        elif len(self.is_a_ancestors()) != 0:   # this concept has ancestors: which means it is not the root
            anc = next(iter(self.ancestors['is_a']))
            self.root = concept_dict[anc].find_root()
            return self.root
        else:
            self.root = self.id
            return self.root


#load concepts as Concept class instances
def load_concepts(id_label_file):
    global concept_dict
    concept_dict = {}
    with open(id_label_file, 'r') as txtfile:
        lines = txtfile.readlines()
        for line in lines:
            line = line.rstrip("\n")
            tokens = line.split("\t")
            concept_dict[tokens[0]] = Concept(tokens[0], tokens[1])


# load direct parent by different relations into class instances created by load_concepts() method
def load_parents(all_relations_file):
    with open(all_relations_file, 'r') as txtfile:
        lines = txtfile.readlines()
        for line in lines:
            line = line.rstrip("\n")
            tokens = line.split("\t")
            if tokens[1] not in concept_dict[tokens[0]].parents:
                parents = set()
            else:
                parents = concept_dict[tokens[0]].parents[tokens[1]]
            parents.add(tokens[2])
            concept_dict[tokens[0]].parents[tokens[1]] = parents


# loading part of speech tags from a file
def load_POS_tags_of_concepts(post_tags_file):
    with open(post_tags_file, 'r') as csvfile:
        rows = csv.reader(csvfile)
        for i, row in enumerate(rows):
            if i==0:    # headers
                continue
            #print(row[1])
            tokens = row[3].split(' | ')
            concept_dict[row[1]].pos_tags = tokens


def compute_closure(labels_file, all_rels_file, pos_tags_file):
    load_concepts(labels_file)
    load_parents(all_rels_file)
    load_POS_tags_of_concepts(pos_tags_file)

    roots = set()
    for con in concept_dict.values():
        con.find_all_ancs_closure()
        con.find_all_ancs()
        rt = con.find_root()
        roots.add(rt)
    print(roots)

    return concept_dict