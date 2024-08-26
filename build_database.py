import streamlit as st
import time
import threading
import os
import json
import fcntl
from datetime import datetime

class SingletonThread:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SingletonThread, cls).__new__(cls)
                cls._instance.thread = None
        return cls._instance

    def start_thread(self, target):
        with self._lock:
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=target)
                self.thread.start()
                return True
        return False

singleton_thread = SingletonThread()

def file_is_locked(filepath):
    locked = None
    file_object = None
    if os.path.exists(filepath):
        try:
            file_object = open(filepath, 'a')
            fcntl.flock(file_object, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = False
        except IOError:
            locked = True
        finally:
            if file_object:
                fcntl.flock(file_object, fcntl.LOCK_UN)
                file_object.close()
    return locked

def save_state(state):
    with open('state.json', 'w') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        json.dump(state, f)
        fcntl.flock(f, fcntl.LOCK_UN)

def load_state():
    if os.path.exists('state.json'):
        with open('state.json', 'r') as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            state = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)
            return state
    return {'process_started': False, 'progress': 0}


def build_database():
    state = load_state()
    total_steps = 100
    for i in range(int(state['progress'] * total_steps), total_steps):
        time.sleep(0.5)
        state['progress'] = (i + 1) / total_steps
        state['last_updated'] = datetime.now().isoformat()
        save_state(state)
    state['process_started'] = False
    state['completed_at'] = datetime.now().isoformat()
    save_state(state)

def main():
    st.title("データベース構築プロセス")

    state = load_state()

    if not state['process_started']:
        if 'completed_at' in state and state['completed_at']:
            st.success(f"前回のデータベース構築は {state['completed_at']} に完了しました。")
        
        if st.button("データベース構築を開始"):
            if not file_is_locked('state.json'):
                if singleton_thread.start_thread(build_database):
                    state['process_started'] = True
                    state['progress'] = 0
                    state['started_at'] = datetime.now().isoformat()
                    save_state(state)
                    st.success("データベース構築プロセスを開始しました。")
                else:
                    st.warning("プロセスは既に実行中です。")
            else:
                st.warning("別のプロセスが実行中です。しばらくしてから再試行してください。")

    if state['process_started']:
        st.info(f"プロセスは {state['started_at']} に開始されました。")
        progress_bar = st.progress(state['progress'])
        status_text = st.empty()
        last_updated_text = st.empty()
        
        status_text.text(f"進捗状況: {state['progress']:.0%}")
        if 'last_updated' in state:
            last_updated_text.text(f"最終更新: {state['last_updated']}")

        if state['progress'] == 1:
            st.success(f"データベース構築が {state['completed_at']} に完了しました！")
            if st.button("状態をリセット"):
                state['process_started'] = False
                state['progress'] = 0
                state.pop('started_at', None)
                state.pop('completed_at', None)
                state.pop('last_updated', None)
                save_state(state)
                st.experimental_rerun()

    if state['process_started']:
        def update_progress():
            while state['process_started']:
                time.sleep(0.1)
                state = load_state()
                progress_bar.progress(state['progress'])
                status_text.text(f"進捗状況: {state['progress']:.0%}")
                if 'last_updated' in state:
                    last_updated_text.text(f"最終更新: {state['last_updated']}")
                if state['progress'] == 1:
                    break

        singleton_thread.start_thread(update_progress)

if __name__ == "__main__":
    main()