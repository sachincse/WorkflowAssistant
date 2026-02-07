import streamlit as st
import time
from workflow_engine_full import WorkflowEngine
from security import SecurityGuard
from dotenv import load_dotenv

# Load Environment
load_dotenv()

# --- FORCE RELOAD LOGIC ---
# If version key is not present or old, clear session
VERSION = "1.5" # Increment this to force reload
if "app_version" not in st.session_state or st.session_state.app_version != VERSION:
    st.cache_data.clear()
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.app_version = VERSION

# Initialize Engine
if 'engine' not in st.session_state:
    st.session_state.engine = WorkflowEngine()
if 'guard' not in st.session_state:
    st.session_state.guard = SecurityGuard()
if "messages" not in st.session_state:
    st.session_state.messages = []

st.set_page_config(
    page_title="Deriv Intelligent Onboarding",
    layout="wide",
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# --- THEME & CSS ---
st.markdown("""
    <style>
    /* Global Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0e1117;
        color: #ffffff;
    }

    /* Glassmorphism Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Input Styling */
    .stTextInput>div>div>input {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: white;
        border-radius: 10px;
    }
    
    /* Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #ff4b4b 0%, #ff9068 100%);
        border: none;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR (Dashboard) ---
with st.sidebar:
    st.title("🛡️ Dashboard")
    st.subheader("System Status")
    
    # Status Indicators
    st.success("✅ Guardrails Active")
    st.info("🧠 Model: GPT-4o-mini (OpenAI)")
    
    # API Registry Status (Using Correct Public Method)
    st.subheader("🔌 Connected APIs")
    try:
        registry = st.session_state.engine.load_api_registry()
        for api in registry["apis"]:
            status_color = "🟢" if api["status"] == "active" else "🔴"
            st.write(f"{status_color} **{api['name']}**")
            st.caption(f"{api['description']}")
    except AttributeError:
        st.error("⚠️ Engine Reload Required. Refresh Page.")

    st.markdown("---")
    if st.button("Reload Config"):
        st.cache_data.clear()
        st.session_state.engine = WorkflowEngine()
        st.rerun()

    # --- LIVE CHECKLIST (Parsing Chat History) ---
    st.markdown("### 📋 Progress")
    
    # Simple heuristic to detect if fields are mentioned in User messages
    # In a real app, the LLM would output this state.
    gathered_info = {
        "Name": False,
        "Role": False,
        "Location": False,
        "Gender": False
    }
    
    # Scan user messages for keywords (very naive, but visual)
    full_text = " ".join([m["content"] for m in st.session_state.messages if m["role"] == "user"]).lower()
    
    if "sachin" in full_text or "name" in full_text: gathered_info["Name"] = True
    if "engineer" in full_text or "manager" in full_text or "role" in full_text: gathered_info["Role"] = True
    if "noida" in full_text or "location" in full_text or "london" in full_text: gathered_info["Location"] = True
    if "male" in full_text or "female" in full_text: gathered_info["Gender"] = True
    
    for field, done in gathered_info.items():
        icon = "✅" if done else "⬜"
        st.write(f"{icon} **{field}**")
    
    # --- POLICY MANAGEMENT ---
    st.markdown("---")
    st.markdown("### 📄 Policy Management")
    
    # Show active policies
    if st.button("View Active Policies"):
        from policy_manager import PolicyManager
        pm = PolicyManager()
        policies = pm.get_all_policies()
        for name, content in policies.items():
            with st.expander(f"📋 {name.replace('_', ' ').title()}"):
                st.text(content[:500] + "..." if len(content) > 500 else content)
    
    # Upload new policy
    st.markdown("#### Upload New Policy")
    uploaded_file = st.file_uploader("Upload Policy Document (.txt)", type=['txt'])
    policy_name = st.text_input("Policy Name", placeholder="e.g., Benefits, Remote Work")
    
    if uploaded_file and policy_name:
        if st.button("Save Policy"):
            from policy_manager import PolicyManager
            pm = PolicyManager()
            content = uploaded_file.read().decode('utf-8')
            success = pm.save_policy(policy_name, content)
            if success:
                st.success(f"✅ {policy_name} policy saved!")
                st.session_state.engine = WorkflowEngine()  # Reload engine
                st.rerun()
            else:
                st.error("❌ Failed to save policy")

# --- MAIN CHAT ---
st.title("Deriv AI Assistant 🤖")
st.markdown("### Conversational Onboarding Agent")

# Message History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
if prompt := st.chat_input("Type your request..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process
    with st.spinner("AI Thinking..."):
        # Pass conversation history to the engine for context
        response = st.session_state.engine.process_request(prompt, st.session_state.messages[:-1]) # Exclude just added prompt
        
        # Add AI message
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

        # Check for Final Workflow Execution
        if "Workflow Finalized" in response:
            st.balloons()
            
            # Display detailed workflow breakdown
            with st.expander("📋 **Complete Onboarding Workflow**", expanded=True):
                # Parse the plan from the response
                lines = response.split("\n")
                for line in lines:
                    if line.strip().startswith("-"):
                        # Display each workflow step
                        if "✅" in line:
                            st.success(line.strip())
                        elif "⚠️" in line:
                            st.warning(line.strip())
                        elif "❌" in line:
                            st.error(line.strip())
                        else:
                            st.info(line.strip())
