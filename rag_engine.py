import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dotenv import load_dotenv

# Load environment variables (.env file)
load_dotenv()

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ---------------------------------------------------------------------------
# Global Embedding Model Singleton (Ultra-lightweight API-based embeddings)
# ---------------------------------------------------------------------------
_GLOBAL_EMBEDDING_CACHE = None

def get_shared_embeddings():
    global _GLOBAL_EMBEDDING_CACHE
    if _GLOBAL_EMBEDDING_CACHE is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        print("[Embedding Cache] Initializing Google Gemini Embeddings (gemini-embedding-001)...")
        _GLOBAL_EMBEDDING_CACHE = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=api_key
        )
    return _GLOBAL_EMBEDDING_CACHE



# ---------------------------------------------------------------------------
# Core Constants: 5 Allowed Destinations & Out-of-Domain Keywords
# ---------------------------------------------------------------------------
CORE_DESTINATIONS = ["Goa", "Mumbai", "Bangalore", "Gujarat", "Uttar Pradesh"]

NON_CORE_KEYWORDS = [
    # Indian States & UTs
    "kashmir", "jammu", "punjab", "haryana", "himachal", "manali", "shimla", "dharamshala", "kullu", "spiti", "kasol",
    "uttarakhand", "rishikesh", "haridwar", "dehradun", "nainital", "mussoorie", "kedarnath", "badrinath",
    "delhi", "new delhi", "noida", "gurgaon", "gurugram", "chandigarh", "amritsar",
    "rajasthan", "jaipur", "udaipur", "jodhpur", "jaisalmer", "pushkar", "bikaner", "mount abu",
    "kerala", "kochi", "munnar", "alleppey", "alappuzha", "wayanad", "trivandrum", "thiruvananthapuram", "kovalam", "varkala",
    "tamil nadu", "chennai", "madurai", "ooty", "kodaikanal", "rameswaram", "coimbatore", "kanchipuram", "pondicherry", "puducherry",
    "andhra pradesh", "visakhapatnam", "vizag", "tirupati", "vijayawada",
    "telangana", "hyderabad", "warangal",
    "odisha", "orissa", "puri", "bhubaneswar", "konark",
    "west bengal", "kolkata", "darjeeling", "siliguri", "sundarbans",
    "bihar", "patna", "gaya", "bodhgaya", "nalanda",
    "jharkhand", "ranchi", "jamshedpur",
    "assam", "guwahati", "kaziranga",
    "meghalaya", "shillong", "cherrapunji", "dawki",
    "sikkim", "gangtok", "pelling",
    "arunachal", "tawang", "nagaland", "kohima", "manipur", "imphal", "mizoram", "aizawl", "tripura", "agartala",
    "madhya pradesh", "bhopal", "indore", "gwalior", "ujjain", "khajuraho", "jabalpur", "kanha",
    "chhattisgarh", "raipur", "bastar",
    "andaman", "nicobar", "port blair", "havelock", "lakshadweep", "ladakh", "leh",
    # International Destinations
    "london", "uk", "england", "paris", "france", "europe", "switzerland", "zurich", "geneva", "interlaken",
    "italy", "rome", "venice", "milan", "florence", "usa", "america", "new york", "california", "los angeles", "san francisco",
    "dubai", "uae", "abu dhabi", "singapore", "thailand", "bangkok", "phuket", "pattaya", "krabi", "chiang mai",
    "bali", "indonesia", "malaysia", "kuala lumpur", "tokyo", "japan", "kyoto", "osaka",
    "australia", "sydney", "melbourne", "canada", "toronto", "vancouver", "germany", "berlin", "munich",
    "spain", "barcelona", "madrid", "maldives", "vietnam", "hanoi", "danang", "turkey", "istanbul", "egypt", "cairo"
]


