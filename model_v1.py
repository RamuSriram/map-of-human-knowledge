"""
Map of Human Knowledge: coverage estimation model (v1, exploratory).

This is the v1 model behind the public explainers (October 2026). It is being
rebuilt on more measurable anchors; treat every number as an order-of-magnitude
estimate. Run: python model_v1.py  (needs numpy; writes results/model_output_v1.json)

coverage(person, category) = K(person, category) / N(category)
  K = knowledge units (KU) the person holds in that category
  N = estimated size of the category's consolidated core, in KU

1 KU ~ an item of learned content that takes a typical learner ~12.5 minutes of
focused study to acquire durably (a concept, a method, a key fact cluster,
~10 words of vocabulary, a grammar pattern).

Overall breadth = union(K) / union(N), removing estimated overlap between
neighbouring categories (first-order inclusion-exclusion).
"""
import json, math
import numpy as np

MIN_PER_KU = 12.5

# ---------------------------------------------------------------- ladder
LADDER = [  # level, KU, label, description
    (0, 200,     "Minimal",      "Everyday exposure only"),
    (1, 1500,    "School",       "Secondary-school level, partly retained"),
    (2, 5000,    "Informed",     "Sustained reading or adjacent work exposure"),
    (3, 12000,   "Degree",       "Undergraduate-level command"),
    (4, 30000,   "Professional", "Graduate training or years of professional practice"),
    (5, 80000,   "Expert",       "10+ years of research or professional leadership"),
    (6, 180000,  "World-class",  "Top of the field and spanning many of its subfields"),
]
LV = np.array([l[0] for l in LADDER], dtype=float)
LK = np.log(np.array([l[1] for l in LADDER], dtype=float))

def ladder_ku(level, scale=1.0):
    level = np.clip(level, 0, 6)
    return np.exp(np.interp(level, LV, LK)) * scale

