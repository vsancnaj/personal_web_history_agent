# (URLs + titles + timestamps)

# import libraries
import sqlite3
import numpy as np
np.float_ = np.float64
from pathlib import Path
from datetime import datetime, timedelta


PROJECT_DIR = Path("/Users/valesanchez/Documents/Cursor/nora")
DB_FILE = PROJECT_DIR / "data" / "history_copy.db"
CHROME_EPOCH = datetime(1601, 1, 1) # starting data from 1601

# if PROJECT_DIR.is_dir():
#     print(f"'{PROJECT_DIR}' is a directory.")
# else:
#     print(f"'{PROJECT_DIR}' is not a directory.")

# if DB_FILE.is_file():
#     print(f"'{DB_FILE}' is a file.")
# else:
#     print(f"'{DB_FILE}' is not a file.")

def convert_chrome_time_to_datetime(chrome_time: int) -> datetime:
    if chrome_time is None:
        return None
    return CHROME_EPOCH + timedelta(microseconds=chrome_time) # beginning point + duration

def convert_datetime_to_chrome(dt: datetime) -> int:
    difference = dt - CHROME_EPOCH
    return int(difference.total_seconds() * 1000000)


def get_history_data(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    start_chrome_time = convert_datetime_to_chrome(start_date)
    end_chrome_time = convert_datetime_to_chrome(end_date)
    
    conn = None
    data_for_langchain = []
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        query = f"""
            SELECT url, title, last_visit_time
            FROM urls
            WHERE last_visit_time BETWEEN {start_chrome_time} AND {end_chrome_time}
            ORDER BY last_visit_time DESC
        """# change this query to certain url history for confidential reasons
        
        cursor.execute(query)
        results = cursor.fetchall()

        
        for row in results:
            url, title, chrome_time = row
            legible_date = convert_chrome_time_to_datetime(chrome_time)
            
            # collection the urls and the relevant metadata
            data_for_langchain.append({
                "url": url,
                "title": title,
                "date": legible_date.isoformat()
            })
            
    except sqlite3.Error as e:
        print(f"Error from SQLite: {e}")
        if not DB_FILE.exists():
            print(f"ERROR: {DB_FILE} NOT FOUND! (Did you copy your Chrome History file?)")
    
    finally:
        if conn:
            conn.close()
    
    return data_for_langchain

if __name__ == "__main__":
    history_records = get_history_data('2025-09-01', '2025-11-01')
    
    print(f"Length of extracted records: {len(history_records)}")
    
    if history_records:
        print(f"First ingestion:\n{history_records[0]}")