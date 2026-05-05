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

def fetch_greenhouse(slug, company_name, filter_montreal=False, filter_keywords=None):
    try:
        r = requests.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true", headers=headers, timeout=10)
        if r.status_code == 200:
            jobs = r.json().get("jobs", [])
            if filter_montreal:
                jobs = [j for j in jobs if "montreal" in j.get("location",{}).get("name","").lower()]
            if filter_keywords:
                jobs = [j for j in jobs if any(k in j.get("title","").lower() for k in filter_keywords)]
            log(f"  {company_name} (Greenhouse/{slug}): {len(jobs)} offres")
            for job in jobs:
                add_job({"id": f"gh-{job.get('id','')}", "title": job.get("title",""), "company": company_name, "location": job.get("location",{}).get("name","Montreal"), "description": job.get("content","")[:500], "salary_min": None, "salary_max": None, "url": job.get("absolute_url",""), "created": job.get("updated_at",""), "category": "Gaming & Entertainment", "source": company_name})
        else:
            log(f"  {company_name} (Greenhouse/{slug}): {r.status_code}")
    except Exception as e:
        log(f"  {company_name} error: {e}")

def fetch_lever(slug, company_name, filter_montreal=False, filter_keywords=None):
    try:
        r = requests.get(f"https://api.lever.co/v0/postings/{slug}?mode=json", headers=headers, timeout=10)
        if r.status_code == 200:
            jobs = r.json() if isinstance(r.json(), list) else []
            if filter_montreal:
                jobs = [j for j in jobs if "montreal" in str(j.get("categories",{}).get("location","")).lower() or "montreal" in str(j.get("categories",{}).get("allLocations",[])).lower()]
            if filter_keywords:
                jobs = [j for j in jobs if any(k in j.get("text","").lower() for k in filter_keywords)]
            log(f"  {company_name} (Lever/{slug}): {len(jobs)} offres")
            for job in jobs:
                cats = job.get("categories", {})
                loc = cats.get("location", "")
                ts = job.get("createdAt", 0)
                created = datetime.utcfromtimestamp(ts/1000).isoformat()+"Z" if ts else ""
                add_job({"id": f"lv-{job.get('id','')}", "title": job.get("text",""), "company": company_name, "location": loc, "description": job.get("descriptionPlain","")[:500], "salary_min": None, "salary_max": None, "url": job.get("hostedUrl",""), "created": created, "category": "Gaming & Entertainment", "source": company_name})
        else:
            log(f"  {company_name} (Lever/{slug}): {r.status_code}")
    except Exception as e:
        log(f"  {company_name} error: {e}")

def fetch_smartrecruiters(slug, company_name, filter_montreal=False, filter_keywords=None):
    try:
        params = {"limit": 100}
        if filter_montreal:
            params["city"] = "Montreal"
        r = requests.get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings", params=params, headers=headers, timeout=10)
        if r.status_code == 200:
            jobs = r.json().get("content", [])
            if filter_keywords:
                jobs = [j for j in jobs if any(k in j.get("name","").lower() for k in filter_keywords)]
            log(f"  {company_name} (SmartRecruiters/{slug}): {len(jobs)} offres")
            for job in jobs:
                add_job({"id": f"sr-{job.get('id','')}", "title": job.get("name",""), "company": company_name, "location": f"{job.get('location',{}).get('city','')}, {job.get('location',{}).get('country','')}", "description": "", "salary_min": None, "salary_max": None, "url": f"https://careers.smartrecruiters.com/{slug}/{job.get('id','')}", "created": job.get("releasedDate",""), "category": "Gaming & Entertainment", "source": company_name})
        else:
            log(f"  {company_name} (SmartRecruiters/{slug}): {r.status_code}")
    except Exception as e:
        log(f"  {company_name} error: {e}")

def fetch_ashby(slug, company_name, filter_montreal=False, filter_keywords=None):
    try:
        r = requests.post("https://jobs.ashbyhq.com/api/non-user-graphql",
            json={"operationName": "ApiJobBoardWithTeams", "variables": {"organizationHostedJobsPageName": slug}, "query": "query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) { jobBoard: jobBoardWithTeams(organizationHostedJobsPageName: $organizationHostedJobsPageName) { jobPostings { id title locationName isListed } } }"},
            headers={**headers, "Content-Type": "application/json"}, timeout=15)
        if r.status_code == 200:
            jobs = r.json().get("data",{}).get("jobBoard",{}).get("jobPostings",[])
            jobs = [j for j in jobs if j.get("isListed")]
            if filter_montreal:
                jobs = [j for j in jobs if "montreal" in str(j.get("locationName","")).lower()]
            if filter_keywords:
                jobs = [j for j in jobs if any(k in j.get("title","").lower() for k in filter_keywords)]
            log(f"  {company_name} (Ashby/{slug}): {len(jobs)} offres")
            for job in jobs:
                add_job({"id": f"ash-{job.get('id','')}", "title": job.get("title",""), "company": company_name, "location": job.get("locationName","Montreal"), "description": "", "salary_min": None, "salary_max": None, "url": f"https://jobs.ashbyhq.com/{slug}/{job.get('id','')}", "created": datetime.utcnow().isoformat()+"Z", "category": "Entertainment", "source": company_name})
        else:
            log(f"  {company_name} (Ashby/{slug}): {r.status_code}")
    except Exception as e:
        log(f"  {company_name} error: {e}")

