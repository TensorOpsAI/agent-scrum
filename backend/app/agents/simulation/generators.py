"""
Simulation Data Generators - Realistic fake data for non-dev board templates.

Each generator produces items that can be placed on a board as stories.
"""
import random
from typing import Optional


CANDIDATE_POOL = [
    {"name": "Sarah Chen", "experience": "8 years", "skills": ["Python", "ML", "AWS"], "education": "MS Computer Science, Stanford", "current_role": "Senior ML Engineer at DataCorp"},
    {"name": "James Martinez", "experience": "3 years", "skills": ["JavaScript", "React", "Node.js"], "education": "BS Software Engineering, UT Austin", "current_role": "Frontend Developer at WebCo"},
    {"name": "Priya Sharma", "experience": "12 years", "skills": ["Java", "Kubernetes", "System Design"], "education": "MS Computer Science, MIT", "current_role": "Staff Engineer at BigTech"},
    {"name": "Michael Johnson", "experience": "5 years", "skills": ["Go", "gRPC", "PostgreSQL"], "education": "BS Computer Science, Georgia Tech", "current_role": "Backend Engineer at FinanceApp"},
    {"name": "Emily Davis", "experience": "2 years", "skills": ["Python", "Django", "SQL"], "education": "Bootcamp Graduate, General Assembly", "current_role": "Junior Developer at StartupX"},
    {"name": "Alex Kim", "experience": "7 years", "skills": ["C++", "Rust", "Systems Programming"], "education": "PhD Computer Science, CMU", "current_role": "Systems Engineer at CloudInfra"},
    {"name": "Lisa Wang", "experience": "4 years", "skills": ["TypeScript", "GraphQL", "Docker"], "education": "BS Computer Science, UC Berkeley", "current_role": "Full Stack Developer at SaaSCo"},
    {"name": "David Brown", "experience": "10 years", "skills": ["Python", "Terraform", "CI/CD"], "education": "MS Information Systems, NYU", "current_role": "DevOps Lead at Enterprise Inc"},
    {"name": "Rachel Green", "experience": "6 years", "skills": ["Swift", "iOS", "UIKit", "SwiftUI"], "education": "BS Computer Science, UCLA", "current_role": "iOS Engineer at MobileFirst"},
    {"name": "Omar Hassan", "experience": "9 years", "skills": ["Scala", "Spark", "Kafka"], "education": "MS Data Science, Columbia", "current_role": "Data Platform Engineer at AnalyticsCo"},
    {"name": "Jennifer Lee", "experience": "1 year", "skills": ["HTML", "CSS", "JavaScript"], "education": "Self-taught", "current_role": "Intern at LocalAgency"},
    {"name": "Carlos Rodriguez", "experience": "15 years", "skills": ["Java", "Spring", "Microservices", "Architecture"], "education": "MS Software Engineering, Purdue", "current_role": "Principal Engineer at TechGiant"},
    {"name": "Natasha Ivanova", "experience": "6 years", "skills": ["Python", "TensorFlow", "NLP"], "education": "PhD Computational Linguistics, Edinburgh", "current_role": "NLP Researcher at AI Lab"},
    {"name": "Tyler Bennett", "experience": "4 years", "skills": ["Ruby", "Rails", "PostgreSQL"], "education": "BS Computer Science, Oregon State", "current_role": "Backend Developer at EcommCo"},
    {"name": "Aisha Patel", "experience": "8 years", "skills": ["Android", "Kotlin", "Firebase"], "education": "MS Mobile Computing, IIT", "current_role": "Senior Android Engineer at RideShare"},
]