# ---------------------------------------------------------------- map
# id, name, short, family, N_central (millions KU), low, high, includes, anchor
CATS = [
 ("math",  "Mathematics & logic",        "Math",        "sci",  3.0, 1.5, 8,
  "Arithmetic to research mathematics, statistics, logic",
  "MSC2020 has 63 areas, 529 sub-areas and 6,022 leaf topics"),
 ("phys",  "Physics & astronomy",        "Physics",     "sci",  3.5, 1.5, 9,
  "Mechanics to cosmology, astronomy, space science",
  "Particle to cosmic scales; judged similar in core size to mathematics"),
 ("chem",  "Chemistry",                  "Chemistry",   "sci",  3.5, 1.5, 10,
  "General, organic, inorganic, physical, materials, biochemistry",
  "CAS Registry lists 290M+ substances (the long tail); the core is far smaller"),
 ("earth", "Earth & environment",        "Earth & env", "sci",  2.5, 1.0, 6,
  "Geology, oceans, weather, climate, energy, sustainability",
  "Smaller research base than physics or biology"),
 ("bio",   "Biology & nature",           "Biology",     "life", 7.0, 3.5, 18,
  "Cells to ecosystems, genetics, evolution, plants, animals, agriculture",
  "About 2.1M described species (Catalogue of Life); molecular to ecosystem scales"),
 ("med",   "Medicine & health",          "Medicine",    "life", 7.0, 3.5, 18,
  "Anatomy, disease, clinical practice, pharmacology, nutrition, public health",
  "ICD-11: ~17,000 codes, 120,000+ codable terms; SNOMED CT: 350,000+ concepts"),
 ("cs",    "Computer science & AI",      "CS & AI",     "tech", 4.0, 2.0, 10,
  "Algorithms, software, systems, networks, security, AI",
  "ACM CCS four-level taxonomy, plus fast-changing technology stacks"),
 ("eng",   "Engineering & technology",   "Engineering", "tech", 8.0, 4.0, 20,
  "Mechanical, electrical, civil, aerospace, materials, manufacturing, transport",
  "OpenAlex's largest field (63.3M works, June 2026); dozens of disciplines"),
 ("econ",  "Economics",                  "Economics",   "soc",  3.0, 1.5, 8,
  "Micro, macro, money, trade, development, economic history",
  "JEL classification, plus the economies of 190+ countries"),
 ("bus",   "Business & work",            "Business",    "soc",  4.0, 2.0, 10,
  "Management, finance, accounting, marketing, careers, industries",
  "General practice plus knowledge of thousands of industries and firms"),
 ("law",   "Law & civics",               "Law",         "soc",  6.0, 3.0, 15,
  "Constitutions, contracts, courts, rights, international law",
  "190+ national legal systems, each with its own statutes and case law"),
 ("psych", "Psychology",                 "Psychology",  "soc",  2.5, 1.2, 6,
  "Memory, emotion, personality, development, cognition, clinical",
  "Core theory is compact; the empirical literature is large"),
 ("soc",   "Social sciences",            "Social sci",  "soc",  6.0, 3.0, 15,
  "Sociology, politics, anthropology, demography, media, education",
  "OpenAlex's second-largest field by volume"),
 ("hist",  "History",                    "History",     "hum",  8.0, 4.0, 20,
  "All regions and eras, military history, archaeology, exploration",
  "Every region and period of the human past"),
 ("phil",  "Philosophy & religion",      "Philosophy",  "hum",  3.0, 1.5, 8,
  "Ethics, logic, mind, political philosophy, religions, mythology",
  "Academic philosophy plus thousands of religious traditions and texts"),
 ("arts",  "Visual arts, film & design", "Arts & film", "hum",  5.0, 2.0, 12,
  "Painting, architecture, design, fashion, crafts, cinema, theatre",
  "Millions of catalogued works across every culture and medium"),
 ("music", "Music",                      "Music",       "hum",  3.5, 1.5, 9,
  "Theory, instruments, Carnatic, Hindustani, Western, folk, film, pop",
  "Hundreds of traditions, each with its own theory and repertoire"),
 ("lit",   "Literature",                 "Literature",  "hum",  8.0, 4.0, 20,
  "Epics, poetry, novels, drama, oral traditions, criticism",
  "About 130M distinct book titles (Google Books count, 2010)"),
 ("lang",  "Languages & linguistics",    "Languages",   "lang", 22.0, 8.0, 60,
  "Individual languages, writing systems, grammar, linguistics",
  "7,170 living languages (Ethnologue, 2026); 600-2,200 class hours each for working proficiency (FSI)"),
 ("gen",   "General & practical",        "General",     "lang", 8.0, 3.0, 20,
  "Everyday know-how, food, sports & games, travel, current affairs, pop culture",
  "About 7M English Wikipedia articles, 66M+ across all languages"),
]
CID = [c[0] for c in CATS]
IDX = {c: i for i, c in enumerate(CID)}
NC = len(CATS)
N_CENTRAL = np.array([c[4] for c in CATS]) * 1e6
N_LOW = np.array([c[5] for c in CATS]) * 1e6
N_HIGH = np.array([c[6] for c in CATS]) * 1e6

FAMILIES = {
    "sci":  "Formal & physical sciences",
    "life": "Life & health",
    "tech": "Technology",
    "soc":  "Society & mind",
    "hum":  "Humanities & arts",
    "lang": "Language & everyday",
}

