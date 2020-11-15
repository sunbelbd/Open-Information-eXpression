"""
vocabulary of oia graph
"""


EDGES = [
            "pred:arg:1",
            "pred:arg:2",
            "pred:arg:3",
            "pred:arg:4",
            "pred:arg:5",
            "pred:arg:6",
            "pred:arg:7",
            "pred:arg:8",
            "pred:arg:9",
            "pred:arg:10",
             "mod_by:pred:arg:1",
             "mod_by:pred:arg:2",
             "mod_by:pred:arg:3",
             "mod_by:pred:arg:4",

             'conj_by:pred:arg:1',
             'conj_by:pred:arg:2',
             'conj_by:pred:arg:3',
             'conj_by:pred:arg:4',

             'mod_by',
             'mod',
             'ref_by',
             'ref',
             'vocative',
             'func:arg',
             'appos',
              'mood',
              'numbered',
              'nonsense',
              'repeat',
              'topic',
              'vocative_by',
    'appos_by',
    'numbered_by']

NODES = ['{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}',
                'VOC', 'WHETHER', 'APPOS', 'AND', 'TIME_IN', 'MISSING',  'PARATAXIS',
                'TOPIC',  '(be)', 'LIST',  'DISCOURSE', 'REPARANDUM']

CONJUNCTION_WORDS = {"en": {"if", "else", "so", "while", "because",
                         "since", "when", "where", "how", "before", "after",
                         "although", "though", "whether", "however", "as", "ever since", "even after"},
                     "cn": {"如果", "所以", "然而", "因为",
                              "既然", "尽管", "因此", "但是", "然后", "之前", "此前", "此后", "之后"}
                     }

language = "en"



IMPORTANT_CONNECTION_WORDS = {"if", "else", "so", "while", "because",
                              "since", "when", "where", "what", "how", "before", "after",
                              "although", "though", "whether", "who", "whom", "whose", }

QUESTION_WORDS = {"en": {"when", "where", "what", "how", "whether", "who", "whom", "whose", },
                  "cn": {"什么", "何时", "何地", "如何", "是否", "谁"}
                  }

NOUN_UPOS = {"NOUN", "PROPN", "PRON", "X", "NUM", "SYM"}
