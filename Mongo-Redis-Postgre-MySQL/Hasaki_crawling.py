# import links
import requests
from bs4 import BeautifulSoup
import numpy as np
import pymongo
import redis
import psycopg2
import mysql.connector
import os
import time
import json

# MongoDB connection details
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongodb:27017/")
MONGO_DATABASE = "hasaki_database"
MONGO_COLLECTION = "hasaki_items"

# Redis connection details
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))

# PostgreSQL connection details
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "postgres")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", 5432))
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "hasaki_db")

# MySQL connection details
MYSQL_HOST = os.environ.get("MYSQL_HOST", "mysql")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", 3306))
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "hasaki_db")
MYSQL_USER = os.environ.get("MYSQL_USER", "hasaki")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "hasaki")


def connect_mongodb():
    """Connects to MongoDB and returns the collection."""
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            client = pymongo.MongoClient(MONGO_URI)
            # Check connection
            client.admin.command('ping')
            print("Connected to MongoDB successfully!")
            db = client[MONGO_DATABASE]
            collection = db[MONGO_COLLECTION]
            return collection
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Failed to connect to MongoDB (attempt {attempt+1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to MongoDB after {max_retries} attempts: {e}")
                raise


def connect_redis():
    """Connects to Redis and returns the client."""
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
            # Check connection
            client.ping()
            print("Connected to Redis successfully!")
            return client
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Failed to connect to Redis (attempt {attempt+1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to Redis after {max_retries} attempts: {e}")
                raise


def connect_postgres():
    """Connects to PostgreSQL and returns the connection."""
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                dbname=POSTGRES_DB
            )
            
            # Create table if it doesn't exist
            with conn.cursor() as cur:
                cur.execute('''
                CREATE TABLE IF NOT EXISTS hasaki_items (
                    id SERIAL PRIMARY KEY,
                    item_name TEXT NOT NULL,
                    description TEXT,
                    new_price TEXT,
                    discount_percent TEXT,
                    old_price TEXT,
                    link_page TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                conn.commit()
            
            print("Connected to PostgreSQL successfully!")
            return conn
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Failed to connect to PostgreSQL (attempt {attempt+1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to PostgreSQL after {max_retries} attempts: {e}")
                raise


def connect_mysql():
    """Connects to MySQL and returns the connection."""
    max_retries = 5
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            
            # Create table if it doesn't exist
            cursor = conn.cursor()
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS hasaki_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                item_name TEXT NOT NULL,
                description TEXT,
                new_price TEXT,
                discount_percent TEXT,
                old_price TEXT,
                link_page TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()
            cursor.close()
            
            print("Connected to MySQL successfully!")
            return conn
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Failed to connect to MySQL (attempt {attempt+1}/{max_retries}): {e}")
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"Failed to connect to MySQL after {max_retries} attempts: {e}")
                raise


def insert_to_mongodb(item_data, collection):
    """Inserts item data into MongoDB."""
    try:
        collection.insert_one(item_data)
        print("Data inserted into MongoDB successfully.")
    except Exception as e:
        print(f"Error inserting data into MongoDB: {e}")


# def cache_in_redis(item_data, redis_client):
#     """Caches item data in Redis using item name as key."""
#     try:
#         key = f"hasaki:{item_data['item_name']}"
#         # Store data as JSON string
#         redis_client.set(key, json.dumps(item_data))
#         # Set expiration time (e.g., 1 hour)
#         redis_client.expire(key, 3600)
#         print(f"Data cached in Redis: {key}")
#     except Exception as e:
#         print(f"Error caching data in Redis: {e}")

def cache_in_redis(item_data, redis_client):
    """Caches item data in Redis using item name as key."""
    try:
        key = f"hasaki:{item_data['item_name']}"
        
        # Chuyển đổi dữ liệu để đảm bảo có thể serialize JSON
        def json_serializable(obj):
            if isinstance(obj, dict):
                return {k: json_serializable(v) for k, v in obj.items()}
            elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                return [json_serializable(i) for i in obj]
            elif hasattr(obj, '__str__'):
                return str(obj)
            else:
                return obj
        
        redis_data = json_serializable(item_data)
        
        # Store data as JSON string
        redis_client.set(key, json.dumps(redis_data))
        # Set expiration time (e.g., 1 hour)
        redis_client.expire(key, 3600)
        print(f"Data cached in Redis: {key}")
    except Exception as e:
        print(f"Error caching data in Redis: {e}")


def insert_to_postgres(item_data, pg_conn):
    """Inserts item data into PostgreSQL."""
    try:
        with pg_conn.cursor() as cur:
            cur.execute('''
            INSERT INTO hasaki_items 
            (item_name, description, new_price, discount_percent, old_price, link_page)
            VALUES (%s, %s, %s, %s, %s, %s)
            ''', (
                item_data['item_name'],
                item_data['description'],
                item_data['new_price'],
                item_data['discount_percent'],
                item_data['old_price'],
                item_data['link_page']
            ))
            pg_conn.commit()
        print("Data inserted into PostgreSQL successfully.")
    except Exception as e:
        print(f"Error inserting data into PostgreSQL: {e}")


def insert_to_mysql(item_data, mysql_conn):
    """Inserts item data into MySQL."""
    try:
        cursor = mysql_conn.cursor()
        cursor.execute('''
        INSERT INTO hasaki_items 
        (item_name, description, new_price, discount_percent, old_price, link_page)
        VALUES (%s, %s, %s, %s, %s, %s)
        ''', (
            item_data['item_name'],
            item_data['description'],
            item_data['new_price'],
            item_data['discount_percent'],
            item_data['old_price'],
            item_data['link_page']
        ))
        mysql_conn.commit()
        cursor.close()
        print("Data inserted into MySQL successfully.")
    except Exception as e:
        print(f"Error inserting data into MySQL: {e}")


def get_links_from_hasaki(link):
    list_links = []
    for num in range(1, 190):  # Reduced range for testing, change back to (0, 190) for full crawl
        list_links.append(link + f'?p={num}')
    return list_links


path = 'https://hasaki.vn/danh-muc/suc-khoe-lam-dep-c3.html'
link_lists = get_links_from_hasaki(path)


def get_detailed_info(idx, lists, f, mongo_collection, redis_client, pg_conn, mysql_conn):
    print('counter :', idx)
    li = lists[idx]
    print("link:", li)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        html_doc = requests.get(li, headers=headers, timeout=30)
        html_doc.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(html_doc.content, 'html.parser')
        # get new price, discount, old price.
        block_price = soup.find_all('div', {'class': 'width_common block_price space_bottom_3'})
        # get name
        name_lists = soup.find_all('div', {'class': 'width_common txt_color_1 space_bottom_3'})
        # get description
        vn_names_divs = soup.find_all('div', class_='vn_names')
        print("len block price:", len(block_price))
        str1 = ' '
        for block, item, des in zip(block_price, name_lists, vn_names_divs):
            new_price_element = block.find('strong', class_='item_giamoi txt_16')
            new_price = new_price_element.text.strip() if new_price_element else "not available"

            span_element_discount = block.find('span', class_='discount_percent2_deal')
            discount_percent = span_element_discount.text.strip() if span_element_discount else "not available"

            span_element_old_price = block.find('span', class_='item_giacu txt_12 right')
            old_price = span_element_old_price.text.strip() if span_element_old_price else "not available"

            item_name_element = item.find('strong')
            item_name = item_name_element.text.strip() if item_name_element else "not available"

            describe = des.text.strip()
            describe_before_comma = describe.split(',')[0].strip()

            str1 = f'{item_name}, {describe_before_comma}, {new_price}, {discount_percent}, {old_price}, \n'
            f.write(str1)

            # Prepare data for MongoDB
            item_data = {
                "item_name": item_name,
                "description": describe_before_comma,
                "new_price": new_price,
                "discount_percent": discount_percent,
                "old_price": old_price,
                "link_page": li  # Add the link page for reference
            }
            
            # Insert to all databases
            insert_to_mongodb(item_data, mongo_collection)
            cache_in_redis(item_data, redis_client)
            insert_to_postgres(item_data, pg_conn)
            insert_to_mysql(item_data, mysql_conn)

    except requests.exceptions.RequestException as e:
        print(f"Request error for link {li}: {e}")
    except AttributeError as e:
        print(f"AttributeError parsing link {li}: {e} - Likely structure change on website.")
    except Exception as e:
        print(f"An unexpected error occurred for link {li}: {e}")


print("link_lists:", len(link_lists))


def write_info_to_csv(lists):
    idx = 0
    f = open('dataset_hasaki.csv', 'w', encoding='utf-8-sig')
    header = "NSX, Description, New Price, Discount percent, Old Price, \n"
    f.write(header)

    # Wait for databases to be ready
    print("Waiting for databases to be ready...")
    time.sleep(5)  # Give containers time to start

    # Connect to all databases
    mongo_collection = connect_mongodb()
    redis_client = connect_redis()
    pg_conn = connect_postgres()
    mysql_conn = connect_mysql()

    while idx < len(lists):
        get_detailed_info(idx, lists, f, mongo_collection, redis_client, pg_conn, mysql_conn)
        idx += 1
        
    # Close connections
    f.close()
    pg_conn.close()  # Close PostgreSQL connection
    mysql_conn.close()  # Close MySQL connection
    
    print("CSV file 'dataset_hasaki.csv' created successfully.")
    print("Data scraping and database insertion completed.")


if __name__ == "__main__":
    print("Starting Hasaki scraper...")
    write_info_to_csv(link_lists)