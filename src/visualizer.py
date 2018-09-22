"""Visualizer for the results."""
import os

import seaborn as sns
import matplotlib.pyplot as plt
import pandas


class Visualizer(object):

    def __init__(self, words, results):
        self.words = words
        self.results = self.preprocess(results)

    def pointplot(self, out):
        plt.figure(num=None, figsize=(9, 6))

        g = self.results.groupby("year")[self.words].sum()
        g.reset_index(inplace=True)

        df = g[["year"] + self.words]
        df = df.melt("year", var_name="cols", value_name="counts")
        ax = sns.pointplot(x="year", y="counts", hue="cols", data=df, palette="bright")
        fig = ax.get_figure()
        fig.savefig(os.path.join(out, 'pointplot.png'))

    def preprocess(self, results):
        results = pandas.DataFrame(results)
        for word in self.words:
            results[word] = results['words'].apply(
                lambda words: 1 if word in words else 0)
        return results