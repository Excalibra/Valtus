import json

def load_results_structure(json_file):
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "Socials": ["instagram", "facebook", "twitter"],
            "Work": ["linkedin", "glassdoor"],
            "GitHub": ["github", "gitlab"],
            "Other": []
        }

def categorize_url(url, category_map):
    url_lower = url.lower()
    for category, keywords in category_map.items():
        for kw in keywords:
            if kw in url_lower:
                return category
    return "Other"

def save_results(grouped_results, filename):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            for category, items in grouped_results.items():
                f.write(f"\n=== {category} ===\n")
                for item in items:
                    url = item.get("url", "")
                    title = item.get("title", "No Title")
                    desc = item.get("description", "")
                    f.write(f"{title}\n")
                    if desc:
                        f.write(f"  {desc}\n")
                    f.write(f"  {url}\n\n")
        print(f"Saved to {filename}")
    except Exception as e:
        print(f"Error saving: {e}")
