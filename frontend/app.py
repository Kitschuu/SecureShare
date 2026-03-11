import os
import streamlit as st
import requests
import base64
import json
import pandas as pd
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from dotenv import load_dotenv
from streamlit_cookies_controller import CookieController

load_dotenv()

# --- API CONFIGURATION ---
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="SecureShare - E2EE", layout="wide")

# --- COOKIE CONTROLLER ---
controller = CookieController()

# --- SESSION STATE ---
# Initialize session state from cookies first, then default
if "access_token" not in st.session_state:
    st.session_state.access_token = controller.get("access_token") 
if "username" not in st.session_state:
    st.session_state.username = controller.get("username")
if "role" not in st.session_state:
    st.session_state.role = controller.get("role")

def get_auth_headers():
    return {"Authorization": f"Bearer {st.session_state.access_token}"}

def decode_jwt(token: str) -> dict:
    """Helper to safely decode JWT payload on the frontend."""
    try:
        parts = token.split(".")
        if len(parts) == 3:
            payload_part = parts[1]
            # Add padding if needed
            padded = payload_part + "=" * ((4 - len(payload_part) % 4) % 4)
            decoded_bytes = base64.urlsafe_b64decode(padded)
            return json.loads(decoded_bytes)
    except Exception as e:
        print(f"Error decoding JWT: {e}")
    return {}

st.title("🔒 SecureShare - Zero Knowledge E2EE File Sharing")
st.markdown("A highly secure, End-to-End Encrypted file sharing platform. Only you and your recipient hold the keys!")

