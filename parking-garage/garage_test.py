# Convert curl syntax to Python, Ansible URI, Node.js, R, PHP, Strest, Go, Dart, JSON, Rust
#   https://curl.trillworks.com/#python

import requests

# Unpark non-existant car
unpark = {'level': '1', 'row': '1', 'space': '0'}
response = requests.post('http://127.0.0.1:8080/unpark', data=unpark)
print(response.status_code, response.json()) # requests.models.Response
# assert response.status_code = 412

# Park cars with handicapped placards
park = {'size': 'compact_car', 'has_handicapped_placard': '1'}
for _ in range(101):
    response = requests.post('http://127.0.0.1:8080/park', data=park)
    print(response.status_code, response.json())
    # assert response.status_code = 200

# Car should be parked in large space (closer than small space) on level 2
status = response.json
# assert status[b'level'] == 2

# Next small space is on level 3
small = {'size': 'small_car', 'has_handicapped_placard': '0'}
response = requests.post('http://127.0.0.1:8080/park', data=small)
print(response.status_code, response.json())
# assert status[b'level'] == 3

# Park large cars
park = {'size': 'large_car', 'has_handicapped_placard': '0'}
for _ in range(79):
    response = requests.post('http://127.0.0.1:8080/park', data=park)
    print(response.status_code, response.json())
print(response.status_code, response.json())
# Large spaces full
# assert response.status_code = 406

# Unpark large car
unpark = {'level': '3', 'row': '8', 'space': '10'}
response = requests.post('http://127.0.0.1:8080/unpark', data=unpark)
print(response.status_code, response.json()) # requests.models.Response

# Park large car
response = requests.post('http://127.0.0.1:8080/park', data=park)
print(response.status_code, response.json())
# assert response.status_code = 200
