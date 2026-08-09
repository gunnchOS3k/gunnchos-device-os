def add(a, b):
    return a + b

def test_add():
    assert add(1, 2) == 3

if __name__ == '__main__':
    test_add()
    print('ok')
