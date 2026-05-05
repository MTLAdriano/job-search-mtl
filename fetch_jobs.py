import requests
import json
import os
import re
from datetime import datetime

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
all_jobs = []
seen_ids = set()

def add_job(job):
    jid = job.get("id", "")
    if jid and jid not in seen_ids:
        seen_ids.add(jid)
        all_jobs.append(job)

def log(msg):
    print(msg, flush=True)

keywords = ["marketing","crm","data","analyst","intelligence","coordinator","brand","insight","communication","player","media","content","strategy","digital"]

# ============================================================
# 1. THE MUSE API
# ============================================================
log("\n[1] The Muse API...")
MUSE_SEARCHES = [
    {"category": "Marketing and PR", "location": "Canada"},
    {"category": "Data and Analytics", "location": "Canada"},
    {"category": "Marketing and PR", "location": "New York City, NY"},
    {"category": "Data and Analytics", "location": "New York City, NY"},
]
for s in MUSE_SEARCHES:
    try:
        r = requests.get("https://www.themuse.com/api/public/jobs", params={"category": s["category"], "location": s["location"], "page": 0, "descending": "true"}, headers=headers, timeout=15)
        data = r.json()
        results = data.get("results", [])
        log(f"  The Muse '{s['category']}' in {s['location']}: {len(results)} results")
        for job in results:
            loc = ", ".join([l.get("name","") for l in job.get("locations", [])])
            add_job({"id": "muse-"+str(job.get("id","")), "title": job.get("name",""), "company": job.get("company",{}).get("name",""), "location": loc, "description": job.get("contents",""), "salary_min": None, "salary_max": None, "url": job.get("refs",{}).get("landing_page",""), "created": job.get("publication_date",""), "category": s["category"], "source": "The Muse"})
    except Exception as e:
        log(f"  The Muse error: {e}")

# ============================================================
# 2. BEHAVIOUR INTERACTIVE — Smartrecruiters
# ============================================================
log("\n[2] Behaviour Interactive (SmartRecruiters)...")
try:
    r = requests.get("https://api.smartrecruiters.com/v1/companies/BehaviourInteractive/postings", headers=headers, timeout=15)
    if r.status_code == 200:
        jobs = r.json().get("content", [])
        relevant = [j for j in jobs if any(k in j.get("name","").lower() for k in keywords)]
        log(f"  Behaviour: {len(jobs)} total, {len(relevant)} relevant")
        for job in relevant:
            add_job({"id": "bh-"+str(job.get("id","")), "title": job.get("name",""), "company": "Behaviour Interactive", "location": job.get("location",{}).get("city","Montreal"), "description": job.get("jobAd",{}).get("sections",{}).get("jobDescription",{}).get("text",""), "salary_min": None, "salary_max": None, "url": "https://www.smartrecruiters.com/BehaviourInteractive/"+str(job.get("id","")), "created": job.get("releasedDate",""), "category": "Gaming", "source": "Behaviour Interactive"})
    else:
        log(f"  Behaviour: {r.status_code}")
except Exception as e:
    log(f"  Behaviour error: {e}")

# ============================================================
# 3. UBISOFT — API careers officielle
# ============================================================
log("\n[3] Ubisoft careers...")
try:
    url = "https://www.ubisoft.com/api/v1/jobs"
    params = {"countries": "Canada", "pageSize": 100, "pageIndex": 0}
    r = requests.get(url, headers=headers, timeout=15)
    log(f"  Ubisoft API: {r.status_code}")
    if r.status_code != 200:
        # Try alternate endpoint
        r = requests.get("https://www.ubisoft.com/en-gb/company/careers/search?countries=Canada", headers=headers, timeout=15)
        log(f"  Ubisoft fallback: {r.status_code}, size: {len(r.text)}")
except Exception as e:
    log(f"  Ubisoft error: {e}")

# ============================================================
# 4. MOMENT FACTORY — Ashby ATS
# ============================================================
log("\n[4] Moment Factory (Ashby)...")
try:
    r = requests.get("https://jobs.ashbyhq.com/api/non-user-graphql", 
        json={"operationName": "ApiJobBoardWithTeams", "variables": {"organizationHostedJobsPageName": "momentfactory"}, "query": "query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) { jobBoard: jobBoardWithTeams(organizationHostedJobsPageName: $organizationHostedJobsPageName) { jobPostings { id title locationName employmentType isListed } } }"},
        headers={**headers, "Content-Type": "application/json"}, timeout=15)
    if r.status_code == 200:
        jobs = r.json().get("data",{}).get("jobBoard",{}).get("jobPostings",[])
        relevant = [j for j in jobs if j.get("isListed") and any(k in j.get("title","").lower() for k in keywords)]
        log(f"  Moment Factory: {len(jobs)} total, {len(relevant)} relevant")
        for job in relevant:
            add_job({"id": "mf-"+str(job.get("id","")), "title": job.get("title",""), "company": "Moment Factory", "location": job.get("locationName","Montreal"), "description": "", "salary_min": None, "salary_max": None, "url": f"https://jobs.ashbyhq.com/momentfactory/{job.get('id','')}", "created": datetime.utcnow().isoformat()+"Z", "category": "Entertainment", "source": "Moment Factory"})
    else:
        log(f"  Moment Factory: {r.status_code}")
except Exception as e:
    log(f"  Moment Factory error: {e}")

