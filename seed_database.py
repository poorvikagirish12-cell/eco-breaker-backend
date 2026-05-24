import os
import psycopg2
from psycopg2.extras import RealDictCursor
from database import get_connection

TAGS_DATA = [
    ("Artificial Intelligence", "Why AI Will Make Us More Human, Not Less", 
     "In this contrarian piece, we explore how AI handles repetitive tasks, freeing human minds for creative and empathetic pursuits."),
    ("Quantum Computing", "The Hype of Quantum Computing: Why We Are Decades Away", 
     "While media outlets hype quantum dominance, practical, error-corrected quantum computers are much further away than promised."),
    ("Space Exploration", "Mars is a Dead End: The Case for Earth's Oceans", 
     "Instead of spending trillions trying to colonize a lifeless desert like Mars, we should explore our own deep oceans."),
    ("Climate Change", "Why Carbon Taxes Fail and Green Subsidies Win", 
     "Punitive taxes lead to political backlash. Subsidizing clean energy innovation is the only politically viable way forward."),
    ("Biotechnology", "The Danger of Curing All Diseases", 
     "Eradicating natural death from disease could lead to catastrophic population pressure and cultural stagnation."),
    ("Cryptography", "Why Perfect Encryption is a Threat to a Free Society", 
     "If governments cannot access any communication, we lose the ability to prevent organized crime and coordinate security."),
    ("Cybersecurity", "Embracing Vulnerability: The Myth of Total Security", 
     "Instead of chasing the impossible dream of unhackable systems, organizations should build highly resilient networks."),
    ("Renewable Energy", "Why Solar Power Alone Cannot Save the Grid", 
     "Without massive breakthroughs in battery storage, solar energy cannot solve the baseload demands of modern cities."),
    ("Robotics", "How Robots Will Save the Working Class", 
     "Rather than stealing jobs, automation will liberate laborers from dangerous and backbreaking work, elevating quality of life."),
    ("Metaverse", "Why the Metaverse is a Regressive Vision", 
     "Seeking isolation in digital headsets is a symptom of societal decline, not a path to human advancement."),
    ("Mental Health", "The Paradox of Happiness: Why Sadness is Essential", 
     "Our obsession with toxic positivity is making us more depressed. True mental health requires accepting negative emotions."),
    ("Education Reform", "Standardized Testing is Bad, But Grades are Necessary", 
     "While rote testing should go, removing academic grading entirely results in grade inflation and lower standards."),
    ("Global Economy", "The Myth of Unlimited Growth", 
     "Our financial systems rely on exponential growth, but we live on a finite planet. We must design steady-state economics."),
    ("Nanotechnology", "Grey Goo and Real Risks of Molecular Tech", 
     "The sci-fi fear of self-replicating nanobots distracts us from the real threat: weaponized nanoparticles in the atmosphere."),
    ("Neuroscience", "Free Will is an Illusion, But We Must Act as if it Exists", 
     "Neuroscience suggests decisions are made before we consciously realize them, but belief in choice keeps society intact."),
    ("Astronomy", "The Case Against Searching for Extraterrestrial Life", 
     "Broadcasting our presence to the universe (METI) might invite hostile civilizations. We should stay quiet and listen."),
    ("Philosophy", "Why Cynicism is the New Optimism", 
     "By expecting less from people and systems, we appreciate small successes and avoid disillusionment."),
    ("Digital Privacy", "Why You Should Care Less About Data Tracking", 
     "Targeted advertising is a minor annoyance compared to the massive benefits of free, highly personalized web services."),
    ("Web3", "Web3: A Solution in Search of a Problem", 
     "Decentralization adds latency and complexity. Most users prefer centralized, efficient services with customer support."),
    ("Genetic Engineering", "Designer Babies: The Case for Enhancing Humanity", 
     "Rather than fear genetic selection, we should use it to eliminate hereditary diseases and boost human cognitive potential."),
    ("Fusion Energy", "Why Nuclear Fusion is Always 30 Years Away", 
     "The engineering hurdles of maintaining plasma stability are so immense that fusion will remain a laboratory curiosity for decades."),
    ("Remote Work", "The Lonely Screen: Why Remote Work Destroys Creativity", 
     "Zoom cannot replace physical friction. Great innovations happen through spontaneous hallway encounters, not scheduled calls."),
    ("Urban Farming", "The Inefficiency of Rooftop Gardens", 
     "Rooftop farming is a greenwashed gimmick. Rural agriculture is thousands of times more energy-efficient and scalable."),
    ("Electric Vehicles", "Electric Vehicles: Shifting Pollution, Not Stopping It", 
     "EVs rely on grids powered by coal and gas. True green transit means investing in high-quality electrified public trains."),
    ("3D Printing", "3D Printing Will Not Revolutionize Manufacturing", 
     "Injection molding and traditional tooling are vastly superior for mass production. 3D printing remains a prototyping tool."),
    ("Oceanography", "Deep Sea Mining: A Necessary Evil", 
     "To get battery minerals for the green transition, mining lifeless abyssal plains is better than mining biodiverse rainforests."),
    ("History", "Why We Misunderstand the Dark Ages", 
     "The medieval period was a time of rapid scientific, agricultural, and artistic progress, not intellectual darkness."),
    ("Classical Music", "Why Modern Pop Music is Structurally Boring", 
     "Pop songs have become shorter, less harmonically complex, and dynamically flat due to algorithmic streaming incentives."),
    ("Modern Art", "The Skillful Craft Hidden in Abstract Expressionism", 
     "Splattering paint is not random. It requires deep knowledge of viscosity, color theory, and spatial balance."),
    ("Creative Writing", "Why AI Writing Tools Make Better Editors Than Authors", 
     "Generative AI excels at syntax corrections and structural critiques, but lacks the lived experience to write original prose."),
    ("Micro-mobility", "The Menace of Electric Scooters on Sidewalks", 
     "Rental scooters clutter walkways and cause pedestrian accidents. We need dedicated micro-lanes, not sidewalk sharing."),
    ("Minimalism", "The Bourgeois Illusion of Minimalist Living", 
     "Minimalism is a luxury of the rich who can afford to buy things only when they need them, rather than storing them."),
    ("Smart Cities", "The Smart City is a Privacy Nightmare", 
     "Sensor-laden cities turn public space into a panopticon, stripping citizens of their right to move anonymously."),
    ("Astrophysics", "Why Dark Matter Might Not Exist", 
     "Instead of inventing invisible matter to fit our gravity formulas, we should modify our understanding of gravity itself."),
    ("Behavioral Economics", "Why Humans are Rationally Irrational", 
     "Our cognitive shortcuts (heuristics) are not bugs; they are evolutionary features that helped us survive in the wild."),
    ("Deep Learning", "Neural Networks are Not Brains", 
     "Deep learning models are statistical pattern matchers, completely lacking the symbolic reasoning and conceptual understanding of brains."),
    ("Augmented Reality", "AR Will Succeed Where VR Failed", 
     "Virtual reality isolates users, while augmented reality enhances our interactions with the physical world, making it socially viable."),
    ("Sustainable Fashion", "The Greenwashing of Organic Cotton", 
     "Organic cotton requires significantly more water and land than conventional cotton, rendering it less sustainable in bulk."),
    ("Telemedicine", "Why the Virtual Doctor Cannot Replace the Stethoscope", 
     "Physical exams reveal subtle signs (smell, skin texture, micro-expressions) that are lost over compressed video streams."),
    ("Drone Tech", "The Threat of Drone Deliveries to Urban Quiet", 
     "If every package is delivered by drone, the sky will buzz constantly, creating severe noise pollution in residential areas."),
    ("Food Tech", "Lab-Grown Meat is a Tech Bro Fantasy", 
     "The bioreactor capacity required to replace even 1% of global meat consumption is economically and physically unfeasible."),
    ("Cognitive Science", "Why Multi-Tasking is a Cognitive Lie", 
     "The brain cannot focus on two tasks at once; it rapidly switches attention, draining energy and lowering performance."),
    ("Astrobiology", "Life in the Universe is Likely Microscopic", 
     "Intelligence is an evolutionary fluke. If we find alien life, it will likely be bacterial film, not stellar travelers."),
    ("Blockchain", "Blockchain: The World's Slowest Database", 
     "Decentralization requires consensus protocols that limit transaction throughput, making blockchains useless for high-speed apps."),
    ("High-Speed Rail", "Why Hyperloops are a Distraction from High-Speed Rail", 
     "Vacuum tube transport introduces single points of failure. We should build proven high-speed bullet trains instead."),
    ("Social Media", "The Case for Banning Algorithmic Feeds", 
     " chronological feeds respect user agency; algorithmic feeds exploit dopamine loops to maximize outrage and screen time."),
    ("Philosophy of Mind", "Consciousness is Not a Software Program", 
     "Computers manipulate symbols without understanding them. Consciousness is biological and cannot be duplicated in silicon."),
    ("Marine Biology", "Why Saving Coral Reefs Requires Global Cooling, Not Gardening", 
     "Local coral restoration projects are band-aids. If ocean temperatures continue to rise, all planted corals will bleach and die."),
    ("Macroeconomics", "Inflation is Not Always a Monetary Phenomenon", 
     "Supply chain shocks, geopolitical conflicts, and corporate pricing power drive inflation far more than central bank money printing."),
    ("Renewable Power", "The Geopolitical Risk of the Green Transition", 
     "Moving away from oil does not end resource dependency; it shifts power to nations controlling lithium, cobalt, and rare earths.")
]

