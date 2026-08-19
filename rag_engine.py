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

    def _search_tavily(self, query: str, max_results: int = 3, include_images: bool = True) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Searches Tavily SERP API for real-time web results and authentic images if TAVILY_API_KEY is configured."""
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
        # 1. Check for outside destination query & Live Search fallback
        is_outside = self._is_outside_destination(query)
        web_results, _ = self._search_tavily(query, max_results=3, include_images=False)

        if is_outside and not web_results and not image_data:
            msg = (
                "I specialize exclusively in our **5 verified core destinations**: **Goa**, **Mumbai**, **Bangalore**, **Gujarat**, and **Uttar Pradesh**.\n\n"
                "To ensure accurate, verified, and grounded advice, I do not provide travel guides for other states or international regions. "
                "Please feel free to ask anything about top attractions, hidden beaches, temples, festivals, food, culture, itineraries, or transport for our 5 core destinations!"
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

        # 3. Add Live Tavily Search Context if available
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

        # 5. Prompt Directives
        system_instruction = (
            "You are an expert, warm, and engaging AI Travel Guide assistant specializing in 5 core regions: Goa, Mumbai, Bangalore, Gujarat, and Uttar Pradesh (equipped with live web search and multimodal visual analysis).\n\n"
            "GUIDELINES FOR USER-FRIENDLY, CULTURALLY RICH & BALANCED RESPONSES:\n"
            "1. BALANCED SYNTHESIS & SUMMARIZATION: Read and synthesize verified facts from the ChromaDB knowledge base and Live Web Search context into a conversational, well-paced travel guide.\n"
            "2. INLINE REGIONAL VERNACULAR WITH HOVER TOOLTIPS (CRITICAL):\n"
            "   - Naturally incorporate authentic regional terms and greetings into sentences.\n"
            "   - NEVER put regional words or their definitions on separate lines, in brackets, or in separate definition bullet points.\n"
            "   - ALWAYS format every regional or local dialect term directly inline using an HTML abbreviation tag with its English meaning in the title attribute: `<abbr title=\"Meaning of word\">RegionalTerm</abbr>`.\n"
            "   - Examples:\n"
            "     * Gujarat: `<abbr title=\"How are you? / I am great!\">Kem Cho? Majama!</abbr>`, `<abbr title=\"sweet-spicy mango pickle\">Chhundo</abbr>`, `<abbr title=\"savory snacks\">Farsan</abbr>`, `<abbr title=\"celebrate and enjoy life\">Jalsa Karo</abbr>`.\n"
            "     * Goa: `<abbr title=\"relaxed, unhurried peaceful living\">Susegad</abbr>`, `<abbr title=\"friend / boss\">Patrao</abbr>`, `<abbr title=\"staple fish curry rice\">Xit Codi</abbr>`, `<abbr title=\"village baker\">Poder</abbr>`.\n"
            "     * Mumbai: `<abbr title=\"Our Mumbai\">Aamchi Mumbai</abbr>`, `<abbr title=\"carefree and fearless\">Bindaas</abbr>`, `<abbr title=\"half cup strong spiced tea\">Cutting Chai</abbr>`, `<abbr title=\"clever quick-fix solution\">Jugaad</abbr>`.\n"
            "     * Bangalore: `<abbr title=\"Please adjust a little bit\">Swalpa Adjust Maadi</abbr>`, `<abbr title=\"buddy / brother\">Maga</abbr>`, `<abbr title=\"savory breakfast snacks\">Thindi</abbr>`, `<abbr title=\"wholesome full meal\">Oota</abbr>`, `<abbr title=\"strong South Indian decoction coffee\">Filter Kaapi</abbr>`.\n"
            "     * Uttar Pradesh: `<abbr title=\"loving spiritual greeting of Braj\">Radhe Radhe!</abbr>`, `<abbr title=\"After you, please (Awadhi courtesy)\">Pehle Aap</abbr>`, `<abbr title=\"refined elegance and hospitality\">Tehzeeb & Nazaakat</abbr>`, `<abbr title=\"magical dawn atmosphere of Varanasi\">Subah-e-Banaras</abbr>`.\n"
            "3. DEEP TRAVEL KNOWLEDGE: Highlight both famous landmarks and lesser-known local gems (e.g., Vasco Saptah festival, Kakolem/Butterfly beaches, Khotachiwadi, Turahalli Forest, Polo Forest, Rani ki Vav, Dev Deepawali, Bateshwar).\n"
            "4. MULTIMODAL IMAGE RECOGNITION: If the traveler has attached an image, visually identify the landmark, architectural style, deity, beach, or dish, and ground your response in its historical and regional context.\n"
            "5. REAL-TIME AWARENESS: When Live Web Search context is provided, use it to give up-to-date festival dates, event timings, and seasonal tips.\n"
            "6. CLEAN OUTPUT: Do NOT include raw bracketed citations like '[Source 1]' or append 'Source Citations:' lists, as sources are automatically rendered by the UI."
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
