# Report Outline

<!-- Format --
The idea is that every paragraph in the final report
is represented by at least one sentence in this outline.
-->

## Introduction

The data set consists of the record of papers published in computer systems conferences during 2017.
Furthermore, I matched these records to their entries in the Semantic Scholar database.
The fields that we I focused on were:
  - paper: title, semantic scholar id (s2id), conference, out-citations, in-citations, authors
  - author: name, Google scholar email, semantic scholar id (s2id) hindex, i10index, number of publications (npubs), as pc chair, as session chair, as panelist, as keynote speaker, as author
The purpose of collecting and analyzing this data was to look for any patterns in the networks and correlations of the data and their fields, and then to clearly document and attempt to explain the results.

## Background

- Context of work on social networks
- Recognized emergent features of social networks

The study of social networks has identified several important, emergent features of such networks that heavily influence their structure: centrality, connected components, bridges, diameter, etc.

Measures of node centrality quantify how 'central' a node is in a network. Here, the meaning of 'central' is highly dependent on the network.
There are several different kinds of centrality measures that vary in what they are good for measuring in different context; they include degree, eigenvector, betweenness and closeness centralities.
*TODO*: describe centralities and how to interpret them

The partitioning of a network into connected components yields that for each node in a partition, there is a path from that node to each other node in its partition.
Connected components separate nodes into groups that are completely connected by the trait that edges represent. Each component can be analyzed as a isolated sub-network.
Sometimes two would-be components are connected by just a few bridges. This is related to closeness and betweeness centrality.

Computer science collaboration analysts have used degree centrality along with correlations of node traits to make determinations about, for example, how likely nodes are to be connected given their features (e.g. gender) [Ghiasi G.].
Along with degree, connections between nodes can be classified by the features of the connected nodes. [Ghiasi G.].

More generally, collaboration networks of scientific researchers analysis has pointed to some specific features being important for how likely authors are to collaborate: co-authorship distance, geographic closeness, cultural closeness, likeness of research institution type (e.g. university or industry) [Knoke D., Yang S.]
There were also some interesting results suggesting that cross-disciplinary collaboration may be comparably important to inter-disciplinary collaboration [Knoke., Yang S.]

## Questions / Hypotheses

I had two main research questions:

_Question_: Which conferences should be considered closely related to the main group of papers / topics, and which should be considered controls, belonging to related topics, but not quite as strongly related to the bulk of the papers? 
_Hypothesis_: The commonly-recognized computer systems conferences would be more related to each other than the purposely-inserted control conferences (via Eitan) in terms of collaboration- and citation-connectivity.

__Question__: How closely to various "influence scores" correlate to various centrality measurements in the 2017 authors' collaboration network?
_Hypothesis_: The influences scores, such as hindex and i10index, would correlate strongly with other emergent measures of node influence, such as various centrality measures.

## Conference Citation Network

In the conference citation network, each node represents a conference from the 2017 data and each directed edge A to B is weighted by the number of papers in B (not necessarily from 2017 data) that were cited by a 2017 paper in A.

*figure: conference citation network with manual labels*

### Analysis

Not very interesting because data very incomplete and no immediate patterns emerged.

## Paper Collaboration Network

In the paper collaboration network, each node represents a paper from the 2017 data and each undirected edge between A and B is weighted by the number of authors that A and B shared.

This network can be colored by many different metrics, including node centralities and paper features.

*figure: paper collaboration network with several colorings*

### Analysis

This network was clean to look at, but seemed hard to read higher-level patterns out of in comparison to the authors collaboration network.

## Author Collaboration Network

In the author collaboration network, each node represents an author and each undirected edge between A and B is weighted by the number of papers in the 2017 data that were co-authored by A and B.

This network was intuitive to look at, but was obviously visually skewed heavily by papers that had huge numbers of authors (such as the Google paper) since just one paper with not very many noteworthy authors can still take up lots of space.

In this network in particular, the idea of node centrality seems to match up the best with the question of "author influence"; perhaps author 'centrality' is correlates in some way with author influence.

This network can be colored by many different metrics, including node centralities and author features.
Two colorings can be used at once to illustrate node-to-node relationships of these features.

*figure: author collaborations network with several colorings and multi-colorings*

### Analysis

The author features pairs matrix yields some interesting results:
- The different centrality metrics seem to measure different things from each other and from the other author features (such as hindex and i10index).
- The eigenvector centrality seems to not correspond to anything meaningful.
- The degree centrality correlates well with traditional measures of author influence and has a log normal distribution.
- The betweenness centrality does not correlate with any other measure than 'as author' and has a bimodal, long-tail distribution.
- The closeness centrality does not correlate with any other measures and has a normal distribution.

There is one large connected component with the majority of authors, and it varies the most in terms of author features. Other, smaller components are more homogeneous.

*figure: author features pairs matrix*

## Conclusions

*TODO*

## References

- Ghiasi G - _On the Compliance of Women Engineers with a Gendered Scientific System_
- Sonnenwald D - _Scientific Collaboration_
- _Social Network Analysis_ by Knoke D. Yang S.