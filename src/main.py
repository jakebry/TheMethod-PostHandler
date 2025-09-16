from src.scraper import scrape_and_store_posts
from src.method_tracker import log_method_working, log_method_stopped
from src.console_anim import Spinner
from src.service_role_setup import initialize_service_role
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(message)s")

RUN_SEQ_DIR = "/app/.cache/run_state"
RUN_SEQ_PATH = os.path.join(RUN_SEQ_DIR, "run_seq.txt")


def _next_run_seq() -> int:
    try:
        os.makedirs(RUN_SEQ_DIR, exist_ok=True)
        if os.path.exists(RUN_SEQ_PATH):
            with open(RUN_SEQ_PATH, "r", encoding="utf-8") as f:
                val = f.read().strip()
                seq = int(val) if val else 0
        else:
            seq = 0
        seq += 1
        with open(RUN_SEQ_PATH, "w", encoding="utf-8") as f:
            f.write(str(seq))
        return seq
    except Exception:
        # Fallback: return a synthetic sequence ID
        return 0


def main():
    run_seq = _next_run_seq()
    if run_seq:
        print(f"[RUNSEQ {run_seq}] START", flush=True)

    # Initialize service role key for database trigger authentication
    print("Initializing service role key for database trigger...", flush=True)
    if not initialize_service_role():
        print("❌ Failed to initialize service role key. Exiting.", flush=True)
        if run_seq:
            print(f"[RUNSEQ {run_seq}] ERROR: service-role-init", flush=True)
        return
    
    spinner = Spinner("Scraping threads and storing in Supabase")
    spinner.start()
    try:
        # Attempt to scrape posts
        method_working = scrape_and_store_posts()
        
        if method_working:
            # Method is working - update the working status
            log_method_working()
            print("Method is working - successfully extracted posts.", flush=True)
        else:
            # Method failed - mark it as stopped
            log_method_stopped()
            print("Method stopped - no posts could be extracted.", flush=True)
            if run_seq:
                print(f"[RUNSEQ {run_seq}] ERROR: no-posts", flush=True)
                
    except Exception as e:
        print(f"Error: {e}", flush=True)
        # Method failed due to exception - mark it as stopped
        log_method_stopped()
        if run_seq:
            print(f"[RUNSEQ {run_seq}] ERROR: exception", flush=True)
        return
    finally:
        spinner.stop()

    print("Scraping process completed.", flush=True)
    if run_seq:
        print(f"[RUNSEQ {run_seq}] END", flush=True)

if __name__ == "__main__":
    try:
        main()
        print("[END] Scraper finished", flush=True)
    except KeyboardInterrupt:
        print("[INFO] Received SIGINT (KeyboardInterrupt), shutting down gracefully.", flush=True)
