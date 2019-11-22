from timeit import timeit
import garage_np as grg
import server as s

# [indx_handi, indx_small, indx_large] = range(nspace_types) # array indices for each type of space
# print(nHan, nSm, nLg)

level, row, space = None, None, None
handicapped, large_car = False, False
_, nSm, nLg = [len(t) for t in grg.Parking().cars]
nPark = nSm

def park_all_small():
    global level, row, space
    p = grg.Parking() # Python3: allocation takes <3% of calc time
    # for _ in range(nSm + nLg):
    for _ in range(nPark):
        try:
            i_set, i_slot = p.assign_space(handicapped, large_car)
            if get_level_row_space:
                level, row, space = grg.toLevel_Row_Space(i_set, i_slot)
        except Exception as e:
            # error, unable to allocate space
            print("Error:", e)


n_test = 10000
def time_park():
    global get_level_row_space, grg
    get_level_row_space = False
    print("Parking: 'allocation only' {:.2f}us".format(timeit(park_all_small, number=n_test)*1e6/n_test/nPark))
    grg.skip_lookup = True
    print("Parking: 'allocation w/o table lookup' {:.2f}us".format(timeit(park_all_small, number=n_test)*1e6/n_test/nPark))
    get_level_row_space = True
    grg.skip_lookup = False
    print("Parking: 'allocation + decode {:.2f}us".format(timeit(park_all_small, number=n_test)*1e6/n_test/nPark))
time_park()

grg.skip_lookup = False
def time_validate_park():
    global s
    # Allocate empty parking data structure
    s.parking = grg.Parking() # use garage_np.py
    params = {b'size': b'compact_car', b'has_handicapped_placard':b'0'}
    for _ in range(nPark):
        try:
            v = s.validate_park(params)
        except Exception as e:
            print(e)
print("Parking: 'total parking' {:.2f}us".format(timeit(time_validate_park, number=n_test)*1e6/n_test/nPark))

