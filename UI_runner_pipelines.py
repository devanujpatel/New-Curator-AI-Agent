import sys, os

# to get imports working:
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from news_data.aura_pipelines import main_daily_fetcher, update_feedbacks, delete_articles
from news_data.db.feedback import FeedbackDB
from news_data.db import articles as arcs, database
from news_data.ranker import embedder as embedder_module
from news_data.ranker import graph_handler as graph_handler_module
from streamlit_js_eval import streamlit_js_eval

# Initialize services
db = database.Database(article_collection="all_articles_layered")
articles_db = arcs.ArticleDB(db)
feedback_db = FeedbackDB(db)
embedder = embedder_module.EmbeddingService()
graph_handler = graph_handler_module.Neo4jGraphHandler("neo4j://127.0.0.1:7687", "neo4j", "PWD",
                                                       "aura-articles-labelled-2")

# # Initialize session state defaults
# if "categories" not in st.session_state:
#     st.session_state.categories = ["business", "technology"]


if "note_state" not in st.session_state:
    st.session_state.note_state = {}

# Fetch articles if not already loaded
if "ranked_articles_dict" not in st.session_state:
    inputs = {
        "country": "us",
        "categories": ["business",],
        "page_size": 50
    }
    ranked_articles_dict = main_daily_fetcher.get_articles(inputs, articles_db, embedder, graph_handler)
    print(f"[INFO]: fetched {len(ranked_articles_dict)} articles")
    st.session_state.ranked_articles_dict = ranked_articles_dict
    st.session_state.current_page = 1
    st.session_state.notes = {}

# Page title
st.markdown("<h1 style='text-align: center;'>AI-Curated News Dashboard</h1>", unsafe_allow_html=True)

# Sidebar - Category selection
# st.sidebar.header("Select Categories")
# business_checked = "business" in st.session_state.categories
# technology_checked = "technology" in st.session_state.categories


# def update_categories():
#     new_categories = []
#     if st.session_state.business_checkbox:
#         new_categories.append("business")
#     if st.session_state.technology_checkbox:
#         new_categories.append("technology")
#     st.session_state.categories = new_categories
#

# st.sidebar.checkbox(
#     "Business",
#     value=business_checked,
#     key="business_checkbox",
#     on_change=update_categories
# )
#
# st.sidebar.checkbox(
#     "Technology",
#     value=technology_checked,
#     key="technology_checkbox",
#     on_change=update_categories
# )

# Pagination setup and controls
articles_per_page = 10
total_pages = (len(st.session_state.ranked_articles_dict) - 1) // articles_per_page + 1

# Calculate articles to display for current page
start_idx = (st.session_state.current_page - 1) * articles_per_page
end_idx = start_idx + articles_per_page
article_ids_to_display = list(st.session_state.ranked_articles_dict.keys())[start_idx:end_idx]

# Display articles grid
cols = st.columns(2, gap="large")

idx = 1
for article_id in article_ids_to_display:

    article = st.session_state.ranked_articles_dict[article_id]

    # if article["category"] not in st.session_state.categories:
    #     continue

    idx += 1

    with cols[idx % 2]:
        # Title + Category
        st.subheader(article["title"])
        st.caption(article.get("category", ""))

        # Scores (inline, tiny font)
        scores_text = (
            f"Interest: {round(article.get('interest_score', 0))} | "
            f"Similarity: {round(article.get('liking_score', 0))} | "
            f"Graph: {round(article.get('graph_score', 0))} | "
            f"🏆 {round(article.get('final_score', 0))}"
        )
        st.caption(scores_text)

        # Description + Link
        st.write(article.get("description", ""))
        st.markdown(f"[Read more]({article['url']})")

        # Entities (inline chips)
        if article.get("entities"):
            st.markdown("**Entities:**")
            ent_cols = st.columns(min(len(article["entities"]), 3))
            for idx, entity in enumerate(article["entities"]):
                with ent_cols[idx % 3]:

                    if st.button(entity[0],
                                 key=f"{article_id}-ent-{idx}-{entity[0]}",
                                 use_container_width=True):
                        st.session_state.ranked_articles_dict = graph_handler.find_similar_articles_by_entity(
                            article_id, entity[0])
                        article_ids_to_display = list(st.session_state.ranked_articles_dict.keys())
                        st.rerun()

        # Themes (inline chips)
        if article.get("themes"):
            st.markdown("**Themes:**", help="Detected themes")
            th_cols = st.columns(min(len(article["themes"]), 3))
            for idx, theme in enumerate(article["themes"]):
                with th_cols[idx % 3]:
                    if st.button(theme[0],
                                 key=f"{article_id}-theme-{idx}-{theme[0]}",
                                 use_container_width=True):
                        st.session_state.ranked_articles_dict = graph_handler.find_similar_articles_by_theme(article_id,
                                                                                                             theme[0])
                        article_ids_to_display = list(st.session_state.ranked_articles_dict.keys())
                        st.rerun()

        # Feedback (compact row)
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        reaction_options = [("❤️", "love"), ("👍", "like"), ("👎", "dislike")]

        for icon, label in reaction_options:
            with {"love": c1, "like": c2, "dislike": c3}[label]:
                is_selected = article["reaction"] == label
                if st.button(icon,
                             key=f"{article_id}_{label}{'_sel' if is_selected else ''}",
                             type="primary" if is_selected else "secondary"):
                    update_feedbacks.update_reaction(
                        article["url"],
                        "skipped" if is_selected else label,
                        feedback_db,
                        graph_handler,
                    )
                    article["reaction"] = "skipped" if is_selected else label
                    st.rerun()

        with c4:
            is_noted = article["note"] != "skipped"
            if st.button("📝 Note",
                         key=f"note_btn_{article_id}",
                         type="primary" if is_noted else "secondary"):
                st.session_state.note_state[article_id] = True

        # Note editor (only expands when active)
        if st.session_state.note_state.get(article_id, False):
            note = article["note"] if article["note"] != "skipped" else ""
            note_text = st.text_area("Note:", value=note, key=f"note_text_{article_id}")
            if st.button("💾 Save", key=f"save_note_{article_id}"):
                st.session_state.note_state[article_id] = False
                article["note"] = note_text
                update_feedbacks.update_note(article["url"], note_text, feedback_db)
                st.rerun()
        st.write("")

st.write("")  # for empty line to add space between widgets

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    if st.button("⬅ Prev") and st.session_state.current_page > 1:
        st.session_state.current_page -= 1

with col2:
    col1_end, col2_end, col3_end = st.columns([1, 2, 1])

    with col2_end:
        st.write(f"Page {st.session_state.current_page} of {total_pages}")

    if st.button("Delete and refetch today articles"):
        delete_articles.delete_today_articles(articles_db, graph_handler, st.session_state.ranked_articles_dict.keys())
        # articles_db.delete_today_articles()
        # TODO
        # graph_handler.delete_today_nodes(st.session_state.ranked_articles_dict.keys())
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

with col3:
    if st.button("Next ➡") and st.session_state.current_page < total_pages:
        st.session_state.current_page += 1
