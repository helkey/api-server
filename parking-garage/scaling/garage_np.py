import math
from numba import jit
import numpy as np
import time

"""
This class contains the state of the parking garage (which spaces are allocated, starting what time...).

All thread-unsafe memory should be contained within only this class. In a high-throughput operation 
  (although this simple example isn't), this class would be a single-thread bottleneck and should be 
  designed to run as fast as possible.

Consequently, this class contains only linear arrays for each space type 
  (handicapped / small / large), with the most desireable spaces listed first 
  to make allocation quick and easy.

Other functions such as coding/decoding of level/space number and price calculations 
  happen separately from this core state information, and can be multi-threaded.
"""

rate_handi = 5    # $/hr
rate_compact = 5  # $/hr
rate_large = 7.5  # $/hr
t_round = 3       # round elapsed time up to nearest 3 sec
c_round = 0.01 # round cost up to nears $0.01
                  
def parking_amount(car_type, slot_type, time_start, time_stop):
    toMin = 60.
    toHr = 60.
    rate = rate_handi if (car_type == indx_handi) else (
        (rate_compact, rate_large)[slot_type == indx_large])
    t_elapsed = time_stop - time_start
    t_charge = math.ceil(t_elapsed / t_round) * t_round
    t_hr = t_charge / toMin / toHr # elapsed time (hours)
    if t_hr < 0:
        raise Exception("Invalid parking time")
    amount_raw = t_hr * rate
    amount_charged = math.ceil(amount_raw / c_round) * c_round
    if amount_charged < 0:
        raise Exception("Parking amount must not be negative")
    # Make really sure not to allow negative amounts
    return max(amount_charged, 0)
# print(parking_cost(indx_handi, indx_handi, 0., 3595.)) # $5


# n_levels = 3
nspace_types = 3              # spaces: reserved, small, large
nrows_per_level = [6, 8, 8]   # redundant info - calculate or use as consistancy check
nrows_handicapped = [2, 0, 0] # rows reserved for handicapped parking (large or small car)
nrows_small = [4, 4, 4]       # open rows for small cars
nrows_large = [0, 4, 4]       # open rows for large cars
nslots_per_row = 10

spaces_per_type = [nslots_per_row * sum(nrows) for nrows
           in [nrows_handicapped, nrows_small, nrows_large]]
total_spaces = sum(spaces_per_type)
[indx_handi, indx_small, indx_large] = range(nspace_types) # array indices for each type of space


# Generate mapping from level/row/slot to set/slot
def genSetSlot():
    # slots_next: next slot number for each parking slot type
    slots_next = [0 for _ in range(nspace_types)]
    setSlot = []
    # Iterate through levels
    for nrows_level in zip(nrows_handicapped, nrows_small, nrows_large):
        setSlotLevel = []
        # Iterate through rows
        for i_set, nrows in enumerate(nrows_level):
            if nrows != 0:
                # Iterate through types of rows
                for _ in range(nrows):
                    slot_start = slots_next[i_set]
                    # Iterate through slots in row
                    setSlotLevel.append([[i_set, slot_start + islot] for islot in range(nslots_per_row)])
                    slots_next[i_set] += nslots_per_row
                # print([[i_set, slot_start + i_slot] for i_slot in range(nslots_per_row)])
        setSlot.append(setSlotLevel)
    return setSlot
setSlot = genSetSlot()
# print(setSlot)


# Generate mapping from set/slot to level/row/slot
def genLevelRowSpace(setSlot):
    max_rows = max(sum(nrows_handicapped), sum(nrows_small), sum(nrows_large))
    LRS = [[None for _ in range(nslots_per_row * max_rows)] for _ in range(nspace_types)]
    for i_level, level in enumerate(setSlot):
        for i_row, row in enumerate(level):
            for i_sl, slot_arr in enumerate(row):
                i_set, i_slot = setSlot[i_level][i_row][i_sl]
                LRS[i_set][i_slot] = [i_level, i_row, i_sl]
    # Remove unallocated values
    LRS = [[slot for slot in set if slot != None] for set in LRS]
    return LRS
levelRowSpace = genLevelRowSpace(setSlot)
# print(levelRowSpace)

# Convert level/row/slot to i_set(type of space), i_slot(number)
def toSet_Slot(level, row, space):
    try:
        # Convert to 0-based level/row/space numbers
        i_set, i_slot = setSlot[level][row][space]
        return i_set, i_slot
    except:
        raise Exception("invalid level/row/space")

