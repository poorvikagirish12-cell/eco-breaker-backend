import os
import random
import psycopg2

# Categories, Tags, and Contrarian Seed Data
TOPICS = [
    {
        "category": "Technology",
        "tag": "Artificial Intelligence",
        "templates": [
            ("Why AI Will Make Us More Human, Not Less", "Repetitive tasks are outsourced, forcing humans to develop higher emotional intelligence and creativity."),
            ("The Myth of AI Consciousness", "Large language models are just advanced autocomplete engines, lacking any real understanding or sentience."),
            ("How AI is Reviving Dead Languages", "Using machine learning to decipher ancient scripts is preserving human heritage in ways never before possible."),
            ("Why We Should Stop Fearing Artificial General Intelligence", "The hardware constraints and cognitive limitations mean sentient robots are science fiction, not an imminent threat.")
        ]
    },
    {
        "category": "Technology",
        "tag": "Quantum Computing",
        "templates": [
            ("The Hype of Quantum Computing: Why We Are Decades Away", "Practical, error-corrected quantum computers require physics breakthroughs we haven't even conceived yet."),
            ("Why Classical Computers Will Always Rule Daily Life", "Quantum computers excel at niche mathematical operations, but classical architectures are far superior for daily computing."),
            ("The Quantum Threat to Encryption is Overstated", "Post-quantum cryptography algorithms are already being deployed long before any quantum threat is built.")
        ]
    },
    {
        "category": "Technology",
        "tag": "Web3",
        "templates": [
            ("Web3: A Solution in Search of a Problem", "Decentralized systems add latency, cost, and complexity, whereas consumers overwhelmingly prefer ease of use and support."),
            ("The True Value of Blockchain Beyond Cryptocurrencies", "Decentralized consensus works wonders for supply chain audits, even if cryptocurrency trading is purely speculative."),
            ("Why Decentralized Finance (DeFi) is Recreating Centralized Banks", "To scale and prevent fraud, DeFi platforms are introducing intermediaries, turning into the very banks they opposed.")
        ]
    },
    {
        "category": "Technology",
        "tag": "Cybersecurity",
        "templates": [
            ("Embracing Vulnerability: The Myth of Total Security", "No system can be 100% secure. Companies should focus on rapid recovery and resilience over fortress building."),
            ("Why the Safest Password is One You Never Remember", "Biometrics and passkeys are replacing passwords, eliminating the human vulnerability factor entirely."),
            ("The Cybersecurity Risk of Smart Appliances", "Your smart fridge or toaster is a potential entry point for botnets, proving that offline appliances are safer.")
        ]
    },
    {
        "category": "Technology",
        "tag": "Robotics",
        "templates": [
            ("How Robots Will Save the Working Class", "Instead of stealing livelihoods, robots will take over hazardous, dirty, and degrading jobs, raising human dignity."),
            ("Why Humanoid Robots are a Bad Design Choice", "Wheeled and specialized form factors are far more efficient than humanoids for warehouse and household labor."),
            ("The Danger of Anthropomorphizing Social Robots", "Attaching emotional states to metal objects leads to unhealthy psychological dependencies and isolated lives.")
        ]
    },
    {
        "category": "Technology",
        "tag": "Metaverse",
        "templates": [
            ("Why the Metaverse is a Regressive Vision", "Escaping into digital headsets is a symptom of physical community breakdown, not a step forward for civilization."),
            ("Virtual Reality's Ergonomic Dead End", "Humans are physically wired to interact with their real environments; headsets cause eye strain and motion sickness."),
            ("How Augmented Reality Will Outlive Virtual Reality", "AR enhances physical interactions instead of replacing them, making it socially acceptable and useful.")
        ]
    },
    {
        "category": "Science",
        "tag": "Space Exploration",
        "templates": [
            ("Mars is a Dead End: The Case for Earth's Oceans", "Colonizing a lifeless radioactive desert is foolish. We should spend those resources exploring deep ocean vents."),
            ("Why Space Tourism is an Environmental Catastrophe", "Launching wealthy tourists into orbit releases massive amounts of soot and carbon directly into the stratosphere."),
            ("The Myth of Mining Asteroids", "The energy required to return heavy metals from space to Earth makes space mining economically unviable compared to land mining.")
        ]
    },
    {
        "category": "Science",
        "tag": "Neuroscience",
        "templates": [
            ("Free Will is an Illusion, But We Must Believe It", "Brain activity precedes conscious choice, but society collapses if we do not hold individuals morally accountable."),
            ("Why Neuro-Enhancement Might Backfire", "Artificially boosting memory or focus can lead to obsessive patterns and reduce creative daydreaming capacity."),
            ("The Limits of Brain-Computer Interfaces", "The brain's neural plasticity rejects foreign electrodes over time, making permanent neural implants highly challenging.")
        ]
    },
    {
        "category": "Science",
        "tag": "Fusion Energy",
        "templates": [
            ("Why Nuclear Fusion is Always 30 Years Away", "Maintaining plasma stability at extreme temperatures requires massive cooling systems that consume most produced energy."),
            ("The Forgotten Promise of Fission Energy", "We chase fusion while ignoring next-generation thorium and molten salt fission reactors, which are ready today."),
            ("Fusion Hype is Diverting Climate Funds", "Spending billions on experimental fusion research drains resources from deploying current renewable infrastructure.")
        ]
    },
    {
        "category": "Science",
        "tag": "Biotechnology",
        "templates": [
            ("The Danger of Curing All Diseases", "Eliminating mortality from disease could cause catastrophic population growth and cultural stagnation."),
            ("Synthetic Biology's Unpredictable Eco-Impact", "Releasing engineered organisms into the wild to clean oil or plastic could mutate and destroy ecosystems."),
            ("The Ethical Case for CRISPR in Agriculture", "Gene editing crops is the only way to feed the planet under extreme climate changes, regardless of GMO fears.")
        ]
    },
    {
        "category": "Environment",
        "tag": "Climate Change",
        "templates": [
            ("Why Carbon Taxes Fail and Green Subsidies Win", "Penalizing carbon usage triggers political backlash. Incentivizing green innovation creates clean energy organically."),
            ("The Outsized Role of Concrete in Global Warming", "We focus on cars and planes, but concrete manufacturing is responsible for more CO2 emissions than aviation."),
            ("Why Adapting to Climate Change is as Important as Stopping It", "Some warming is already locked in. We must build sea walls and irrigate fields instead of assuming we can reverse it.")
        ]
    },
    {
        "category": "Environment",
        "tag": "Renewable Energy",
        "templates": [
            ("Why Solar Power Alone Cannot Save the Grid", "Modern cities consume massive power at night. Without breakthroughs in storage, solar cannot handle base loads."),
            ("The Dark Side of Wind Turbine Disposal", "FRP wind blades cannot be recycled easily and end up in giant landfills, creating an ecological footprint."),
            ("Why Geothermal Energy is the True Green Hero", "Constant, underground geothermal power provides clean baseload energy without relying on weather conditions.")
        ]
    },
    {
        "category": "Environment",
        "tag": "Electric Vehicles",
        "templates": [
            ("Electric Vehicles: Shifting Pollution, Not Stopping It", "EV batteries require mining rare earth metals in fragile ecosystems and rely on coal-heavy electrical grids."),
            ("The Weight Problem of Electric Cars", "EVs are much heavier than gas cars, leading to faster road deterioration and increased toxic tire-particle emissions."),
            ("Why We Need Electrified Buses, Not EV Sedans", "Individual electric cars do not solve traffic or sprawl; mass electric transit is the only real solution.")
        ]
    },
    {
        "category": "Economy",
        "tag": "Remote Work",
        "templates": [
            ("The Lonely Screen: Why Remote Work Destroys Creativity", "Great innovations occur through spontaneous physical encounters, which scheduled Zoom calls cannot duplicate."),
            ("Why Remote Work is a Privilege of the Wealthy", "Office workers rejoice, but service, manufacturing, and transport workers are left behind, widening inequality."),
            ("How Remote Work is Devastating Downtown Ecosystems", "The collapse of commercial office occupancy is killing local small businesses and reducing city tax revenues.")
        ]
    },
    {
        "category": "Economy",
        "tag": "Macroeconomics",
        "templates": [
            ("The Myth of Unlimited Economic Growth", "Exponential economic growth on a finite planet is mathematically impossible. We must study steady-state systems."),
            ("Inflation is Not Always a Monetary Issue", "Supply chain disruptions and geopolitical conflicts trigger rising prices far more than interest rate policies."),
            ("Why Deflation is Not the Enemy of Consumers", "Falling prices allow savers to buy goods cheaper, challenging the central bank narrative that mild inflation is healthy.")
        ]
    },
    {
        "category": "Society",
        "tag": "Education Reform",
        "templates": [
            ("Standardized Testing is Bad, But Grades are Necessary", "Grades ensure accountability and maintain educational standards, even if tests favor rote memorization."),
            ("Why University Degrees are Overvalued", "Trade schools and self-directed digital portfolios yield better careers with zero debt compared to humanities degrees."),
            ("The Failure of Digital-Only Classrooms", "Children require social classrooms and physical peer interactions to develop emotional maturity and focus.")
        ]
    },
    {
        "category": "Society",
        "tag": "Social Media",
        "templates": [
            ("The Case for Banning Algorithmic Feeds", "Forced chronological feeds restore user control, while algorithms optimize for outrage to keep users hooked."),
            ("How Likes and Retweets Distort Public Discourse", "Quantifiable metrics reward extreme opinions and discourage nuance, nuance being the core of constructive debate."),
            ("Why Social Media is Making Us More Lonely", "Digital connections replace deep local friendships, creating an epidemic of hyper-connected isolation.")
        ]
    },
    {
        "category": "Society",
        "tag": "Minimalism",
        "templates": [
            ("The Bourgeois Illusion of Minimalist Living", "Minimalism requires the safety net of wealth; poor people store items because they cannot afford to replace them."),
            ("Why Aesthetic Minimalism is Architecturally Depressing", "Sterile, grey, boxy rooms deprive human eyes of color and patterns, increasing indoor anxiety."),
            ("The Consumption Trap of Buying Minimalist Brands", "Buying premium simple products to replace functional ones is just consumerism disguised as virtue.")
        ]
    },
    {
        "category": "Philosophy",
        "tag": "Stoicism",
        "templates": [
            ("Stoicism: The Danger of Emotional Suppression", "Modern Stoics often suppress grief and anger, leading to psychological stress and a lack of empathy."),
            ("Why Ancient Stoicism Doesn't Fit Corporate Success", "Stoics advocated for societal detachment, not grinding 80 hours a week to climb a corporate ladder."),
            ("Stoicism as a Tool for Political Inaction", "By focusing solely on what you can control internally, Stoicism can discourage citizens from fighting systemic injustices.")
        ]
    },
    {
        "category": "Philosophy",
        "tag": "Existentialism",
        "templates": [
            ("The Burden of Absolute Freedom", "Existential freedom means you have no excuses for your failures, creating deep-seated anxiety (angst)."),
            ("Why Creating Your Own Meaning is Exhausting", "Without traditional community guidelines, humans struggle to maintain self-authored purpose day in and day out."),
            ("Sartre was Wrong: Hell is Not Other People", "Hell is isolation. Other people are the mirror through which we understand ourselves and find warmth.")
        ]
    }
]

