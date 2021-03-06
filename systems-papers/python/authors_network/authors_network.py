import numpy as np
import networkx as nx
from scipy import stats
import itertools as it
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import authors.persons_features as pf_data
from utils.debug import *
import utils.shared_utils as utils
from utils.json import *
import csv
import utils.csv as u_csv
from tqdm import tqdm
import authors_network.correlations as correlations

DIR_PARENT = "authors_network/"
DIR_DATA   = DIR_PARENT + "data/"
DIR_GEPHI  = DIR_PARENT + "gephi/"
DIR_FIGS   = DIR_PARENT + "figs/"

CENTRALITY_KEYS = \
  [ "degree"
  , "eigenvector"
  , "betweenness"
  , "closeness" ]

PERSONSFEATURES_KEYS = \
      [ "npubs"
      , "hindex"
      , "hindex5y"
      , "i10index"
      , "i10index5y"
      , "citedby"
      , "as_pc_chair"
      , "as_pc"
      , "as_session_chair"
      , "as_panelist"
      , "as_keynote_speaker"
      , "as_author" ]

def save_centrality_data(data, centrality_name, suffix=""):
  dump_json(data, DIR_DATA+centrality_name+"_centralities"+suffix)

def load_centrality_data(centrality_name, suffix=""):
  return load_json(DIR_DATA+centrality_name+"_centralities"+suffix)

