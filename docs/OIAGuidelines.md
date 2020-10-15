
We suggest to annotate the OIA graph in three steps: 

1 identify all nodes;
2 link the nodes with proper edges;
3 reorganize the graph into DAG. 

### Nodes

#### Constant Nodes

#### Predicate Nodes


Eventive facts are facts about entities' actions or status, which is generally expressed by the \emph{subj}, \emph{obj} and \emph{*comp} dependencies. In OIA, the \emph{pred.arg.1} always points to the subject of the event, and \emph{pred.arg.2} to \emph{pred.arg.N} refer to the (multiple) objects. An simple example is illustrated by Figure~\ref{fig:basic_action}. Events themselves can be arguments of predicates as well, as illustrated by Figure~\ref{fig:fact_as_arg}.


#### Function Nodes 

### Edges

\textbf{Adjective/Adverbial Modification.}\ 
Simple modifiers for nouns, verbs, and prepositions are directly merged into the corresponding phrase. For those who are either complex or not adjacent to the headword,  we use the predicate ``Modification'' with two argument B and A (or an edge from B to A with label \emph{mod}) to express the relation of A modifies B. The ``today" in Figure~\ref{fig:basic_action} is an example.

\vspace{0.05in}

\noindent\textbf{Modification by Preposition.}\  For modifications with prepositions such as ``A in B" or ``A for B", we take the preposition as the predicate and A, B as the arguments. However, if A is an argument of another predicate, to preserve the single-root property, we reverse the edge from predicate to A and add a \emph{as:} prefix to the label, that is, a new edge from A to the predicate with the label \emph{as:pred.arg.1}. Figure~\ref{fig:complex_conj} is an example.

\vspace{0.05in}

\noindent\textbf{Modification by Relative clause.}\  When the relative clause B modifies an argument \emph{a} of some other predicate/function, that is,  B itself conveys a predicate/function with argument \emph{a}. We reverse the related edge in B and add the \emph{as:} prefix as we do for Modification by Preposition. Figure~\ref{fig:fact_as_modifier} illustrates this case. If B does not involve \emph{a} as argument but an argument \emph{b} referencing \emph{a}, like ``which'', ``who'', we do the same thing to \emph{b}, and add an edge from \emph{a} to \emph{b} with label \emph{ref}.

%In other cases, the fact A and B are connected through a wh-word such as ``when, where, which'', etc., we then take the connection word as the predicate and do the same  as in ``Modification~by~Preposition". 

\subsection{Cross-Fact Relations} 

\vspace{0.05in} 

\noindent\textbf{Cross-sentential Connectives.}\   Sentential connectives are ignored in many OIE systems, but they are the ``first class citizen'' in our scheme. Sentential connectives such as ``therefore'', ``so'', ``if'' and  ``because'' can represent logical and temporal relations between sentences. We treat them as predicates and facts/propositions as arguments.  An example is shown in Figure~\ref{fig:basic_logic}.

\vspace{0.05in}

\noindent\textbf{Conjunction/Disjunction.}\   The conjunction and disjunction are expressed by ``and'' and ``or'' among a list of parallel components. OIA annotation adds a connecting predicate node delegating the components such as ``and'' for two components and ``\{1\} and \{2\} or \{3\}'' for three components, and then link to the arguments with ``pred.arg.\#index''. This is illustrated by Figure~\ref{fig:basic_logic}. More complex situations like Figure~\ref{fig:complex_conj} will be detailed in the Appendix. 
%However, in a more complex situation when the different prepositions are involved in the parallel components, we process each component separately and independently, then connect these components to the conjunction node with an edge labeled ``as:pred.arg.\#index''. It is necessary due to the single-root requirement of OIA. Figure~\ref{fig:complex_conj} is an illustration.

\vspace{0.05in}

\noindent\textbf{Adverbial Clause.}\   We first build the OIA sub-graph for the adverbial clause, and then connect the modified predicate to root of the sub-graph with edge \emph{mod}.


\vspace{0.05in}

%\noindent\textbf{Other UD annotated Relations.}\ 
%There are several UD annotations that describe the relationship between two fact A and B, for example, \emph{appos}, \emph{vocative}, and \emph{parataxis}, etc. 
%For each such annotation, we add a predicate named with that annotation and takes A and B as arguments. 

\subsection{Questions and Wh-Clauses}

We treat question words and wh-words as functions \cite{groenendijk1984studies,hamblin1976questions, groenendijk2009inquisitive} and the root of the OIA graph/sub-graph for sentence/clauses. If the question words/wh-words are the argument of the head predicate of the sentence/clause (for ``what'', ``who''), the connecting edge is reversed and add \emph{as:} prefix to the label; otherwise (for ``when'', ``where''), we connect the function to the head predicate of the sentence/clause with the label \emph{func.arg.1}. For polarity questions such as ``Do you know Bob?'', to avoid confusing the usage of question words and the verb-predicate ``do'', we introduce a predefined function ``Whether" as stated in Table \ref{tab:predefined_func_pred}. See Figure~\ref{fig:showcase2} and Figure~\ref{fig:basic_question}.

\subsection{Reference} 

In natural language sentences, words like ``it, that, which'' are used to refer an entity already mentioned in text. We express this knowledge by adding an edge \emph{ref} from the entity to the reference word. Again, if this edge violates the requirement of single-root DAG, the edge will be reversed as \emph{as:ref}.  Figure~\ref{fig:basic_logic} shows the annotation for reference. 
