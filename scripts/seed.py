"""Populate the database with demo users, questions and experiences.

Usage:  python -m scripts.seed
Demo logins (password for all: Demo@1234):
    admin@interviewhub.dev      (admin)
    mod@interviewhub.dev        (moderator)
    student@interviewhub.dev    (student)
"""
from sqlalchemy import select

from app.core.database import SessionLocal, init_db
from app.modules.auth import schemas as auth_schemas
from app.modules.auth import service as auth_service
from app.modules.auth.models import User
from app.modules.experiences import schemas as exp_schemas
from app.modules.experiences import service as exp_service
from app.modules.questions import service as q_service
from app.modules.questions.schemas import QuestionCreate

PASSWORD = "Demo@1234"

QUESTIONS = [
    # (text, topic, difficulty, company, role, tags, model_answer)
    ("Explain the difference between a process and a thread.", "os", "easy", "Infosys", "Software Engineer",
     ["process", "thread"],
     "A process is an independent program in execution with its own address space, while a thread is a "
     "lightweight unit of execution inside a process that shares memory and resources with sibling threads. "
     "Context switching between threads is cheaper. Threads need synchronization such as mutex or semaphore."),
    ("What is a deadlock and what are the four necessary conditions?", "os", "medium", "Wipro", "Software Engineer",
     ["deadlock", "concurrency"],
     "Deadlock occurs when processes wait forever for resources held by each other. The Coffman conditions are "
     "mutual exclusion, hold and wait, no preemption and circular wait. Prevention breaks one condition; "
     "avoidance uses banker's algorithm."),
    ("Explain virtual memory and paging.", "os", "medium", "Intel", "Systems Engineer", ["memory", "paging"],
     "Virtual memory gives each process an address space larger than physical memory. Pages map to frames via a "
     "page table; the TLB caches translations; a page fault loads a missing page from disk."),
    ("What are ACID properties in a database?", "dbms", "easy", "Oracle", "Software Engineer", ["transactions"],
     "Atomicity means all or nothing, consistency keeps constraints valid, isolation means concurrent "
     "transactions do not interfere, durability means committed data survives crashes via logging."),
    ("Explain normalization up to BCNF with an example.", "dbms", "medium", "TCS", "Software Engineer",
     ["normalization"],
     "Normalization removes redundancy. 1NF atomic values, 2NF no partial dependency on a composite key, 3NF no "
     "transitive dependency, BCNF every determinant is a candidate key."),
    ("What is the difference between clustered and non-clustered indexes?", "dbms", "medium", "Microsoft",
     "Software Engineer", ["index"],
     "A clustered index defines the physical order of rows and there is only one per table. A non-clustered index "
     "is a separate structure with pointers to rows; a table can have many. B-tree is typical."),
    ("Write a SQL query to find the second highest salary.", "dbms", "easy", "Accenture", "Associate Engineer",
     ["sql"],
     "SELECT MAX(salary) FROM employee WHERE salary < (SELECT MAX(salary) FROM employee); or use DENSE_RANK "
     "window function, or ORDER BY salary DESC LIMIT 1 OFFSET 1 with DISTINCT."),
    ("Reverse a linked list iteratively and recursively.", "dsa", "easy", "Amazon", "SDE Intern",
     ["linked-list"],
     "Iterative: keep prev, current and next pointers; point current.next to prev and advance. O(n) time O(1) "
     "space. Recursive: reverse the rest then set head.next.next to head and head.next to null."),
    ("Find the longest substring without repeating characters.", "dsa", "medium", "Amazon", "SDE",
     ["sliding-window", "string", "hashing"],
     "Use a sliding window with a hashmap of last seen index. Move the left pointer past a repeated character. "
     "Track the maximum window length. O(n) time."),
    ("Detect a cycle in a directed graph.", "dsa", "medium", "Google", "SDE",
     ["graph", "dfs"],
     "Run DFS with three colours or a recursion stack; a back edge to a node on the stack means a cycle. "
     "Alternatively Kahn's topological sort: if not all nodes are processed there is a cycle."),
    ("Explain the difference between BFS and DFS and when you would use each.", "dsa", "easy", "Flipkart",
     "SDE Intern", ["graph", "bfs", "dfs"],
     "BFS explores level by level using a queue and finds shortest paths in unweighted graphs. DFS goes deep using "
     "a stack or recursion and suits topological sort, cycle detection and connected components."),
    ("Find the kth largest element in an array.", "dsa", "medium", "Microsoft", "SDE", ["heap", "quickselect"],
     "Use a min heap of size k: push each element and pop when size exceeds k, O(n log k). Quickselect gives "
     "average O(n)."),
    ("Solve the 0/1 knapsack problem.", "dsa", "hard", "Goldman Sachs", "Analyst", ["dynamic-programming"],
     "Dynamic programming: dp[i][w] is the best value using first i items with capacity w; either skip item i or "
     "take it if weight fits. O(nW) time, can be reduced to O(W) space."),
    ("Merge k sorted lists.", "dsa", "hard", "Google", "SDE", ["heap", "linked-list"],
     "Push the head of each list into a min heap; pop the smallest, append it, push its next. O(N log k)."),
    ("Explain the four pillars of OOP with examples.", "oop", "easy", "Infosys", "Software Engineer",
     ["oop"],
     "Encapsulation hides state behind methods, abstraction exposes essential behaviour, inheritance reuses a "
     "parent class, polymorphism lets one interface have many implementations via overriding or overloading."),
    ("What is the difference between an abstract class and an interface?", "oop", "easy", "Cognizant",
     "Programmer Analyst", ["oop", "java"],
     "An abstract class can have state, constructors and implemented methods and supports single inheritance. An "
     "interface defines a contract; a class can implement many interfaces. Use interfaces for capabilities."),
    ("Explain SOLID principles.", "oop", "medium", "Thoughtworks", "Application Developer", ["design-principles"],
     "Single responsibility, open closed, Liskov substitution, interface segregation and dependency inversion. "
     "Together they make code modular, testable and extensible."),
    ("What happens when you type a URL into the browser?", "networks", "medium", "Google", "SDE",
     ["dns", "http", "tcp"],
     "DNS resolution finds the IP, a TCP handshake opens a connection, TLS negotiates encryption, the browser sends "
     "an HTTP request, the server responds, and the browser parses HTML, fetches assets and renders."),
    ("Difference between TCP and UDP.", "networks", "easy", "Cisco", "Network Engineer", ["tcp", "udp"],
     "TCP is connection oriented, reliable, ordered with flow and congestion control. UDP is connectionless, "
     "lightweight and has no delivery guarantee; used for streaming, gaming and DNS."),
    ("Design a URL shortener.", "system-design", "medium", "Amazon", "SDE", ["scalability", "hashing"],
     "Generate a short key using base62 of an id or a hash, store key to URL in a key value store, redirect with "
     "301 or 302, add caching, rate limiting, analytics and handle collisions and expiry."),
    ("Design a rate limiter.", "system-design", "hard", "Uber", "SDE", ["rate-limiting", "redis"],
     "Use token bucket or sliding window counters per client stored in Redis with atomic operations; return 429 "
     "when exceeded; distribute with consistent hashing."),
    ("Explain bias-variance tradeoff.", "ml", "medium", "Microsoft", "ML Engineer", ["ml"],
     "Bias is error from overly simple assumptions causing underfitting; variance is sensitivity to training data "
     "causing overfitting. Regularization, more data and cross validation help find the balance."),
    ("How does gradient descent work? Compare batch, stochastic and mini-batch.", "ml", "medium", "NVIDIA",
     "ML Engineer", ["optimization"],
     "Gradient descent updates parameters opposite to the gradient of the loss scaled by a learning rate. Batch "
     "uses all data, stochastic uses one sample, mini-batch uses small batches balancing noise and speed."),
    ("Explain precision, recall and F1 score.", "ml", "easy", "Fractal", "Data Scientist", ["metrics"],
     "Precision is TP over predicted positives, recall is TP over actual positives, F1 is their harmonic mean; "
     "useful for imbalanced classes such as fraud detection."),
    ("What is the difference between REST and GraphQL?", "web", "medium", "Razorpay", "Backend Engineer",
     ["api", "rest", "graphql"],
     "REST exposes resources at multiple endpoints with fixed responses; GraphQL exposes one endpoint where the "
     "client queries exactly the fields it needs, avoiding over-fetching, with a typed schema."),
    ("Explain how JWT authentication works.", "web", "medium", "Razorpay", "Backend Engineer", ["security", "jwt"],
     "The server signs a token containing claims with a secret; the client sends it in the Authorization bearer "
     "header; the server verifies the signature and expiry without session storage."),
    ("Tell me about yourself.", "hr", "easy", None, None, ["introduction"],
     "Give a concise story: current education, key projects with impact, relevant skills, and why you are "
     "interested in this role and company. Keep it under two minutes."),
    ("Why do you want to join our company?", "hr", "easy", None, None, ["motivation"],
     "Connect company products, culture and values to your interests and skills; mention research about the "
     "company and how the role helps your growth."),
    ("Describe a time you resolved a conflict in a team.", "behavioral", "medium", None, None,
     ["teamwork", "star"],
     "Use the STAR method: situation, task, action and result. Show listening, empathy, a clear action you took "
     "and a measurable positive outcome."),
    ("Tell me about a project you are proud of and the challenges you faced.", "behavioral", "medium", None, None,
     ["projects", "star"],
     "Pick a relevant project, explain the problem, your role, the technical challenge, how you solved it, the "
     "result with metrics and what you learned."),
    ("A train 150 m long passes a pole in 15 seconds. What is its speed in km/h?", "aptitude", "easy", "TCS",
     "Associate Engineer", ["speed"],
     "Speed equals distance over time: 150 divided by 15 is 10 metres per second, which is 36 km per hour."),
]