# overlap coefficients: share of the smaller body of knowledge shared by two categories
OVERLAP = {
 ("math","phys"):.25, ("math","cs"):.20, ("math","econ"):.10, ("math","eng"):.15, ("math","phil"):.03,
 ("phys","chem"):.20, ("phys","eng"):.20, ("phys","earth"):.15, ("phys","cs"):.03,
 ("chem","bio"):.20, ("chem","med"):.10, ("chem","eng"):.10, ("chem","earth"):.10,
 ("bio","med"):.30, ("bio","earth"):.15, ("bio","psych"):.08,
 ("med","psych"):.10,
 ("cs","eng"):.20, ("cs","bus"):.03,
 ("eng","bus"):.05, ("eng","earth"):.05, ("eng","arts"):.03,
 ("econ","bus"):.30, ("econ","soc"):.15, ("econ","hist"):.05, ("econ","law"):.05,
 ("bus","law"):.08,
 ("law","soc"):.15, ("law","phil"):.05, ("law","hist"):.05,
 ("psych","soc"):.10, ("psych","phil"):.10, ("psych","lang"):.10, ("psych","cs"):.05,
 ("soc","hist"):.15, ("soc","phil"):.05,
 ("hist","lit"):.05, ("hist","arts"):.05, ("hist","phil"):.05, ("hist","music"):.02,
 ("phil","lit"):.05, ("phil","lang"):.08, ("econ","phil"):.05, ("bio","cs"):.03, ("hist","lang"):.03, ("earth","soc"):.03, ("music","phys"):.02,
 ("arts","lit"):.08, ("arts","music"):.08,
 ("lit","lang"):.08,
}
for c in CID:
    if c != "gen":
        OVERLAP.setdefault(("gen", c), .05)
PAIRS = [(IDX[a], IDX[b], v) for (a, b), v in OVERLAP.items()]

def union(K, ov_scale=1.0):
    """K: array (..., NC). first-order inclusion-exclusion"""
    tot = K.sum(axis=-1)
    for i, j, a in PAIRS:
        tot = tot - a * ov_scale * np.minimum(K[..., i], K[..., j])
    return tot

# ---------------------------------------------------------------- people
PER_LANG_KU = 12000  # educated native command of one language

# levels in category order (lang handled via languages + linguistics level)
def L(**kw):
    return kw