# Modifiers to expand templates up to 200 items
MODIFIERS = [
    ("An In-Depth View", "A critical exploration into how we perceive this topic, analyzing hidden systemic factors."),
    ("A Radical Re-evaluation", "Re-assessing popular beliefs and debunking mainstream media headlines regarding this field."),
    ("The Unspoken Truths", "Uncovering the financial and cultural motives behind public narratives around this subject."),
    ("The Counter-Intuitive Facts", "Examining empirical data that contradicts mainstream consensus and challenges orthodoxy."),
    ("Looking at the Future", "Predicting long-term trends and societal shifts that will alter how we interface with this topic."),
    ("A Historical Warning", "Drawing lessons from past historical failures to warn against repeating mistakes in this domain.")
]

def generate_blogs():
    print("Generating 200 blogs data...")
    blogs = []
    
    # 1. Add all base templates
    for topic in TOPICS:
        for title, content in topic["templates"]:
            blogs.append({
                "category": topic["category"],
                "tag": topic["tag"],
                "title": title,
                "content": content
            })
            
    # 2. Expand programmatically to exactly 200 blogs using modifiers
    random.seed(42) # Deterministic generation
    base_count = len(blogs)
    i = 0
    
    while len(blogs) < 200:
        base_blog = blogs[i % base_count]
        modifier_title, modifier_desc = random.choice(MODIFIERS)
        
        # Build modified title and content
        new_title = f"{modifier_title}: {base_blog['title']}"
        new_content = f"{modifier_desc} {base_blog['content']}"
        
        # Check for duplicate titles
        if not any(b["title"] == new_title for b in blogs):
            blogs.append({
                "category": base_blog["category"],
                "tag": base_blog["tag"],
                "title": new_title,
                "content": new_content
            })
        i += 1

    return blogs

