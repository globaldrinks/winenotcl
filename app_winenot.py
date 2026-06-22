import streamlit as st
import os
import time
import pandas as pd
import re
import unicodedata
import requests
from datetime import datetime
from rapidfuzz import process, fuzz

# --- GLOBAL BROADCAST SYSTEM ---
# This dictionary is shared across ALL connected users/sessions
@st.cache_resource
def get_global_broadcast_channel():
    return {"message": None, "timestamp": None}

broadcast_channel = get_global_broadcast_channel()

# Check if there is an active broadcast the user hasn't seen yet
if broadcast_channel["message"]:
    # Check if this specific session has already acknowledged this broadcast
    if st.session_state.get("last_seen_broadcast") != broadcast_channel["timestamp"]:
        # Display the announcement at the very top of the app
        st.toast(f"📢 **ANNOUNCEMENT:** {broadcast_channel['message']}", icon="🔔")
        # Alternative: use st.info() if you want a persistent banner instead of a fading toast
        # st.info(f"📢 **Announcement:** {broadcast_channel['message']}")


# --- VISIT COUNTER LOGIC ---
COUNTER_FILE = "counter.txt"
if not os.path.exists(COUNTER_FILE):
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        f.write("0")

if "tracked_visit" not in st.session_state:
    st.session_state.tracked_visit = True
    with open(COUNTER_FILE, "r", encoding="utf-8") as f:
        try:
            current_count = int(f.read().strip())
        except ValueError:
            current_count = 0
    new_count = current_count + 1
    with open(COUNTER_FILE, "w", encoding="utf-8") as f:
        f.write(str(new_count))

# --- INITIALIZE SESSION STATE FOR THE TREE ---
if "current_category" not in st.session_state:
    st.session_state.current_category = "main"

# 1. Page Config
st.set_page_config(page_title="Asistente MOVI Night", page_icon="🍷")
st.title("Asistente Virtual MOVI 🍷")

# 2. Define URL and Load Data
SHEET_URL = "https://docs.google.com/spreadsheets/d/1dMokuYm06WAqB8VJxgHEH0nYHzItH-wa59xhoTnDhK8/edit "

def get_csv_url(url):
    try:
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if match:
            sheet_id = match.group(1)
            return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=MOVI"
    except:
        pass
    return None

CSV_URL = get_csv_url(SHEET_URL)

def clean_string(text):
    text = str(text).lower().strip()
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

@st.cache_data(ttl=10)
def load_faqs_tree():
    fallback_df = pd.DataFrame([
        {"category": "main", "question": "🍇 Search by Vineyard", "answer": "TREE_NODE"},
        {"category": "Search by Vineyard", "question": "Viña 1", "answer": "Vino 1"}
    ])
    if not CSV_URL:
        return fallback_df
    try:
        df = pd.read_csv(CSV_URL, storage_options={"timeout": 5})
        df.columns = [str(col).strip().lower() for col in df.columns]
        
        if 'category' in df.columns and 'question' in df.columns and 'answer' in df.columns:
            return df.dropna(subset=['category', 'question'])
        return fallback_df
    except:
        return fallback_df

df_faqs = load_faqs_tree()

# --- INITIALIZE SESSION STATE FOR THE TREE ---
if "current_category" not in st.session_state:
    st.session_state.current_category = "main"

# --- GLOBAL BROADCAST SYSTEM ---
# This dictionary lives in the server memory and is shared by all connected users
@st.cache_resource
def get_global_broadcast_channel():
    return {"message": None, "timestamp": None}

broadcast_channel = get_global_broadcast_channel()

# 1. Page Config
st.set_page_config(page_title="Asistente Bocas Moradas", page_icon="🍷")
st.title("🤖 Hola Wine Lover! 🍷")

# 2. Define URL and Load Data
# ... [Keep your existing get_csv_url, clean_string, and load_faqs_tree functions here] ...
df_faqs = load_faqs_tree()


# =====================================================================
# 3. CREATE / RENDER CHAT HISTORY & LIVE BROADCASTS
# =====================================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Estoy acá para ayudarte! Explora las opciones de abajo o hazme una pregunta directamente."}
    ]

if "waiting_for_email" not in st.session_state:
    st.session_state.waiting_for_email = None

# --- TOAST TRIGGER (Fading Notification) ---
# If an admin has broadcasted a message globally
# --- TOAST TRIGGER (Fading Notification) ---
if broadcast_channel["message"]:
    if st.session_state.get("last_seen_broadcast") != broadcast_channel["timestamp"]:
        # Using an emoji and bold text to catch attention immediately
        st.toast(f"📢 **NOTIFICACIÓN:** {broadcast_channel['message']}", icon="🍷")
        st.session_state.last_seen_broadcast = broadcast_channel["timestamp"]
        
        # A tiny sleep forces the Streamlit execution thread to pause for a moment,
        # ensuring the UI renders and holds the element on spotty mobile connections.
        time.sleep(1)

# Render the persistent chat room logs on screen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# =====================================================================


# 4. PREDEFINED BUTTONS INTERFACE (DYNAMIC TREE)
# ... [The rest of your code continues below here] ...

# 4. PREDEFINED BUTTONS INTERFACE (DYNAMIC TREE)
st.write("---") 
st.write(f"💡 **Explore Options ({st.session_state.current_category}):**")

button_pressed = None