# ============================================================
# 5. GAMELOFT — site direct
# ============================================================
log("\n[5] Gameloft careers...")
try:
    r = requests.get("https://careers.gameloft.com/api/positions?location=Montreal", headers=headers, timeout=15)
    log(f"  Gameloft API: {r.status_code}")
    if r.status_code == 200:
        jobs = r.json() if isinstance(r.json(), list) else r.json().get("positions", r.json().get("jobs", []))
        relevant = [j for j in jobs if any(k in str(j.get("title",j.get("name",""))).lower() for k in keywords)]
        log(f"  Gameloft: {len(relevant)} relevant")
        for job in relevant:
            title = job.get("title", job.get("name",""))
            add_job({"id": "gl-"+str(job.get("id",title)), "title": title, "company": "Gameloft Montreal", "location": "Montreal", "description": job.get("description",""), "salary_min": None, "salary_max": None, "url": job.get("url", "https://careers.gameloft.com"), "created": job.get("date",""), "category": "Gaming", "source": "Gameloft"})
    else:
        log(f"  Gameloft: {r.status_code}")
except Exception as e:
    log(f"  Gameloft error: {e}")

# ============================================================
# 6. KEYWORDS STUDIOS — Greenhouse correct slug
# ============================================================
log("\n[6] Keywords Studios...")
for slug in ["keywords-studios", "keywordsstudios", "keywordsintl"]:
    try:
        r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", headers=headers, timeout=10)
        if r.status_code == 200:
            jobs = r.json().get("jobs", [])
            relevant = [j for j in jobs if any(k in j.get("title","").lower() for k in keywords)]
            log(f"  Keywords ({slug}): {len(jobs)} total, {len(relevant)} relevant")
            for job in relevant:
                add_job({"id": "kw-"+str(job.get("id","")), "title": job.get("title",""), "company": "Keywords Studios", "location": job.get("location",{}).get("name",""), "description": "", "salary_min": None, "salary_max": None, "url": job.get("absolute_url",""), "created": job.get("updated_at",""), "category": "Gaming", "source": "Keywords Studios"})
            break
        else:
            log(f"  Keywords ({slug}): {r.status_code}")
    except Exception as e:
        log(f"  Keywords error: {e}")

# ============================================================
# 7. BUSINESS FRANCE VIE — API correcte
# ============================================================
log("\n[7] Business France VIE...")
VIE_PARAMS = [
    {"villeDestination": "Montreal", "pays": "Canada"},
    {"villeDestination": "New York", "pays": "USA"},
]
for vp in VIE_PARAMS:
    try:
        # Try different API endpoints
        for endpoint in [
            f"https://mon-vie-via.businessfrance.fr/api/v1/offres?villeDestination={vp['villeDestination']}&limit=100",
            f"https://mon-vie-via.businessfrance.fr/api/offres?ville={vp['villeDestination']}&limit=100",
        ]:
            r = requests.get(endpoint, headers=headers, timeout=15)
            log(f"  VIE {vp['villeDestination']} ({endpoint[-50:]}): {r.status_code}")
            if r.status_code == 200:
                try:
                    data = r.json()
                    items = data if isinstance(data, list) else data.get("content", data.get("offres", data.get("items", [])))
                    log(f"  VIE {vp['villeDestination']}: {len(items)} offres")
                    for job in items:
                        title = job.get("intitule", job.get("titre", job.get("poste", "")))
                        co = job.get("entreprise", {})
                        if isinstance(co, dict): co = co.get("raisonSociale", co.get("nom", ""))
                        add_job({"id": "vie-"+str(job.get("id", job.get("reference", title))), "title": title, "company": str(co), "location": f"{vp['villeDestination']}", "description": job.get("descriptifMission", job.get("mission", "")), "salary_min": None, "salary_max": None, "url": f"https://mon-vie-via.businessfrance.fr/offres/detail/{job.get('id','')}", "created": job.get("datePublication",""), "category": "VIE", "source": "Business France VIE"})
                    break
                except: pass
    except Exception as e:
        log(f"  VIE error: {e}")

# ============================================================
# 8. ADZUNA
# ============================================================
APP_ID = os.environ.get("ADZUNA_APP_ID", "")
APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
if APP_ID and APP_KEY:
    log("\n[8] Adzuna...")
    for s in [{"what": "marketing analyst", "where": "Montreal"}, {"what": "CRM", "where": "Montreal"}]:
        try:
            r = requests.get("https://api.adzuna.com/v1/api/jobs/ca/search/1", params={"app_id": APP_ID, "app_key": APP_KEY, "results_per_page": 10, "what": s["what"], "where": s["where"]}, headers=headers, timeout=15)
            if r.status_code == 200:
                for job in r.json().get("results",[]):
                    add_job({"id": "az-"+str(job.get("id","")), "title": job.get("title",""), "company": job.get("company",{}).get("display_name",""), "location": job.get("location",{}).get("display_name",""), "description": job.get("description",""), "salary_min": job.get("salary_min"), "salary_max": job.get("salary_max"), "url": job.get("redirect_url",""), "created": job.get("created",""), "category": "Marketing", "source": "Adzuna"})
        except Exception as e:
            log(f"  Adzuna error: {e}")

# ============================================================
# SAVE
# ============================================================
log(f"\nTotal: {len(all_jobs)} jobs")
all_jobs.sort(key=lambda j: j.get("created","") or "", reverse=True)
os.makedirs("data", exist_ok=True)
with open("data/jobs.json", "w", encoding="utf-8") as f:
    json.dump({"updated": datetime.utcnow().isoformat()+"Z", "count": len(all_jobs), "jobs": all_jobs}, f, ensure_ascii=False, indent=2)
log(f"Saved to data/jobs.json")
