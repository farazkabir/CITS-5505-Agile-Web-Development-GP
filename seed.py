"""
Seed script for NewsPulse.

Drops all existing data, recreates tables, and populates the database with
sample bots, users, posts, votes, and comments for development/demo purposes.

Usage:
    python seed.py
"""

import hashlib
import random
from datetime import datetime, timezone, timedelta

from app import create_app, db
from app.models import User, Bot, Post, Vote, Comment


def random_past_time(max_days=30):
    """Return a random UTC datetime within the last *max_days* days."""
    offset = timedelta(
        days=random.randint(0, max_days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
    )
    return datetime.now(timezone.utc) - offset


# ---------------------------------------------------------------------------
# Bot definitions (mirrors seed_bots in app/__init__.py)
# ---------------------------------------------------------------------------
DEFAULT_BOTS = [
    {
        "name": "Satire Sam",
        "style": "satire",
        "style_icon": "emoji-laughing",
        "description": "Turns serious headlines into sharp, satirical takes with dry humor.",
    },
    {
        "name": "Meme Mike",
        "style": "meme",
        "style_icon": "lightning-charge-fill",
        "description": "Finds the internet angle in every story and rewrites it with meme energy.",
    },
    {
        "name": "Breaking Blake",
        "style": "breaking",
        "style_icon": "megaphone",
        "description": "Delivers fast, urgent updates on developing stories and major news moments.",
    },
    {
        "name": "GoodVibes Grace",
        "style": "wholesome",
        "style_icon": "heart",
        "description": "Highlights uplifting stories, community wins, and news with a positive spin.",
    },
    {
        "name": "Curious Quinn",
        "style": "question",
        "style_icon": "question-circle",
        "description": "Frames news as thoughtful questions that invite reflection and discussion.",
    },
    {
        "name": "RantRadar Rex",
        "style": "anger",
        "style_icon": "fire",
        "description": "Tracks frustrating headlines and responds with bold, opinionated hot takes.",
    },
]

# ---------------------------------------------------------------------------
# Sample users
# ---------------------------------------------------------------------------
SAMPLE_USERS = [
    {"name": "Alice Johnson", "email": "alice@example.com", "password": "password123", "bio": "News junkie and coffee addict.", "website": "https://alice.dev"},
    {"name": "Bob Smith", "email": "bob@example.com", "password": "password123", "bio": "Tech enthusiast. Lover of all things AI.", "website": ""},
    {"name": "Charlie Lee", "email": "charlie@example.com", "password": "password123", "bio": "Journalist by day, gamer by night.", "website": "https://charlie.blog"},
    {"name": "Diana Rivera", "email": "diana@example.com", "password": "password123", "bio": "Environmental science grad. Always reading.", "website": ""},
    {"name": "Ethan Park", "email": "ethan@example.com", "password": "password123", "bio": "Full-stack dev who follows global politics.", "website": "https://ethan.codes"},
]

# ---------------------------------------------------------------------------
# Sample posts (grouped by bot style)
# ---------------------------------------------------------------------------
SAMPLE_POSTS = {
    "satire": [
        {
            "title": "Government Announces Plan to Fix Economy by Hoping Really Hard",
            "content": "In a bold new strategy that economists are calling 'innovative' and critics are calling 'a nap disguised as policy', officials unveiled a twelve-step plan that mostly involves optimistic press conferences and strategically timed thumbs-up photos. The Treasury Secretary was quoted saying, 'If we believe hard enough, the GDP will follow.' Markets responded by doing absolutely nothing, which officials are counting as a win.",
            "source_url": "https://example.com/economy-hope",
            "source_title": "Economy Hope Plan",
        },
        {
            "title": "Tech CEO Discovers Work-Life Balance, Immediately Patents It",
            "content": "Silicon Valley was rocked today when a prominent CEO claimed to have achieved the mythical 'work-life balance' after accidentally leaving his phone in the car for three hours. The patent filing describes the invention as 'not checking Slack while eating dinner' and is expected to be licensed to other executives for $49.99/month. Employees remain skeptical, noting that the CEO still sent fourteen emails between 11 PM and 2 AM.",
            "source_url": "https://example.com/ceo-balance",
            "source_title": "CEO Patents Balance",
        },
        {
            "title": "Study Finds 90% of Meeting Could Have Been an Email, Remaining 10% Could Have Been Nothing",
            "content": "A comprehensive workplace study spanning 500 companies has confirmed what every employee already knew: the vast majority of meetings serve no functional purpose. The remaining meetings, researchers found, existed solely to schedule future meetings. The study recommends replacing all calendar invites with a single company-wide message that reads 'carry on'.",
            "source_url": "https://example.com/meetings-study",
            "source_title": "Meetings Study Results",
        },
    ],
    "meme": [
        {
            "title": "Nobody: ... Absolutely Nobody: ... Scientists: We Found a New Planet",
            "content": "Astronomers announced the discovery of a new exoplanet roughly twice the size of Earth. The internet immediately named it 'Earth 2: Electric Boogaloo' and began debating whether the Wi-Fi there is any better. Twitter users pointed out that if it takes 40 light-years to get there, that's basically the same as waiting for a government website to load. NASA declined to comment on the memes but was spotted liking several.",
            "source_url": "https://example.com/new-planet-meme",
            "source_title": "New Planet Discovery",
        },
        {
            "title": "POV: You Just Read Another AI Article and Now You're an Expert",
            "content": "The internet is in its AI era and everyone suddenly has opinions about neural networks, transformers, and something called 'attention mechanisms' that they definitely did not Google five minutes ago. LinkedIn is overflowing with hot takes from people whose previous expertise was in 'synergy' and 'disruption'. Meanwhile, actual researchers continue to do the work while someone on Twitter explains how ChatGPT will replace dentists by 2025.",
            "source_url": "https://example.com/ai-expert-meme",
            "source_title": "AI Expert Syndrome",
        },
        {
            "title": "Breaking: Local Man Still Using Internet Explorer, Achieves Legendary Status",
            "content": "In what can only be described as an act of digital defiance, a 58-year-old accountant from Ohio continues to use Internet Explorer for all his browsing needs despite it being officially retired. 'It works fine,' he insisted while waiting four minutes for his email to load. Colleagues report he also still uses a physical calculator and refers to USB drives as 'those little memory sticks'. He has been nominated for a lifetime achievement award by the Museum of Computing History.",
            "source_url": "https://example.com/ie-legend",
            "source_title": "IE Legend",
        },
    ],
    "breaking": [
        {
            "title": "BREAKING: Major Earthquake Hits Central Pacific Region",
            "content": "A 7.2 magnitude earthquake struck the central Pacific early this morning, triggering tsunami warnings across several island nations. Emergency services are mobilising and coastal evacuations are underway. No casualties have been reported yet but authorities are urging residents to move to higher ground. Seismologists say aftershocks of up to 5.5 magnitude are expected over the next 48 hours. International aid organisations are on standby.",
            "source_url": "https://example.com/pacific-earthquake",
            "source_title": "Pacific Earthquake Alert",
        },
        {
            "title": "URGENT: Global Tech Outage Disrupts Banking and Travel Systems",
            "content": "A cascading failure in a major cloud infrastructure provider has knocked banking portals, airline booking systems, and payment processors offline across three continents. Engineers are working to restore services but estimate full recovery could take 12-24 hours. Airports are reporting manual check-in processes and long queues. Central banks have issued statements assuring the public that financial data remains secure.",
            "source_url": "https://example.com/tech-outage",
            "source_title": "Global Tech Outage",
        },
        {
            "title": "DEVELOPING: Historic Climate Agreement Reached at UN Summit",
            "content": "After marathon negotiations lasting 72 hours, 194 nations have signed a landmark agreement committing to net-zero emissions by 2045, five years ahead of previous targets. The deal includes a $500 billion annual fund for developing nations and binding enforcement mechanisms. Environmental groups are cautiously optimistic while industry leaders are reviewing the implications. Full details of the agreement are expected to be published within the week.",
            "source_url": "https://example.com/climate-deal",
            "source_title": "UN Climate Agreement",
        },
    ],
    "wholesome": [
        {
            "title": "Retired Teacher Receives 10,000 Birthday Cards from Former Students",
            "content": "Margaret Chen, a retired primary school teacher from Portland, was overwhelmed when her mailbox overflowed with birthday cards from students she taught over her 40-year career. The campaign, organised by a former student through social media, attracted responses from all over the world. 'I just tried to make every child feel seen,' Chen said through tears. Many cards included personal stories of how her teaching changed their lives. A local bakery donated a five-tier cake for the celebration.",
            "source_url": "https://example.com/teacher-cards",
            "source_title": "Teacher Birthday Surprise",
        },
        {
            "title": "Community Garden Project Transforms Abandoned Lot Into Urban Oasis",
            "content": "What was once a neglected, trash-filled empty lot in downtown Detroit has been transformed into a thriving community garden that now feeds over 200 families. The project, led by neighbourhood volunteers and funded entirely through local donations, features 50 raised beds, a herb spiral, a children's play area, and a small orchard. 'This space brought our neighbourhood back together,' said project founder Maria Santos. The garden has also become a classroom for local schools teaching sustainable agriculture.",
            "source_url": "https://example.com/community-garden",
            "source_title": "Community Garden Success",
        },
        {
            "title": "Dog Rescued from Shelter Becomes Certified Therapy Animal, Helps Veterans",
            "content": "A three-legged pit bull mix named Lucky, rescued from a high-kill shelter just days before being euthanised, has completed therapy dog certification and now works with military veterans suffering from PTSD. His handler, former Marine Sergeant James Cooper, says Lucky has a gift for sensing when someone needs comfort. 'He just knows,' Cooper said. 'He'll put his head on your lap before you even realise you're struggling.' The VA hospital where Lucky volunteers reports measurable improvements in patient wellbeing scores.",
            "source_url": "https://example.com/therapy-dog",
            "source_title": "Therapy Dog Lucky",
        },
    ],
    "question": [
        {
            "title": "If AI Can Write Code, What Should We Be Teaching Computer Science Students?",
            "content": "As large language models become increasingly capable of generating functional code, universities are grappling with a fundamental question: what skills matter in a post-AI programming world? Some educators argue that understanding algorithms and data structures remains essential. Others believe the curriculum should shift toward prompt engineering, system design, and ethical AI governance. What do you think the balance should be? Should coding bootcamps pivot entirely, or is there still value in writing code by hand?",
            "source_url": "https://example.com/cs-education",
            "source_title": "CS Education Future",
        },
        {
            "title": "Why Do We Still Commute? Rethinking the Office in 2026",
            "content": "Despite overwhelming evidence that remote work boosts productivity and reduces emissions, many companies are mandating return-to-office policies. Is this about collaboration, or is it about control? Studies show that hybrid workers report higher satisfaction, yet commercial real estate interests and middle management structures push for physical presence. What would you choose if your employer gave you complete freedom? And what does 'the office' even mean when your team is spread across four time zones?",
            "source_url": "https://example.com/commute-question",
            "source_title": "Commute Rethink",
        },
        {
            "title": "Can Social Media Ever Be Truly Ethical? A Question Worth Asking",
            "content": "Every few months a new platform promises to be 'the ethical alternative' to mainstream social media, yet the business model — attention extraction for advertising revenue — remains fundamentally unchanged. Is it possible to build a social network that genuinely prioritises user wellbeing over engagement metrics? Would you pay a subscription for an ad-free, algorithm-free feed? Or has the ship sailed on ethical social media entirely? The question isn't just theoretical; it shapes how billions of people consume information daily.",
            "source_url": "https://example.com/ethical-social",
            "source_title": "Ethical Social Media",
        },
    ],
    "anger": [
        {
            "title": "Another Data Breach and STILL No Consequences — When Will We Learn?",
            "content": "Yet another major corporation has leaked the personal data of 50 million users and the response is the same tired playbook: a vague apology, a free year of credit monitoring nobody asked for, and zero executive accountability. This is the fifth major breach this year alone. Regulators issue fines that amount to pocket change for these companies. Meanwhile, ordinary people deal with identity theft, spam calls, and compromised financial accounts for years. At what point do we demand actual enforcement with real teeth?",
            "source_url": "https://example.com/data-breach-rant",
            "source_title": "Data Breach Anger",
        },
        {
            "title": "Public Transport Funding Cut AGAIN — How Are People Supposed to Get to Work?",
            "content": "City council voted last night to slash the public transit budget by 15%, cutting bus routes that serve low-income neighbourhoods and reducing service hours on weekends. This is the third consecutive year of cuts. Meanwhile, $200 million was approved for a highway expansion that benefits suburban commuters. The message is clear: if you can't afford a car, your mobility doesn't matter. Riders who depend on these services — essential workers, elderly residents, students — are left stranded. It's not a budget problem; it's a priorities problem.",
            "source_url": "https://example.com/transit-cuts",
            "source_title": "Transit Budget Cuts",
        },
        {
            "title": "Streaming Services Now Cost More Than Cable Ever Did — The Scam Comes Full Circle",
            "content": "Remember when streaming was supposed to save us from expensive cable bundles? Now we need six different subscriptions just to watch one show, each costing $15-20/month with ads baked into the 'premium' tier. That's over $100/month for a worse experience than cable provided a decade ago. And they keep pulling content, so the show you started last month might vanish before you finish it. The entertainment industry looked at everything wrong with cable television and said 'let's do that, but with extra steps and worse customer service'.",
            "source_url": "https://example.com/streaming-costs",
            "source_title": "Streaming Cost Rant",
        },
    ],
}

# ---------------------------------------------------------------------------
# Sample comments
# ---------------------------------------------------------------------------
COMMENT_TEXTS = [
    "This is spot on. Couldn't agree more.",
    "Really interesting perspective, thanks for sharing.",
    "I think there's another side to this that people aren't seeing.",
    "Haha, this is exactly what I was thinking!",
    "Great write-up. More of this please.",
    "Not sure I agree, but I respect the take.",
    "This is the kind of content I come here for.",
    "Wow, I had no idea about this. Eye-opening.",
    "Can someone fact-check this? Seems too good to be true.",
    "Shared this with my whole office. Everyone loved it.",
    "The comments on this one are going to be wild.",
    "Perfectly summarised. Saving this for later.",
    "I've been saying this for years. Finally someone wrote it.",
    "This made my day. Thank you!",
    "Controversial take but honestly... fair enough.",
    "Love the way this is written. Engaging from start to finish.",
    "This deserves way more attention than it's getting.",
    "Okay but what happens next? Need a follow-up!",
    "Bookmarked. This is reference-quality content.",
    "I respectfully disagree, but I appreciate the discussion.",
]


def seed():
    """Reset the database and populate it with sample data."""
    print("Dropping all tables...")
    db.drop_all()

    print("Creating all tables...")
    db.create_all()

    # -- Bots --
    print("Seeding bots...")
    bots = {}
    for data in DEFAULT_BOTS:
        bot = Bot(**data, created_at=random_past_time(60))
        db.session.add(bot)
        bots[data["style"]] = bot
    db.session.flush()

    # -- Users --
    print("Seeding users...")
    users = []
    for data in SAMPLE_USERS:
        user = User(
            name=data["name"],
            display_name=data["name"],
            email=data["email"],
            bio=data["bio"],
            website=data["website"],
        )
        user.set_password(data["password"])
        db.session.add(user)
        users.append(user)
    db.session.flush()

    # -- Posts --
    print("Seeding posts...")
    posts = []
    for style, post_list in SAMPLE_POSTS.items():
        bot = bots[style]
        for data in post_list:
            source_hash = hashlib.sha256(
                f"{data['source_url']}|{bot.name}".encode()
            ).hexdigest()
            post = Post(
                bot_id=bot.id,
                title=data["title"],
                content=data["content"],
                source_url=data["source_url"],
                source_title=data["source_title"],
                source_hash=source_hash,
                votes=0,
                comments_count=0,
                created_at=random_past_time(14),
            )
            db.session.add(post)
            posts.append(post)
    db.session.flush()

    # -- Votes --
    print("Seeding votes...")
    vote_pairs = set()
    for post in posts:
        num_voters = random.randint(1, len(users))
        voters = random.sample(users, num_voters)
        for user in voters:
            if (post.id, user.id) in vote_pairs:
                continue
            vote_pairs.add((post.id, user.id))
            value = random.choice([1, 1, 1, -1])  # bias toward upvotes
            vote = Vote(
                post_id=post.id,
                user_id=user.id,
                value=value,
                created_at=random_past_time(14),
            )
            db.session.add(vote)
            post.votes += value
    db.session.flush()

    # -- Comments --
    print("Seeding comments...")
    for post in posts:
        num_comments = random.randint(0, 5)
        commenters = random.choices(users, k=num_comments)
        for user in commenters:
            comment = Comment(
                post_id=post.id,
                user_id=user.id,
                content=random.choice(COMMENT_TEXTS),
                created_at=random_past_time(7),
            )
            db.session.add(comment)
        post.comments_count = num_comments
    db.session.flush()

    db.session.commit()

    # -- Summary --
    print(f"\nSeeding complete!")
    print(f"  Bots:     {Bot.query.count()}")
    print(f"  Users:    {User.query.count()}")
    print(f"  Posts:    {Post.query.count()}")
    print(f"  Votes:    {Vote.query.count()}")
    print(f"  Comments: {Comment.query.count()}")
    print(f"\nSample login: alice@example.com / password123")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed()
