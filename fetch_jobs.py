import requests
import json
import os
from datetime import datetime

APP_ID = os.environ.get("ADZUNA_APP_ID", "")
APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")

if not APP_ID or not APP_KEY:
    print("Error: ADZUNA_APP_ID and ADZUNA_APP_KEY must be set as GitHub Secrets")
    exit(1)

SEARCHES = [
    {"what": "marketing analyst", "where": "Montreal"},
    {"what": "CRM marketing", "where": "Montreal"},
    {"what": "data analyst marketing", "where": "Montreal"},
    {"what": "market research analyst", "where": "Montreal"},
    {"what": "digital marketing", "where": "Montreal"},
    {"what": "gaming marketing", "where": "Canada"},
    {"what": "marketing coordinator", "where": "Montreal"},
    {"what": "business analyst marketing", "where": "Montreal"},
]

def fetch_jobs(what, where):
    url = "https://api.adzuna.com/v1/api/jobs/ca/search/1"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 8,
        "what": what,
        "where": where,
        "sort_by": "date",
        "distance": 30,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        print(f"  '{what}' in {where}: {len(results)} results")
        return results
    except Exception as e:
        print(f"  Error '{what}': {e}")
        return []

all_jobs = []
seen_ids = set()

for search in SEARCHES:
    jobs = fetch_jobs(search["what"], search["where"])
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

print(f"Total: {len(all_jobs)} unique jobs")

output = {
    "updated": datetime.utcnow().isoformat() + "Z",
    "count": len(all_jobs),
    "jobs": all_jobs
}

os.makedirs("data", exist_ok=True)
with open("data/jobs.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Saved to data/jobs.json")
