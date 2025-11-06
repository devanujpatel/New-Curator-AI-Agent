def delete_today_articles(articles_db, graph_handler, ids):
    articles_db.delete_today_articles()
    graph_handler.delete_today_nodes(ids)

