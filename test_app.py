from app import app

with app.test_client() as client:
    response = client.get('/')
    print('Status:', response.status_code)
    print('Data length:', len(response.data))
    if response.status_code != 200:
        print('Error:', response.data.decode())