if not st.session_state.waiting_for_email:
    if st.session_state.current_category != "main":
        if st.button("⬅️ Volver al Menú Principal", use_container_width=True):
            st.session_state.current_category = "main"
            st.rerun()

    # Filtrado por categorías
    current_rows = df_faqs[df_faqs['category'].apply(clean_string) == clean_string(st.session_state.current_category)]
    questions_list = current_rows['question'].tolist()
    
    max_buttons_per_row = 3
    for i in range(0, len(questions_list), max_buttons_per_row):
        row_questions = questions_list[i : i + max_buttons_per_row]
        cols = st.columns(len(row_questions))
        for idx, question in enumerate(row_questions):
            with cols[idx]:
                if st.button(question, key=f"btn_{st.session_state.current_category}_{i+idx}", use_container_width=True):
                    cleaned_q = clean_string(question)
                    is_parent = df_faqs['category'].apply(clean_string).eq(cleaned_q).any()
                    
                    if is_parent:
                        st.session_state.current_category = question
                        st.rerun()
                    else:
                        button_pressed = question
                        
    st.write("")
    if st.button("✨ Quiero más info & Updates de próximos eventos", key="btn_more_info", use_container_width=True):
        button_pressed = "more info"

# 5. CHAT INPUT LOGIC (Cambiado a st.chat_input para mejor UX)
placeholder_text = "Escribe tu email aquí..." if st.session_state.waiting_for_email else "Hazme una pregunta sobre vinos..."
user_typed_input = st.chat_input(placeholder_text)

# Capturar la acción ya sea por botón de arriba o por escritura manual
final_input = None
if button_pressed:
    final_input = button_pressed
elif user_typed_input:
    final_input = user_typed_input

# Procesar la entrada del usuario si existe
if final_input:
    # 1. Agregar inmediatamente el mensaje del usuario al estado
    st.session_state.messages.append({"role": "user", "content": final_input})
    
    # 2. Lógica cuando estamos esperando un Email
    if st.session_state.waiting_for_email:
        user_email = final_input.strip()
        unanswered_question = st.session_state.waiting_for_email
        
        FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd97qfIqBnK7fy2qKNQJ4t5vauriks29CFy-KXSj6qFGXTsbA/formResponse"
        form_data = {
            "entry.1621915346": user_email,          
            "entry.409076594": unanswered_question   
        }
        try:
            response = requests.post(FORM_URL, data=form_data, timeout=5)
            print(f"--- Google Form Status: {response.status_code} ---") 
        except Exception as e:
            print(f"--- Form Submission Error: {str(e)} ---")
            with open("leads_log.txt", "a", encoding="utf-8") as f:
                f.write(f"Date: {datetime.now()} | Email: {user_email} | Question: {unanswered_question} (Form Fail)\n")
            
        bot_response = "¡Gracias! Nos contactaremos contigo por correo a la brevedad. ¡Disfruta la feria! 🍷"
        st.session_state.waiting_for_email = None

    # 3. Lógica Normal de preguntas / solicitud de info
    else:
        clean_input = clean_string(final_input)
        
        if "more info" in clean_input or clean_input == "info":
            bot_response = "¡Con gusto te enviaremos más información! Por favor, escribe tu email aquí abajo."
            st.session_state.waiting_for_email = "Requested General More Info"
                
        else:
            all_questions = df_faqs['question'].tolist()
            # Búsqueda difusa segura contra nulos (None)
            best_match = process.extractOne(clean_input, [clean_string(q) for q in all_questions], scorer=fuzz.WRatio, score_cutoff=60)
                    
            if best_match is not None: # El fix crítico para evitar el crash
                matched_index = best_match[2]
                bot_response = df_faqs.iloc[matched_index]['answer']
            else:
                bot_response = f"Ups, no tengo una respuesta exacta para '{final_input}', pero si me dejas tu email, te responderemos en privado a la brevedad."
                st.session_state.waiting_for_email = final_input

    # Agregar respuesta del bot y recargar la página para mostrar los cambios
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    st.rerun()

# 6. SECRET ADMIN PANEL
st.write("---")
with st.expander("🔒 Admin Panel (Leads & Stats)"):
    password = st.text_input("Enter Admin Password:", type="password")
    if password == "mysecret123":
        with open(COUNTER_FILE, "r", encoding="utf-8") as f:
            total_visits = f.read().strip()
        st.write(f"📈 **Total Website Visits:** `{total_visits}`")
        
        st.write("---")
        st.subheader("📢 Broadcast Alert to All Users")
        broadcast_text = st.text_input("Enter toast message:", placeholder="e.g., ¡Cata especial en stand 3 en 5 minutos! 🍷")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Send Live Toast", use_container_width=True):
                if broadcast_text.strip():
                    new_timestamp = time.time()
                    
                    # 1. Update the global channel
                    broadcast_channel["message"] = broadcast_text.strip()
                    broadcast_channel["timestamp"] = new_timestamp
                    
                    # 2. Pre-emptively mark it as "seen" for the Admin's own session 
                    # so the admin doesn't get a double pop-up
                    st.session_state.last_seen_broadcast = new_timestamp
                    
                    st.success("Toast broadcasted successfully!")
                    
                    # 3. Give the server a brief millisecond to register the state before rerunning
                    time.sleep(0.2)
                    st.rerun()
        with col2:
            if st.button("🗑️ Clear Active Toast", use_container_width=True):
                broadcast_channel["message"] = None
                broadcast_channel["timestamp"] = None
                st.info("Broadcast cleared.")
                st.rerun()