def seed_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL environment variable is not set. Please set it to connect to Supabase.")
        return

    print("Connecting to database...")
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        # 1. Ensure default author user exists
        print("Ensuring default author exists...")
        cur.execute("SELECT user_id FROM users WHERE username = 'editor' OR email = 'editor@echobreaker.com'")
        user_row = cur.fetchone()
        
        if user_row:
            author_id = user_row["user_id"]
            print(f"Using existing author ID: {author_id}")
        else:
            # Create a default verified author
            cur.execute(
                """
                INSERT INTO users (username, email, password_hash, is_verified_author, is_active)
                VALUES ('editor', 'editor@echobreaker.com', 'pbkdf2_sha256$100000$a94b895f324838$1c3b526f8a9a6b5c7d8e', TRUE, TRUE)
                RETURNING user_id
                """
            )
            author_id = cur.fetchone()["user_id"]
            print(f"Created new author ID: {author_id}")

        # 2. Insert tags and articles
        print(f"Seeding {len(TAGS_DATA)} tags and blogs...")
        for tag_name, title, content in TAGS_DATA:
            # Insert Tag
            cur.execute(
                "INSERT INTO tags (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING tag_id",
                (tag_name,)
            )
            tag_id = cur.fetchone()["tag_id"]
            
            # Insert Article
            cur.execute(
                """
                INSERT INTO articles (author_id, title, content, view_count, status, published_at)
                VALUES (%s, %s, %s, %s, 'PUBLISHED', NOW())
                ON CONFLICT DO NOTHING
                RETURNING article_id
                """,
                (author_id, title, content, 25) # Give it some initial views
            )
            article_row = cur.fetchone()
            
            if article_row:
                article_id = article_row["article_id"]
                # Associate tag with article
                cur.execute(
                    "INSERT INTO article_tags (article_id, tag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (article_id, tag_id)
                )
        
        conn.commit()
        print("Database successfully seeded with 50 tags and contrarian articles!")
    except Exception as e:
        print("Error during database seeding:", e)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    seed_db()
