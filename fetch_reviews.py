import argparse
import os
import re
import pandas as pd
from bs4 import BeautifulSoup
import emoji
from google_play_scraper import Sort, reviews

def clean_text(text):
    if not isinstance(text, str):
        return ""
    
    # 1. Remove HTML tags
    text = BeautifulSoup(text, "html.parser").get_text()
    
    # 2. Remove URLs
    text = re.sub(r'http\S+|www\.\S+', '', text)
    
    # 3. Remove Emojis
    text = emoji.replace_emoji(text, replace='')
    
    # 4. Remove unnecessary special characters (keep punctuation, alphanumeric, spaces)
    # We'll allow standard punctuation like , . ! ? ' " and alphanumeric.
    text = re.sub(r'[^A-Za-z0-9\s\.,!\?\'\"]+', ' ', text)
    
    # 5. Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def main():
    parser = argparse.ArgumentParser(description="Fetch and preprocess Google Play Store reviews for Blinkit.")
    parser.add_argument('--count', type=int, default=3000, help='Number of reviews to fetch (approximate)')
    parser.add_argument('--output', type=str, default='blinkit_reviews.csv', help='Output CSV file name')
    parser.add_argument('--app_id', type=str, default='com.grofers.customerapp', help='Google Play App ID')
    parser.add_argument('--lang', type=str, default='en', help='Language code')
    parser.add_argument('--country', type=str, default='in', help='Country code')
    args = parser.parse_args()

    print(f"Fetching approximately {args.count} reviews for {args.app_id}...")
    
    # Fetch reviews
    result, continuation_token = reviews(
        args.app_id,
        lang=args.lang,
        country=args.country,
        sort=Sort.NEWEST,
        count=args.count
    )
    
    if not result:
        print("No reviews fetched.")
        return

    print(f"Fetched {len(result)} reviews. Preprocessing...")
    
    # Convert to DataFrame
    df = pd.DataFrame(result)
    
    # Required fields mapping based on what google-play-scraper returns
    # google-play-scraper returns: reviewId, content, score, at, reviewCreatedVersion, replyContent, etc.
    
    # Select and rename columns
    columns_mapping = {
        'reviewId': 'Review ID',
        'content': 'Original Review Text',
        'score': 'Star Rating',
        'at': 'Review Date',
        'reviewCreatedVersion': 'App Version',
        'replyContent': 'Developer Reply'
    }
    
    # Keep only the columns we need, ignore if some are missing but they should be there
    available_cols = [col for col in columns_mapping.keys() if col in df.columns]
    df = df[available_cols].rename(columns=columns_mapping)
    
    # Ensure missing columns (like Developer Reply or App Version) are added if they didn't exist in result
    for target_col in columns_mapping.values():
        if target_col not in df.columns:
            df[target_col] = None

    # Remove duplicates
    initial_len = len(df)
    df.drop_duplicates(subset=['Review ID'], inplace=True)
    print(f"Dropped {initial_len - len(df)} duplicate reviews.")

    # Drop null reviews
    df.dropna(subset=['Original Review Text'], inplace=True)

    # Clean text
    df['Cleaned Review Text'] = df['Original Review Text'].apply(clean_text)

    # Filter out empty or very short reviews (<5 words)
    def word_count(text):
        if not text:
            return 0
        return len(text.split())

    df['word_count'] = df['Cleaned Review Text'].apply(word_count)
    df_filtered = df[df['word_count'] >= 5].copy()
    
    print(f"Dropped {len(df) - len(df_filtered)} reviews with fewer than 5 words.")
    
    # Drop the temporary word_count column
    df_filtered.drop(columns=['word_count'], inplace=True)
    
    # Reorder columns
    final_cols = [
        'Review ID', 
        'Original Review Text', 
        'Cleaned Review Text', 
        'Star Rating', 
        'Review Date', 
        'App Version', 
        'Developer Reply'
    ]
    df_filtered = df_filtered[final_cols]
    
    # Ensure the output directory exists
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(output_path, exist_ok=True)
    
    final_output_file = os.path.join(output_path, args.output)
    
    # Save to CSV
    df_filtered.to_csv(final_output_file, index=False, encoding='utf-8')
    
    print(f"Successfully saved {len(df_filtered)} cleaned reviews to {final_output_file}")

if __name__ == "__main__":
    main()