def write_sql_file(blogs):
    sql_path = "c:/Users/poorv/OneDrive/Desktop/tessa/task 6/database/seed_blogs_200.sql"
    print(f"Writing SQL file to {sql_path}...")
    
    os.makedirs(os.path.dirname(sql_path), exist_ok=True)
    
    with open(sql_path, "w", encoding="utf-8") as f:
        f.write("-- ================================================================================\n")
        f.write("-- ECHOBREAKER — 200 CONTRARIAN BLOGS SEED DATA\n")
        f.write("-- Run this in your Supabase SQL Editor (Dashboard → SQL Editor → New query)\n")
        f.write("-- ================================================================================\n\n")
        
        f.write("-- 1. Ensure default author user exists\n")
        f.write("INSERT INTO users (username, email, password_hash, is_verified_author, is_active)\n")
        f.write("VALUES ('editor', 'editor@echobreaker.com', 'pbkdf2_sha256$100000$a94b895f324838$1c3b526f8a9a6b5c7d8e', TRUE, TRUE)\n")
        f.write("ON CONFLICT (email) DO NOTHING;\n\n")
        
        f.write("-- 2. Seed 200 Tags & Blog Articles\n")
        
        for idx, blog in enumerate(blogs, 1):
            # Escape single quotes in SQL strings
            safe_tag = blog['tag'].replace("'", "''")
            safe_title = blog['title'].replace("'", "''")
            safe_content = blog['content'].replace("'", "''")
            views = random.randint(5, 150)
            
            f.write(f"-- Blog {idx}: {blog['tag']}\n")
            f.write(f"INSERT INTO tags (name) VALUES ('{safe_tag}') ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name;\n")
            f.write("INSERT INTO articles (author_id, title, content, view_count, status, published_at)\n")
            f.write(f"VALUES ((SELECT user_id FROM users WHERE email='editor@echobreaker.com'), '{safe_title}', '{safe_content}', {views}, 'PUBLISHED', NOW() - INTERVAL '{random.randint(1, 30)} days')\n")
            f.write("ON CONFLICT DO NOTHING;\n")
            f.write("INSERT INTO article_tags (article_id, tag_id)\n")
            f.write(f"VALUES ((SELECT article_id FROM articles WHERE title='{safe_title}' LIMIT 1), (SELECT tag_id FROM tags WHERE name='{safe_tag}' LIMIT 1))\n")
            f.write("ON CONFLICT DO NOTHING;\n\n")
            
        f.write("-- ================================================================================\n")
        f.write("-- END OF SEED SCRIPT\n")
        f.write("-- ================================================================================\n")
        
    print("SQL seed file successfully created!")

