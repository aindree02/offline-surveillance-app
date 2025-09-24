from bing_image_downloader import downloader
import os, shutil

base_dir = "known_faces"

# Celebrities and multiple search queries for more variety
celebrities_queries = {
    "elon_musk": ["elon musk", "elon musk portrait", "elon musk photoshoot"],
    "emma_watson": ["emma watson", "emma watson photoshoot", "emma watson red carpet"],
    "leonardo_dicaprio": ["leonardo dicaprio", "leonardo dicaprio young", "leonardo dicaprio photoshoot"],
    "shah_rukh_khan": ["shah rukh khan", "shahrukh khan young", "shahrukh khan photoshoot"],
    "taylor_swift": ["taylor swift", "taylor swift live performance", "taylor swift photoshoot"]
}

# Each query downloads ~15 images, so 3 queries → ~45-50 images
images_per_query = 30

for folder_name, queries in celebrities_queries.items():
    existing_path = os.path.join(base_dir, folder_name)

    for query in queries:
        print(f" Downloading {images_per_query} images for {folder_name} with query: {query}")
        downloader.download(query, limit=images_per_query,
                            output_dir='temp_downloads',
                            adult_filter_off=True,
                            force_replace=False,
                            timeout=60)

        # Move downloaded images to the correct known_faces folder
        temp_path = os.path.join('temp_downloads', query)
        if os.path.exists(temp_path):
            for img_file in os.listdir(temp_path):
                shutil.move(os.path.join(temp_path, img_file),
                            os.path.join(existing_path, img_file))

    print(f" Added ~50 new images for {folder_name}")

# Cleanup temp folder
if os.path.exists('temp_downloads'):
    shutil.rmtree('temp_downloads')
    print("🧹 Cleaned up temporary folder!")



