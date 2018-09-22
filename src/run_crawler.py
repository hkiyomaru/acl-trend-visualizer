"""Main script."""
import argparse

from investigator import Investigator


def load_word_list(path):
    with open(path) as f:
        return [line.strip() for line in f if line.strip() != ""]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('WORDLIST', help='path to a word list file')
    parser.add_argument('-y', '--year', default="16,17,18",
                        help='years of conferences (e.g., input "--year 16,17,18")')
    parser.add_argument('-t', '--type', default="ls", choices=["l", "s", "ls"],
                        help='submission types ("l" (long), "s" (short), or "ls")')
    parser.add_argument('--tmp-dir', default="tmp",
                        help='path to save pdf files temporarily')
    parser.add_argument('-j', '--jobs', default=1, type=int,
                        help='number of jobs')
    parser.add_argument('--output', default="result.json",
                        help='path to the output file')
    args = parser.parse_args()

    investigator = Investigator(args.year, args.type)
    word_list = load_word_list(args.WORDLIST)
    investigator.search(word_list, args.output, tmp_dir=args.tmp_dir, jobs=args.jobs)


if __name__ == '__main__':
    main()