# Convert i_set(type of space), i_slot(number) to Level/Row/Space
def toLevel_Row_Space(i_set, i_slot):
    try:
        level, row, space = levelRowSpace[i_set][i_slot]
        return level, row, space
    except:
        raise Exception("invalid space/slot")
        
        
default_time = 0 # default time for unallocated parking slots
err = -1
class Parking:
    def __init__(self):
        # Array of start time per parking space
        # self.times = [[default_time for _ in range(spaces_per_type[indx])]
        #              for indx in range(nspace_types)]
        self.times = [np.zeros(spaces_per_type[indx], dtype=np.int) for indx in range(nspace_types)]
        # Array of car types per parking space (needed for cost calculation)
        self.cars = [np.zeros(spaces_per_type[indx], dtype=np.int) for indx in range(nspace_types)]
                
    # Assign parking space (if available)
    def assign_space(self, handicapped, large_car):
        time = time_sec()           # time in seconds
        if time == default_time:
            raise("Invalid time " + str(time))
        if handicapped:
            return self.alloc_handi_sp(time, large_car)
        # i_type: type of car parked
        i_type = (indx_small, indx_large)[large_car]
        return self.alloc_open_sp(time, large_car, i_type)

    # Allocate handicapped space
    def alloc_handi_sp(self, time, large_car):
        try:
            # Large or small cars fit in handicapped spaces
            i_set, i_slot  = self.alloc(time, indx_handi, indx_handi)
            return i_set, i_slot
        except:
            # Look in open spaces depending on car size
            if large_car:
                return self.alloc_open_sp(time, large_car, indx_handi)
            # For small cars w/handicap placard, choose closest open space
            try:
                slot_small = self.get_slot(indx_small)
            except:
                slot_small = err # no small slots available
            try:
                slot_large = self.get_slot(indx_large)
                if slot_small == err:
                    return self.alloc_open_sp(time, large_car, indx_handi)
            except:
                if slot_small == err:
                    raise Exception("Not avail") # no small or large spaces available
                
                else:
                    return self.alloc_open_sp(time, small_car, indx_handi) # no large spaces available
            floor_s, row_s, _ = levelRowSpace[indx_small][slot_small]
            floor_l, row_l, _ = levelRowSpace[indx_large][slot_large]
            chose_large = (floor_l < floor_s) or (
                (floor_l == floor_s) and (row_l < row_s))
            return self.alloc_open_sp(time, chose_large, indx_handi)
            
    # Allocate regular small or large space
    def alloc_open_sp(self, time, large_car, i_type):
        if not large_car:
            try:
                return self.alloc(time, indx_small, i_type)
            except:
                pass
        return self.alloc(time, indx_large, i_type)

    # Allocate parking space from particular set (handicapped, small car, large car)
    def alloc(self, time, i_set, i_type):
        try:
            i_slot = self.find_slot(i_set)
            self.times[i_set][i_slot] = time
            self.cars[i_set][i_slot] = i_type
            return i_set, i_slot
        except ValueError:
            raise Exception("Not avail")

    # Release parking space
    def release_space(self, i_set, i_slot):
        try:
            t_parked = self.times[i_set][i_slot]
            car_type = self.cars[i_set][i_slot]
        except:
            raise Exception("Illegal set/slot")
        if t_parked != default_time:
            self.times[i_set][i_slot]=default_time
            return t_parked, car_type
        raise Exception("Space empty")

    # Find empty space in array
    def find_slot(self, i_set):
        # Use Python arrays: return self.times[i_set].index(default_time)
        # Use numpy directly: np.where(self.times[i_set] == default_time)[0][0]
        if skip_lookup:
            return 1 # skip array lookup for profiling timing
        time_arr = self.times[i_set]
        return find_Slot(default_time, time_arr)
skip_lookup = False


@jit(nopython=True)
def find_Slot(val, arr_time):
    for i, v in enumerate(arr_time):
        if arr_time[i] == val:
            return i
    return err

# Get current system time in seconds
def time_sec():
    return time.time()

# Artificially add time to the clock to make testing easier
time_off = 0 # 3600 - add an hour for testing
def time_rec():
    return time.time() + time_off

    
# Test that convertion tables in both direction have the same number of elements
def test_table_len():
    lenLevelRowSpace = len([slot for set in levelRowSpace for slot in set])
    lenSetSlot = len([slot for level in setSlot for row in level for slot in row])
    print(lenSetSlot, lenLevelRowSpace)
    # assert lenSetSlot == lenLevelRowSpace
# test_table_len()




