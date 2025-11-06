# from prefect import flow, task

# @flow()
def update_reaction(url, new_reaction, feedback_db, graph_handler):
    feedback_db.update_reaction(url, new_reaction)
    graph_handler.update_reaction(url, new_reaction)

# @flow()
def update_note(url, note_text, feedback_db):
    feedback_db.update_notes(url, note_text)

