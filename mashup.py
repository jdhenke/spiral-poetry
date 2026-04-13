#!/usr/bin/python
'''
MARKOV MODEL MASHUPS

Creates 'lyrical mashups' using Markov Models.
Can use characters or words as state. (You should add more mediums!)

Example files used:
    mashup.py       # this script
    sonnets.txt     # all of shakespeare's sonnets
    rhcp.txt        # all of red hot chili peppers lyrics
    gaga.txt        # all of lady gaga's lyrics

Input:
    ./mashup.py sonnets.txt              # randomly generate text similar to
                                         # shakespeare's sonnets
    
    ./mashup.py sonnets.txt rhcp.txt     # mashup shakespeare and the RHCP

    ./mashup.py *.txt                    # mashup all three

    ./mashup.py mashup.py                # inception

Output:
    mashup of source documents
    adjust constants and main to fit your needs!

Copyright (c) 2013 Joseph Henke

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
copies of the Software, and to permit persons to whom the Software is furnished
to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
SOFTWARE.
'''

import re, sys, random
from abc import *
from pprint import pprint
import json

def main():
    # ADJUST THESE!!!
    order = 1
    length = 10
    Handler = WordHandler
    paths = sys.argv[1:]
    if len(paths) == 0:
        print('No input specified')
        sys.exit(1)
    sources = [Handler(path) for path in paths]
    mc = MarkovChain(order, sources)
    with open("data.json", "w") as f:
        f.write(json.dumps(mc.distro))
    # seq = mc.walk(length)
    # for i in range(len(seq) - order):
    #     print seq[i], mc.distro[tuple(seq[i:i+order])]
    # mashup = Handler.format(seq)
    # print mashup

class FileHandler(object, metaclass=ABCMeta):
    def __init__(self, path):
        self.path = path
    def get_counts(self, order):
        counts = {}
        data = self.get_states()
        for i in range(len(data) - order):
            previous_state = tuple(data[i:i+order])
            counts.setdefault(previous_state, {})
            next_state = data[i+order]
            counts[previous_state].setdefault(next_state, 0)
            counts[previous_state][next_state] += 1
        return counts
    @abstractmethod
    def get_states(self):
        '''returns list of states found in data'''
    @staticmethod
    @abstractmethod
    def format(states):
        '''returns raw format associated with states'''

class CharHandler(FileHandler):
    def get_states(self):
        return tuple([x for x in open(self.path).read() if x not in ('\n', '\r')])
    @staticmethod
    def format(states):
        return ''.join(states) 

class WordHandler(FileHandler):
    def get_states(self):
        words = re.split(r'\s+', open(self.path).read())
        return tuple([x for x in words if len(x) > 0])
    @staticmethod
    def format(states):
        return ' '.join(states)

class MarkovChain(object):
    def __init__(self, order, handlers):
        self.order = order
        self.distro = self._get_distro(handlers)
    def _get_distro(self, handlers):
        '''
        returns dictionary
        keys = tuples of previous states
        values = list of tuples (next_state, cdf)
            cdf at index i => cdf of going to any of states in [0,i) = cdf
            {B:1, C:1, A:2} => [(B, 0), (C, 0.25), (A, 0.5)]
        no gurantees on ordering of states
        guarantees cdfs are increasing
        '''

        # get normalized global counts
        global_counts = {}
        for handler in handlers:
            source_counts = handler.get_counts(self.order)
            for previous_states, next_states in source_counts.items():
                total = 1.0 * sum(next_states.values())
                for next_state, count in next_states.items():
                    global_counts.setdefault(previous_states, {})
                    global_counts[previous_states].setdefault(next_state, 0)
                    global_counts[previous_states][next_state] += count / total

        # create cumulative probability distribution
        distro = {}
        for previous_states, next_states in global_counts.items():
            total = 1.0 * sum(next_states.values())
            assert len(previous_states) == 1
            distro[previous_states[0]] = []
            cdf = 0.0
            for next_state, count in next_states.items():
                distro[previous_states[0]].append((next_state, cdf))
                cdf += count / total

        return distro

    def walk(self, length):
        '''
        returns list of states, using this model's transition probabilities
        when choosing next state based on previous states.
        starts with random states.

        '''
        previous_states = random.choice(list(self.distro.keys()))
        output = list(previous_states)
        while len(output) < length:
            options = self.distro[previous_states]
            next_state = self.choose_next(options)
            output.append(next_state)
            previous_states = previous_states[1:] + (next_state, )
        return output

    def choose_next(self, options):
        '''randomly chooses next state based on probabilities'''
        r = random.random()
        last = None
        for datum, prob in options:
            if r < prob:
                return last
            else:
                last = datum
        return last

if __name__ == '__main__':
    main()