LEAD_POOL = [
    {"company": "TechStart Inc.", "contact": "VP Engineering", "budget": "$50K-100K", "timeline": "Q2 2025", "need": "DevOps automation platform", "size": "50 employees"},
    {"company": "MegaCorp International", "contact": "CTO", "budget": "$500K+", "timeline": "Q3 2025", "need": "Enterprise data analytics suite", "size": "10,000+ employees"},
    {"company": "GreenEnergy Solutions", "contact": "Head of IT", "budget": "$100K-250K", "timeline": "Q1 2025", "need": "IoT monitoring dashboard", "size": "200 employees"},
    {"company": "FinanceFirst Bank", "contact": "CISO", "budget": "$200K-500K", "timeline": "Immediate", "need": "Compliance automation tool", "size": "5,000 employees"},
    {"company": "HealthTech Labs", "contact": "Product Director", "budget": "$75K-150K", "timeline": "Q2 2025", "need": "Patient portal modernization", "size": "300 employees"},
    {"company": "RetailMax Group", "contact": "VP Digital", "budget": "$150K-300K", "timeline": "Q4 2025", "need": "Omnichannel inventory system", "size": "2,000 employees"},
    {"company": "EduLearn Platform", "contact": "CEO", "budget": "$25K-50K", "timeline": "ASAP", "need": "LMS integration API", "size": "15 employees"},
    {"company": "AutoDrive Systems", "contact": "Engineering Director", "budget": "$1M+", "timeline": "Multi-year", "need": "Fleet management platform", "size": "500 employees"},
    {"company": "MediaStream Co.", "contact": "VP Product", "budget": "$100K-200K", "timeline": "Q1 2025", "need": "Content delivery optimization", "size": "150 employees"},
    {"company": "CloudSecure LLC", "contact": "Head of Engineering", "budget": "$50K-75K", "timeline": "Q2 2025", "need": "Zero-trust network solution", "size": "80 employees"},
    {"company": "DataMining Corp", "contact": "Chief Data Officer", "budget": "$300K-500K", "timeline": "Q3 2025", "need": "Real-time analytics pipeline", "size": "1,200 employees"},
    {"company": "SmartHome Devices", "contact": "CTO", "budget": "$75K-125K", "timeline": "Q2 2025", "need": "Device management platform", "size": "100 employees"},
    {"company": "LogiChain Solutions", "contact": "VP Operations", "budget": "$200K-400K", "timeline": "Q1 2025", "need": "Supply chain visibility tool", "size": "800 employees"},
    {"company": "CyberDefend Inc.", "contact": "CISO", "budget": "$150K-250K", "timeline": "Immediate", "need": "SOC automation platform", "size": "400 employees"},
    {"company": "BioPharm Research", "contact": "IT Director", "budget": "$500K-750K", "timeline": "Q4 2025", "need": "Lab data management system", "size": "3,000 employees"},
]


INCIDENT_POOL = [
    {"type": "SQL Injection", "severity": "High", "systems": ["Login API", "User DB"], "vector": "Malicious input in email field", "cvss": "7.8"},
    {"type": "Cross-Site Scripting (XSS)", "severity": "Medium", "systems": ["Web Dashboard"], "vector": "Unsanitized user input in comments", "cvss": "5.4"},
    {"type": "Ransomware Detection", "severity": "Critical", "systems": ["File Server", "Backup System"], "vector": "Phishing email with malicious attachment", "cvss": "9.8"},
    {"type": "Unauthorized Access", "severity": "High", "systems": ["Admin Panel", "IAM"], "vector": "Credential stuffing from leaked database", "cvss": "8.1"},
    {"type": "Data Exfiltration", "severity": "Critical", "systems": ["Customer DB", "API Gateway"], "vector": "Compromised service account", "cvss": "9.1"},
    {"type": "DDoS Attack", "severity": "High", "systems": ["Public API", "CDN"], "vector": "Volumetric UDP flood from botnet", "cvss": "7.5"},
    {"type": "Privilege Escalation", "severity": "High", "systems": ["Linux Servers", "Container Runtime"], "vector": "Kernel vulnerability CVE-2024-XXXX", "cvss": "7.8"},
    {"type": "Insecure API Endpoint", "severity": "Medium", "systems": ["REST API v2"], "vector": "Missing authentication on internal endpoint", "cvss": "6.5"},
    {"type": "Certificate Expiry", "severity": "Low", "systems": ["TLS Certificates", "Load Balancer"], "vector": "Expired SSL certificate on subdomain", "cvss": "3.7"},
    {"type": "Suspicious Login Activity", "severity": "Medium", "systems": ["SSO", "VPN"], "vector": "Multiple failed logins from foreign IPs", "cvss": "5.3"},
    {"type": "Malware on Endpoint", "severity": "High", "systems": ["Developer Workstation"], "vector": "Trojanized npm package in CI pipeline", "cvss": "7.2"},
    {"type": "Cloud Misconfiguration", "severity": "Critical", "systems": ["S3 Buckets", "IAM Policies"], "vector": "Public read access on sensitive data bucket", "cvss": "9.0"},
    {"type": "Insider Threat", "severity": "High", "systems": ["Source Code Repo", "Secrets Manager"], "vector": "Departing employee cloned proprietary repos", "cvss": "8.0"},
    {"type": "Zero-Day Exploit", "severity": "Critical", "systems": ["Web Framework", "Application Server"], "vector": "Unpatched RCE in dependency library", "cvss": "9.8"},
    {"type": "Phishing Campaign", "severity": "Medium", "systems": ["Email", "Credentials"], "vector": "Targeted spear-phishing of finance team", "cvss": "6.1"},
]


