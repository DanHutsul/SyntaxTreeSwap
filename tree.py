from flask import Flask, request
from nltk.tree import *
from itertools import permutations
import json
import re

app = Flask(__name__)

TOSWAP_LABELS = ['NP']
TOFIND_LABELS = [',', 'CC']


def find_swap_index(parent, to_find_labels, to_swap_labels):
    """
    Function to find indexes of labels around which to swap subtrees

    Parameters:
    parent (nltk.Tree): parent tree
    to_find_labels (list(str)): list of labels that should be found
    to_swap_labels (list(str)): list of labels that should be on both
        sides of the found label

    Returns:
    list(int): list of indexes
    """
    out = []
    if len(parent) < 3:
        return out

    for x in range(1, len(parent)-1):
        if type(parent[x]) is not Tree:
            continue
        if parent[x].label() in to_find_labels:
            if parent[x+1].label() in to_swap_labels and parent[x-1].label() in to_swap_labels:
                out.append(x)
    return out


def get_values_to_swap(parent, deep, to_find_labels, to_swap_labels):
    """
    Recursive DFS Function to find all indexes of labels
        around which to swap subtrees

    Parameters:
    parent (nltk.Tree): parent tree
    deep (list(int)): index of the functions depth
    to_find_labels (list(str)): list of labels that should be found
    to_swap_labels (list(str)): list of labels that should be on both
        sides of the found label

    Returns:
    dict(list(int) : list(int)): list of indexes
    """
    out = {}
    indexes = find_swap_index(parent, to_find_labels, to_swap_labels)
    if len(indexes) > 0:
        out[tuple(deep)] = indexes

    for x in range(len(parent)):
        if type(parent[x]) is Tree:
            out.update(get_values_to_swap(
                parent[x], deep + [x], to_find_labels, to_swap_labels))
        else:
            continue
    return out


def swap_subtrees(parent, original, new):
    """
    Function to swap subtrees by index

    Parameters:
    parent (nltk.Tree): parent tree
    original (list(list(int))): indexes of the original subtrees
    new (list(list(int))): indexes of the new subtrees

    Returns:
    (nltk.Tree): new tree
    """
    temp = []
    for idx in new:
        temp.append(parent[idx])

    for x in range(len(new)):
        parent[original[x]] = temp[x]

    return parent


@app.route('/paraphrase', methods=['GET'])
def paraphrase():
    tree = request.args.get('tree', None)
    parent = Tree.fromstring(tree)

    paraphrases = []

    swap_indices = get_values_to_swap(parent, [], TOFIND_LABELS, TOSWAP_LABELS)
    for key, value in swap_indices.items():
        to_swap_idxs = []
        # Convert indexes of swap axis to indexes of items being swapped
        for idx in value:
            to_swap_idxs.append(idx-1)
            to_swap_idxs.append(idx+1)

        to_swap_idxs = set(to_swap_idxs)
        # Get permutations of indexes of items being swapped
        value_permutations = list(permutations(to_swap_idxs))
        # Save original order of indexes
        original_order = [list(key) + [idx] for idx in value_permutations[0]]
        for perm in value_permutations[1:]:
            new_order = [list(key) + [idx] for idx in perm]
            # Clean the output and add it to the output
            paraphrases.append([{'tree': re.sub(
                ' +', ' ', str(swap_subtrees(parent, original_order, new_order)).replace('\n', ''))}])

    return {'paraphrases': paraphrases}


if __name__ == "__main__":
    app.run()