PEOPLE = [
 # ---------------- benchmarks
 dict(id="avg", name="Average adult", group="benchmark",
      role="Global benchmark",
      basis="About 9 years of schooling (world mean 8.8, UNDP 2025), a service-sector job, one native language plus a little of a second.",
      langs=[("Native language (modest schooling)", .7), ("Second language (basic)", .2)], ling=0.0,
      lv=L(math=1.0, phys=.7, chem=.6, earth=.9, bio=.9, med=1.1, cs=.8, eng=.7, econ=.8, bus=1.6,
           law=.9, psych=.9, soc=1.0, hist=1.0, phil=1.2, arts=1.3, music=1.4, lit=.8, gen=3.9)),
 dict(id="grad", name="Indian engineering graduate", group="benchmark",
      role="Typical B.Tech, ~5 years in IT",
      basis="Four-year B.Tech (computer science or allied branch), about five years in an IT job, typical reading and media habits.",
      langs=[("Native language, e.g. Telugu", 1.0), ("English (professional)", .6), ("Hindi (conversational)", .3)], ling=0.7,
      lv=L(math=2.5, phys=1.9, chem=1.5, earth=1.3, bio=1.1, med=1.2, cs=3.3, eng=2.4, econ=1.3, bus=2.0,
           law=1.2, psych=1.2, soc=1.4, hist=1.5, phil=1.4, arts=1.5, music=1.5, lit=1.3, gen=4.15)),
 dict(id="iq", name="High-IQ adult", group="benchmark",
      role="IQ ~145 (top 0.1%), not famous",
      basis="Master's in electrical engineering (illustrative), reads about 40 books a year across subjects. Assumed to learn roughly 1.5 to 2 times more per hour than average, but with the same hours in a day.",
      langs=[("Native language", 1.0), ("Second language (fluent)", .8), ("Third language (partial)", .3)], ling=1.5,
      lv=L(math=3.4, phys=3.2, chem=2.2, earth=2.1, bio=2.3, med=1.9, cs=3.3, eng=4.0, econ=2.4, bus=2.3,
           law=1.8, psych=2.4, soc=2.3, hist=2.7, phil=2.7, arts=2.0, music=1.8, lit=2.5, gen=4.7)),
 # ---------------- individuals
 dict(id="musk", name="Elon Musk", group="individual", role="Entrepreneur, engineer",
      basis="BA physics and BS economics, University of Pennsylvania (1997); by his account left a Stanford PhD programme within days (1995); has run SpaceX engineering as CEO and CTO since 2002; Tesla CEO since 2008; co-founded Zip2, X.com/PayPal, Neuralink, The Boring Company and xAI.",
      langs=[("English", 1.0), ("Afrikaans (school level, assumed)", .15)], ling=1.0,
      lv=L(math=3.0, phys=3.5, chem=2.6, earth=2.0, bio=1.8, med=1.5, cs=3.4, eng=4.8, econ=3.0, bus=5.2,
           law=1.8, psych=1.6, soc=1.8, hist=2.3, phil=1.8, arts=1.4, music=1.2, lit=2.1, gen=4.4)),
 dict(id="gates", name="Bill Gates", group="individual", role="Technologist, philanthropist",
      basis="Left Harvard (1975) to co-found Microsoft, wrote much of its early software and was CEO until 2000; has led the Gates Foundation's work on global health, vaccines and development since 2000; founded TerraPower and Breakthrough Energy; books on climate (2021) and pandemic preparedness (2022).",
      langs=[("English", 1.0)], ling=1.0,
      lv=L(math=3.2, phys=2.4, chem=2.0, earth=2.8, bio=3.0, med=3.3, cs=4.6, eng=2.8, econ=3.0, bus=5.2,
           law=2.2, psych=1.8, soc=2.8, hist=2.7, phil=1.8, arts=1.5, music=1.2, lit=2.2, gen=4.7)),
 dict(id="tao", name="Terence Tao", group="individual", role="Mathematician",
      basis="PhD Princeton (1996); Fields Medal (2006); UCLA professor; hundreds of papers across harmonic analysis, PDEs, combinatorics, number theory, random matrices and compressed sensing; active in formal proof and AI-assisted mathematics.",
      langs=[("English", 1.0)], ling=1.0,
      lv=L(math=6.0, phys=3.0, chem=1.3, earth=1.2, bio=1.3, med=1.3, cs=3.8, eng=2.1, econ=1.6, bus=1.1,
           law=1.1, psych=1.4, soc=1.3, hist=1.7, phil=2.1, arts=1.2, music=1.3, lit=1.6, gen=4.0)),
 dict(id="hassabis", name="Demis Hassabis", group="individual", role="AI researcher, Google DeepMind CEO",
      basis="Computer science, Cambridge (1997); game designer and programmer (Theme Park, Elixir Studios); PhD cognitive neuroscience, UCL (2009); co-founded DeepMind (2010): AlphaGo, AlphaFold; Nobel Prize in Chemistry (2024); founded Isomorphic Labs for drug discovery.",
      langs=[("English", 1.0)], ling=1.3,
      lv=L(math=3.3, phys=2.4, chem=2.6, earth=1.5, bio=3.3, med=2.3, cs=5.4, eng=2.6, econ=1.8, bus=3.8,
           law=1.4, psych=4.1, soc=1.7, hist=2.1, phil=2.4, arts=2.3, music=1.3, lit=1.8, gen=4.55)),
 dict(id="doudna", name="Jennifer Doudna", group="individual", role="Biochemist",
      basis="PhD Harvard (1989); UC Berkeley professor; co-developed CRISPR-Cas9 genome editing (2012); Nobel Prize in Chemistry (2020); founded the Innovative Genomics Institute; co-founded several biotech companies; public work on the ethics of gene editing.",
      langs=[("English", 1.0)], ling=1.0,
      lv=L(math=2.4, phys=2.4, chem=4.8, earth=1.2, bio=5.5, med=3.2, cs=1.8, eng=2.3, econ=1.3, bus=2.8,
           law=2.0, psych=1.3, soc=1.8, hist=1.5, phil=2.2, arts=1.2, music=1.3, lit=1.5, gen=4.0)),
 dict(id="buffett", name="Warren Buffett", group="individual", role="Investor",
      basis="MS economics, Columbia (1951), studying under Benjamin Graham; ran Berkshire Hathaway for about six decades (CEO until the end of 2025, chairman until September 2026); deep exposure to insurance, finance, accounting and dozens of industries; a famously heavy reader of annual reports.",
      langs=[("English", 1.0)], ling=1.0,
      lv=L(math=2.4, phys=1.0, chem=1.0, earth=1.0, bio=1.0, med=1.2, cs=1.0, eng=1.6, econ=4.2, bus=5.7,
           law=2.6, psych=2.3, soc=1.8, hist=2.5, phil=1.6, arts=1.0, music=1.4, lit=1.5, gen=4.55)),
 dict(id="chomsky", name="Noam Chomsky", group="individual", role="Linguist, public intellectual",
      basis="PhD linguistics, University of Pennsylvania (1955); taught at MIT from 1955; founded generative grammar (Syntactic Structures, 1957); a central figure in cognitive science and the philosophy of language and mind; 150+ books on linguistics, politics and media.",
      langs=[("English", 1.0), ("Hebrew (MA thesis on Modern Hebrew)", .5), ("Reading French and German (assumed)", .2)], ling=5.8,
      lv=L(math=3.0, phys=1.3, chem=1.0, earth=1.0, bio=2.0, med=1.0, cs=2.8, eng=1.0, econ=2.2, bus=1.3,
           law=2.2, psych=4.4, soc=4.1, hist=3.7, phil=4.8, arts=1.2, music=1.1, lit=2.2, gen=4.4)),
 dict(id="sen", name="Amartya Sen", group="individual", role="Economist, philosopher",
      basis="Schooled at Santiniketan; Presidency College, Calcutta; PhD Cambridge (1959); Nobel Prize in Economics (1998) for welfare economics and social choice; Harvard professor of economics and philosophy; books on development, justice, famine, and Indian history and culture.",
      langs=[("Bengali", 1.0), ("English", 1.0), ("Sanskrit (reading, assumed partial)", .3)], ling=1.5,
      lv=L(math=3.4, phys=1.3, chem=1.0, earth=1.3, bio=1.3, med=1.9, cs=1.0, eng=1.0, econ=5.8, bus=1.3,
           law=2.3, psych=1.8, soc=4.4, hist=3.5, phil=4.8, arts=1.8, music=1.6, lit=3.0, gen=4.4)),
 dict(id="pichai", name="Sundar Pichai", group="individual", role="Engineer, Alphabet CEO",
      basis="B.Tech metallurgical engineering, IIT Kharagpur (1993); MS materials science, Stanford; MBA, Wharton (2002); worked at Applied Materials and McKinsey; led Chrome and Android at Google; CEO of Google (2015) and Alphabet (2019).",
      langs=[("Tamil", 1.0), ("English", 1.0), ("Hindi (partial, assumed)", .3)], ling=1.0,
      lv=L(math=2.8, phys=2.8, chem=2.7, earth=1.3, bio=1.3, med=1.3, cs=3.8, eng=3.8, econ=2.7, bus=5.0,
           law=2.2, psych=1.8, soc=1.8, hist=1.8, phil=1.5, arts=1.3, music=1.2, lit=1.5, gen=4.4)),
 dict(id="obama", name="Barack Obama", group="individual", role="Lawyer, politician, author",
      basis="BA political science, Columbia (1983); JD Harvard (1991) and president of the Harvard Law Review; taught constitutional law at the University of Chicago Law School (1992-2004); US President (2009-2017); author of three bestselling books.",
      langs=[("English", 1.0), ("Indonesian (childhood, partial)", .2)], ling=1.0,
      lv=L(math=1.5, phys=1.3, chem=1.0, earth=1.8, bio=1.3, med=2.0, cs=1.3, eng=1.2, econ=3.0, bus=2.0,
           law=5.0, psych=2.0, soc=4.8, hist=3.8, phil=2.7, arts=1.8, music=2.0, lit=3.3, gen=4.7)),
 dict(id="tyson", name="Neil deGrasse Tyson", group="individual", role="Astrophysicist, science communicator",
      basis="BA physics, Harvard (1980); PhD astrophysics, Columbia (1991); director of the Hayden Planetarium since 1996; served on US presidential commissions on the aerospace industry (2001) and space exploration (2004); hosted Cosmos (2014) and StarTalk; many popular-science books.",
      langs=[("English", 1.0)], ling=1.0,
      lv=L(math=3.5, phys=5.0, chem=2.4, earth=2.9, bio=2.3, med=1.3, cs=2.0, eng=2.3, econ=1.5, bus=1.8,
           law=1.3, psych=1.8, soc=2.4, hist=3.0, phil=2.2, arts=1.8, music=1.4, lit=2.0, gen=4.7)),
 dict(id="jennings", name="Ken Jennings", group="individual", role="Quiz champion, author",
      basis="BA English and computer science, BYU (2000); worked as a software engineer; 74-game Jeopardy! winning streak (2004); won the Greatest of All Time tournament (2020); Jeopardy! host since 2021; trivia and geography books. Grew up partly in South Korea and Singapore.",
      langs=[("English", 1.0)], ling=1.3,
      lv=L(math=2.2, phys=1.8, chem=1.8, earth=2.2, bio=2.0, med=1.7, cs=3.0, eng=1.5, econ=1.8, bus=1.8,
           law=1.5, psych=1.7, soc=2.5, hist=3.3, phil=1.8, arts=2.6, music=2.6, lit=3.3, gen=6.0)),
 dict(id="rahman", name="A. R. Rahman", group="individual", role="Composer",
      basis="Left school to work as a musician; diploma in Western classical music on a Trinity College London scholarship; film composer across Tamil, Hindi and international cinema, working in Carnatic, Hindustani, Western classical, Sufi and electronic idioms; two Oscars and two Grammys; founded KM Music Conservatory (2008); directed Le Musk.",
      langs=[("Tamil", .9), ("English (professional)", .6), ("Hindi (working)", .4)], ling=1.0,
      lv=L(math=1.2, phys=1.3, chem=.8, earth=.9, bio=.9, med=1.0, cs=2.2, eng=2.3, econ=1.2, bus=2.5,
           law=1.3, psych=1.5, soc=1.5, hist=1.5, phil=2.4, arts=3.6, music=6.0, lit=1.8, gen=4.0)),
 dict(id="harari", name="Yuval Noah Harari", group="individual", role="Historian",
      basis="DPhil history, Oxford (2002), specialising in medieval and military history; professor at the Hebrew University of Jerusalem; Sapiens, Homo Deus, 21 Lessons and Nexus span world history, biology, economics and AI.",
      langs=[("Hebrew", 1.0), ("English", .9)], ling=1.0,
      lv=L(math=1.3, phys=1.3, chem=1.0, earth=1.8, bio=2.5, med=1.3, cs=1.9, eng=1.0, econ=2.7, bus=1.3,
           law=1.8, psych=2.3, soc=3.8, hist=5.5, phil=3.5, arts=1.5, music=1.1, lit=2.3, gen=4.4)),
 dict(id="shetty", name="Devi Shetty", group="individual", role="Cardiac surgeon, hospital founder",
      basis="MBBS, Kasturba Medical College (1979); FRCS (England) and cardiothoracic training at Guy's Hospital; 15,000+ heart operations; performed India's first neonatal heart surgery (1992); founded Narayana Hrudayalaya, now Narayana Health (2001); helped design the Yeshasvini low-cost insurance scheme.",
      langs=[("Native language (Kannada region)", 1.0), ("English", 1.0), ("Hindi (working, assumed)", .4), ("Bengali (partial, assumed)", .2)], ling=0.8,
      lv=L(math=1.5, phys=1.6, chem=2.2, earth=1.0, bio=3.0, med=5.4, cs=1.5, eng=1.8, econ=2.2, bus=4.3,
           law=1.8, psych=2.0, soc=2.2, hist=1.5, phil=1.6, arts=1.1, music=1.1, lit=1.3, gen=4.2)),
 dict(id="ghosh", name="Amitav Ghosh", group="individual", role="Novelist, essayist",
      basis="BA history and MA sociology, University of Delhi; DPhil social anthropology, Oxford (1982), with fieldwork in an Egyptian village; novels including the Ibis trilogy; nonfiction on climate change and colonial history; Jnanpith Award (2018).",
      langs=[("Bengali", 1.0), ("English", 1.0), ("Hindi", .5), ("Egyptian Arabic (fieldwork, assumed working)", .4)], ling=1.8,
      lv=L(math=1.3, phys=1.3, chem=1.1, earth=2.8, bio=2.0, med=1.3, cs=1.0, eng=1.1, econ=2.3, bus=1.3,
           law=1.3, psych=1.6, soc=4.2, hist=4.5, phil=2.3, arts=1.8, music=1.2, lit=5.6, gen=4.6)),
]

