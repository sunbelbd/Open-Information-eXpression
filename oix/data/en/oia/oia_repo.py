"""
oia repo
"""
import os

from tinydb import TinyDB, Query

from oix.oia.graphs.utils import CompactJSONEncoder

script_directory = os.path.dirname(os.path.realpath(__file__))
standardized_oia_path = os.path.join(script_directory, "oia_standard.json")

class OIARepo(object):
    """
    OIARepo
    """

    def __init__(self, db_file_path=None):

        if db_file_path is None:
            db_file_path = standardized_oia_path

        self.db = TinyDB(db_file_path, ensure_ascii=False, encoding="UTF8", cls=CompactJSONEncoder)

        self.indexes = dict()

        for table in {'train', 'dev', 'test'}:
            index = dict()
            for doc in self.db.table(table):
                index[doc['meta']['uri']] = doc.doc_id
            self.indexes[table] = index

    def get(self, source, uri):
        """
        TODO: add doc string
        """

        uri = str(uri)
        try:
            doc_id = self.indexes[source][uri]
        except Exception as e:

            raise Exception("sample with uri={0} not exist".format(uri))

        return self.db.table(source).get(doc_id=doc_id)

    def insert(self, source, oia_graphs):
        """

        @param source:
        @type source:
        @param uri:
        @type uri:
        @param oia_graph:
        @type oia_graph:
        @return:
        @rtype:
        """

        if isinstance(oia_graphs, (tuple, list)):
            data = [x.data() for x in oia_graphs]
            self.db.table(source).insert_multiple(data)
        else:
            data = oia_graphs.data()
            self.db.table(source).insert(data)

    def put(self, source, uri, oia_graph):
        """
        TODO: add doc string
        """

        new_sample = oia_graph.data()
        Sample = Query()

        self.db.table(source).update(new_sample, Sample.meta.uri == uri)

    def all(self, source):
        """

        @param source:
        @type source:
        @return:
        @rtype:
        """

        return self.db.table(source).all()

