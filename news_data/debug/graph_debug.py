"""from ranker.graph_handler import GraphHandler

gh = GraphHandler(graph_path="graph_data/new_graph.json")

num_nodes = gh.graph.number_of_nodes()
num_edges = gh.graph.number_of_edges()
print(f"Number of nodes: {num_nodes} and edges: {num_edges}")
print(gh.get_closeness_to_liked(int(-8552835669932543736)))"""

import networkx as nx
import community as community_louvain
from ranker.graph_handler import GraphHandler

gh = GraphHandler(graph_path="graph_data/new_graph.json")
G = gh.graph

# Compute the best partition using the Louvain method
partition = community_louvain.best_partition(G)

# The 'partition' variable will be a dictionary where keys are nodes
# and values are the community IDs they belong to.
# Group nodes by community
communities = {}
for node, community_id in partition.items():
    if community_id not in communities:
        communities[community_id] = []
    communities[community_id].append(node)

# Print summary
print(f"🔍 Community Detection Results:")
print(f"📈 Total Communities Found: {len(communities)}")
print(f"📝 Total Nodes: {len(partition)}")
print(f"📊 Average Community Size: {len(partition) / len(communities):.2f}")
print("-" * 50)

# Print each community
for community_id, nodes in communities.items():
    print(f"🏘️  Community {community_id}: {len(nodes)} nodes")
    print(f"   Members: {', '.join(map(str, nodes))}")
    print()

# You can also calculate the modularity of the partition
modularity = community_louvain.modularity(partition, G)
print(f"Modularity: {modularity}")