for p in PEOPLE:
    missing = [c for c in CID if c != "lang" and c not in p["lv"]]
    assert not missing, (p["id"], missing)

def person_K(p, scale=1.0, lang_ku=PER_LANG_KU, noise=None):
    """returns KU vector (NC,). noise: dict cat->level offset"""
    K = np.zeros(NC)
    for c in CID:
        if c == "lang":
            lv_ling = p["ling"] + (noise.get("lang", 0) if noise else 0)
            k = sum(prof for _, prof in p["langs"]) * lang_ku
            k *= math.exp(noise.get("langprof", 0)) if noise else 1
            k += ladder_ku(lv_ling, scale)
            K[IDX[c]] = k
        else:
            lv = p["lv"][c] + (noise.get(c, 0) if noise else 0)
            K[IDX[c]] = ladder_ku(lv, scale)
    return K

# ---------------------------------------------------------------- central
UN_N = union(N_CENTRAL)
central = {}
for p in PEOPLE:
    K = person_K(p)
    cov = K / N_CENTRAL
    uk = union(K)
    central[p["id"]] = dict(K=K, cov=cov, overall=uk / UN_N, eq=cov.mean(), unionK=uk)

# ---------------------------------------------------------------- Monte Carlo
rng = np.random.default_rng(20260926)
S = 6000
sig = lambda lo, hi: math.log(hi / lo) / (2 * 1.645)
sigN = np.array([sig(l, h) for l, h in zip(N_LOW, N_HIGH)])
# per-category size draws (median-centred), plus a common size factor
logN = np.log(N_CENTRAL)[None, :] + rng.normal(0, 1, (S, NC)) * sigN[None, :]
commonN = rng.normal(0, sig(1/2, 2), (S, 1))           # common x/÷2 (90%)
Ns = np.exp(logN + commonN)
ladder_scale = np.exp(rng.normal(0, sig(1/1.6, 1.6), S))  # common x/÷1.6
lang_scale = np.exp(rng.normal(0, sig(1/1.5, 1.5), S))
ov_scale = rng.uniform(0.5, 1.5, S)
UN_Ns = np.array([union(Ns[s], ov_scale[s]) for s in range(S)])

