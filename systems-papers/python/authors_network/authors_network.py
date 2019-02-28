import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter

from utils.json import *

DIR_PARENT = "authors_network/"
DIR_DATA   = DIR_PARENT + "data/"
DIR_GEPHI  = DIR_PARENT + "gephi/"
DIR_FIGS   = DIR_PARENT + "figs/"

class AuthorsNetwork:
  def __init__(self):
    self.authors = {} # author_id => paper_id
    self.papers  = {} # paper_id  => paper (dict)
    self.author_names = {} # author_id => string
    self.graph = nx.Graph()

    self.attributes = {} # keep track of modifications to graph

  def write(self):
    suffix = "".join(
      [ "_" + k + "=" + str(v)
      for (k,v) in self.attributes.items() ])
    nx.write_gexf(self.graph, DIR_GEPHI + "authors-network"+suffix+".gexf")

  def add_paper(self, paper):
    paper_id = paper["id"]
    self.papers[paper_id] = paper
    for author in paper["authors"]:
      author_id, author_name = extract_author_id_name(author)
      if author_id:
        self.add_author_id_name(author_id, author_name)
        self.add_author_paper(author_id, paper_id)
    return paper_id

  def get_paper(self, paper_id): return self.papers[paper_id]

  def add_author_id_name(self, author_id, author_name):
    if not author_id in self.authors:
      self.authors[author_id] = []
      self.author_names[author_id] = author_name

  # add to author a paper they wrote
  def add_author_paper(self, author_id, paper_id):
    self.get_author_papers(author_id).append(paper_id)

  def get_author_papers(self, author_id): return self.authors[author_id]

  # get author list (in data set) of the given paper
  def get_paper_authors(self, paper_id):
    for author in self.get_paper(paper_id)["authors"]:
      author_id, author_name = extract_author_id_name(author)
      if author_id: yield author_id

  # gets list of authors that the given author has collaborated with
  def get_author_collaborators(self, author_id, paper_ids):
    for paper_id in paper_ids:
      for a_id in self.get_paper_authors(paper_id):
        if a_id != author_id: yield (a_id, paper_id)

  # fill self.graph : nx.Graph
  def fill_graph(self):
    # nodes
    for author_id in self.authors.keys():
      self.graph.add_node(author_id,
        attr_dict = {"author-name": self.author_names[author_id]})
    # edges
    for author_id, paper_ids in self.authors.items():
      for (a_id, paper_id) in self.get_author_collaborators(author_id, paper_ids):
        self.graph.add_edge(author_id, a_id,
          attr_dict = {"paper-title": self.papers[paper_id]["title"]})

  def print_statistics(self):
    print("-------------------------------------------")
    print("-- Graph Statistics -----------------------")
    print()
    print("   isolates:", nx.number_of_isolates(self.graph))
    print("    density:", nx.density(self.graph))
    print("    bridges:", len(list(nx.bridges(self.graph))))
    print("    cliques:", nx.graph_clique_number(self.graph))
    print(" conn-comps:", nx.number_connected_components(self.graph))
    print()
    print("-------------------------------------------")

  def calculate_centralities(self):
    # dump calculated data
    dump_json(nx.degree_centrality(self.graph),
      DIR_DATA + "degree_centralities")
    dump_json(nx.eigenvector_centrality(self.graph),
      DIR_DATA + "eigenvector_centralities")
    dump_json(nx.closeness_centrality(self.graph),
      DIR_DATA + "closeness_centralities")
    dump_json(nx.betweenness_centrality(self.graph),
      DIR_DATA + "betweenness_centralities")

  def plot_centralities(self):
    suffix = ""
    # PARAMETERS
    SHOW_FIG = False
    version = 2.1

    # helper function for plotting the 4 centralities graphs
    def plot_histogram(
      position,
      title,
      xlabel, ylabel,
      bins,
      xmax,
      data
    ):
      xmax = None
      data = list(data)
      if xmax: data = list(filter(lambda x: x <= xmax, data))
      print("max for", xlabel, ":", max(list(data)))
      xlabel_prefix = "Log of "
      ylabel_prefix = "Log of "
      plt.subplot(position)
      plt.title(title)
      plt.xlabel(xlabel_prefix + xlabel)
      plt.ylabel(ylabel_prefix + ylabel)
      plt.xscale("log")
      plt.grid(True)

      # x0, x1 = min(data), max(data)
      # xticks = np.array([ x1 / 10**i  for i in np.arange(20,-1,-1) ])
      # if title == "Eigenvector Centralities":
      #   xticks_labels = map(lambda x: "{:.2e}".format(x), xticks)
      # else:
      #   xticks_labels = map(lambda x: round(x, 2), xticks)
      # plt.xticks(xticks, xticks_labels, rotation=15)

      plt.hist(data, bins,
        log = True,
        histtype = "bar",
        facecolor = "blue")

    authors_count = len(self.authors)
    plot_histogram(221,
      "Degree Centralities", "Degree", "Nodes",
      bins = 50, xmax = 30,
      data = map(lambda x: x * authors_count,
        load_json(DIR_DATA + "degree_centralities").values()))

    plot_histogram(222,
      "Eigenvector Centralities", "Eigenvector Centrality", "Node Share",
      bins = 100, xmax = 0.00003,
      data = load_json(DIR_DATA + "eigenvector_centralities").values())

    plot_histogram(223,
      "Closeness Centralities", "Closeness Centrality", "Node Share",
      bins = 50, xmax = 30,
      data = load_json(DIR_DATA + "closeness_centralities").values())

    plot_histogram(224,
      "Betweenness Centralities", "Betweenness Centrality", "Node Share",
      bins = 50, xmax = 30,
      data = load_json(DIR_DATA + "betweenness_centralities").values())

    # SUFFIX
    suffix += "_v"+str(version)

    # FIGURE
    if SHOW_FIG:
      plt.show()
    else:
      fig = plt.gcf()
      fig.set_size_inches(11.0, 8.5)
      plt.tight_layout()
      fig.savefig(DIR_FIGS+"centralities"+suffix + ".png", dpi=100)

  def to_adjacency_matrix(self):
    # matrix of author-author collaborations
    matrix = [[ 0
      for _ in range(len(self.authors)) ]
      for _ in range(len(self.authors))  ]
    # calculate author indices
    authors_is = {}
    author_i = 0
    for author_id in self.authors.keys():
      authors_is[author_id] = author_i
      author_i += 1
    # fill author-author edges
    for author_id in self.authors.keys():
      for a_id in self.get_author_collaborators(author_id):
        matrix[ authors_is[author_id] ][ authors_is[a_id] ] = 1
    return np.matrix(matrix)

  # transpose of adjacency matrix
  def to_transformed_adjacency_matrix(self):
    return self.to_adjacency_matrix().T

  # nodes are given a value cc-size indicating the size (in nodes) of the
  # connected component they are a part of
  def fill_ccsizes(self):
    for comp in nx.connected_components(self.graph):
      for node in comp:
        self.graph.node[node]["cc-size"] = len(comp)
    
    self.attributes["coloring"] = "cc-size"

  # def calculate_centralities(self):
  #   # dump calculated data
  #   dump_json(nx.degree_centrality(self.graph),
  #     DIR_DATA + "degree_centralities")
  #   dump_json(nx.eigenvector_centrality(self.graph),
  #     DIR_DATA + "eigenvector_centralities")
  #   dump_json(nx.closeness_centrality(self.graph),
  #     DIR_DATA + "closeness_centralities")
  #   dump_json(nx.betweenness_centrality(self.graph),
  #     DIR_DATA + "betweenness_centralities")

  def fill_centralities(self, centrality, calculate=False):
    if calculate:
      print("    - calculating "+centrality+" centrality...")
      centrality_functions = {
        "degree": nx.degree_centrality,
        "eigenvector": nx.eigenvector_centrality,
        "closeness": nx.closeness_centrality,
        "betweenness": nx.betweenness_centrality
      }
      centralities = centrality_functions[centrality](self.graph)
      # if   centrality == "degree"      : centralities = xs.degree_centrality(self.graph)
      # elif centrality == "eigenvector" : centralities = xs.eigenvector_centrality(self.graph)
      # elif centrality == "closeness"   : centralities = xs.closeness_centrality(self.graph)
      # elif centrality == "Betweenness" : centralities = xs.betweenness_centrality(self.graph)
    else:
      centralities = load_json(DIR_DATA + centrality+"_centralities")
    
    for node, c in centralities.items():
      self.graph.node[node][centrality+"-centrality"] = c

    self.attributes["centrality"] = centrality

  def fill_all_centralities(self, calculate=False):
    centrality_names = ["degree", "eigenvector", "closeness", "betweenness"]
    for centrality_name in centrality_names:
      self.fill_centralities(centrality_name, calculate=calculate)

    self.attributes["centrality"] = "all"

  # remove all nodes except for those in the cc_ranked connected component,
  # where components are ranked from largest to smallest node count
  def isolate_component(self, cc_rank):
    self.graph = \
      sorted(nx.connected_component_subgraphs(self.graph),
        key = len, reverse = True) \
      [cc_rank]

    self.attributes["cc-rank"] = cc_rank

def extract_author_id_name(author):
  # success - author in data set (has id)
  if "ids" in author and "name" in author and len(author["ids"]) > 0:
    return author["ids"][0], author["name"]
  # failure - author not in data set (doesn't have id)
  else:
    print(author)
    return (False, False)