# ============================================================
# GAMING & ENTERTAINMENT — MONTREAL (TOUTES LES OFFRES)
# ============================================================
log("\n=== GAMING & ENTERTAINMENT - MONTREAL ===")

# Ubisoft — Workday via SmartRecruiters
log("\n[1] Ubisoft...")
fetch_smartrecruiters("Ubisoft", "Ubisoft Montreal", filter_montreal=True)
# Fallback Greenhouse
fetch_greenhouse("ubisoft", "Ubisoft Montreal", filter_montreal=True)

# Behaviour Interactive
log("\n[2] Behaviour Interactive...")
fetch_smartrecruiters("BehaviourInteractive", "Behaviour Interactive", filter_montreal=True)
fetch_greenhouse("behaviour-interactive", "Behaviour Interactive", filter_montreal=True)
fetch_lever("behaviour", "Behaviour Interactive", filter_montreal=True)

# EA Montreal
log("\n[3] EA Montreal...")
fetch_greenhouse("ea", "EA Montreal", filter_montreal=True)
fetch_lever("ea", "EA Montreal", filter_montreal=True)
fetch_smartrecruiters("ElectronicArts", "EA Montreal", filter_montreal=True)

# Gameloft
log("\n[4] Gameloft...")
fetch_smartrecruiters("Gameloft", "Gameloft Montreal", filter_montreal=True)
fetch_greenhouse("gameloft-montreal", "Gameloft Montreal", filter_montreal=True)

# WB Games Montreal
log("\n[5] WB Games Montreal...")
fetch_greenhouse("warnermediagames", "WB Games Montreal", filter_montreal=True)
fetch_lever("warnermedia", "WB Games Montreal", filter_montreal=True)
fetch_smartrecruiters("WarnerMediaGames", "WB Games Montreal", filter_montreal=True)

# Keywords Studios
log("\n[6] Keywords Studios...")
for slug in ["keywordsgroup", "keywords-group", "keywordsintl", "keywordsstudiosgroup"]:
    fetch_greenhouse(slug, "Keywords Studios", filter_montreal=False)

# ============================================================
# ENTERTAINMENT & CREATIVE — MONTREAL
# ============================================================
log("\n=== ENTERTAINMENT & CREATIVE ===")

# Cirque du Soleil
log("\n[7] Cirque du Soleil...")
fetch_greenhouse("cirquedusoleil", "Cirque du Soleil", filter_montreal=False)
fetch_lever("cirquedusoleil", "Cirque du Soleil", filter_montreal=False)
fetch_smartrecruiters("CirqueDuSoleil", "Cirque du Soleil", filter_montreal=False)
fetch_ashby("cirque-du-soleil", "Cirque du Soleil", filter_montreal=False)

# Moment Factory
log("\n[8] Moment Factory...")
fetch_ashby("momentfactory", "Moment Factory", filter_montreal=False)
fetch_greenhouse("moment-factory", "Moment Factory", filter_montreal=False)
fetch_lever("momentfactory", "Moment Factory", filter_montreal=False)

# Framestore
log("\n[9] Framestore...")
fetch_greenhouse("framestore", "Framestore", filter_montreal=True)
fetch_lever("framestore", "Framestore", filter_montreal=True)
fetch_smartrecruiters("Framestore", "Framestore", filter_montreal=True)

# Rodeo FX
log("\n[10] Rodeo FX...")
fetch_greenhouse("rodeofx", "Rodeo FX", filter_montreal=False)
fetch_lever("rodeofx", "Rodeo FX", filter_montreal=False)
fetch_smartrecruiters("RodeoFX", "Rodeo FX", filter_montreal=False)
fetch_ashby("rodeo-fx", "Rodeo FX", filter_montreal=False)

# ============================================================
# MEDIA & AGENCES — MONTREAL
# ============================================================
log("\n=== MEDIA & AGENCES ===")

# Radio-Canada / CBC
log("\n[11] Radio-Canada...")
fetch_greenhouse("radio-canada", "Radio-Canada", filter_montreal=True)
fetch_lever("radiocanada", "Radio-Canada", filter_montreal=True)
fetch_smartrecruiters("RadioCanada", "Radio-Canada", filter_montreal=True)
fetch_ashby("radio-canada", "Radio-Canada", filter_montreal=True)

# TVA / Quebecor
log("\n[12] TVA / Quebecor...")
fetch_greenhouse("quebecor", "TVA / Quebecor", filter_montreal=True)
fetch_lever("quebecor", "TVA / Quebecor", filter_montreal=True)
fetch_smartrecruiters("Quebecor", "TVA / Quebecor", filter_montreal=True)