LEVEL_SD = 0.35
mc = {}
for p in PEOPLE:
    covs = np.zeros((S, NC)); overall = np.zeros(S); eq = np.zeros(S)
    lvl_noise = rng.normal(0, LEVEL_SD, (S, NC))
    langprof_noise = rng.normal(0, 0.25, S)
    for s in range(S):
        noise = {c: lvl_noise[s, IDX[c]] for c in CID}
        noise["langprof"] = langprof_noise[s]
        K = person_K(p, ladder_scale[s], PER_LANG_KU * lang_scale[s], noise)
        covs[s] = K / Ns[s]
        overall[s] = union(K, ov_scale[s]) / UN_Ns[s]
        eq[s] = covs[s].mean()
    mc[p["id"]] = dict(covs=covs, overall=overall, eq=eq)

def pct(a, q):
    return float(np.percentile(a, q))

# ratio robustness: each person vs average adult, in the same simulated world
ratios = {}
for p in PEOPLE:
    r = mc[p["id"]]["overall"] / mc["avg"]["overall"]
    ratios[p["id"]] = (pct(r, 10), float(np.median(r)), pct(r, 90))

# ---------------------------------------------------------------- ceilings
hours_life = 80 * 365 * 16           # perfect-memory, 16 waking hours/day, 80 years
hours_real = 50 * 2000               # 50 working years of full-time learning
ku_life = hours_life * 60 / MIN_PER_KU
ku_real = hours_real * 60 / MIN_PER_KU
ceil_life = ku_life / UN_N
ceil_real = ku_real / UN_N
map_years = UN_N * MIN_PER_KU / 60 / 2000