class AuthorsNetwork:
  def __init__(self):
    self.authors = {}      # author_id => paper_id
    self.papers  = {}      # paper_id  => paper (dict)
    self.author_names = {} # author_id => string

    # author_name => person_features
    self.persons_features_named = { f["name"]: f for f in pf_data.getPersonsFeatures() }
    # author_id => person_features
    self.persons_features = {}

    self.missing_names    = set()
    self.used_names       = set()

    self.attributes = {} # keep track of modifications to graph

    self.graph = nx.Graph()

  def correlate_closeness_npubs(self):
    closenesses = nx.closeness_centrality(self.graph)
    c = [ closenesses[aid] for aid in closenesses.keys() if "npubs" in self.persons_features[aid] ]
    p = [ self.persons_features[aid]["npubs"] for aid in closenesses.keys() if "npubs" in self.persons_features[aid] ]
    return np.corrcoef(c, p)

  def get_suffix(self):
    return "".join(
      [ "_" + k + "=" + str(v)
        for (k,v) in self.attributes.items() ])

  def write(self):
    nx.write_gexf(self.graph, DIR_GEPHI + "authors-network"+self.get_suffix()+".gexf")

  def add_paper(self, paper):
    paper_id = paper["id"] if "id" in paper else paper["paperId"]
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
      if author_name in self.persons_features_named:
        self.persons_features[author_id] = \
          self.persons_features_named[author_name]
      else:
        self.missing_names.add(author_name)

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
      self.graph.add_node(author_id)
      author_name = self.author_names[author_id]
      node_attr = self.graph.node[author_id]
      node_attr["author-id"]   = author_id
      node_attr["author-name"] = self.author_names[author_id]

      if author_name in self.persons_features_named:
        pf = self.persons_features_named[author_name]
        for key, value in pf.items():
          node_attr[key] = str(value)
        self.used_names.add(author_name)

    # edges
    for author_id, paper_ids in self.authors.items():
      for (a_id, paper_id) in \
        self.get_author_collaborators(author_id, paper_ids) \
      :
        self.graph.add_edge(author_id, a_id,
          attr_dict = {"paper-title": self.papers[paper_id]["title"]})

  def print_statistics(self):
    message("-------------------------------------------")
    message("-- Graph Statistics -----------------------")
    message()
    message("   isolates:", nx.number_of_isolates(self.graph))
    message("    density:", nx.density(self.graph))
    message("    bridges:", len(list(nx.bridges(self.graph))))
    message("    cliques:", nx.graph_clique_number(self.graph))
    message(" conn-comps:", nx.number_connected_components(self.graph))
    message()
    message("-------------------------------------------")

  def fill_features(self):
    isolates = nx.isolates(self.graph)
    for node in isolates: self.graph.node[node]["isolate"] = True

    bridges = nx.bridges(self.graph)
    for node in isolates: self.graph.node[node]["isolate"] = True

  def calculate_centralities(self):
    suffix = self.get_suffix()

    # dump calculated data

    log("Calculating Nodes' Degree Centrality...", lvl=1)
    save_centrality_data(nx.degree_centrality(self.graph),
      "degree", suffix)

    log("Calculating Nodes' Eigenvector Centrality...", lvl=1)
    save_centrality_data(nx.eigenvector_centrality(self.graph),
      "eigenvector", suffix)

    log("Calculating Nodes' Closeness Centrality...", lvl=1)
    save_centrality_data(nx.closeness_centrality(self.graph),
      "closeness", suffix)

    log("Calculating Nodes' Betweenness Centrality...", lvl=1)
    save_centrality_data(
      nx.betweenness_centrality(self.graph, normalized=False),
      "betweenness", suffix)

  def plot_centralities(self):
    # debug("missing names:", self.missing_names)
    debug("missing names count:", len(self.missing_names))
    debug("used names count:", len(self.used_names))

    # PARAMETERS
    SHOW_FIG = False
    SAVE_FIG = False
    version = 3.1

    plt.title("Authors Network: Centralities")

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
      # debug("max for", xlabel, ":", max(list(data)))
      if xmax: data = list(filter(lambda x: x <= xmax, data))
      xlabel_prefix = ""
      ylabel_prefix = ""
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

    node_count = self.graph.number_of_nodes()

    plot_histogram(221,
      "Degree Centralities", "Degree", "Nodes",
      bins = 50, xmax = 30,
      data = map(lambda x: x * node_count,
        load_centrality_data("degree").values()))

    plot_histogram(222,
      "Eigenvector Centralities",
      "Normalized Eigenvector Centrality","Node Share",
      bins = 100, xmax = 0.00003,
      data = load_centrality_data("eigenvector").values())

    plot_histogram(223,
      "Closeness Centralities",
      "Normalized Closeness Centrality", "Node Share",
      bins = 50, xmax = 30,
      data = map(lambda x: x * node_count,
        load_centrality_data("closeness").values()))

    plot_histogram(224,
      "Betweenness Centralities",
      "Normalized Betweenness Centrality", "Node Share",
      bins = 50, xmax = 30,
      data = load_centrality_data("betweenness").values())

    # FIGURE
    if SHOW_FIG:
      plt.show()
    elif SAVE_FIG:
      fig = plt.gcf()
      fig.set_size_inches(11.0, 8.5)
      plt.tight_layout()
      fig.savefig(DIR_FIGS+"centralities_v"+str(version)+".png", dpi=100)

  def plot_component_centralities(self):
    cc_rank = self.attributes["cc-rank"]
    suffix = "cc-rank="+str(cc_rank)

    # PARAMETERS
    SHOW_FIG = False
    version = 3

    plt.title("Component "+str(cc_rank)+" Centralities")

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
      # debug("max for", xlabel, ":", max(list(data)))
      if xmax: data = list(filter(lambda x: x <= xmax, data))
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

    authors_count = self.graph.number_of_nodes()

    #########################################################

    plot_histogram(221,
      "Degree Centralities", "Degree", "Nodes",
      bins = 50, xmax = 30,
      data = map(lambda x: x * node_count,
        load_centrality_data("degree", suffix).values()))

    plot_histogram(222,
      "Eigenvector Centralities",
      "Eigenvector Centrality","Node",
      bins = 100, xmax = 0.00003,
      data = load_centrality_data("eigenvector", suffix).values())

    plot_histogram(223,
      "Closeness Centralities",
      "Closeness Centrality", "Node",
      bins = 50, xmax = 30,
      data = map(lambda x: x * node_count,
        load_centrality_data("closeness", suffix).values()))

    plot_histogram(224,
      "Betweenness Centralities",
      "Betweenness Centrality", "Node",
      bins = 50, xmax = 30,
      data = load_centrality_data("betweenness", suffix).values())

    # FIGURE
    if SHOW_FIG:
      plt.show()
    else:
      fig = plt.gcf()
      fig.set_size_inches(11.0, 8.5)
      plt.tight_layout()
      fig.savefig(DIR_FIGS+"centralities_"+
        "v"+str(version)+
        +suffix+
      ".png", dpi=100)

  def print_centralities_correlations(self):
    centrality_data = {
      name: list(load_centrality_data(name).values())
      for name in CENTRALITY_KEYS
    }

    for (name1, name2) in it.combinations(CENTRALITY_KEYS, 2):
      data1 = centrality_data[name1]
      data2 = centrality_data[name2]
      r, pv = stats.stats.pearsonr(data1, data2)
      message("="*40)
      message("Correlating:", name1, "and", name2)
      message("      r =", r)
      message("p-value =", pv)

  def save_all_correlations_csv(self):
    data = {} # author_name => { attr_key : attr_val }
    suffix = self.get_suffix()

    def set_attr(author_name, attr_key, attr_val):
      if not author_name in data: data[author_name] = {}
      data[author_name][attr_key] = attr_val

    # centralities data
    for cent_key in CENTRALITY_KEYS:
      # centrality_dict : node_id => cent_val
      centrality_dict = load_centrality_data(cent_key, suffix)
      for author_id, cent_val in centrality_dict.items():
        author_name = self.author_names[author_id]
        cent_val = round(cent_val, 4)
        set_attr(author_name, cent_key, cent_val)

    for author_name in data.keys():
      if author_name in self.persons_features_named:
        author_features = self.persons_features_named[author_name]
        for pf_key in PERSONSFEATURES_KEYS:
          if pf_key in author_features:
            try:
              pf_val = int(author_features[pf_key].strip())
            except:
              pf_val = ""
            set_attr(author_name, pf_key, pf_val)

    correlations.save_correlations_csv(
      CENTRALITY_KEYS + PERSONSFEATURES_KEYS,
      data,
      suffix,
      DIR_DATA)


  def print_high_centraltity_authors(self, centrality_name, n=10):
    centrality_key = centrality_name+"-centrality"
    centrality_data = load_centrality_data(centrality_name)
    centralities_list = list(centrality_data.keys())
    centralities_ordered = sorted(centralities_list,
      key = lambda x: x[1], reverse = True)
    i = 0
    for node in centralities_ordered:
      if i >= n: break
      attr = self.graph.node[node]
      message("-"*20, lvl=1)
      message("name:", attr["author-name"], lvl=1)
      message(centrality_key+":", attr[centrality_key], lvl=1)
      if " papers" in attr:
        message("papers:", attr[" papers"], lvl=1)
      i += 1

    # for node, centrality in centrality_data.items():
    #   print(self.graph.node[node])

  def get_adjacency_matrix(self):
    return nx.adjacency_matrix(self.graph)

  def save_adjacency_matrix_npz(self):
    adjmat = self.get_adjacency_matrix()
    with open(DIR_DATA+"adjacency_matrix.npz", "wb+") as file: sparse.save_npz(file, adjmat)

  def save_adjacency_matrix_csv(self):
    adjmat = self.get_adjacency_matrix()
    adjmat_list = adjmat.todense().tolist()

    with open(DIR_DATA+"adjacency_matrix.csv", "w+") as file:
      writer = csv.writer(file)
      node_ids = list(self.graph.nodes())
      writer.writerow([""] + node_ids)
      for node_i in range(len(node_ids)):
        node_id = node_ids[node_i]
        adjmat_row = list(map(str,adjmat_list[node_i]))
        writer.writerow([node_id] + adjmat_row)

  # nodes are given a value cc-size indicating the size (in nodes) of the
  # connected component they are a part of
  def fill_ccsizes(self):
    for comp in nx.connected_components(self.graph):
      for node in comp:
        self.graph.node[node]["cc-size"] = len(comp)

    self.attributes["coloring"] = "cc-size"

  def fill_centralities(self, centrality, calculate=False):
    suffix = ""
    if "cc-rank" in self.attributes:
      suffix += "cc-rank="+str(self.attributes["cc-rank"])

    if calculate:
      log("    - calculating "+centrality+" centrality...")
      centrality_functions = {
        "degree"      : nx.degree_centrality,
        "eigenvector" : nx.eigenvector_centrality,
        "closeness"   : nx.closeness_centrality,
        "betweenness" : nx.betweenness_centrality
      }
      centralities = centrality_functions[centrality](self.graph)
    else:
      centralities = load_centrality_data(centrality, suffix)

    for node, c in centralities.items():
      self.graph.node[node][centrality+"-centrality"] = c

    self.attributes["centrality"] = centrality

  def fill_all_centralities(self, calculate=False):
    CENTRALITY_KEYS = ["degree", "eigenvector", "closeness", "betweenness"]
    for centrality_name in CENTRALITY_KEYS:
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

    if False:
      message("number of nodes:",self.graph.number_of_nodes())
      exit()

  def get_author_id_to_author_name_email_dict(self):
    # self.author_names     : author_id => author_name
    # self.persons_features : author_id => person_features
    # author_name_email : author_id => (author_name, author_email)
    author_name_email = {}

    missing = []
    for author_id, person_features in self.persons_features.items():
      author_name = self.author_names[author_id]
      author_email = person_features["gs_email"] if "gs_email" in person_features else ""
      author_name_email[author_id] = (author_name, author_email)

    return author_name_email

  def save_author_id_to_author_name_email_csv(self):
    author_name_email = self.get_author_id_to_author_name_email_dict()
    u_csv.dump_csv(author_name_email, DIR_DATA+"author_id_to_author_name_email.csv",
        headers=["author_id", "author_name", "author_email"])

    # with open(DIR_DATA+"author_id_to_author_name_email.csv", "w+") as file:
    #   writer = csv.writer(file)
    #   writer.writerow(["author_id", "author_name", "author_email"])
    #   for author_id, (author_name, author_email) in tqdm(author_name_email.items()):
    #     writer.writerow([author_id, author_name, author_email])

def extract_author_id_name(author):
  # success - author in data set (has id)
  if "ids" in author and "name" in author and len(author["ids"]) > 0:
    return author["ids"][0], utils.normalized_author_name(author["name"])
  # failure - author not in data set (doesn't have id)
  else:
    # debug(author)
    return (False, False)
