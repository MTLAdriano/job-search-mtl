import requests
import json
import os
from datetime import datetime
 
APP_ID = "ff7f670e"
APP_KEY = "5fa6082af9eccbf4a12075b18de5f493"
 
SEARCHES = [
    {"what": "CRM analyst marketing", "where": "Montreal", "category": "marketing-jobs"},
    {"what": "market intelligence data analyst", "where": "Montreal", "category": "marketing-jobs"},
    {"what": "player engagement gaming marketing", "where": "Montreal", "category": "marketing-jobs"},
    {"what": "marketing analyst entertainment gaming", "where": "Montreal", "category": "marketing-jobs"},
    {"what": "data analyst entertainment media", "where": "Montreal", "category": "it-jobs"},
]
 
def fetch_jobs(what, where, category):
    url = "https://api.adzuna.com/v1/api/jobs/ca/search/1"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 10,
        "what": what,
        "where": where,
        "category": category,
        "sort_by": "date",
        "content-type": "application/json"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("results", [])
    except Exception as e:
        print(f"Error fetching {what}: {e}")
        return []
 
all_jobs = []
seen_ids = set()
 
for search in SEARCHES:
    jobs = fetch_jobs(search["what"], search["where"], search["category"])
    for job in jobs:
        job_id = job.get("id", "")
        if job_id and job_id not in seen_ids:
            seen_ids.add(job_id)
            all_jobs.append({
                "id": job_id,
                "title": job.get("title", ""),
                "company": job.get("company", {}).get("display_name", ""),
                "location": job.get("location", {}).get("display_name", ""),
                "description": job.get("description", ""),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "url": job.get("redirect_url", ""),
                "created": job.get("created", ""),
                "category": job.get("category", {}).get("label", ""),
            })
 
output = {
    "updated": datetime.utcnow().isoformat() + "Z",
    "count": len(all_jobs),
    "jobs": all_jobs
}
 
os.makedirs("data", exist_ok=True)
with open("data/jobs.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
 
print(f"Saved {len(all_jobs)} jobs to data/jobs.json")
 