# ---------------------------------------------------------------- output
out = dict(
    minPerKU=MIN_PER_KU,
    ladder=[dict(level=l, ku=k, label=lab, desc=d, hours=round(k * MIN_PER_KU / 60))
            for l, k, lab, d in LADDER],
    families=FAMILIES,
    categories=[dict(id=c[0], name=c[1], short=c[2], family=c[3],
                     N=c[4], low=c[5], high=c[6], includes=c[7], anchor=c[8],
                     share=float(c[4] * 1e6 / N_CENTRAL.sum()))
                for c in CATS],
    mapTotal=float(N_CENTRAL.sum()), mapUnion=float(UN_N), mapYears=float(map_years),
    ceilings=dict(life=float(ceil_life), real=float(ceil_real),
                  lifeHours=hours_life, realHours=hours_real,
                  lifeKU=float(ku_life), realKU=float(ku_real)),
    perLangKU=PER_LANG_KU,
    people=[],
)
for p in PEOPLE:
    cen = central[p["id"]]; m = mc[p["id"]]
    cells = []
    for c in CID:
        i = IDX[c]
        lvl = p["ling"] if c == "lang" else p["lv"][c]
        cells.append(dict(
            cat=c, level=lvl, ku=float(cen["K"][i]),
            cov=float(cen["cov"][i] * 100),
            lo=pct(m["covs"][:, i], 10) * 100, hi=pct(m["covs"][:, i], 90) * 100))
    peak = int(np.argmax(cen["cov"]))
    top3 = [CID[i] for i in np.argsort(-cen["cov"])[:3]]
    out["people"].append(dict(
        top3=top3,
        eqLo=pct(m["eq"], 10) * 100, eqHi=pct(m["eq"], 90) * 100,
        id=p["id"], name=p["name"], group=p["group"], role=p["role"], basis=p["basis"],
        langs=[dict(name=n, prof=pr) for n, pr in p["langs"]], ling=p["ling"],
        cells=cells,
        overall=float(cen["overall"] * 100),
        overallLo=pct(m["overall"], 10) * 100, overallHi=pct(m["overall"], 90) * 100,
        eq=float(cen["eq"] * 100),
        unionKU=float(cen["unionK"]),
        hours=float(cen["unionK"] * MIN_PER_KU / 60),
        peakCat=CID[peak], peakCov=float(cen["cov"][peak] * 100),
        ratioVsAvg=ratios[p["id"]],
    ))

