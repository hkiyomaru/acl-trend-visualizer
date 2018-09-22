"""Crawler for ACL Anthology."""
import multiprocessing
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


class Crawler(object):

    def __init__(self, years, ptypes, max_pid=300):
        """

        :param years: a list of strings which indicate years to gather.
        :param ptypes: a string which indicates submission type ("l" (long), "s" (short), or "lt").
        :param max_pid: maximum number of accepted papers for a conference.

        """
        assert len(set(ptypes) - set("sl")) == 0, "Invalid ptypes were specified: %s" % ptypes
        self.params = [{"year": year, "ptype": ptype, "pid": pid}
                       for year in years.split(",") for ptype in ptypes for pid in range(1, max_pid)]

    def search(self, words, tmp_dir="tmp", jobs=1):
        os.makedirs(tmp_dir, exist_ok=True)

        params = self._make_chunks(self.params, words, tmp_dir, jobs)
        with multiprocessing.Pool(processes=jobs) as pool:
            results = pool.starmap(self._search, params)

        return [item for subresults in results for item in subresults]

    def _search(self, params, words, tmp_dir):
        _results = []
        for param in params:
            url = URL_FORMAT.format(
                year=param["year"],
                ptype=self._make_ptype(param["ptype"]),  # "l" -> 1, "s" -> 2
                pid=param["pid"])
            basename = os.path.basename(url)
            path_paper = os.path.join(tmp_dir, basename)
            ok = self._save_paper(url, path_paper)
            if ok > 0:
                continue
            else:
                _results.append({
                    "url": url,
                    "year": param["year"],
                    "ptype": param["ptype"],
                    "pid": param["pid"],
                    "words": self._check_words(words, path_paper)})
                self._delete_paper(path_paper)
        return _results

    def _check_words(self, words, path):

        def convert_pdf_to_text(_path):
            with open(_path, "rb") as f:
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

        try:
            text = convert_pdf_to_text(path)
        except Exception as e:
            print(e, file=sys.stderr)
            text = ""
        word_list = set(text.split())
        return [word for word in words if word in word_list]

    @staticmethod
    def _clean_text(text):
        return text.replace("-\n", "").replace("\n", "").lower()

    @staticmethod
    def _save_paper(url, path):
        print("Downloading", url, file=sys.stderr)
        try:
            r = requests.get(url)
        except requests.RequestException as e:
            print(e, file=sys.stderr)
            return 1

        if r.url == "https://www.aclweb.org/404.shtml":
            print("Status Code: 404", file=sys.stderr)
            return 1
        elif r.status_code == 200:
            with open(path, "wb") as f:
                f.write(r.content)
            return 0
        else:
            print("Status Code:", r.status_code, file=sys.stderr)
            return 1

    @staticmethod
    def _delete_paper(path):
        if os.path.exists(path) is True:
            os.remove(path)

    @staticmethod
    def _make_ptype(ptype):
        if ptype == "l":
            return "1"
        elif ptype == "s":
            return "2"

    @staticmethod
    def _make_chunks(params, words, tmp_dir, n):
        if n < 1:
            print("Invalid parallelism.")
            sys.exit(1)
        return [(params[i::n], words, tmp_dir) for i in range(n)]
