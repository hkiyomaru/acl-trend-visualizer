"""Main script to run a visualizer."""
import argparse

from utils import load_word_list
from utils import load_results
from visualizer import Visualizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('WORDLIST', help='path to a word list file')
    parser.add_argument('RESULTS', help='path to a result file')
    parser.add_argument('--output', default="pointplot.png",
                        help='path to the output file')
    args = parser.parse_args()

    words = load_word_list(args.WORDLIST)
    results = load_results(args.RESULTS)
    visualizer = Visualizer(words, results)
    visualizer.pointplot(args.output)


if __name__ == '__main__':
    main()