# --- AUTH WALL ---
if not st.session_state.access_token:
    st.info("Please login or register to access the secure platform.")
    tab1, tab2 = st.tabs(["Login", "Register"])

    # ----------------- TAB 1: LOGIN -----------------
    with tab1:
        st.header("Login")
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login"):
            try:
                resp = requests.post(f"{API_URL}/auth/login", data={"username": login_user, "password": login_pass}, timeout=10)
                if resp.status_code == 200:
                    token = resp.json().get("access_token")
                    st.session_state.access_token = token
                    st.session_state.username = login_user
                    
                    # Fetch Role from Token
                    decoded_payload = decode_jwt(token)
                    role = decoded_payload.get("role", "user")
                    st.session_state.role = role
                    
                    # Save to cookies
                    controller.set("access_token", token)
                    controller.set("username", login_user)
                    controller.set("role", role)
                    
                    st.success(f"Logged in successfully as {login_user}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except requests.exceptions.RequestException as e:
                st.error("Could not connect to the backend server. Please try again later.")
                st.toast("Connection Error", icon="🔌")

    # ----------------- TAB 2: REGISTER -----------------
    with tab2:
        st.header("Register")
        st.info("Registration generates a new 2048-bit RSA Key Pair. We only store your Public Key.")
        
        reg_user = st.text_input("Username", key="reg_user")
        reg_email = st.text_input("Email", key="reg_email")
        reg_pass = st.text_input("Password", type="password", key="reg_pass")
        
        if st.button("Register"):
            payload = {"username": reg_user, "email": reg_email, "password": reg_pass}
            try:
                resp = requests.post(f"{API_URL}/auth/register", json=payload, timeout=10)
                
                if resp.status_code == 201:
                    data = resp.json()
                    st.success(data["message"])
                    st.warning(data["instructions"])
                    
                    st.download_button(
                        label="Download Private Key (.pem)",
                        data=data["private_key"],
                        file_name=f"{reg_user}_private_key.pem",
                        mime="application/x-pem-file"
                    )
                else:
                    try:
                        st.error(resp.json().get("detail", "Registration failed"))
                    except ValueError:
                        st.error(f"Error from server: {resp.text}")
            except requests.exceptions.RequestException as e:
                st.error("Could not connect to the backend server for registration.")

else:
    # --- AUTHENTICATED STATE: SIDEBAR NAVIGATION ---
    st.sidebar.title(f"Welcome, {st.session_state.username}!")
    st.sidebar.write(f"**Role:** {st.session_state.role.capitalize()}")
    st.sidebar.divider()
    
    # Establish Navigation Options Based on Role
    nav_options = ["Share a File", "Secure Inbox"]
    
    if st.session_state.role == "admin":
        nav_options.append("Admin Dashboard")
        
    choice = st.sidebar.radio("Navigation", nav_options)
    
    st.sidebar.divider()
    if st.sidebar.button("Logout"):
        st.session_state.access_token = None
        st.session_state.username = None
        st.session_state.role = None
        
        # Remove cookies
        controller.remove("access_token")
        controller.remove("username")
        controller.remove("role")
        st.rerun()

    # ----------------- PAGE: SEND FILE -----------------
    if choice == "Share a File":
        st.header("Securely Share a File")
        
        try:
            users_resp = requests.get(f"{API_URL}/users", headers=get_auth_headers(), timeout=10)
            if users_resp.status_code == 401:
                st.session_state.access_token = None
                controller.remove("access_token")
                st.toast("Session expired. Please log in again.", icon="⏰")
                st.rerun()
            elif users_resp.status_code == 200:
                users = users_resp.json()
                user_options = {u["username"]: (u["id"], u["public_key"]) for u in users if u["username"] != st.session_state.username}
            else:
                st.error("Failed to load users.")
                user_options = {}
        except requests.exceptions.RequestException:
            st.error("Failed to connect to the backend.")
            user_options = {}

        if user_options:
            
            selected_user = st.selectbox("Select Recipient", [""] + list(user_options.keys()))
            file_to_send = st.file_uploader("1. Choose a file to send")
            sender_private_key_file = st.file_uploader("2. Upload your Private Key (.pem) for Digital Signing", type=["pem"])
            
            if st.button("Encrypt & Send") and file_to_send and sender_private_key_file and selected_user:
                receiver_id, receiver_pub_key_pem = user_options[selected_user]
                file_data = file_to_send.read()
                
                try:
                    sender_private_key = RSA.import_key(sender_private_key_file.read())
                    receiver_public_key = RSA.import_key(receiver_pub_key_pem)
                    
                    # 1. Generate AES-256 session key
                    session_key = get_random_bytes(32)
                    
                    # 2. Encrypt the file using AES-GCM
                    cipher_aes = AES.new(session_key, AES.MODE_GCM)
                    ciphertext, tag = cipher_aes.encrypt_and_digest(file_data)
                    encrypted_file_blob = cipher_aes.nonce + tag + ciphertext
                    
                    # 3. Encrypt the AES session key using Recipient's RSA Public Key
                    cipher_rsa = PKCS1_OAEP.new(receiver_public_key)
                    encrypted_aes_key = cipher_rsa.encrypt(session_key)
                    
                    # 4. Digital Signature
                    file_hash = SHA256.new(encrypted_file_blob)
                    signature = pkcs1_15.new(sender_private_key).sign(file_hash)
                    
                    enc_aes_key_b64 = base64.b64encode(encrypted_aes_key).decode('utf-8')
                    signature_b64 = base64.b64encode(signature).decode('utf-8')
                    
                    files = {"file": (file_to_send.name, encrypted_file_blob, "application/octet-stream")}
                    data = {
                        "receiver_id": receiver_id,
                        "encrypted_aes_key": enc_aes_key_b64,
                        "digital_signature": signature_b64,
                        "filename": file_to_send.name
                    }
                    
                    try:
                        resp = requests.post(f"{API_URL}/files/share", headers=get_auth_headers(), data=data, files=files, timeout=10)
                        if resp.status_code == 401:
                            st.session_state.access_token = None
                            controller.remove("access_token")
                            st.toast("Session expired. Please log in again.", icon="⏰")
                            st.rerun()
                        elif resp.status_code == 200:
                            st.success("File encrypted, digitally signed, and securely sent!")
                        else:
                            st.error(f"Server error: {resp.text}")
                    except requests.exceptions.RequestException:
                        st.error("Network error while sending the file.")
                except Exception as e:
                    st.error(f"Encryption failed. Did you upload the correct Private Key? Error: {str(e)}")

    # ----------------- PAGE: INBOX -----------------
    elif choice == "Secure Inbox":
        st.header("Your Secure Inbox")
        
        try:
            resp = requests.get(f"{API_URL}/files/shared", headers=get_auth_headers(), timeout=10)
            if resp.status_code == 401:
                st.session_state.access_token = None
                controller.remove("access_token")
                st.toast("Session expired. Please log in again.", icon="⏰")
                st.rerun()
            elif resp.status_code == 200:
                shared_files = resp.json()
                if not shared_files:
                    st.info("No files shared with you yet.")
            else:
                st.error("Failed to fetch shared files.")
                shared_files = []
        except requests.exceptions.RequestException:
            st.error("Failed to fetch shared files (Check Server Connection).")
            shared_files = []
        
        if shared_files:
            
            for index, sf in enumerate(shared_files):
                with st.expander(f"📁 {sf['filename']} (From: {sf['sender_username']})"):
                    receiver_priv_key_file = st.file_uploader(f"Upload your Private Key to Decrypt", type=["pem"], key=f"key_{sf['share_id']}_{index}")
                    
                    if st.button("Verify Signature & Decrypt", key=f"btn_{sf['share_id']}_{index}") and receiver_priv_key_file:
                        try:
                            dl_resp = requests.get(f"{API_URL}/files/download/{sf['share_id']}", headers=get_auth_headers(), timeout=15)
                            
                            if dl_resp.status_code == 401:
                                st.session_state.access_token = None
                                controller.remove("access_token")
                                st.toast("Session expired. Please log in again.", icon="⏰")
                                st.rerun()
                            elif dl_resp.status_code == 200:
                                payload = dl_resp.json()
                            
                                try:
                                    enc_file_blob = base64.b64decode(payload["encrypted_file_blob"])
                                    enc_aes_key = base64.b64decode(payload["encrypted_aes_key"])
                                    signature = base64.b64decode(payload["digital_signature"])
                                    
                                    sender_pub_key = RSA.import_key(payload["sender_public_key"])
                                    receiver_priv_key = RSA.import_key(receiver_priv_key_file.read())
                                    
                                    # 1. Verify Digital Signature
                                    file_hash = SHA256.new(enc_file_blob)
                                    pkcs1_15.new(sender_pub_key).verify(file_hash, signature)
                                    st.success("✅ Digital Signature Verified! The file originates from the true sender and hasn't been tampered with.")
                                    
                                    # 2. Decrypt AES Key
                                    cipher_rsa = PKCS1_OAEP.new(receiver_priv_key)
                                    session_key = cipher_rsa.decrypt(enc_aes_key)
                                    
                                    # 3. Decrypt the File
                                    nonce = enc_file_blob[:16]
                                    tag = enc_file_blob[16:32]
                                    ciphertext = enc_file_blob[32:]
                                    
                                    cipher_aes = AES.new(session_key, AES.MODE_GCM, nonce=nonce)
                                    decrypted_data = cipher_aes.decrypt_and_verify(ciphertext, tag)
                                    
                                    st.success("✅ File Decrypted Successfully!")
                                    st.download_button(
                                        label="⬇️ Download Original File",
                                        data=decrypted_data,
                                        file_name=payload["filename"],
                                        mime="application/octet-stream",
                                        key=f"dl_{sf['share_id']}_{index}"
                                    )
                                    
                                except (ValueError, TypeError) as e:
                                    st.error("🚨 TAMPER WARNING OR WRONG KEY! Signature Verification or Decryption failed.")
                                    st.error(f"Details: {str(e)}")
                            
                                except Exception as e:
                                    st.error(f"An unexpected error occurred: {str(e)}")
                            else:
                                st.error("Failed to download payload from server.")
                        except requests.exceptions.RequestException:
                            st.error("Network error while downloading the file.")

    # ----------------- PAGE: ADMIN DASHBOARD -----------------
    elif choice == "Admin Dashboard":
        # Additional safety check (Frontend validation)
        if st.session_state.role != "admin":
            st.error("You are not authorized to view this page.")
        else:
            st.header("Security & Audit Dashboard")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Global Statistics")
                if st.button("Refresh Stats", key="refresh_stats"):
                    try:
                        stats_resp = requests.get(f"{API_URL}/admin/stats", headers=get_auth_headers(), timeout=10)
                        if stats_resp.status_code == 401:
                            st.session_state.access_token = None
                            controller.remove("access_token")
                            st.toast("Session expired. Please log in again.", icon="⏰")
                            st.rerun()
                        elif stats_resp.status_code == 200:
                            stats = stats_resp.json()
                            c1, c2 = st.columns(2)
                            c1.metric("Registered Users", stats["total_users"])
                            c2.metric("Total Encrypted Files", stats["total_files"])
                            
                            c3, c4 = st.columns(2)
                            c3.metric("Active Shares", stats["total_shares"])
                            c4.metric("Total Actions", stats["total_actions"])
                        else:
                            st.error("Stats disabled for regular users or server error.")
                    except requests.exceptions.RequestException:
                        st.error("Failed to connect to the backend server to refresh stats.")
            
            with col2:
                st.subheader("Server File Integrity Matcher")
                st.info("Scan physical server blobs against their initial upload database hashes to detect backend server tampering.")
                if st.button("Run Deep Integrity Check"):
                    try:
                        int_resp = requests.get(f"{API_URL}/admin/integrity-check", headers=get_auth_headers(), timeout=30)
                        if int_resp.status_code == 401:
                            st.session_state.access_token = None
                            controller.remove("access_token")
                            st.toast("Session expired. Please log in again.", icon="⏰")
                            st.rerun()
                        elif int_resp.status_code == 200:
                            report = int_resp.json()
                            st.write(f"**Total Files Checked Server-Side:** {report['total_files']}")
                            
                            if report['compromised_files']:
                                st.error(f"🚨 ALERT: {len(report['compromised_files'])} file(s) corrupted or modified at rest!")
                                st.json(report['compromised_files'])
                            else:
                                st.success("✅ Safe: All physical files perfectly match their un-tampered encrypted states.")
                        else:
                            st.error(f"Integrity check failed. Unauthorized. ({int_resp.status_code})")
                    except requests.exceptions.RequestException:
                         st.error("Failed to connect to the backend server to run integrity check.")
                        
            st.divider()
            st.subheader("System Audit Logs")
            if st.button("Load Recent Audit Trail"):
                try:
                    logs_resp = requests.get(f"{API_URL}/admin/logs?limit=50", headers=get_auth_headers(), timeout=10)
                    if logs_resp.status_code == 401:
                        st.session_state.access_token = None
                        controller.remove("access_token")
                        st.toast("Session expired. Please log in again.", icon="⏰")
                        st.rerun()
                    elif logs_resp.status_code == 200:
                        logs = logs_resp.json()
                        if logs:
                            df = pd.DataFrame(logs)
                            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                            st.dataframe(df[['timestamp', 'action', 'user_id']], use_container_width=True)
                        else:
                            st.info("No logs present.")
                    else:
                        st.error("Failed to load audit trail.")
                except requests.exceptions.RequestException:
                    st.error("Failed to connect to the backend server to load logs.")
