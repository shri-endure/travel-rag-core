// Destination Data Catalog
const DESTINATIONS = {
    goa: {
        id: "goa",
        name: "Goa",
        apiName: "Goa",
        icon: "palmtree",
        title: "Goa Travel Guide",
        summary: "Sun-kissed beaches, clifftop forts, UNESCO World Heritage churches, spicy seafood thalis, and Susegad culture.",
        themeClass: "theme-goa",
        budget: "₹1,200 – ₹12,000/day",
        transport: "Scooters & Ferries",
        placeholder: "e.g., What are the best beaches in North vs South Goa for relaxation and water sports?",
        suggestions: [
            { icon: "waves", text: "Best Beaches & Water Sports", q: "What are the best beaches in North vs South Goa for relaxation and water sports?" },
            { icon: "utensils", text: "Goan Seafood Thali & Cafes", q: "What is a traditional Goan Fish Curry Thali and where to try authentic Goan food?" },
            { icon: "cloud-rain", text: "Monsoon & Dudhsagar Falls", q: "How is Goa during the monsoon and how to visit Dudhsagar Falls?" },
            { icon: "bike", text: "Scooter Rental & Budget Tips", q: "What are the scooter rental costs, fuel rules, and budget travel tips in Goa?" },
            { icon: "landmark", text: "Old Goa & Fontainhas", q: "Tell me about Old Goa UNESCO churches and Fontainhas Latin Quarter." }
        ]
    },
    mumbai: {
        id: "mumbai",
        name: "Mumbai",
        apiName: "Mumbai",
        icon: "building-2",
        title: "Mumbai Travel Guide",
        summary: "Gateway of India, UNESCO CSMT, sunset along Marine Drive, vibrant street food, and historic Irani cafes.",
        themeClass: "theme-mumbai",
        budget: "₹1,000 – ₹12,000/day",
        transport: "Local Trains (UTS) & Taxis",
        placeholder: "e.g., What are the best street food spots and local transport options in Mumbai?",
        suggestions: [
            { icon: "utensils", text: "Iconic Street Food & Irani Cafes", q: "What are the must-try street foods (Vada Pav, Pav Bhaji) and best Irani cafes in Mumbai?" },
            { icon: "sun", text: "Marine Drive & Gateway Sunset", q: "Tell me about Marine Drive sunset, Gateway of India, and Colaba Causeway." },
            { icon: "train", text: "Local Train & Rush Hour Tips", q: "How do I travel via Mumbai Local Trains and avoid peak rush hours?" },
            { icon: "sparkles", text: "Siddhivinayak & Haji Ali", q: "How to visit Siddhivinayak Temple, Mount Mary Church, and Haji Ali Dargah?" },
            { icon: "wallet", text: "Budget Travel Breakdown", q: "What is the daily budget breakdown and transport tips for Mumbai?" }
        ]
    },
    bangalore: {
        id: "bangalore",
        name: "Bangalore",
        apiName: "Bangalore",
        icon: "trees",
        title: "Bangalore Travel Guide",
        summary: "Lush botanical parks, royal Tudor palace, legendary filter coffee & benne dosas, and buzzing craft breweries.",
        themeClass: "theme-bangalore",
        budget: "₹1,000 – ₹11,000/day",
        transport: "Namma Metro & BMTC Buses",
        placeholder: "e.g., Where can I find the best filter coffee and traditional Benne Dosa?",
        suggestions: [
            { icon: "coffee", text: "Filter Coffee & Benne Dosa", q: "Where can I find the crispest Benne Dosa and traditional Filter Coffee in Bangalore?" },
            { icon: "trees", text: "Lalbagh & Cubbon Park", q: "Tell me about Lalbagh Botanical Garden and Cubbon Park walking trails." },
            { icon: "castle", text: "Bangalore Palace & Heritage", q: "How to plan a visit to Bangalore Palace and Tipu Sultan's Summer Palace?" },
            { icon: "sunrise", text: "Nandi Hills Sunrise Trip", q: "What is the best way to plan an early morning sunrise trip to Nandi Hills?" },
            { icon: "beer", text: "Top Craft Breweries", q: "Which are the top craft microbreweries in Indiranagar and Koramangala?" }
        ]
    },
    gujarat: {
        id: "gujarat",
        name: "Gujarat",
        apiName: "Gujarat",
        icon: "sun",
        title: "Gujarat Travel Guide",
        summary: "World's tallest Statue of Unity, Asiatic lions in Gir, magical White Rann, Solanki stepwells, and grand vegetarian thalis.",
        themeClass: "theme-gujarat",
        budget: "₹900 – ₹11,000/day",
        transport: "GSRTC Buses & Expressways",
        placeholder: "e.g., How to book a Gir Lion Safari and visit Rann of Kutch?",
        suggestions: [
            { icon: "compass", text: "Gir Asiatic Lion Safari", q: "How do I book an Asiatic Lion Safari at Gir National Park in advance?" },
            { icon: "sparkles", text: "Rann Utsav & White Desert", q: "When is Rann Utsav held in the White Desert and how do I get a tourist permit?" },
            { icon: "landmark", text: "Somnath & Dwarka Temples", q: "Tell me about the sacred Somnath and Dwarkadhish pilgrimage circuit." },
            { icon: "utensils", text: "Grand Gujarati Thali & Farsan", q: "What items are included in an authentic Grand Gujarati Thali and Farsan?" },
            { icon: "file-text", text: "Alcohol Permit Guidelines", q: "What is the alcohol permit procedure for non-resident tourists in Gujarat?" }
        ]
    },
    uttar_pradesh: {
        id: "uttar_pradesh",
        name: "Uttar Pradesh",
        apiName: "Uttar Pradesh",
        icon: "landmark",
        title: "Uttar Pradesh Travel Guide",
        summary: "The timeless Taj Mahal, sacred Varanasi Ganga Ghats, Lucknow's Awadhi culinary legacy, and holy Ayodhya-Mathura.",
        themeClass: "theme-uttar_pradesh",
        budget: "₹800 – ₹10,000/day",
        transport: "Vande Bharat & E-Rickshaws",
        placeholder: "e.g., How to experience the Varanasi Ghats, Ganga Aarti and Taj Mahal?",
        suggestions: [
            { icon: "heart", text: "Taj Mahal Rules & Sunrise", q: "What are the best hours and official guidelines for visiting the Taj Mahal in Agra?" },
            { icon: "flame", text: "Varanasi Ghats & Ganga Aarti", q: "How can I attend the evening Maha Ganga Aarti at Dashashwamedh Ghat in Varanasi?" },
            { icon: "utensils", text: "Lucknow Awadhi Kebabs", q: "Where to taste famous Lucknowi Tunday Kebabs and Awadhi Dum Biryani?" },
            { icon: "sparkles", text: "Ayodhya Ram Mandir", q: "How to plan a pilgrimage to Ram Janmabhoomi Temple in Ayodhya?" },
            { icon: "shopping-bag", text: "Banarasi Silk & Chikankari", q: "Where are the best markets for genuine Banarasi Silk and Lucknowi Chikankari?" }
        ]
    }
};

