import streamlit as st
import os
import shutil
from pathlib import Path
import time
import json

# ロックファイルのパス
LOCK_FILE = "file_manager_lock.json"

def acquire_lock(user_id):
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, 'r') as f:
            lock_data = json.load(f)
        if time.time() - lock_data['timestamp'] < 300:  # 5分のタイムアウト
            return False
    
    with open(LOCK_FILE, 'w') as f:
        json.dump({"user_id": user_id, "timestamp": time.time()}, f)
    return True

def release_lock(user_id):
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE, 'r') as f:
            lock_data = json.load(f)
        if lock_data['user_id'] == user_id:
            os.remove(LOCK_FILE)

def list_files(directory):
    files = []
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            files.append(f"📁 {item}")
        else:
            files.append(f"📄 {item}")
    return files

def main():
    st.title("Simple File Manager with Lock")

    # ユーザーIDの生成（実際のアプリケーションでは認証システムを使用）
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(time.time())

    # ロックの取得を試みる
    if acquire_lock(st.session_state.user_id):
        st.success("You have exclusive access to the file manager.")
        
        # 以下、通常のファイルマネージャーの機能
        if 'current_path' not in st.session_state:
            st.session_state.current_path = os.getcwd()

        st.write(f"Current Directory: {st.session_state.current_path}")

        files = list_files(st.session_state.current_path)
        selected_file = st.selectbox("Select a file or directory:", files)

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Open"):
                if selected_file.startswith("📁"):
                    new_path = os.path.join(st.session_state.current_path, selected_file[2:])
                    st.session_state.current_path = new_path
                    st.experimental_rerun()
                elif selected_file.startswith("📄"):
                    file_path = os.path.join(st.session_state.current_path, selected_file[2:])
                    with open(file_path, "r") as f:
                        content = f.read()
                    st.text_area("File Content", content, height=300)

        with col2:
            if st.button("Delete"):
                if selected_file:
                    file_path = os.path.join(st.session_state.current_path, selected_file[2:])
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                    st.success(f"Deleted: {selected_file}")
                    st.experimental_rerun()

        with col3:
            if st.button("Go Up"):
                st.session_state.current_path = str(Path(st.session_state.current_path).parent)
                st.experimental_rerun()

        uploaded_file = st.file_uploader("Upload a file", type=["txt", "pdf", "png", "jpg", "jpeg", "py"])
        if uploaded_file is not None:
            file_path = os.path.join(st.session_state.current_path, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"File uploaded: {uploaded_file.name}")
            st.experimental_rerun()

        if st.button("Release Lock"):
            release_lock(st.session_state.user_id)
            st.experimental_rerun()

    else:
        st.error("The file manager is currently in use by another user. Please try again later.")

if __name__ == "__main__":
    main()