# Sid Lee
log("\n[13] Sid Lee...")
fetch_greenhouse("sidlee", "Sid Lee", filter_montreal=True)
fetch_lever("sidlee", "Sid Lee", filter_montreal=True)
fetch_smartrecruiters("SidLee", "Sid Lee", filter_montreal=True)
fetch_ashby("sid-lee", "Sid Lee", filter_montreal=True)

# lg2
log("\n[14] lg2...")
fetch_greenhouse("lg2", "lg2", filter_montreal=True)
fetch_lever("lg2agency", "lg2", filter_montreal=True)
fetch_smartrecruiters("lg2", "lg2", filter_montreal=True)
fetch_ashby("lg2", "lg2", filter_montreal=True)

# ============================================================
# THE MUSE — backup
# ============================================================
log("\n=== THE MUSE (backup) ===")
kw_muse = ["marketing","crm","data analyst","market intelligence","brand","digital marketing","media","communications"]
for s in [{"category": "Marketing and PR", "location": "Canada"}, {"category": "Data and Analytics", "location": "Canada"}]:
    try:
        r = requests.get("https://www.themuse.com/api/public/jobs", params={"category": s["category"], "location": s["location"], "page": 0}, headers=headers, timeout=15)
        results = r.json().get("results", [])
        relevant = [j for j in results if any(k in j.get("name","").lower() for k in kw_muse)]
        log(f"  The Muse '{s['category']}': {len(results)} total, {len(relevant)} relevant")
        for job in relevant:
            loc = ", ".join([l.get("name","") for l in job.get("locations", [])])
            add_job({"id": "muse-"+str(job.get("id","")), "title": job.get("name",""), "company": job.get("company",{}).get("name",""), "location": loc, "description": job.get("contents","")[:500], "salary_min": None, "salary_max": None, "url": job.get("refs",{}).get("landing_page",""), "created": job.get("publication_date",""), "category": s["category"], "source": "The Muse"})
    except Exception as e:
        log(f"  The Muse error: {e}")

# ============================================================
# BUSINESS FRANCE VIE
# ============================================================
log("\n=== BUSINESS FRANCE VIE ===")
for city in ["Montreal", "New+York"]:
    try:
        r = requests.get(f"https://mon-vie-via.businessfrance.fr/offres/recherche?villeDestination={city}", headers=headers, timeout=15)
        log(f"  VIE {city}: {r.status_code}, {len(r.text)} chars")
        titles = re.findall(r'class="offer-title[^"]*"[^>]*>([^<]+)<', r.text)
        companies = re.findall(r'class="offer-company[^"]*"[^>]*>([^<]+)<', r.text)
        links = re.findall(r'href="(/offres/detail/[^"]+)"', r.text)
        log(f"  VIE {city}: {len(titles)} offres trouvees")
        for i, title in enumerate(titles):
            co = companies[i] if i < len(companies) else ""
            link = "https://mon-vie-via.businessfrance.fr" + links[i] if i < len(links) else "https://mon-vie-via.businessfrance.fr"
            add_job({"id": f"vie-{city}-{i}", "title": title.strip(), "company": co.strip(), "location": city.replace("+", " "), "description": "", "salary_min": None, "salary_max": None, "url": link, "created": datetime.utcnow().isoformat()+"Z", "category": "VIE", "source": "Business France VIE"})
    except Exception as e:
        log(f"  VIE {city} error: {e}")

# ============================================================
# ADZUNA
# ============================================================
APP_ID = os.environ.get("ADZUNA_APP_ID", "")
APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
if APP_ID and APP_KEY:
    log("\n=== ADZUNA ===")
    for s in [{"what": "marketing analyst", "where": "Montreal"}, {"what": "CRM", "where": "Montreal"}, {"what": "data analyst", "where": "Montreal"}]:
        try:
            r = requests.get("https://api.adzuna.com/v1/api/jobs/ca/search/1", params={"app_id": APP_ID, "app_key": APP_KEY, "results_per_page": 10, "what": s["what"], "where": s["where"]}, headers=headers, timeout=15)
            if r.status_code == 200:
                results = r.json().get("results", [])
                log(f"  Adzuna '{s['what']}': {len(results)}")
                for job in results:
                    add_job({"id": "az-"+str(job.get("id","")), "title": job.get("title",""), "company": job.get("company",{}).get("display_name",""), "location": job.get("location",{}).get("display_name",""), "description": job.get("description",""), "salary_min": job.get("salary_min"), "salary_max": job.get("salary_max"), "url": job.get("redirect_url",""), "created": job.get("created",""), "category": "Marketing", "source": "Adzuna"})
        except Exception as e:
            log(f"  Adzuna error: {e}")

# ============================================================
# SAVE
# ============================================================
log(f"\n{'='*50}")
log(f"Total: {len(all_jobs)} offres uniques")
all_jobs.sort(key=lambda j: j.get("created","") or "", reverse=True)
os.makedirs("data", exist_ok=True)
with open("data/jobs.json", "w", encoding="utf-8") as f:
    json.dump({"updated": datetime.utcnow().isoformat()+"Z", "count": len(all_jobs), "jobs": all_jobs}, f, ensure_ascii=False, indent=2)
log(f"Saved to data/jobs.json")