import os
HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "results", "model_output_v1.json"), "w"), indent=1)

# ---------------------------------------------------------------- report
print(f"Map total {N_CENTRAL.sum()/1e6:.1f}M KU, union {UN_N/1e6:.1f}M KU, ~{map_years:,.0f} study-years")
print(f"Ceilings: perfect-memory lifetime {ceil_life*100:.2f}%  realistic {ceil_real*100:.2f}%")
hdr = "".join(f"{c[:5]:>7}" for c in CID)
print(f"{'person':22}{hdr}{'  OVERALL':>10}{'  p10-p90':>16}{'   eq':>7}{'  unionKU':>10}{'  xAvg':>6}")
for p in out["people"]:
    row = "".join(f"{c['cov']:7.3f}" for c in p["cells"])
    print(f"{p['name'][:22]:22}{row}{p['overall']:10.3f}  {p['overallLo']:.3f}-{p['overallHi']:.3f}{p['eq']:7.3f}{p['unionKU']:10,.0f}{p['ratioVsAvg'][1]:6.1f}")
print("\nratio vs avg (p10, p50, p90):")
for p in out["people"]:
    r = p["ratioVsAvg"]; print(f"  {p['name']:28} {r[0]:.1f}  {r[1]:.1f}  {r[2]:.1f}")
print("\nshares:", {c['id']: round(c['share']*100, 1) for c in out['categories']})