const GLOBAL_SUGGESTIONS = [
    { icon: "utensils", text: "Mumbai Street Food & Irani Cafes", q: "What are the best street food places and budget travel tips in Mumbai?", dest: "mumbai" },
    { icon: "palmtree", text: "Goa Beaches & Water Sports", q: "What are the top beaches, water sports, and monsoon travel tips for Goa?", dest: "goa" },
    { icon: "coffee", text: "Bangalore Coffee & Breweries", q: "Recommend a traditional South Indian breakfast trail and craft breweries in Bangalore", dest: "bangalore" },
    { icon: "landmark", text: "Gujarat Somnath & Gir Safari", q: "How to plan a trip to Somnath temple and Gir Lion Safari in Gujarat?", dest: "gujarat" },
    { icon: "flame", text: "Varanasi Ghats & Taj Mahal", q: "What is the best way to experience Varanasi Ganga Aarti and the Taj Mahal in Uttar Pradesh?", dest: "uttar_pradesh" }
];

let selectedDestination = null;
let conversationHistory = [];

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    renderGlobalSuggestions();
    setupEventListeners();
    checkHealth();
    handleUrlRouting();
    refreshIcons();
});

window.addEventListener("hashchange", handleUrlRouting);

function refreshIcons() {
    if (window.lucide) {
        window.lucide.createIcons();
    }
}

function handleUrlRouting() {
    const hash = window.location.hash.replace("#", "").toLowerCase();
    if (DESTINATIONS[hash]) {
        selectDestination(hash, false);
    } else {
        resetToAllDestinations(false);
    }
}

// Setup Event Listeners
function setupEventListeners() {
    const input = document.getElementById("user-query-input");
    if (input) {
        input.addEventListener("keypress", (e) => {
            if (e.key === "Enter") submitQuery();
        });
    }
}

