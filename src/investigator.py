"""Crawler for ACL Anthology."""
import json
import os
import requests
import sys

from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO


URL_FORMAT = "http://aclweb.org/anthology/P{year}-{ptype}{pid:03d}"


class Investigator(object):

    def __init__(self, years, targets):
        """

        :param year: a list of strings which indicate years to gather.
        :param targets: "l" (long), "s" (short), or "lt".

        """
        self.years = years.split(",")
        self.targets = targets

    def search(self, words, out, tmp_dir="tmp"):
        os.makedirs(tmp_dir, exist_ok=True)

        exists = {}
        for year in self.years:
            exists[year] = {}
            for target, ptype in zip(self.targets, self._convert_targets_to_ptype(self.targets)):
                exists[year][target] = {}
                for pid in range(1, 999):
                    url = URL_FORMAT.format(year=year, ptype=ptype, pid=pid)
                    basename = os.path.basename(url)
                    path_paper = os.path.join(tmp_dir, basename)
                    ok = self._save_paper(url, path_paper)
                    if ok > 0:
                        break
                    else:
                        exists[year][target][pid] = self._exist(words, path_paper)
                        self._delete_paper(path_paper)

        with open(out, "wt") as f:
            json.dump(exists, f)

    def _exist(self, words, path):

        def convert_to_text():
            with open(path, "rb") as f:
                resource_manager = PDFResourceManager()
                outfp = StringIO()
                codec = "utf-8"
                laparams = LAParams()
                laparams.all_texts = True
                device = TextConverter(resource_manager, outfp, codec=codec, laparams=laparams)
                interpreter = PDFPageInterpreter(resource_manager, device)
                for page in PDFPage.get_pages(f):
                    interpreter.process_page(page)
                return self._clean_text(outfp.getvalue())

        text = convert_to_text()
        word_list = set(text.split())
        return [word for word in words if word in word_list]

    @staticmethod
    def _clean_text(text):
        return text.replace("-\n", "").replace("\n", "").lower()

    @staticmethod
    def _save_paper(url, path):
        print("Downloading", url)
        try:
            r = requests.get(url)
        except requests.RequestException as e:
            print(e)
            return 1

        if r.url == 'https://www.aclweb.org/404.shtml':
            print("Status Code: 404")
            return 1
        elif r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            return 0
        else:
            print("Status Code:", r.status_code)
            return 1

    @staticmethod
    def _delete_paper(path):
        if os.path.exists(path) is True:
            os.remove(path)

    @staticmethod
    def _convert_targets_to_ptype(targets):
        if targets == "l":
            return "1"
        elif targets == "t":
            return "2"
        elif targets == "ls":
            return "12"
        elif targets == "sl":
            return "21"
        else:
            print("Invalid paper types were specified.")
            sys.exit(1)