def seed_db_directly(blogs):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL is not set. Skipping direct database seeding. (You can still run the SQL file.)")
        return
        
    print("DATABASE_URL is set! Seeding database directly...")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # 1. Ensure user
        cur.execute(
            """
            INSERT INTO users (username, email, password_hash, is_verified_author, is_active)
            VALUES ('editor', 'editor@echobreaker.com', 'pbkdf2_sha256$100000$a94b895f324838$1c3b526f8a9a6b5c7d8e', TRUE, TRUE)
            ON CONFLICT (email) DO NOTHING
            """
        )
        cur.execute("SELECT user_id FROM users WHERE email = 'editor@echobreaker.com'")
        author_id = cur.fetchone()[0]
        
        # 2. Seed
        for idx, blog in enumerate(blogs, 1):
            cur.execute(
                "INSERT INTO tags (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING tag_id",
                (blog['tag'],)
            )
            tag_id = cur.fetchone()[0]
            
            cur.execute(
                """
                INSERT INTO articles (author_id, title, content, view_count, status, published_at)
                VALUES (%s, %s, %s, %s, 'PUBLISHED', NOW() - INTERVAL '%s days')
                RETURNING article_id
                """,
                (author_id, blog['title'], blog['content'], random.randint(5, 150), random.randint(1, 30))
            )
            article_id = cur.fetchone()[0]
            
            cur.execute(
                "INSERT INTO article_tags (article_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (article_id, tag_id)
            )
            
        conn.commit()
        print("Direct database seeding completed successfully!")
    except Exception as e:
        print("Failed to seed database directly:", e)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    blogs = generate_blogs()
    write_sql_file(blogs)
    seed_db_directly(blogs)
