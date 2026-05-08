from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


# =========================================
# BOT PERSONAS
# =========================================

bot_personas = {
    "Bot A": """
    I believe AI and crypto will solve all human problems.
    I am highly optimistic about technology, Elon Musk,
    and space exploration. I dismiss regulatory concerns.
    """,

    "Bot B": """
    I believe late-stage capitalism and tech monopolies
    are destroying society. I am highly critical of AI,
    social media, and billionaires. I value privacy and nature.
    """,

    "Bot C": """
    I strictly care about markets, interest rates,
    trading algorithms, and making money.
    I speak in finance jargon and view everything
    through the lens of ROI.
    """
}


# =========================================
# LOAD EMBEDDING MODEL
# =========================================

print("Loading embedding model...")

model = SentenceTransformer('all-MiniLM-L6-v2')

print("Embedding model loaded successfully.\n")


# =========================================
# CREATE PERSONA EMBEDDINGS
# =========================================

persona_names = list(bot_personas.keys())
persona_texts = list(bot_personas.values())

persona_embeddings = model.encode(persona_texts)

# Convert to float32 for FAISS
persona_embeddings = np.array(persona_embeddings).astype('float32')

# Normalize embeddings for cosine similarity
faiss.normalize_L2(persona_embeddings)


# =========================================
# CREATE FAISS VECTOR INDEX
# =========================================

dimension = persona_embeddings.shape[1]

# Inner Product index
# After normalization, Inner Product = Cosine Similarity
index = faiss.IndexFlatIP(dimension)

# Add persona embeddings to vector store
index.add(persona_embeddings)

print("FAISS vector database initialized.\n")


# =========================================
# ROUTING FUNCTION
# =========================================

def route_post_to_bots(post_content: str, threshold: float = 0.85):

    print("=" * 60)
    print("NEW POST RECEIVED")
    print("=" * 60)

    print(f"\nPost Content:\n{post_content}\n")

    # -------------------------------------
    # Generate embedding for incoming post
    # -------------------------------------

    post_embedding = model.encode([post_content])

    post_embedding = np.array(post_embedding).astype('float32')

    # Normalize for cosine similarity
    faiss.normalize_L2(post_embedding)

    # -------------------------------------
    # Search vector database
    # -------------------------------------

    k = len(bot_personas)

    scores, indices = index.search(post_embedding, k=k)

    matched_bots = []

    print("Similarity Scores:\n")

    for score, idx in zip(scores[0], indices[0]):

        bot_name = persona_names[idx]

        print(f"{bot_name}: {score:.4f}")

        if score >= threshold:

            matched_bots.append({
                "bot": bot_name,
                "similarity_score": round(float(score), 4)
            })

    return matched_bots


# =========================================
# TEST CASES
# =========================================

test_posts = [

    "OpenAI released a powerful new AI coding model that may replace junior developers.",

    "Federal Reserve interest rates are impacting crypto and stock markets heavily.",

    "Big tech monopolies are destroying online privacy and manipulating society."
]


# =========================================
# RUN TESTS
# =========================================

for post in test_posts:

    matched = route_post_to_bots(post, threshold=0.50)

    print("\nMatched Bots:\n")

    if matched:

        for bot in matched:
            print(bot)

    else:
        print("No matching bots found.")

    print("\n" + "#" * 60 + "\n")