// Select a destination stamp
function selectDestination(destKey, updateHash = true) {
    const dest = DESTINATIONS[destKey];
    if (!dest) return;
    selectedDestination = dest;

    if (updateHash) window.location.hash = destKey;

    // Reset Chat Memory & Image on State Switch for a Fresh State View
    conversationHistory = [];
    clearSelectedImage();
    const queryInput = document.getElementById("user-query-input");
    if (queryInput) queryInput.value = "";

    // Show Top Breadcrumb Bar & Hide Hero Header Text
    document.getElementById("dest-top-bar").classList.remove("hidden");
    document.getElementById("hero-header-section").classList.add("hidden");
    document.getElementById("dest-crumb-name").innerText = dest.name;

    // Update Active Stamp Card Visuals
    document.querySelectorAll(".stamp-card").forEach(card => card.classList.remove("active"));
    const activeCard = document.getElementById(`stamp-${destKey}`);
    if (activeCard) activeCard.classList.add("active");

    // Apply Theme to Workspace Panel
    const panel = document.getElementById("workspace-panel");
    panel.className = `workspace-card ${dest.themeClass}`;

    // Show Destination Meta Header
    const metaHeader = document.getElementById("dest-meta-header");
    if (metaHeader) metaHeader.classList.remove("hidden");
    const metaTitle = document.getElementById("dest-meta-title");
    if (metaTitle) metaTitle.innerText = dest.title;
    const metaSummary = document.getElementById("dest-meta-summary");
    if (metaSummary) metaSummary.innerText = dest.summary;

    // Update Input Placeholder
    if (queryInput) queryInput.placeholder = dest.placeholder;

    // Reset Chat Thread to Fresh State-Specific Welcome
    const thread = document.getElementById("chat-thread");
    if (thread) {
        thread.innerHTML = `
            <div class="chat-msg assistant-msg">
                <div class="msg-avatar">
                    <i data-lucide="sparkles" class="avatar-icon"></i>
                </div>
                <div class="msg-body">
                    <div class="msg-header">
                        <span class="msg-author">AI Travel Guide</span>
                        <span class="msg-badge">${escapeHtml(dest.name)} Guide</span>
                    </div>
                    <div class="msg-content markdown-body">
                        <p>Welcome to the <strong>${escapeHtml(dest.name)}</strong> Travel Guide!</p>
                        <p>Ask me anything about ${escapeHtml(dest.name)}'s heritage monuments, hidden beaches/forests, local food, or cultural festivals. You can also upload a photo to identify landmarks.</p>
                    </div>
                </div>
            </div>
        `;
    }

    // Render State-Specific Quick Suggestions
    const chipsContainer = document.getElementById("quick-chips-container");
    chipsContainer.innerHTML = dest.suggestions.map(s => `
        <button class="chip-btn btn-icon-gap" onclick="executeSuggestion('${escapeHtml(s.q)}')">
            <i data-lucide="${s.icon}" class="icon-xs"></i> ${s.text}
        </button>
    `).join("");

    refreshIcons();

    // Smooth scroll down to workspace
    document.getElementById("workspace-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

// Reset back to All Destinations / Home
function resetToAllDestinations(updateHash = true) {
    selectedDestination = null;
    if (updateHash) window.location.hash = "home";

    // Reset Chat Memory & Image for Fresh Home View
    conversationHistory = [];
    clearSelectedImage();
    const queryInput = document.getElementById("user-query-input");
    if (queryInput) {
        queryInput.value = "";
        queryInput.placeholder = "Ask a question or upload a photo of a temple, beach, or landmark...";
    }

    // Hide Top Breadcrumb Bar & Show Hero Header Text
    document.getElementById("dest-top-bar").classList.add("hidden");
    document.getElementById("hero-header-section").classList.remove("hidden");

    // Remove Active Stamp Highlighting
    document.querySelectorAll(".stamp-card").forEach(card => card.classList.remove("active"));

    // Reset Workspace Theme
    const panel = document.getElementById("workspace-panel");
    panel.className = "workspace-card theme-default";

    // Hide Destination Meta Header
    const metaHeader = document.getElementById("dest-meta-header");
    if (metaHeader) metaHeader.classList.add("hidden");

    // Reset Chat Thread to Fresh Initial Home Welcome
    const thread = document.getElementById("chat-thread");
    if (thread) {
        thread.innerHTML = `
            <div class="chat-msg assistant-msg">
                <div class="msg-avatar">
                    <i data-lucide="sparkles" class="avatar-icon"></i>
                </div>
                <div class="msg-body">
                    <div class="msg-header">
                        <span class="msg-author">AI Travel Guide</span>
                        <span class="msg-badge">5 Core Destinations</span>
                    </div>
                    <div class="msg-content markdown-body">
                        <p>Hello! I am your AI Travel Assistant, verified across <strong>Goa</strong>, <strong>Mumbai</strong>, <strong>Bangalore</strong>, <strong>Gujarat</strong>, and <strong>Uttar Pradesh</strong>.</p>
                        <p>Ask me anything about temples, heritage, monuments, beaches, local food, or itineraries. I remember our conversation, so feel free to ask follow-up questions!</p>
                    </div>
                </div>
            </div>
        `;
    }

    // Render Global Suggestions
    renderGlobalSuggestions();
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// Complete Fresh Page Reset
function resetToFreshPage() {
    clearChatHistory();
    resetToAllDestinations(true);
    const input = document.getElementById("user-query-input");
    if (input) input.value = "";
    window.location.hash = "";
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// App Information Modal Controls
function openAppInfoModal() {
    const modal = document.getElementById("info-modal-backdrop");
    if (modal) modal.classList.remove("hidden");
    refreshIcons();
}

function closeAppInfoModal(event) {
    if (event && event.target && event.target.id !== "info-modal-backdrop" && !event.target.closest(".btn-close-modal")) {
        return;
    }
    const modal = document.getElementById("info-modal-backdrop");
    if (modal) modal.classList.add("hidden");
}


// Render Global Suggestions
function renderGlobalSuggestions() {
    const chipsContainer = document.getElementById("quick-chips-container");
    chipsContainer.innerHTML = GLOBAL_SUGGESTIONS.map(s => `
        <button class="chip-btn btn-icon-gap" onclick="executeGlobalSuggestion('${s.dest}', '${escapeHtml(s.q)}')">
            <i data-lucide="${s.icon}" class="icon-xs"></i> ${s.text}
        </button>
    `).join("");
    refreshIcons();
}

function executeGlobalSuggestion(destKey, query) {
    selectDestination(destKey);
    document.getElementById("user-query-input").value = query;
    submitQuery();
}

function executeSuggestion(query) {
    document.getElementById("user-query-input").value = query;
    submitQuery();
}

// Global Image Upload State
let selectedImageData = null;

function triggerImagePicker() {
    const fileInput = document.getElementById("user-image-input");
    if (fileInput) fileInput.click();
}

function handleImageUpload(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function (e) {
        selectedImageData = e.target.result;
        const container = document.getElementById("image-preview-container");
        const previewImg = document.getElementById("image-preview-img");
        const previewName = document.getElementById("image-preview-name");

        if (previewImg) {
            previewImg.src = selectedImageData;
            previewImg.style.display = "block";
        }
        if (previewName) previewName.textContent = file.name || "Landmark photo attached";
        if (container) container.style.display = "inline-flex";
    };
    reader.readAsDataURL(file);
}

function clearSelectedImage() {
    selectedImageData = null;
    const container = document.getElementById("image-preview-container");
    const previewImg = document.getElementById("image-preview-img");
    const fileInput = document.getElementById("user-image-input");
    if (container) container.style.display = "none";
    if (previewImg) {
        previewImg.src = "";
        previewImg.style.display = "none";
    }
    if (fileInput) fileInput.value = "";
}


// Append a Message to the Chat Thread
function appendChatMessage(role, contentHtml, sources = [], title = "", imageAttached = null) {
    const thread = document.getElementById("chat-thread");
    if (!thread) return;

    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-msg ${role === "user" ? "user-msg" : "assistant-msg"}`;

    if (role === "user") {
        let imgHtml = "";
        if (imageAttached) {
            imgHtml = `<div class="user-msg-image-wrap"><img src="${imageAttached}" alt="User uploaded landmark" class="user-msg-image" /></div>`;
        }
        msgDiv.innerHTML = `
            <div class="msg-body">
                <div class="msg-content user-bubble">
                    ${imgHtml}
                    ${contentHtml ? `<div>${escapeHtml(contentHtml)}</div>` : ""}
                </div>
            </div>
            <div class="msg-avatar user-avatar">
                <i data-lucide="user" class="avatar-icon"></i>
            </div>
        `;
    } else {
        let sourcesHtml = "";
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <div class="msg-sources">
                    <span class="sources-label"><i data-lucide="shield-check" class="icon-xs"></i> Verified Sources:</span>
                    ${sources.map(s => {
                const label = typeof s === "object" ? `${s.destination} (${s.source})` : s;
                if (typeof s === "object" && s.url) {
                    return `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer" class="source-tag source-tag-link"><i data-lucide="external-link" class="icon-xs"></i> ${escapeHtml(label)}</a>`;
                }
                return `<span class="source-tag"><i data-lucide="file-text" class="icon-xs"></i> ${escapeHtml(label)}</span>`;
            }).join(" ")}
                </div>
            `;
        }

        msgDiv.innerHTML = `
            <div class="msg-avatar">
                <i data-lucide="sparkles" class="avatar-icon"></i>
            </div>
            <div class="msg-body">
                <div class="msg-header">
                    <span class="msg-author">AI Travel Guide</span>
                    ${title ? `<span class="msg-badge">${title}</span>` : ""}
                </div>
                <div class="msg-content markdown-body">${contentHtml}</div>
                ${sourcesHtml}
            </div>
        `;
    }

    thread.appendChild(msgDiv);
    refreshIcons();
    msgDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Clear Chat Memory & Reset Thread
function clearChatHistory() {
    conversationHistory = [];
    clearSelectedImage();
    const thread = document.getElementById("chat-thread");
    if (thread) {
        thread.innerHTML = `
            <div class="chat-msg assistant-msg">
                <div class="msg-avatar">
                    <i data-lucide="sparkles" class="avatar-icon"></i>
                </div>
                <div class="msg-body">
                    <div class="msg-header">
                        <span class="msg-author">AI Travel Guide</span>
                        <span class="msg-badge">Memory Cleared</span>
                    </div>
                    <div class="msg-content markdown-body">
                        <p>Conversation memory has been cleared! Ask me any travel question about <strong>Goa</strong>, <strong>Mumbai</strong>, <strong>Bangalore</strong>, <strong>Gujarat</strong>, or <strong>Uttar Pradesh</strong>, or upload a photo of a landmark.</p>
                    </div>
                </div>
            </div>
        `;
        refreshIcons();
    }
}

// Submit Travel Query with Real-Time Token Streaming & Memory
async function submitQuery() {
    const input = document.getElementById("user-query-input");
    let queryText = input.value.trim();
    const imageToSend = selectedImageData;

    if (!queryText && !imageToSend) return;
    if (!queryText && imageToSend) {
        queryText = "What landmark, temple, or place is this, and tell me about it?";
    }

    input.value = "";
    const destName = selectedDestination ? selectedDestination.apiName : undefined;

    // 1. Append User Message with attached Image
    appendChatMessage("user", queryText, [], "", imageToSend);
    clearSelectedImage();

    // 2. Add to Local Memory
    const currentTurn = { role: "user", content: queryText };
    const historyToSend = [...conversationHistory];
    conversationHistory.push(currentTurn);

    // 3. Create Assistant Message Element in Chat Thread for Streaming
    const thread = document.getElementById("chat-thread");
    const msgDiv = document.createElement("div");
    msgDiv.className = "chat-msg assistant-msg";
    const titleBadge = destName ? destName : "AI Travel Guide";

    msgDiv.innerHTML = `
        <div class="msg-avatar">
            <i data-lucide="sparkles" class="avatar-icon"></i>
        </div>
        <div class="msg-body">
            <div class="msg-header">
                <span class="msg-author">AI Travel Guide</span>
                <span class="msg-badge">${escapeHtml(titleBadge)}</span>
            </div>
            <div class="msg-content markdown-body" id="streaming-content"><p class="streaming-cursor">Thinking & retrieving grounded travel knowledge...</p></div>
            <div class="msg-sources" id="streaming-sources" style="display: none;"></div>
        </div>
    `;
    thread.appendChild(msgDiv);
    refreshIcons();
    msgDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });

    const contentEl = msgDiv.querySelector("#streaming-content");
    const sourcesEl = msgDiv.querySelector("#streaming-sources");
    if (contentEl) contentEl.removeAttribute("id");
    if (sourcesEl) sourcesEl.removeAttribute("id");

    let fullAnswer = "";
    let receivedSources = [];

    try {
        const res = await fetch("/query/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: queryText,
                destination: destName,
                top_k: 4,
                chat_history: historyToSend,
                image_data: imageToSend
            })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            contentEl.innerHTML = `<p style="color: #dc2626;">Error: ${escapeHtml(errData.detail || "Query failed")}</p>`;
            return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n\n");
            buffer = lines.pop(); // Keep partial chunk in buffer

            for (const block of lines) {
                const trimmed = block.trim();
                if (!trimmed.startsWith("data:")) continue;

                try {
                    const jsonStr = trimmed.replace(/^data:\s*/, "");
                    const data = JSON.parse(jsonStr);

                    if (data.type === "sources") {
                        receivedSources = data.sources || [];
                        if (receivedSources.length > 0) {
                            sourcesEl.innerHTML = `
                                <span class="sources-label"><i data-lucide="shield-check" class="icon-xs"></i> Verified Sources:</span>
                                ${receivedSources.map(s => {
                                const label = typeof s === "object" ? `${s.destination} (${s.source})` : s;
                                if (typeof s === "object" && s.url) {
                                    return `<a href="${escapeHtml(s.url)}" target="_blank" rel="noopener noreferrer" class="source-tag source-tag-link"><i data-lucide="external-link" class="icon-xs"></i> ${escapeHtml(label)}</a>`;
                                }
                                return `<span class="source-tag"><i data-lucide="file-text" class="icon-xs"></i> ${escapeHtml(label)}</span>`;
                            }).join(" ")}
                            `;
                            sourcesEl.style.display = "flex";
                            refreshIcons();
                        }
                    } else if (data.type === "token") {
                        fullAnswer += data.token;
                        contentEl.innerHTML = marked.parse(fullAnswer);
                        msgDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
                    } else if (data.type === "error") {
                        contentEl.innerHTML += `<p style="color: #dc2626;">Error: ${escapeHtml(data.error)}</p>`;
                    }
                } catch (parseErr) {
                    console.error("SSE parse error", parseErr, trimmed);
                }
            }
        }

        // Finalize conversation memory
        if (fullAnswer.trim()) {
            conversationHistory.push({ role: "assistant", content: fullAnswer.trim() });
            contentEl.innerHTML = marked.parse(fullAnswer);
            refreshIcons();
        }

    } catch (err) {
        contentEl.innerHTML = `<p style="color: #dc2626;">Network error: ${escapeHtml(err.message)}</p>`;
    }
}


// Generate Quick 3-Day Itinerary

async function generateQuickItinerary() {
    if (!selectedDestination) return;

    const queryPrompt = `Generate a comprehensive 3-Day itinerary for ${selectedDestination.name}`;
    appendChatMessage("user", queryPrompt);
    conversationHistory.push({ role: "user", content: queryPrompt });

    showLoading(`Designing personalized 3-Day ${selectedDestination.name} Itinerary with Gemini...`);

    try {
        const res = await fetch("/itinerary", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                destination: selectedDestination.apiName,
                days: 3,
                budget: "Mid-Range",
                interests: ["Culture & Heritage", "Local Food & Cafes", "Sightseeing"],
                pace: "Moderate"
            })
        });
        const data = await res.json();
        hideLoading();

        if (data.error || res.status >= 400) {
            appendChatMessage("assistant", `Itinerary generation failed: ${data.detail || data.error}`);
            return;
        }

        const itineraryText = data.itinerary || data.answer;
        conversationHistory.push({ role: "assistant", content: itineraryText });

        const parsedHtml = marked.parse(itineraryText);
        appendChatMessage("assistant", parsedHtml, data.sources || [], `3-Day Itinerary • ${selectedDestination.name}`);

    } catch (err) {
        hideLoading();
        appendChatMessage("assistant", `Error generating itinerary: ${err.message}`);
    }
}

// Trigger Ingestion
async function triggerIngestion() {
    showLoading("Re-indexing destination knowledge files into Chroma Vector DB...");
    try {
        const res = await fetch("/reindex", { method: "POST" });
        const data = await res.json();
        hideLoading();
        alert(`Knowledge Base Ingested Successfully!\nTotal Vectors: ${data.total_vectors || 97}`);
    } catch (err) {
        hideLoading();
        alert(`Ingestion failed: ${err.message}`);
    }
}

// Check Backend Health
async function checkHealth() {
    try {
        const res = await fetch("/health");
        const data = await res.json();
        if (data.status === "healthy") {
            document.getElementById("status-text").innerText = "Gemini & Chroma Ready";
            document.getElementById("status-badge").className = "badge ready";
        }
    } catch (err) {
        document.getElementById("status-text").innerText = "Connecting to Server...";
    }
}

function showLoading(msg) {
    document.getElementById("loading-message").innerText = msg;
    document.getElementById("loading-overlay").classList.remove("hidden");
}

function hideLoading() {
    document.getElementById("loading-overlay").classList.add("hidden");
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