def generate_candidates(count: int = 5, context: Optional[str] = None) -> list[dict]:
    """Generate simulated candidate items for Talent Acquisition boards."""
    pool = list(CANDIDATE_POOL)
    random.shuffle(pool)
    candidates = pool[:count]

    items = []
    for c in candidates:
        title = f"{c['name']} — {c['current_role']}"
        description = (
            f"**Candidate:** {c['name']}\n"
            f"**Experience:** {c['experience']}\n"
            f"**Education:** {c['education']}\n"
            f"**Current Role:** {c['current_role']}\n"
            f"**Skills:** {', '.join(c['skills'])}\n"
        )
        if context:
            description += f"\n**Applied for:** {context[:200]}"
        items.append({
            "title": title,
            "description": description,
            "acceptance_criteria": f"Skills: {', '.join(c['skills'])}. Experience: {c['experience']}.",
        })
    return items


def generate_leads(count: int = 5, context: Optional[str] = None) -> list[dict]:
    """Generate simulated lead items for Sales boards."""
    pool = list(LEAD_POOL)
    random.shuffle(pool)
    leads = pool[:count]

    items = []
    for lead in leads:
        title = f"{lead['company']} — {lead['need']}"
        description = (
            f"**Company:** {lead['company']} ({lead['size']})\n"
            f"**Contact:** {lead['contact']}\n"
            f"**Budget:** {lead['budget']}\n"
            f"**Timeline:** {lead['timeline']}\n"
            f"**Need:** {lead['need']}\n"
        )
        if context:
            description += f"\n**Account context:** {context[:200]}"
        items.append({
            "title": title,
            "description": description,
            "acceptance_criteria": f"Budget: {lead['budget']}. Timeline: {lead['timeline']}.",
        })
    return items


def generate_incidents(count: int = 5, context: Optional[str] = None) -> list[dict]:
    """Generate simulated incident items for CISO boards."""
    pool = list(INCIDENT_POOL)
    random.shuffle(pool)
    incidents = pool[:count]

    items = []
    for inc in incidents:
        title = f"[{inc['severity']}] {inc['type']} — {', '.join(inc['systems'][:2])}"
        description = (
            f"**Type:** {inc['type']}\n"
            f"**Severity:** {inc['severity']} (CVSS {inc['cvss']})\n"
            f"**Affected Systems:** {', '.join(inc['systems'])}\n"
            f"**Attack Vector:** {inc['vector']}\n"
        )
        if context:
            description += f"\n**Threat category:** {context[:200]}"
        items.append({
            "title": title,
            "description": description,
            "acceptance_criteria": f"Severity: {inc['severity']}. CVSS: {inc['cvss']}.",
        })
    return items


TEMPLATE_GENERATORS = {
    "talent_acquisition": generate_candidates,
    "sales": generate_leads,
    "ciso": generate_incidents,
}


def generate_items(template_id: str, count: int = 5, context: Optional[str] = None) -> list[dict]:
    """Generate simulated items for a given template.

    Returns a list of dicts with title, description, acceptance_criteria.
    """
    generator = TEMPLATE_GENERATORS.get(template_id)
    if not generator:
        return []
    return generator(count=count, context=context)
