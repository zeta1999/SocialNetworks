import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import conferences.conferences as conf_data
from utils.json import *
from scipy import sparse
import csv

DIR_PARENT = "papers_network/"
DIR_DATA   = DIR_PARENT + "data/"
DIR_GEPHI  = DIR_PARENT + "gephi/"
DIR_FIGS   = DIR_PARENT + "figs/"

class PapersNetwork:
  def __init__(self):
    self.papers_data = None # paper_id  => paper
    self.papers      = {}   # paper_id  => [author_id]
    self.authors     = {}   # author_id => [paper_id]
    
    # paper_id => conference_name
    self.paper_conferences = conf_data.load_s2_conferences()
    
    self.attributes = {}

    self.graph = nx.Graph()

  def write(self):
    suffix = "".join([ "_" + k + "=" + v for (k,v) in self.attributes.items() ])
    nx.write_gexf(self.graph, DIR_GEPHI+"papers-network"+suffix+".gexf")

  def add_papers(self, papers):
    self.papers_data = papers
    for paper_id, paper in papers.items(): self.add_paper(paper)

  def add_paper(self, paper):
    paper_id = paper["id"]

    author_ids = []
    # to add each author
    def add_author(author_id):
      # add to papers
      author_ids.append(author_id)
      # add to authors
      if not author_id in self.authors: self.authors[author_id] = []
      self.authors[author_id].append(paper_id)

    # collect paper's authors
    for author in paper["authors"]:
      author_id = extract_author_id(author)
      add_author(author_id)
    self.papers[paper_id] = author_ids

  def fill_graph(self):
    # nodes: papers

    # attr: filling conferences:
    self.attributes["color"] = "conf"

    for paper_id, paper in self.papers_data.items():
      self.graph.add_node(paper_id)
      title = paper["title"] if "title" in paper else "no title"
      self.graph.node[paper_id]["title"] = title
      self.graph.node[paper_id]["conf"] = self.paper_conferences[paper_id]

    # edges: shared authors (collaborations)
    for paper_id, author_ids in self.papers.items(): # for each paper
      for author_id in author_ids:           # for each paper by author
        for p_id in self.authors[author_id]: # for each other paper by author
          if paper_id != p_id:
            self.graph.add_edge(paper_id, p_id)

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

  def fill_node_centralities(self, centrality_name):
    data = load_json(DIR_DATA+centrality_name+"_centralities")
    # set color attributes
    for node, value in data.items():
      self.graph.node[node][centrality_name+"-centrality"] = value
    # set graph attribute
    self.attributes["centrality"] = centrality_name

  # remove all nodes except for those in the cc_ranked connected component,
  # where components are ranked from largest to smallest node count
  def isolate_component(self, cc_rank):
    self.graph = \
      sorted(nx.connected_component_subgraphs(self.graph),
        key = len, reverse = True) \
      [cc_rank]

    self.attributes["cc-rank"] = cc_rank

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

  def get_paper_id_to_paper_title_dict(self):
    # self.papers_data             :: paper_id => paper
    # paper_id_to_paper_title_dict :: paper_id => paper_title
    paper_id_to_paper_title_dict = { p_id : p["title"] for p_id, p in self.papers_data.items() }
    return paper_id_to_paper_title_dict

  def save_paper_id_to_paper_title_csv(self):
    paper_id_to_paper_title_dict = self.get_paper_id_to_paper_title_dict()
    with open(DIR_DATA+"paper_id_to_paper_title.csv", "w+") as file:
      writer = csv.writer(file)
      writer.writerow(["paper_id", ])

  def save_author_id_to_author_name_email_csv(self):
    author_name_email = self.get_author_id_to_author_name_email_dict()
    with open(DIR_DATA+"author_id_to_author_name_email.csv", "w+") as file:
      writer = csv.writer(file)
      writer.writerow(["author_id", "author_name", "author_email"])
      for author_id, (author_name, author_email) in tqdm(author_name_email.items()):
        writer.writerow([author_id, author_name, author_email])

def extract_author_id(author):
  # success - author in data set (has id)
  if "ids" in author and len(author["ids"]) > 0: return author["ids"][0]
  # failure - author not in data set (doesn't have id)
  else: return False