EXPERIENCES = [
    dict(company="Amazon", role_title="SDE Intern", year=2026, mode="on-campus", outcome="selected", difficulty=4,
         summary="Online assessment with two DSA problems followed by two technical interviews focused on "
                 "data structures and Amazon leadership principles.",
         tips="Practice medium LeetCode problems and prepare STAR stories for leadership principles.",
         rounds=[{"name": "Online Assessment", "description": "Two coding questions in 90 minutes on HackerRank."},
                 {"name": "Technical 1", "description": "Linked list reversal and a sliding window problem."},
                 {"name": "Technical 2 + LP", "description": "Graph BFS problem and behavioural questions."}],
         questions=[{"text": "Given a binary tree, return its level order traversal.", "topic": "dsa",
                     "tags": ["tree", "bfs"]},
                    {"text": "Tell me about a time you disagreed with your manager.", "topic": "behavioral",
                     "tags": ["star"]}]),
    dict(company="Infosys", role_title="Software Engineer", year=2026, mode="on-campus", outcome="selected",
         difficulty=2,
         summary="Aptitude test, a pseudo-code round and a combined technical plus HR interview. Interviewers were "
                 "friendly and focused on OOP and DBMS basics.",
         tips="Revise OOP pillars and basic SQL queries; be thorough with your resume projects.",
         rounds=[{"name": "Aptitude", "description": "Quant, logical and verbal sections."},
                 {"name": "Interview", "description": "OOP concepts, normalization and project discussion."}],
         questions=[{"text": "What is method overloading versus method overriding?", "topic": "oop",
                     "tags": ["polymorphism"]}]),
    dict(company="Google", role_title="SDE", year=2025, mode="off-campus", outcome="rejected", difficulty=5,
         summary="Phone screen followed by four onsite rounds. Questions were graph heavy and expected optimal "
                 "solutions with clean code and complexity analysis.",
         tips="Communicate your thinking aloud and practice graphs and dynamic programming.",
         rounds=[{"name": "Phone screen", "description": "Interval merging problem."},
                 {"name": "Onsite", "description": "Graph cycle detection, DP and a Googleyness round."}],
         questions=[{"text": "Merge overlapping intervals in a list of intervals.", "topic": "dsa",
                     "tags": ["sorting", "intervals"]}]),
    dict(company="Razorpay", role_title="Backend Engineer", year=2026, mode="referral", outcome="pending",
         difficulty=3,
         summary="Machine coding round to build a small payments ledger API, then a system design discussion about "
                 "idempotency and retries.",
         tips="Know REST design, idempotency keys and database transactions well.",
         rounds=[{"name": "Machine coding", "description": "Build a ledger REST API in 2 hours."},
                 {"name": "Design", "description": "Idempotent payment API design."}],
         questions=[{"text": "How would you make a payment API idempotent?", "topic": "system-design",
                     "tags": ["idempotency", "api"]}]),
]


def ensure_user(db, email, name, role):
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = auth_service.register(db, auth_schemas.RegisterRequest(
            name=name, email=email, password=PASSWORD, college="PES University", target_role="Software Engineer"))
    user.role = role
    db.commit()
    return user


def run() -> None:
    init_db()
    db = SessionLocal()
    try:
        admin = ensure_user(db, "admin@interviewhub.dev", "Admin", "admin")
        ensure_user(db, "mod@interviewhub.dev", "Moderator", "moderator")
        student = ensure_user(db, "student@interviewhub.dev", "Demo Student", "student")
        if q_service.all_questions(db):
            print("Database already seeded.")
            return
        for text, topic, diff, company, role, tags, answer in QUESTIONS:
            q_service.create(db, QuestionCreate(text=text, topic=topic, difficulty=diff, company=company,
                                                role_title=role, tags=tags, model_answer=answer), admin)
        for exp in EXPERIENCES:
            exp_service.create(db, student, exp_schemas.ExperienceCreate(**exp))
        db.commit()
        print(f"Seeded {len(QUESTIONS)} questions and {len(EXPERIENCES)} experiences.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
