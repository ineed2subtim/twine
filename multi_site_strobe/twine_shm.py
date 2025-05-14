import time
import random
import pw_logging as log
from multiprocessing import shared_memory

def create_sharedmem(shm_name="SynchTwine_SU"):
    rand_num = random.randrange(100)
    cacheline_bytes = 8
    new_shm_name = shm_name + str(rand_num)
    shm_p = shared_memory.SharedMemory(create=True, size=cacheline_bytes, name=new_shm_name)
    return new_shm_name, shm_p

def remove_sharedmem(shm_p):
    shm_p.close()
    #time.sleep(5)
    #shm_p.unlink()
    return

def synch_twine(action, shm_p, timeout=1000):
    if not shm_p:
        log.log(log.INFO, "Cannot synch. Could not create shared memory")
        return
    action_len = len(action)
    print(type(action_len))
    time_limit = timeout #Exit while loop after time_limit seconds
    time_diff = 0
    twine_ready = "stub"
    time_start = time.time()  # Update start time

    log.log(log.DEBUG, f"twine_ready : {twine_ready}")
    while (twine_ready != action and time_diff < time_limit ):
        action_ba = bytearray(action, 'utf-8')
        if (len(shm_p.buf) > 0 and bytes(shm_p.buf[:action_len]) == action_ba):
            twine_ready = action
            log.log(log.INFO, f"Exiting synch_twine due to sharedmemory signal, time_diff is {time_diff}")
            return
        time_curr = time.time()  # Update current time
        time_diff = time_curr - time_start
        # Reset filepointer to the beginning of file
        time.sleep(20)
    log.log(log.INFO, f"Exiting due to time_diff {time_diff}")
    return
