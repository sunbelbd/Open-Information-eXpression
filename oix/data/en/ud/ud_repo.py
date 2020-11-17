"""
UD repo
"""
import zipfile

import os

from tqdm import tqdm

scriptDirectory = os.path.dirname(os.path.realpath(__file__))


class UDRepo(object):
    """
    UDRepo
    """

    def __init__(self):
        self.train = []
        self.dev = []
        self.test = []

        # file_paths = [os.path.join(scriptDirectory, 'UD_English-EWT', "en_ewt-ud-{0}.conllu").format(x)
        #              for x in {"train", "dev", "test"}]
#        self.patches = set([x.strip() for x in open(os.path.join(scriptDirectory, "patch"), "r")
#                            if not x.startswith("#")])

        zip = zipfile.ZipFile(os.path.join(scriptDirectory, 'UD_English-EWT.zip'))

        # self.patches = set([x.strip() for x in open(os.path.join(scriptDirectory, "patch"), "r")
        #                    if not x.startswith("#")])

        index = 0

        # available files in the container
        for tag in ["train", "dev", "test"]:
            file_path = "UD_English-EWT/en_ewt-ud-{0}.conllu".format(tag)
            # extract a specific file from zip
            f = zip.open(file_path)
            content = f.read().decode("utf8")
            for index, sentence, ud in self.parse_ud_file(content, index):
                getattr(self, tag).append((index, sentence, ud))

            f.close()

    def parse_ud_file(self, file_content, base_index):
        """

        :param file_content:
        :return:
        """

        text = None
        ud = []
        index = base_index

        file_content = file_content

        for line in file_content.split("\n"):
            if line.startswith("# sent_id = "):
                continue
            if line.startswith("# newdoc id = "):
                continue
            if not line.strip():
                continue

            if line.startswith("# text = "):
                if text:
                    index += 1
                    # if text not in self.patches:

                    yield index, text, ud
                    text = None
                    ud = []

                text = line[9:]
                ud = []
            else:
                ud.append(line.split("\t"))

        if text:
            index += 1
            # if text not in self.patches:
            yield index, text, ud

    def search(self, query):
        """

        :param query:
        :return:
        """

        return [(index, text) for index, text, ud in self.train + self.dev + self.test if query in text]

    def get(self, x, source=None):
        """

        :param sentence:
        :return:
        """
        # if isinstance(x, int):
        #     return next((index, text, ud) for index, text, ud in self.train + self.dev + self.test if index == x)
        # else:
        #     return next((index, text, ud) for index, text, ud in self.train + self.dev + self.test if text.strip() == x.strip())

        if source is None or source == "all":
            source = self.train + self.dev + self.test
        else:
            source = getattr(self, source)

        if isinstance(x, int):
            return [(index, text, ud) for index, text, ud in source if index == x]
        else:
            return [(index, text, ud) for index, text, ud in source if text.strip() == x.strip()]

    def get_all(self, x, ud=None):
        """TODO: add doc string
    """
        source = self.train + self.dev + self.test
        return [(index, text, ud) for index, text, ud in source]

    def random(self):
        """

        :return:
        """
        import random
        return random.choice(self.train)

    def random_test(self):
        """

        :return:
        """
        import random
        return random.choice(self.test)

    def all(self):
        """

        :return:
        """

        return self.train + self.dev
