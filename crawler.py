import re
import requests
import csv
import pandas as pd
from fake_useragent import UserAgent
import time
import random
import os

# Ép Python sử dụng UTF-8 cho console
os.environ["PYTHONIOENCODING"] = "utf-8"

# Thêm biến để theo dõi thời gian
start_time = time.time()

def extract_product_id(url):
    match = re.search(r'p(\d+)\.html', url)
    if match:
        return match.group(1)
    return None

def get_reviews(product_id):
    url = f"https://tiki.vn/api/v2/reviews?product_id={product_id}"
    headers = {
        'User-Agent': UserAgent().random,
        'Accept': 'application/json',
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Lỗi khi gọi API đánh giá cho product_id {product_id}: {e}")
        return None

input_file = 'input.csv'
output_file = 'output.csv'

try:
    df = pd.read_csv(input_file, encoding='utf-8')
    # Lọc bỏ URL trùng lặp và chuyển thành danh sách
    urls = list(dict.fromkeys(df['URL'].tolist()))  # Giữ nguyên thứ tự, loại bỏ trùng lặp
    print(f"Tổng số URL ban đầu: {len(df['URL'])}")
    print(f"Tổng số URL sau khi lọc trùng: {len(urls)}")
except Exception as e:
    print(f"Lỗi khi đọc file CSV: {e}")
    exit()

all_reviews = []

LINKS_PER_BREAK = 5
links_processed = 0
total_urls = len(urls)

# Ước tính thời gian trung bình cho mỗi URL
avg_wait_time = (15 + 20) / 2
avg_break_time = (60 + 180) / 2
estimated_time_per_url = avg_wait_time + (avg_break_time / LINKS_PER_BREAK)

for url in urls:
    print(f"\nXử lý URL: {url} ({links_processed + 1}/{total_urls})")
    
    product_id = extract_product_id(url)
    if not product_id:
        print(f"Không tìm thấy ID sản phẩm trong URL: {url}")
        continue
    
    print(f"Product ID: {product_id}")
    
    reviews_data = get_reviews(product_id)
    if reviews_data and 'data' in reviews_data and reviews_data['data']:
        print(f"Đã tìm thấy {len(reviews_data['data'])} đánh giá.")
        for review in reviews_data['data']:
            rating = review.get('rating', 'N/A')
            content = review.get('content', 'N/A')
            if rating != 'N/A' and content != 'N/A' and content.strip() != '':
                cleaned_content = content.replace('\r\n', '. ').replace('\n', '. ').replace('\r', '. ')
                all_reviews.append({
                    'Sao': rating,
                    'Nội dung': cleaned_content
                })
                print(f"- Nội dung: {cleaned_content}")
                print(f"  Sao: {rating}")
    else:
        print(f"Không có đánh giá nào cho product_id {product_id} hoặc lỗi API.")
    
    links_processed += 1
    
    # Hiển thị thời gian đã trôi qua và ước tính thời gian còn lại
    elapsed_time = time.time() - start_time
    remaining_urls = total_urls - links_processed
    estimated_remaining_time = remaining_urls * estimated_time_per_url
    
    print(f"Thời gian đã trôi qua: {elapsed_time/60:.2f} phút")
    print(f"Ước tính thời gian còn lại: {estimated_remaining_time/60:.2f} phút")
    
    # Thời gian chờ ngẫu nhiên từ 15 đến 20 giây
    wait_time = random.uniform(15, 20)
    print(f"Chờ {wait_time:.2f} giây trước khi xử lý link tiếp theo...")
    time.sleep(wait_time)
    
    # Kiểm tra xem có cần nghỉ sau khi xử lý đủ số link không
    if links_processed % LINKS_PER_BREAK == 0 and links_processed < len(urls):
        break_time = random.uniform(60, 180)
        print(f"Đã xử lý {links_processed} link. Nghỉ {break_time/60:.2f} phút...")
        time.sleep(break_time)

if all_reviews:
    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['Sao', 'Nội dung'])
            writer.writeheader()
            writer.writerows(all_reviews)
        print(f"\nĐã ghi {len(all_reviews)} đánh giá vào file {output_file}")
    except Exception as e:
        print(f"Lỗi khi ghi file CSV: {e}")
else:
    print("\nKhông có đánh giá nào để ghi vào file CSV.")

# Hiển thị thời gian hoàn tất cuối cùng
total_time = time.time() - start_time
print(f"\nCông việc hoàn tất! Tổng thời gian: {total_time/60:.2f} phút")