class TravelRAGEngine:
    def __init__(self, persist_directory: Optional[str] = None):
        base_dir = Path(__file__).resolve().parent

        self.data_directory = str(base_dir / "data")
        self.persist_directory = persist_directory or str(base_dir / "chroma_storage")
        
        # 1. Use Shared Global Embeddings (Instant startup)
        self.embeddings = get_shared_embeddings()
        self.vector_store: Optional[Chroma] = None

    def _init_llm(self, model_name: Optional[str] = None):
        """Initializes Google Gemini Chat Model with resilient high-quota model fallbacks."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("[Warning] GOOGLE_API_KEY is not set in .env")
            return None
        
        models_to_try = [model_name] if model_name else ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-pro"]
        for model in models_to_try:
            if not model:
                continue
            try:
                return ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=api_key,
                    temperature=0.2
                )
            except Exception:
                continue
        return None


    def load_and_chunk_documents(self, chunk_size: int = 1200, chunk_overlap: int = 150) -> List[Document]:
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
                import shutil
                try:
                    shutil.rmtree(self.persist_directory, ignore_errors=True)
                except Exception:
                    pass

        # Otherwise create fresh index in rate-limit-safe batches
        import time
        chunks = self.load_and_chunk_documents()
        self.vector_store = Chroma(
            collection_name="travel_knowledge",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        batch_size = 25
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            self.vector_store.add_documents(batch)
            if i + batch_size < len(chunks):
                time.sleep(2)

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
        import re
        q_lower = query.lower()
        
        # 1. If any of the 5 core states or primary cities is explicitly mentioned, allow it
        core_keywords = [
            "goa", "mumbai", "bangalore", "bengaluru", "gujarat", "uttar pradesh", "up",
            "agra", "varanasi", "banaras", "kashi", "lucknow", "ayodhya", "mathura", "vrindavan",
            "somnath", "dwarka", "ahmedabad", "kutch", "rann of kutch", "surat", "vadodara",
            "panaji", "vasco", "calangute", "baga", "anjuna", "candolim", "palolem", "morjim", "colva",
            "indiranagar", "koramangala", "malleshwaram", "basavanagudi", "whitefield"
        ]
        for core in core_keywords:
            if re.search(r'\b' + re.escape(core) + r'\b', q_lower):
                return False
                
        # 2. If a known non-core destination is mentioned, strictly flag it as outside
        for non_core in NON_CORE_KEYWORDS:
            if re.search(r'\b' + re.escape(non_core) + r'\b', q_lower):
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

    def _search_tavily(self, query: str, max_results: int = 3, include_images: bool = False) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Searches Tavily SERP API for real-time web results if TAVILY_API_KEY is configured."""
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key or not api_key.strip():
            return [], []
        
        try:
            import requests
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key.strip(),
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                    "include_images": include_images,
                    "include_answer": False
                },
                timeout=6
            )
            if response.status_code == 200:
                data = response.json()
                results = []
                for item in data.get("results", []):
                    results.append({
                        "title": item.get("title", "Web Result"),
                        "url": item.get("url", ""),
                        "content": item.get("content", "")
                    })
                return results, []
            else:
                print(f"[Tavily Notice] Status {response.status_code}: {response.text[:100]}")
                return [], []

        except Exception as e:
            print(f"[Tavily Warning] Could not reach Tavily API: {e}")
            return [], []

    def _build_rag_prompt_and_sources(
        self,
        query: str,
        destination_filter: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        image_data: Optional[str] = None
    ) -> Tuple[Optional[str], List[Dict[str, Any]], Optional[str]]:
        """Prepares retrieved ChromaDB context, live Tavily web search, and structured prompt."""
        # 1. Strict Out-of-Domain Guardrail Check (Block unsupported states immediately)
        is_outside = self._is_outside_destination(query)
        if is_outside and not image_data:
            msg = (
                "I specialize exclusively in our **5 verified core destinations**: **Goa**, **Mumbai**, **Bangalore**, **Gujarat**, and **Uttar Pradesh**.\n\n"
                "To ensure accurate, verified, and culturally authentic advice, I do not provide travel guides for other states (such as Punjab, Kashmir, Kerala, Rajasthan, Delhi, etc.) or international destinations.\n\n"
                "Please feel free to ask anything about top attractions, hidden beaches, temples, festivals, local cuisine, itineraries, or transport for our 5 core destinations!"
            )
            return None, [], msg

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
                sources.append({"destination": dest, "source": src, "snippet": doc.page_content[:120] + "...", "url": None})
                seen_sources.add(src_key)

        context_str = "\n\n".join(context_parts) if context_parts else "No specific verified documents found in database."

        # 3. Add Live Tavily Search Context if available (Only for supported domains)
        web_results, _ = self._search_tavily(query, max_results=3, include_images=False)
        web_parts = []
        if web_results:
            for r in web_results:
                web_parts.append(f"[Web Source: {r['title']} | URL: {r['url']}]:\n{r['content']}")
                sources.append({
                    "destination": "Live Web Search",
                    "source": f"Tavily: {r['title']}",
                    "snippet": r["content"][:140] + "..." if len(r["content"]) > 140 else r["content"],
                    "url": r["url"]
                })
        web_context_str = "\n\n".join(web_parts) if web_parts else "No live web search context used."

        # 4. Format conversational chat history
        history_text = ""
        if chat_history and len(chat_history) > 0:
            history_lines = []
            for item in chat_history[-6:]:
                role = "Traveler" if item.get("role") in ["user", "human"] else "Assistant"
                history_lines.append(f"{role}: {item.get('content', '')}")
            history_text = "\n".join(history_lines)

        # 5. Prompt Directives with Verified Dialect Lexicon
        system_instruction = (
            "You are an expert, warm, and engaging AI Travel Guide assistant specializing strictly in 5 core regions: "
            "Goa, Mumbai, Bangalore, Gujarat, and Uttar Pradesh (equipped with live web search and multimodal visual analysis).\n\n"
            "STRICT DOMAIN BOUNDARY:\n"
            "- You MUST refuse to provide travel itineraries, hotel lists, or guides for regions outside our 5 core destinations "
            "(e.g., Punjab, Kashmir, Kerala, Rajasthan, Delhi, London, Paris). Redirect the traveler politely to our 5 destinations.\n\n"
            "GUIDELINES FOR USER-FRIENDLY, CULTURALLY RICH & FACTUAL RESPONSES:\n"
            "1. BALANCED SYNTHESIS: Read and synthesize verified facts from ChromaDB knowledge base and Live Web Search context.\n"
            "2. INLINE REGIONAL VERNACULAR WITH HOVER TOOLTIPS (CRITICAL):\n"
            "   - Naturally incorporate authentic regional terms and greetings directly into sentences.\n"
            "   - NEVER put regional words or definitions on separate lines or in definition bullet points.\n"
            "   - ALWAYS format every regional or local dialect term directly inline using an HTML abbreviation tag with its exact English meaning in the title attribute: `<abbr title=\"Exact Meaning\">RegionalTerm</abbr>`.\n"
            "   - ACCURACY IS MANDATORY: Only use regional terms and meanings if they are 100% culturally accurate. Never guess or invent meanings. Use this verified lexicon:\n"
            "     * Goa (Konkani): <abbr title=\"May God bless you / Thank you\">Dev Borem Korum</abbr> (or Dev Bare Korun), <abbr title=\"Relaxed, contented, unhurried peaceful living\">Susegad</abbr>, <abbr title=\"Traditional Goan fish curry rice staple\">Xit Codi</abbr>, <abbr title=\"Village baker who delivers fresh bread on bicycle\">Poder</abbr>, <abbr title=\"Friend, respected master of the house\">Patrao</abbr>, <abbr title=\"Traditional distilled spirit from cashew apple or coconut toddy\">Feni</abbr>, <abbr title=\"Multi-layered Goan coconut milk dessert\">Bebinca</abbr>, <abbr title=\"How are you?\">Kitem Cholam?</abbr>, <abbr title=\"I am doing well\">Boro Aasa</abbr>.\n"
            "     * Gujarat (Gujarati): <abbr title=\"How are you? / I am great!\">Kem Cho? Majama!</abbr>, <abbr title=\"Traditional savory snacks like dhokla, thepla, and khandvi\">Farsan</abbr>, <abbr title=\"Sweet and spicy grated mango pickle\">Chhundo</abbr>, <abbr title=\"Slow-cooked winter mixed vegetable delicacy with fenugreek dumplings\">Undhiyu</abbr>, <abbr title=\"Celebrate and enjoy life to the fullest!\">Jalsa Karo!</abbr>, <abbr title=\"Traditional greeting (Hail Lord Krishna)\">Jai Shri Krishna</abbr>.\n"
            "     * Mumbai (Marathi / Bambaiya): <abbr title=\"Our Mumbai (phrase of pride and belonging)\">Aamchi Mumbai</abbr>, <abbr title=\"Carefree, fearless, and relaxed attitude\">Bindaas</abbr>, <abbr title=\"Half-cup strong spiced Indian tea\">Cutting Chai</abbr>, <abbr title=\"Clever, creative quick-fix workaround\">Jugaad</abbr>, <abbr title=\"Spicy sprouted lentil curry garnished with farsan and onions\">Misal Pav</abbr>, <abbr title=\"Iconic deep-fried spiced potato fritter in a bread bun\">Vada Pav</abbr>, <abbr title=\"Traditional respectful Marathi greeting\">Namaskar</abbr>.\n"
            "     * Bangalore (Kannada / Local Slang): <abbr title=\"Please adjust a little bit (classic Bangalore expression of accommodation)\">Swalpa Adjust Maadi</abbr>, <abbr title=\"Close buddy, friend, or brother\">Maga</abbr>, <abbr title=\"Traditional South Indian savory breakfast items like idli, vada, and dosa\">Thindi</abbr>, <abbr title=\"Wholesome full traditional meal served with rice and sambar\">Oota</abbr>, <abbr title=\"Strong South Indian chicory-infused decoction coffee with frothed milk\">Filter Kaapi</abbr>, <abbr title=\"Crispy golden butter dosa famous in Karnataka\">Benne Dosa</abbr>, <abbr title=\"Quick-service vegetarian standing breakfast eateries\">Darshini</abbr>, <abbr title=\"Go safely and return soon (traditional warm farewell)\">Hogi Baa</abbr>, <abbr title=\"Warm respectful Kannada greeting\">Namaskara</abbr>.\n"
            "     * Uttar Pradesh (Hindi / Awadhi / Braj): <abbr title=\"Loving devotional greeting and chant of Braj (Mathura-Vrindavan)\">Radhe Radhe!</abbr>, <abbr title=\"After you, please (emblematic of Lucknow's refined Awadhi courtesy)\">Pehle Aap</abbr>, <abbr title=\"Refined cultural elegance, polite etiquette, and hospitality\">Tehzeeb & Nazaakat</abbr>, <abbr title=\"Magical, serene dawn atmosphere along the Varanasi ghats\">Subah-e-Banaras</abbr>, <abbr title=\"Melt-in-the-mouth Awadhi spiced minced meat kebab\">Galouti Kebab</abbr>, <abbr title=\"Varanasi's winter saffron milk foam sweet garnished with pistachios\">Malaiyo</abbr>, <abbr title=\"Traditional respectful greeting\">Namaste</abbr>.\n"
            "3. MULTIMODAL IMAGE RECOGNITION: If the traveler has attached an image, visually identify the landmark, architectural style, deity, beach, or dish, and ground your response in its historical and regional context.\n"
            "4. REAL-TIME AWARENESS: When Live Web Search context is provided for our 5 states, use it to give up-to-date festival dates (e.g. Vasco Saptah, Dev Deepawali) and seasonal tips.\n"
            "5. CLEAN OUTPUT: Do NOT include raw bracketed citations like '[Source 1]' or append 'Source Citations:' lists, as sources are automatically rendered by the UI."
        )

        full_prompt = f"""{system_instruction}

--- PRIOR CONVERSATION CONTEXT ---
{history_text if history_text else "No prior conversation."}

--- VERIFIED REGIONAL KNOWLEDGE BASE (CHROMADB) ---
{context_str}

--- LIVE WEB SEARCH CONTEXT (TAVILY) ---
{web_context_str}

--- TRAVELER'S QUESTION ---
{query}

--- USER-FRIENDLY & CULTURALLY RICH TRAVEL GUIDE RESPONSE ---"""

        return full_prompt, sources, None

    def generate_answer(
        self,
        query: str,
        destination_filter: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        image_data: Optional[str] = None
    ) -> Dict[str, Any]:
        """Hybrid Grounded Multimodal RAG: ChromaDB + Live Tavily Search + Gemini Vision + Regional Vernacular."""
        full_prompt, sources, direct_answer = self._build_rag_prompt_and_sources(
            query=query,
            destination_filter=destination_filter,
            chat_history=chat_history,
            image_data=image_data
        )

        if direct_answer:
            return {"answer": direct_answer, "sources": sources, "images": []}

        llm = self._init_llm()
        if not llm:
            return {
                "answer": "Gemini LLM could not be initialized. Please check your GOOGLE_API_KEY in .env.",
                "sources": sources,
                "images": []
            }

        try:
            import re
            if image_data:
                img_url = image_data if image_data.startswith("data:") else f"data:image/jpeg;base64,{image_data}"
                message = HumanMessage(
                    content=[
                        {"type": "text", "text": full_prompt},
                        {"type": "image_url", "image_url": img_url}
                    ]
                )
                res = llm.invoke([message])
            else:
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
            
            # Clean up bracketed source markers
            answer_text = re.sub(r'(\n|\r\n)*(###?\s*)?(Source Citations?|Sources Used|References?):?(\n|\r\n)*((\*|-)\s*\[[^\]]+\](\n|\r\n)*)+', '', answer_text, flags=re.IGNORECASE)
            answer_text = re.sub(r'\[Source \d+[^\]]*\]', '', answer_text)
            answer_text = answer_text.strip()

            return {
                "answer": answer_text,
                "sources": sources,
                "images": []
            }
        except Exception as e:
            return {
                "answer": f"Error generating answer from knowledge base: {str(e)}",
                "sources": sources,
                "images": []
            }

    def generate_answer_stream(
        self,
        query: str,
        destination_filter: Optional[str] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        image_data: Optional[str] = None
    ):
        """Streams real-time response tokens using Gemini streaming with immediate source metadata emission."""
        import json
        full_prompt, sources, direct_answer = self._build_rag_prompt_and_sources(
            query=query,
            destination_filter=destination_filter,
            chat_history=chat_history,
            image_data=image_data
        )

        # 1. First event: Emit verified sources immediately
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources, 'destination_filter': destination_filter})}\n\n"

        if direct_answer:
            yield f"data: {json.dumps({'type': 'token', 'token': direct_answer})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            return

        llm = self._init_llm()
        if not llm:
            yield f"data: {json.dumps({'type': 'error', 'error': 'Gemini LLM could not be initialized.'})}\n\n"
            return

        try:
            if image_data:
                img_url = image_data if image_data.startswith("data:") else f"data:image/jpeg;base64,{image_data}"
                messages = [
                    HumanMessage(
                        content=[
                            {"type": "text", "text": full_prompt},
                            {"type": "image_url", "image_url": img_url}
                        ]
                    )
                ]
                stream = llm.stream(messages)
            else:
                stream = llm.stream(full_prompt)

            for chunk in stream:
                token_text = ""
                if hasattr(chunk, "content"):
                    if isinstance(chunk.content, list):
                        token_text = "".join(str(part.get("text", part) if isinstance(part, dict) else part) for part in chunk.content)
                    else:
                        token_text = str(chunk.content)
                elif hasattr(chunk, "text"):
                    token_text = str(chunk.text)
                else:
                    token_text = str(chunk)

                if token_text:
                    yield f"data: {json.dumps({'type': 'token', 'token': token_text})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"




if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    engine = TravelRAGEngine()
    
    # Test query for Vasco Saptah & Hidden Beaches
    query = "Tell me about Vasco Saptah and hidden beaches like Kakolem in Goa"
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
