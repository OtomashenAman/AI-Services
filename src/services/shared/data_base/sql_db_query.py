from . import settings
import pymysql
from urllib.parse import quote_plus
import logging



logger = logging.getLogger(__name__)

def get_database():
    """Establishes a connection to the MySQL database.
    Returns:
        pymysql.connections.Connection: A connection object to the MySQL database.
    """

    db = pymysql.connect(
    host=settings.MYSQL_DB_HOST,
    user=settings.MYSQL_DB_USER,
    password=settings.MYSQL_DB_PASSWORD,
    database=settings.MYSQL_DB_NAME,
    port=settings.MYSQL_DB_PORT,
    ssl={"fake_flag_to_enable_tls":True}
    )
    return db

def execute_query(query: str, params: dict = None):
    """
    Executes a SQL query against the MySQL database.

    Args:
        query (str): The SQL query to execute.
        params (dict, optional): Parameters to bind to the query.

    Returns:
        list: A list of rows returned by the query.
    """
    db = None
    try:
        db = get_database()
        cursor = db.cursor(pymysql.cursors.DictCursor)
        cursor.execute(query, params or {})
        result = cursor.fetchall()
        db.commit()
        return result
    except pymysql.MySQLError as e:
        logger.error(f"Error executing query: {e}")
        raise
    finally:
        if db:
            db.close()


