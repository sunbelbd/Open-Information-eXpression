
# Annotation Guidelines for Open Information Annotation (1.0 Beta)

Please read the paper:

*  "A Predicate-Function-Argument Annotation of Natural Language for Open-Domain Information eXpression", Mingming Sun, et.al, EMNLP 2020

before read the detailed annotation guidelines. 

We suggest to annotate the OIA graph in three steps: 

1. Identify phrases;
2. Identify relationships between phrases;
3. Reorganize the graph into DAG. 

## Identify Phrases

The nodes in OIA are simple phrases, following the tradition of OIE. 
By simple phrase, we mean a fixed expression, or a phrase with a headword together with :

1. its auxiliary, determiner dependents; 
2. adjacent "ADJ/ADV" modifiers.

We use simple phrases as the basic element of OIA graph, because:
1. It greatly reduce the number of nodes in the graph (compared to the word-level graphs), and thus greatly decrease the overload of reading and annotation the OIA graph;
2. The knowledge inside simple phrases is simple and can be easily recovered by dependency parsing and some simple rules. 

### Simple Noun Phrases

Examples:

* Not only did Bush not know who **General Pervez Musharraf** was, he seems to have confused coup-making with "taking office," and moreover went on to suggest that **the overthrow of an elected prime minister** and the installation in power of the Pakistan military, then **the world's strongest supporter of the Taliban**, would bring "stability!"

Sepecial Cases:

1. Noun of Noun: For noun phrases connected by "of", we take the whole of-phrase as a simple noun phrase. 
The relationship expressed by the word "of" is so complicated that we leave it for future processing if necessary.


### Simple Verbal Phrases

Examples:

* Many people at Enron already have this type of chair, but we **rarely, if ever, have** a surplus because they **are so popular**.

Special Cases:

1. be + ADJ: we take the be + ADJ phrase (like the "are so popular" in above sentence) as one phrase, 
since it is much more informative than a single "be" phrase. 
That is, we apply the Informativeness Improvement operator in advance.  


### Simple Conjunction Phrases  

Examples:

* ... they don't want to work hard, **just because** you bruised your own ego.
* I've been fuming over this fact for a few weeks now, **ever since** some organizations and governments suggested we need to accept the fact that Hezbollah will get involved in running Lebanon.
* There are numerous other examples of such Orwellian nomenclature, used every day **not only** by terror chiefs **but also** by Western media.  (not only {1" but also {2")
* His military intelligence has captured major figures like Abu Zubayda **and** Khalid Shaykh Muhammad **, as well as** nearly 500 other al-Qaeda operatives, over 400 of whom the Pakistanis have turned over to the US.  ({1" and {2", as well as {3")

### Simple Question Phrases

Examples:
* We all know what happened, but even to this day, there are many different versions and opinions on how it happened and **what effect** Chernobyl will have on the health of people affected by the fallout.
* As a parent, I can well imagine how painful it must be for those families **whose children** are succumbing to radiation poisoning.

## Identify relationships between nodes

### Modifications
#### Adjective/Adverbial Modification
Simple modifiers for nouns, verbs, and prepositions are directly merged into the corresponding phrase. 
For those who are either complex or not adjacent to the headword,  
we use the predicate "Modification" with two argument B and A to express the relation of A modifies B.

Since the "Modification" is very common, we use an abbreviation -an edge from B to A with label "mod"
 - to express the same meaning. 

#### Modification by Preposition
  
For modifications with prepositions such as "A in B" or "A for B", we take the preposition as the predicate and A, B as the arguments. 
However, if A is an argument of another predicate, to preserve the single-root property, we reverse the edge from predicate to A and 
add a **as:** prefix to the label, that is, a new edge from A to the predicate with the label **as:pred.arg.1**. 


#### Modification by Relative clause
  
When the relative clause B modifies an argument "a" of some other predicate/function, 
that is,  B itself conveys a predicate/function with argument "a", we reverse 
the related edge in B and add the "as:" prefix as we do for Modification by Preposition. 
If B does not involve "a" as argument but an argument "b" referencing "a", 
like "which", "who", we do the same thing to "b", and add an edge from "a" to "b" with label "ref".

### Cross-Fact Relations

#### Cross-sentential Connectives
   
Sentential connectives are ignored in many OIE systems, but they are the **first class citizen**
 in our scheme. Sentential connectives such as "therefore", "so", "if" and  "because" can represent logical and 
 temporal relations between sentences. We treat them as predicates and facts/propositions as arguments.  

#### Conjunction/Disjunction
  
The conjunction and disjunction are expressed by "and" and "or" among a list of parallel components. 
OIA annotation adds a connecting predicate node delegating the components such as "and" for two components and "\{1\" and \{2\" or \{3\"" for three components, and then link to the arguments with "pred.arg.\#index".
However, in a more complex situation when the different prepositions are involved in the parallel components, 
we process each component separately and independently, then connect these components to the conjunction node with an edge labeled "as:pred.arg.\#index". 
It is necessary due to the single-root requirement of OIA.

#### Adverbial Clause
   
We first build the OIA sub-graph for the adverbial clause, and then connect the modified predicate to 
root of the sub-graph with edge "mod".


### Questions and Wh-Clauses

We treat question words and wh-words as functions and the root of the OIA graph/sub-graph for sentence/clauses. 
If the question words/wh-words are the argument of the head predicate of the sentence/clause (for "what", "who"), the connecting edge is reversed and add "as:" prefix to the label; 
otherwise (for "when", "where"), we connect the function to the head predicate of the sentence/clause with the label "func.arg.1". 
For polarity questions such as "Do you know Bob?", to avoid confusing the usage of question words and the verb-predicate "do", we introduce a predefined function "Whether" as the root of the sub-OIA graph.

### Reference

In natural language sentences, words like "it, that, which" are used to refer an entity already mentioned in text. 
We express this knowledge by adding an edge "ref" from the entity to the reference word. 
Again, if this edge violates the requirement of single-root DAG, the edge will be reversed as "as:ref".   




### Other UD annotated Relations
There are several UD annotations that describe the relationship between two fact A and B, 
for example, "appos", "vocative", and "parataxis", etc. 
For each such annotation, we add a predicate named with that annotation and takes A and B as arguments. 
