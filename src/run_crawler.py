"""Main script to run a crawler."""
import argparse

from utils import load_word_list
from utils import save_results
from crawler import Crawler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('WORDLIST', help='path to a word list file')
    parser.add_argument('-c', '--conference', default="acl,naacl,emnlp",
                        help='conferences (e.g., input "--year acl,naacl,emnlp")')
    parser.add_argument('-y', '--year', default="13,14,15,16,17,18",
                        help='years of conferences (e.g., input "--year 16,17,18")')
    parser.add_argument('-t', '--type', default="l,s",
                        help='submission types ("l" (long), "s" (short), or "l,s")')
    parser.add_argument('--tmp-dir', default="tmp",
                        help='path to save pdf files temporarily')
    parser.add_argument('-j', '--jobs', default=1, type=int,
                        help='number of jobs')
    parser.add_argument('--output', default="result.json",
                        help='path to the output file')
    args = parser.parse_args()

    word_list = load_word_list(args.WORDLIST)
    investigator = Crawler(args.conference, args.year, args.type)
    results = investigator.search(word_list, tmp_dir=args.tmp_dir, jobs=args.jobs)
    save_results(results, args.output)


if __name__ == '__main__':
    main()
