import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class RestartHandler(FileSystemEventHandler):
    def __init__(self, command):
        self.command = command
        self.process = None
        self.restart()

    def restart(self):
        if self.process:
            self.process.terminate()  # 기존 프로세스 종료
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()

        print(f"\n[Watchdog] Restarting app due to changes...")
        # 새 프로세스 시작
        self.process = subprocess.Popen(self.command, shell=True)

    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            self.restart()

if __name__ == "__main__":
    # 프로젝트 루트(inline-hwp-ai)로 이동 후 실행한다고 가정
    # 감시 대상: gui, backend 폴더
    target_command = "python -m gui.app"
    
    print(f"[Watchdog] Watching for changes in .py files...")
    
    handler = RestartHandler(target_command)
    observer = Observer()
    
    # GUI 및 Backend 코드 변경 감시
    observer.schedule(handler, path="gui", recursive=True)
    observer.schedule(handler, path="backend", recursive=True)
    
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if handler.process:
            handler.process.terminate()
            
    observer.join()
