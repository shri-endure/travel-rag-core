import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# Load environment variables (.env file)
load_dotenv()

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# ---------------------------------------------------------------------------
# Global Embedding Model Singleton (Speeds up initializations & eliminates lag)
# ---------------------------------------------------------------------------
_GLOBAL_EMBEDDING_CACHE = None

def get_shared_embeddings():
    global _GLOBAL_EMBEDDING_CACHE
    if _GLOBAL_EMBEDDING_CACHE is None:
        print("[Embedding Cache] Loading sentence-transformers model once...")
        _GLOBAL_EMBEDDING_CACHE = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _GLOBAL_EMBEDDING_CACHE


# ---------------------------------------------------------------------------
# Core Constants: 5 Allowed Destinations & Curated Travel Photo Catalog
# ---------------------------------------------------------------------------
CORE_DESTINATIONS = ["Goa", "Mumbai", "Bangalore", "Gujarat", "Uttar Pradesh"]

NON_CORE_KEYWORDS = [
    "kashmir", "andaman", "nicobar", "kerala", "rajasthan", "ladakh", "himachal",
    "manali", "shimla", "rishikesh", "uttarakhand", "delhi", "punjab", "kolkata",
    "chennai", "tamil nadu", "hyderabad", "telangana", "odisha", "assam", "meghalaya",
    "sikkim", "paris", "london", "switzerland", "bali", "dubai", "thailand", "singapore"
]

