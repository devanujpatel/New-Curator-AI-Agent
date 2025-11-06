"""import json
import networkx as nx
from networkx.readwrite import json_graph
from pyvis.network import Network
import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path
import tempfile

st.set_page_config(layout="wide", page_title="Interactive Graph")

# ===== Hardcoded path to JSON file =====
json_path = Path(r"C:\DEV\coding\MSN\graph_data\all_articles_graph.json")  # Change to your file path

# ===== Load JSON & convert to NetworkX =====
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Convert "edges" -> "links" for networkx compatibility
if "edges" in data and "links" not in data:
    data["links"] = data.pop("edges")

G = json_graph.node_link_graph(data)

# ===== Create Pyvis network =====
net = Network(height="600px", width="100%", directed=G.is_directed(), notebook=False, bgcolor="#ffffff")

# Physics + spread apart nodes
net.set_options(""
var options = {
  "interaction": { "hover": true, "navigationButtons": true },
  "nodes": {
    "shape": "box",
    "font": { "size": 18, "face": "arial" },
    "margin": 10,
    "widthConstraint": { "maximum": 300 }
  },
  "edges": {
    "smooth": { "type": "dynamic" },
    "font": { "size": 14, "align": "top" }
  },
  "physics": {
    "enabled": true,
    "barnesHut": {
      "gravitationalConstant": -25000,
      "centralGravity": 0.05,
      "springLength": 250,
      "springConstant": 0.02,
      "avoidOverlap": 1
    },
    "stabilization": {
      "enabled": true,
      "iterations": 300
    }
  }
}
"")

# Add nodes
for node, attrs in G.nodes(data=True):
    title = attrs.get("title", str(node))
    url = attrs.get("url", "")
    tooltip = f"<b>{title}</b><br>{attrs.get('description','')}"
    net.add_node(node, label=title, title=tooltip, shape="box", href=url)

# Add edges
for u, v, attrs in G.edges(data=True):
    weight = attrs.get("weight", 1)
    net.add_edge(u, v, value=weight, title=f"Weight: {weight}")

# ===== Save & render in Streamlit =====
tmp_dir = tempfile.mkdtemp()
html_path = Path(tmp_dir) / "graph.html"
net.save_graph(str(html_path))

# Use full browser width & height
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

components.html(html_content, height=600, width=2000, scrolling=True)
"""
import streamlit as st
from pyvis.network import Network
import json
import streamlit.components.v1 as components

# Load your JSON file
json_path = r"/graph_data/all_articles_graph.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Create a bigger, styled PyVis network
net = Network(
    height="900px",
    width="100%",
    bgcolor="#1e1e1e",
    font_color="white",
    notebook=False
)

# Physics tuned for readability
net.barnes_hut(
    gravity=-30000,
    central_gravity=0.2,
    spring_length=200,
    spring_strength=0.005,
    damping=0.09
)

# Add nodes
for node in data["nodes"]:
    net.add_node(
        node["id"],
        label=node["title"],  # Show article title
        shape="box",
        size=25,  # Bigger node
        font={"size": 20},  # Bigger font
        title=node.get("description", ""),  # Tooltip
        color="#ff8c00" if node.get("category") == "business" else "#1f77b4"
    )

# Add edges with weights as labels
for edge in data["edges"]:
    weight = edge.get("weight", 1)
    net.add_edge(
        edge["source"],
        edge["target"],
        value=weight,
        title=f"Weight: {weight}",  # Tooltip on hover
        color="#cccccc"
    )

# Save and render
net.save_graph("graph.html")
with open("graph.html", "r", encoding="utf-8") as f:
    html_content = f.read()

components.html(html_content, height=600, width=2000, scrolling=True)