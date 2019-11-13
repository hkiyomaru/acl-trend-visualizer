"""Main script to run a crawler."""
import argparse
import multiprocessing
import tempfile
from io import StringIO
from logging import getLogger, StreamHandler, Formatter, DEBUG

import jsonlines
import requests
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfpage import PDFPage

parser = argparse.ArgumentParser()
parser.add_argument('WORDLIST', help='path to the word list')
parser.add_argument('-c', '--conference', default="acl,naacl,emnlp", help='conferences (default: acl,naacl,emnlp)')
parser.add_argument('-y', '--year', default="13,14,15,16,17,18,19", help='years (default: 13,14,15,16,17,18,19")')
parser.add_argument('-t', '--type', default="l,s", help='submission types (default: ls (long & short))')
parser.add_argument('-j', '--jobs', default=1, type=int, help='parallelism')
parser.add_argument('--output', default="result.jsonl", help='path to the output file')
args = parser.parse_args()

logger = getLogger(__name__)
handler = StreamHandler()
handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.propagate = False
logger.setLevel(DEBUG)

logger.debug(f'Loading a word list...')
with open(args.WORDLIST) as f:
    word_list = [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]
logger.debug(f'# words:       {len(word_list)}')

logger.debug(f'Loading an year list...')
year_list = args.year.split(',')

logger.debug(f'Loading a conference list...')
CONFERENCE_ID_MAP = {
    'naacl': 'N',
    'acl': 'P',
    'emnlp': 'D'
}
conference_list = args.conference.split(',')
conference_id_list = [CONFERENCE_ID_MAP[conference] for conference in conference_list]

logger.debug(f'Loading a submission type list...')
STYPE_ID_MAP = {
    'l': '1',
    's': '2'
}
stype_list = args.type.split(',')
stype_id_list = [STYPE_ID_MAP[stype] for stype in stype_list]

paper_id_list = [pid for pid in range(1, 1000)]

logger.debug(f'Constructing a parameter list...')
parameters = []
for year in year_list:
    for conference_id in conference_id_list:
        for stype_id in stype_id_list:
            for paper_id in paper_id_list:
                parameters.append({
                    'year': year,
                    'conference_id': conference_id,
                    'stype_id': stype_id,
                    'paper_id': paper_id
                })

logger.debug(f'Years: {len(year_list)} ({",".join(year_list)})')
logger.debug(f'Conferences: {len(conference_list)} ({",".join(conference_list)})')
logger.debug(f'Submission types: {len(stype_list)} ({",".join(stype_list)})')
logger.debug(f'Papers: {len(paper_id_list)} (from {paper_id_list[0]} to {paper_id_list[-1]})')
logger.debug(f'Total parameters: {len(parameters)}')

logger.debug(f'Splitting the parameters into {args.jobs} chunks...')
n_parameters = len(parameters)
n_parameters_in_chunk = (n_parameters // args.jobs) + 1
parameter_chunks = [parameters[i:i + n_parameters_in_chunk] for i in range(0, n_parameters, n_parameters_in_chunk)]
assert n_parameters == sum(len(parameter_chunk) for parameter_chunk in parameter_chunks)


def process(parameter_chunk):
    """Search words.

    :param parameter_chunk: A list of parameters to retrieve PDF files.
    :return: the result of search.
    """
    result = []

    last_parameter = parameter_chunk[0]
    last_status_code = 200
    for parameter in parameter_chunk:
        url = "http://aclweb.org/anthology/%(conference_id)s%(year)s-%(stype_id)s%(paper_id)03d.pdf" % parameter

        if last_status_code == 404:
            conditions = (
                last_parameter['year'] == parameter['year'],
                last_parameter['conference_id'] == parameter['conference_id'],
                last_parameter['stype_id'] == parameter['stype_id'],
                last_parameter['paper_id'] <= parameter['paper_id'],
            )
            if all(conditions):
                logger.debug(f'Skip downloading {url}')
                continue

        logger.debug(f'Downloading {url}')
        status_code, words = search(url)
        if status_code == 200:
            parameter['words'] = words
            result.append(parameter)
        elif status_code == 404:
            logger.debug(f'404: {url}')
        else:
            logger.debug(f'Status code: {status_code}')

        last_parameter = parameter
        last_status_code = status_code
    return result


def search(url):
    """Search words from a paper.

    :param url: A URL to a paper.
    :return: The status code and a list of included words.
    """
    result = []

    try:
        r = requests.get(url)
    except requests.RequestException as e:
        logger.debug(str(e))
        return -1, result

    if r.status_code == 200:
        # save the pdf
        pdf_fp = tempfile.TemporaryFile()
        pdf_fp.write(r.content)

        # extract the text
        resource_manager = PDFResourceManager()
        output_fp = StringIO()
        device = TextConverter(resource_manager, output_fp, codec="utf-8", laparams=LAParams(all_texts=True))
        interpreter = PDFPageInterpreter(resource_manager, device)
        try:
            for page in PDFPage.get_pages(pdf_fp):
                interpreter.process_page(page)
            text = output_fp.getvalue()
        except Exception as e:
            logger.debug(e)
            text = ''
        pdf_fp.close()  # remove the pdf file

        # extract words from the text
        words_in_text = text.replace("-\n", "").replace("\n", " ").lower().split()

        # search
        for word in word_list:
            n = len(word.split())
            ngrams = [' '.join(ngram) for ngram in list(zip(*(words_in_text[i:] for i in range(n))))]
            if word in ngrams:
                result.append(word)

    return r.status_code, result


logger.debug(f'Launching jobs...')
with multiprocessing.Pool(processes=args.jobs) as pool:
    results = pool.map(process, parameter_chunks)

logger.debug(f'Merging results...')
results = [result for sub_results in results for result in sub_results]

logger.debug(f'Saving results...')
with open(args.output, 'w') as f:
    with jsonlines.Writer(f) as writer:
        writer.write_all(results)