# (Title, URL, Source Citation, Category)
CURATED_PHOTOS: Dict[str, Tuple[str, str, str, str]] = {
    # --- TEMPLES & SPIRITUAL LANDMARKS ---
    "somnath": ("Somnath Jyotirlinga Temple, Gujarat", "https://images.unsplash.com/photo-1609766418204-94aae0ecfddc?w=800", "Gujarat Tourism / Unsplash", "temple"),
    "dwarka": ("Dwarkadhish Temple, Gujarat", "https://images.unsplash.com/photo-1609766418204-94aae0ecfddc?w=800", "Gujarat Tourism / Unsplash", "temple"),
    "dwarkadhish": ("Dwarkadhish Temple, Gujarat", "https://images.unsplash.com/photo-1609766418204-94aae0ecfddc?w=800", "Gujarat Tourism / Unsplash", "temple"),
    "siddhivinayak": ("Shree Siddhivinayak Temple, Mumbai", "https://images.unsplash.com/photo-1548013146-72479768bada?w=800", "Maharashtra Tourism / Unsplash", "temple"),
    "haji ali": ("Haji Ali Dargah, Mumbai", "https://images.unsplash.com/photo-1566552881560-0be86c532107?w=800", "Incredible India / Unsplash", "temple"),
    "kashi": ("Kashi Vishwanath & Ganga Ghats, Varanasi", "https://images.unsplash.com/photo-1561359313-0639aad49ca6?w=800", "UP Tourism / Unsplash", "temple"),
    "varanasi": ("Varanasi Ganga Ghats & Evening Aarti", "https://images.unsplash.com/photo-1561359313-0639aad49ca6?w=800", "UP Tourism / Unsplash", "temple"),
    "ghat": ("Varanasi Dashashwamedh Ghat", "https://images.unsplash.com/photo-1561359313-0639aad49ca6?w=800", "UP Tourism / Unsplash", "temple"),
    "aarti": ("Maha Ganga Aarti at Dashashwamedh Ghat", "https://images.unsplash.com/photo-1561359313-0639aad49ca6?w=800", "UP Tourism / Unsplash", "temple"),
    "ayodhya": ("Shri Ram Janmabhoomi Temple, Ayodhya", "https://images.unsplash.com/photo-1548013146-72479768bada?w=800", "UP Tourism / Unsplash", "temple"),
    "ram mandir": ("Shri Ram Janmabhoomi Temple, Ayodhya", "https://images.unsplash.com/photo-1548013146-72479768bada?w=800", "UP Tourism / Unsplash", "temple"),
    "bom jesus": ("Basilica of Bom Jesus, Old Goa", "https://images.unsplash.com/photo-1614082242765-7c98ca0f3df3?w=800", "Goa Tourism / Unsplash", "temple"),
    "old goa": ("Basilica of Bom Jesus & Se Cathedral", "https://images.unsplash.com/photo-1614082242765-7c98ca0f3df3?w=800", "Goa Tourism / Unsplash", "temple"),
    "sun temple": ("Sun Temple, Modhera", "https://images.unsplash.com/photo-1609137144820-21a4f0093848?w=800", "Gujarat Tourism / Unsplash", "temple"),
    "iskcon": ("ISKCON Temple, Bangalore", "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=800", "Karnataka Tourism / Unsplash", "temple"),
    "mathura": ("Shri Krishna Janmabhoomi, Mathura", "https://images.unsplash.com/photo-1548013146-72479768bada?w=800", "UP Tourism / Unsplash", "temple"),
    "vrindavan": ("Banke Bihari & Prem Mandir, Vrindavan", "https://images.unsplash.com/photo-1548013146-72479768bada?w=800", "UP Tourism / Unsplash", "temple"),

    # --- MONUMENTS & HERITAGE ---
    "taj mahal": ("The Taj Mahal, Agra", "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800", "UP Tourism / Unsplash", "monument"),
    "agra": ("The Taj Mahal, Agra", "https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800", "UP Tourism / Unsplash", "monument"),
    "gateway of india": ("Gateway of India, Mumbai", "https://images.unsplash.com/photo-1570168007204-dfb528c6958f?w=800", "Maharashtra Tourism / Unsplash", "monument"),
    "marine drive": ("Marine Drive Promenade, Mumbai", "https://images.unsplash.com/photo-1566552881560-0be86c532107?w=800", "Maharashtra Tourism / Unsplash", "monument"),
    "statue of unity": ("Statue of Unity, Kevadia", "https://images.unsplash.com/photo-1609137144820-21a4f0093848?w=800", "Gujarat Tourism / Unsplash", "monument"),
    "bangalore palace": ("Bangalore Palace", "https://images.unsplash.com/photo-1596176530529-78163a4f7af2?w=800", "Karnataka Tourism / Unsplash", "monument"),
    "lalbagh": ("Lalbagh Botanical Garden Glass House", "https://images.unsplash.com/photo-1580655653885-65763b2597d0?w=800", "Karnataka Tourism / Unsplash", "nature"),
    "cubbon": ("Cubbon Park Trails, Bangalore", "https://images.unsplash.com/photo-1593693397690-362cb9666fc2?w=800", "Karnataka Tourism / Unsplash", "nature"),
    "elephanta": ("Elephanta Caves, Mumbai", "https://images.unsplash.com/photo-1605649487212-47bdab064df7?w=800", "Maharashtra Tourism / Unsplash", "monument"),
    "csmt": ("CSMT World Heritage Terminus, Mumbai", "https://images.unsplash.com/photo-1567157577867-05ccb1388e66?w=800", "Maharashtra Tourism / Unsplash", "monument"),
    "rann of kutch": ("White Desert, Rann of Kutch", "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=800", "Gujarat Tourism / Unsplash", "nature"),
    "white rann": ("White Desert, Rann of Kutch", "https://images.unsplash.com/photo-1618773928121-c32242e63f39?w=800", "Gujarat Tourism / Unsplash", "nature"),
    "gir": ("Asiatic Lions in Gir National Park", "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=800", "Gujarat Forest Dept / Unsplash", "nature"),
    "lion": ("Asiatic Lion in Gir Forest", "https://images.unsplash.com/photo-1546182990-dffeafbe841d?w=800", "Gujarat Forest Dept / Unsplash", "nature"),
    "dudhsagar": ("Dudhsagar Waterfalls, Goa", "https://images.unsplash.com/photo-1588668214407-6ea9a6d8c272?w=800", "Goa Tourism / Unsplash", "nature"),
    "nandi hills": ("Nandi Hills Sunrise Point", "https://images.unsplash.com/photo-1587474260584-136574528ed5?w=800", "Karnataka Tourism / Unsplash", "nature"),
    "fontainhas": ("Fontainhas Latin Quarter, Panaji", "https://images.unsplash.com/photo-1582510003544-4d00b7f74220?w=800", "Goa Tourism / Unsplash", "monument"),
    "lucknow": ("Rumi Darwaza & Bara Imambara, Lucknow", "https://images.unsplash.com/photo-1599661046827-dacff0c0f09a?w=800", "UP Tourism / Unsplash", "monument"),

    # --- BEACHES (Only matched when beach or coastal water sport keywords occur) ---
    "baga": ("Baga Beach, North Goa", "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800", "Goa Tourism / Unsplash", "beach"),
    "calangute": ("Calangute Beach, North Goa", "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800", "Goa Tourism / Unsplash", "beach"),
    "palolem": ("Palolem Beach, South Goa", "https://images.unsplash.com/photo-1544644181-1484b3fdfc62?w=800", "Goa Tourism / Unsplash", "beach"),
    "anjuna": ("Anjuna Beach & Flea Market, Goa", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800", "Goa Tourism / Unsplash", "beach"),

    # --- LOCAL FOOD & SPECIALTIES ---
    "vada pav": ("Mumbai Vada Pav", "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800", "Mumbai Food Trails / Unsplash", "food"),
    "pav bhaji": ("Mumbai Pav Bhaji", "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800", "Mumbai Food Trails / Unsplash", "food"),
    "fish curry": ("Goan Fish Curry Thali", "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=800", "Goa Culinary / Unsplash", "food"),
    "seafood": ("Goan Seafood Specialties", "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=800", "Goa Culinary / Unsplash", "food"),
    "benne dosa": ("Crispy Butter Benne Dosa", "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=800", "Bangalore Food Guide / Unsplash", "food"),
    "dosa": ("Crispy South Indian Dosa", "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=800", "Bangalore Food Guide / Unsplash", "food"),
    "filter coffee": ("Traditional South Indian Filter Coffee", "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800", "Bangalore Coffee Trails / Unsplash", "food"),
    "thali": ("Grand Gujarati Vegetarian Thali", "https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=800", "Gujarat Culinary / Unsplash", "food"),
    "kebab": ("Lucknow Tunday Kebabs & Awadhi Flavors", "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=800", "Awadhi Cuisine / Unsplash", "food"),
    "biryani": ("Lucknowi Awadhi Dum Biryani", "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?w=800", "Awadhi Cuisine / Unsplash", "food")
}


class TravelRAGEngine:
    def __init__(self, persist_directory: Optional[str] = None):
        base_dir = Path(__file__).resolve().parent
        self.data_directory = str(base_dir / "data")
        self.persist_directory = persist_directory or str(base_dir / "chroma_storage")
        
        # 1. Use Shared Global Embeddings (Instant startup)
        self.embeddings = get_shared_embeddings()
        self.vector_store: Optional[Chroma] = None

    def _init_llm(self):
        """Initializes Google Gemini Chat Model with resilient model fallbacks."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("[Warning] GOOGLE_API_KEY is not set in .env")
            return None
        
        for model in ["gemini-3-flash-preview", "gemini-3.5-flash", "gemini-3.6-flash", "gemini-2.5-flash"]:
            try:
                return ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=api_key,
                    temperature=0.2
                )
            except Exception:
                continue
        return None

    def load_and_chunk_documents(self, chunk_size: int = 700, chunk_overlap: int = 100) -> List[Document]:
        """Reads all .txt files in data/ and splits them into LangChain Document chunks."""
        data_path = Path(self.data_directory)
        txt_files = list(data_path.glob("*.txt"))
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        all_chunks = []
        for file_path in txt_files:
            file_name = file_path.name
            destination = file_name.replace(".txt", "").replace("_", " ").title()
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Split the text
            chunks = splitter.split_text(content)
            
            # Wrap each text chunk into a Document with metadata
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": file_name,
                        "destination": destination,
                        "chunk_id": f"{file_name}_chunk_{i}"
                    }
                )
                all_chunks.append(doc)
                
        return all_chunks

    def build_vector_store(self, force_reload: bool = False) -> Chroma:
        """Indexes all document chunks into ChromaDB."""
        # Load existing collection if available and force_reload is False
        if os.path.exists(self.persist_directory):
            if not force_reload:
                self.vector_store = Chroma(
                    collection_name="travel_knowledge",
                    embedding_function=self.embeddings,
                    persist_directory=self.persist_directory
                )
                count = self.vector_store._collection.count()
                if count > 0:
                    return self.vector_store
            else:
                try:
                    old_store = Chroma(
                        collection_name="travel_knowledge",
                        embedding_function=self.embeddings,
                        persist_directory=self.persist_directory
                    )
                    old_store.delete_collection()
                except Exception:
                    pass

        # Otherwise create fresh index
        chunks = self.load_and_chunk_documents()
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name="travel_knowledge",
            persist_directory=self.persist_directory
        )
        return self.vector_store

    def ingest_documents(self, force_reload: bool = True) -> Dict[str, Any]:
        """Ingests raw text files from data/ into ChromaDB."""
        self.build_vector_store(force_reload=force_reload)
        count = self.vector_store._collection.count() if self.vector_store else 0
        return {"status": "success", "total_vectors": count}

    def retrieve(self, query: str, destination_filter: Optional[str] = None, k: Optional[int] = None) -> List[Document]:
        """Performs semantic similarity search on ChromaDB with optional destination filter."""
        if self.vector_store is None:
            self.build_vector_store(force_reload=False)
            
        search_filter = None
        if destination_filter and destination_filter.lower() not in ["all", "none", ""]:
            search_filter = {"destination": destination_filter.title()}
            default_k = 6
        else:
            default_k = 8

        actual_k = k if k is not None else default_k

        try:
            results = self.vector_store.similarity_search(
                query=query,
                k=actual_k,
                filter=search_filter
            )
            return results
        except Exception as e:
            print(f"[Error during retrieval]: {e}")
            return []

    def _is_outside_destination(self, query: str) -> bool:
        """Checks if the query is specifically asking about a non-core destination outside our 5 states."""
        q_lower = query.lower()
        
        # If any of the 5 core states or known cities is explicitly mentioned, allow it
        for core in ["goa", "mumbai", "bangalore", "bengaluru", "gujarat", "uttar pradesh", "agra", "varanasi", "lucknow", "ayodhya", "mathura", "vrindavan", "somnath", "dwarka", "ahmedabad", "kutch"]:
            if core in q_lower:
                return False
                
        # If a known non-core destination is mentioned
        for non_core in NON_CORE_KEYWORDS:
            if non_core in q_lower:
                return True
                
        return False

    def _find_matching_images(self, query: str, answer: str, destination_filter: Optional[str] = None) -> List[Dict[str, str]]:
        """Finds precisely matched real photos with Title, URL, Citation, and destination affinity."""
        import re
        combined_text = f"{query} {answer} {destination_filter or ''}".lower()
        matched = []
        seen_urls = set()

        is_temple_query = any(w in combined_text for w in ["temple", "mandir", "spiritual", "darshan", "jyotirlinga", "ghat", "aarti", "church", "cathedral", "mosque", "dargah"])
        is_food_query = any(w in combined_text for w in ["food", "dish", "eat", "curry", "dosa", "pav", "thali", "kebab", "biryani", "breakfast", "cafe", "restaurant", "culinary"])

        # Determine target destination if known
        active_dest = None
        for d in ["goa", "mumbai", "bangalore", "gujarat", "uttar pradesh"]:
            if destination_filter and d in destination_filter.lower():
                active_dest = d
                break
            elif d in query.lower():
                active_dest = d
                break

        for key, (title, url, citation, category) in CURATED_PHOTOS.items():
            # Destination affinity check
            if active_dest:
                cit_lower = citation.lower()
                title_lower = title.lower()
                if active_dest == "mumbai" and not ("mumbai" in cit_lower or "maharashtra" in cit_lower or "mumbai" in title_lower):
                    continue
                if active_dest == "goa" and not ("goa" in cit_lower or "goa" in title_lower):
                    continue
                if active_dest == "gujarat" and not ("gujarat" in cit_lower or "gujarat" in title_lower):
                    continue
                if active_dest in ["uttar pradesh", "up"] and not ("up" in cit_lower or "uttar pradesh" in cit_lower or "agra" in title_lower or "varanasi" in title_lower or "lucknow" in title_lower or "ayodhya" in title_lower):
                    continue
                if active_dest in ["bangalore", "bengaluru"] and not ("karnataka" in cit_lower or "bangalore" in cit_lower or "bangalore" in title_lower):
                    continue

            if is_temple_query and category in ["beach", "food"]:
                continue
            if is_food_query and category in ["beach"]:
                continue

            # Exact word-boundary match to prevent substring collision
            pattern = r'\b' + re.escape(key) + r'\b'
            if re.search(pattern, combined_text) and url not in seen_urls:
                matched.append({
                    "title": title,
                    "url": url,
                    "citation": citation
                })
                seen_urls.add(url)
                if len(matched) >= 2:
                    break

        return matched

    def generate_answer(
        self,
        query: str,
        destination_filter: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Hybrid Grounded RAG: Anchored in ChromaDB Knowledge Base + Enhanced with Gemini Travel Intelligence for complete, intact responses."""
        
        # 1. Check for outside destination query
        if self._is_outside_destination(query):
            msg = (
                "I specialize exclusively in our **5 verified core destinations**: **Goa**, **Mumbai**, **Bangalore**, **Gujarat**, and **Uttar Pradesh**.\n\n"
                "To ensure accurate, verified, and grounded advice, I do not provide travel guides for other states or international regions. "
                "Please feel free to ask anything about top attractions, temples, food, culture, itineraries, or transport for our 5 core destinations!"
            )
            return {
                "answer": msg,
                "sources": [],
                "images": []
            }

        # 2. Retrieve relevant chunks from ChromaDB vector database
        retrieved_docs = self.retrieve(query, destination_filter=destination_filter)
        
        context_parts = []
        sources = []
        seen_sources = set()

        for i, doc in enumerate(retrieved_docs, 1):
            dest = doc.metadata.get("destination", "Unknown")
            src = doc.metadata.get("source", "Unknown")
            context_parts.append(f"[Destination: {dest} | File: {src}]:\n{doc.page_content}")
            
            src_key = (dest, src)
            if src_key not in seen_sources:
                sources.append({"destination": dest, "source": src, "snippet": doc.page_content[:120] + "..."})
                seen_sources.add(src_key)

        context_str = "\n\n".join(context_parts) if context_parts else "No specific verified documents found in database."

        # 3. Format conversational chat history
        history_text = ""
        if chat_history and len(chat_history) > 0:
            history_lines = []
            for item in chat_history[-6:]:
                role = "Traveler" if item.get("role") in ["user", "human"] else "Assistant"
                history_lines.append(f"{role}: {item.get('content', '')}")
            history_text = "\n".join(history_lines)

        # 4. Hybrid Augmented Prompt Template
        system_instruction = (
            "You are an expert, comprehensive, and friendly AI Travel Guide assistant specializing in 5 core regions: Goa, Mumbai, Bangalore, Gujarat, and Uttar Pradesh.\n\n"
            "GUIDELINES FOR INTACT & COMPREHENSIVE RESPONSES:\n"
            "1. PRIMARY KNOWLEDGE BASE GROUNDING: Anchor your answers firmly in the verified context provided below (including specific attractions, local dishes, transport modes, routes, and regional advice).\n"
            "2. INTELLIGENT TRAVEL SYNTHESIS: Use your travel expertise to provide complete, thorough, engaging, and practical responses. Seamlessly explain descriptions, highlight cultural significance, suggest optimal visit order, and share helpful traveler tips (such as best times of day, what to expect, and practical etiquette).\n"
            "3. MULTI-TURN CONTINUITY: If conversation history is present, maintain context naturally to answer follow-up queries cohesively.\n"
            "4. SCOPE INTEGRITY: Stay strictly focused on the 5 core destinations. Do not invent non-existent places or false pricing.\n"
            "5. STRUCTURE: Use clear bold headings, organized bullet points, and an inviting tone. Do NOT include raw bracketed citations like '[Source 1]' or append 'Source Citations:' lists, as sources are rendered by the system UI."
        )

        full_prompt = f"""{system_instruction}

--- PRIOR CONVERSATION CONTEXT ---
{history_text if history_text else "No prior conversation."}

--- VERIFIED REGIONAL KNOWLEDGE BASE ---
{context_str}

--- TRAVELER'S QUESTION ---
{query}

--- COMPLETE & DETAILED TRAVEL GUIDE RESPONSE ---"""

        llm = self._init_llm()
        if not llm:
            return {
                "answer": "Gemini LLM could not be initialized. Please check your GOOGLE_API_KEY in .env.",
                "sources": sources,
                "images": []
            }

        try:
            import re
            res = llm.invoke(full_prompt)
            if hasattr(res, "content"):
                if isinstance(res.content, list):
                    answer_text = "".join(
                        str(part.get("text", part) if isinstance(part, dict) else (part.text if hasattr(part, "text") else part))
                        for part in res.content
                    )
                else:
                    answer_text = str(res.content)
            else:
                answer_text = str(res)
            
            # Clean up any accidental raw source dump blocks or bracketed [Source N] markers
            answer_text = re.sub(r'(\n|\r\n)*(###?\s*)?(Source Citations?|Sources Used|References?):?(\n|\r\n)*((\*|-)\s*\[[^\]]+\](\n|\r\n)*)+', '', answer_text, flags=re.IGNORECASE)
            answer_text = re.sub(r'\[Source \d+[^\]]*\]', '', answer_text)
            answer_text = answer_text.strip()

            # Find relevant real travel photos with title & citation
            images = self._find_matching_images(query, answer_text, destination_filter)
            
            # Append image cards with title and citation
            image_markdown = ""
            if images:
                image_blocks = []
                for img in images:
                    block = f"![{img['title']}]({img['url']})\n\n*Photo: {img['title']} | Citation: {img['citation']}*"
                    image_blocks.append(block)
                image_markdown = "\n\n" + "\n\n".join(image_blocks)
            
            return {
                "answer": answer_text + image_markdown,
                "sources": sources,
                "images": images
            }
        except Exception as e:
            return {
                "answer": f"Error generating answer from knowledge base: {str(e)}",
                "sources": sources,
                "images": []
            }


if __name__ == "__main__":
    engine = TravelRAGEngine()
    
    # Test query for temples
    query = "What are the most sacred temples to visit in Gujarat and Uttar Pradesh?"
    print(f"\n--- Asking RAG Engine: '{query}' ---\n")
    result = engine.generate_answer(query)
    print("=== AI RESPONSE ===")
    print(result["answer"])
    print("\n=== SOURCES ===")
    for s in result["sources"]:
        print(f"- {s['destination']} ({s['source']})")
    print("\n=== IMAGES ===")
    for img in result["images"]:
        print(f"- {img['title']} | Citation: {img['citation']}")
