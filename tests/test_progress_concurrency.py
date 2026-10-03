import threading
import time
import pytest
from services import progress_service

def test_progress_service_state_concurrency():
    # Setup initial run
    progress_service.mulai(50, target_subfolder="input1")
    
    # Read state immediately
    state = progress_service.ambil_progress()
    assert state["status"] == "RUNNING"
    assert state["total"] == 50
    assert state["target_subfolder"] == "input1"
    assert state["selesai"] == 0

    # Simulate heavy concurrent reading (like client polling /progress)
    stop_poll = threading.Event()
    read_errors = []

    def poller():
        while not stop_poll.is_set():
            p = progress_service.ambil_progress()
            # Under concurrency, total should NEVER be 0 once started with 50
            if p["status"] == "RUNNING" and p["total"] != 50:
                read_errors.append(f"Invalid total observed: {p}")
            if p["status"] == "RUNNING" and p["target_subfolder"] != "input1":
                read_errors.append(f"Invalid target_subfolder observed: {p}")
            time.sleep(0.001)

    t = threading.Thread(target=poller)
    t.start()

    # Simulate engine updating files rapidly
    for i in range(1, 51):
        progress_service.update_file_and_progress(f"doc_{i}.pdf", i)
        time.sleep(0.002)

    stop_poll.set()
    t.join()

    # Complete the process
    progress_service.selesai(jumlah_selesai=50)

    final_state = progress_service.ambil_progress()
    assert final_state["status"] == "FINISHED"
    assert final_state["persen"] == 100
    assert final_state["selesai"] == 50
    assert final_state["total"] == 50
    assert final_state["target_subfolder"] == "input1"
    assert len(read_errors) == 0, f"Read errors occurred during concurrency: {read_errors}"

def test_selesai_never_wipes_to_zero():
    progress_service.mulai(20, target_subfolder="sub_test")
    progress_service.update_progress(20)
    progress_service.selesai(jumlah_selesai=20)

    state = progress_service.ambil_progress()
    assert state["status"] == "FINISHED"
    assert state["selesai"] == 20
    assert state["total"] == 20

def test_selesai_recovers_if_total_was_zero():
    # If engine started with 0 and completed 15 files
    progress_service.mulai(0, target_subfolder="batch_sub")
    progress_service.update_file_and_progress("sample.pdf", 15)
    progress_service.selesai(jumlah_selesai=15)

    state = progress_service.ambil_progress()
    assert state["status"] == "FINISHED"
    assert state["selesai"] == 15
    assert state["total"] == 15
    assert state["persen"] == 100
    assert state["target_subfolder"] == "batch_sub"
