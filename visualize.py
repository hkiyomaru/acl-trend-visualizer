import argparse
from logging import getLogger, StreamHandler, Formatter, DEBUG

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

parser = argparse.ArgumentParser()
parser.add_argument('WORDLIST', help='path to the word list')
parser.add_argument('RESULT', help='path to the result')
parser.add_argument('--output', default="pointplot.png", help='path to the output file')
args = parser.parse_args()

logger = getLogger(__name__)
handler = StreamHandler()
handler.setFormatter(Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.propagate = False
logger.setLevel(DEBUG)

logger.debug('Loading a word list...')
with open(args.WORDLIST) as f:
    word_list = [line.strip().lower() for line in f if line.strip() and not line.startswith("#")]
logger.debug(f'# words:       {len(word_list)}')

logger.debug('Reading the result...')
result_df = pd.read_json(args.RESULT, orient='records', lines=True)
for word in word_list:
    result_df[word] = result_df['words'].apply(lambda words: 1 if word in words else 0)

logger.debug('Grouping the result...')
g = result_df.groupby('year')[word_list].sum()
g.reset_index(inplace=True)

logger.debug('Reshaping the result...')
reshaped_df = g[['year'] + word_list]
reshaped_df = reshaped_df.melt('year', var_name='cols', value_name='counts')

logger.debug('Configuring the visualization settings...')
plt.figure(num=None, figsize=(20, 10))
plt.rcParams["font.size"] = 32

logger.debug('Visualizing the result...')
ax = sns.pointplot(x='year', y='counts', hue='cols', data=reshaped_df)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0)
fig = ax.get_figure()
fig.savefig(args.output, bbox_inches='tight')
