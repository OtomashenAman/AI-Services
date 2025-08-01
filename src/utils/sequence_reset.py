from sqlalchemy import text

#  Sequence reset utility
def reset_qa_pairs_sequence(session):
    session.execute(text("""
        SELECT setval(
            'qa_pairs_id_seq',  -- make sure this is correct sequence name
            COALESCE((SELECT MAX(id) FROM qa_pairs), 1),
            true
        );
    """))