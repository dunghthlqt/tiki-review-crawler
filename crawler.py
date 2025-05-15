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
    base_url = "https://tiki.vn/api/v2/reviews"
    headers = {
        'User-Agent': UserAgent().random,
        'Accept': 'application/json',
    }
    params = {
        'product_id': product_id,
        'page': 1,
        'sort': 'score|desc'
    }
    
    session = requests.Session()
    
    all_reviews = []
    
    while True:
        try:
            response = session.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            reviews = data.get('data', [])
            if not reviews:
                break
                
            all_reviews.extend(reviews)
            
            paging = data.get('paging', {})
            current_page = paging.get('current_page', 1)
            last_page = paging.get('last_page', 1)
            
            if current_page >= last_page:
                break
                
            params['page'] += 1
            time.sleep(random.uniform(1, 3))
            
        except requests.RequestException as e:
            print(f"Lỗi khi gọi API tại trang {params['page']} cho product_id {product_id}: {e}")
            break
    
    return {'data': all_reviews}

input_file = 'input.csv'
output_file = 'output.csv'

try:
    df = pd.read_csv(input_file, encoding='utf-8')
    # Lọc bỏ URL trùng lặp và chuyển thành danh sách
    urls = list(dict.fromkeys(df['URL'].tolist()))
    print(f"Tổng số URL ban đầu: {len(df['URL'])}")
    print(f"Tổng số URL sau khi lọc trùng: {len(urls)}")
except Exception as e:
    print(f"Lỗi khi đọc file CSV: {e}")
    exit()

all_reviews = []
existing_reviews = set()  # Tập hợp để theo dõi các bộ (rating, cleaned_content) đã tồn tại

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
                # Kiểm tra xem cặp (rating, cleaned_content) đã tồn tại chưa
                review_tuple = (rating, cleaned_content)
                if review_tuple not in existing_reviews:
                    all_reviews.append({
                        'Sao': rating,
                        'Nội dung': cleaned_content
                    })
                    existing_reviews.add(review_tuple)
                    print(f"- Nội dung: {cleaned_content}")
                    print(f"  Sao: {rating}")
                else:
                    print(f"- Đánh giá trùng lặp bị bỏ qua: {cleaned_content} (Sao: {rating})")
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