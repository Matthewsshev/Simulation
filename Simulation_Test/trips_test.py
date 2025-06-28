import csv

def read_csv(path):
    with open(f'Simulation_Temp/{path}', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # Convert each row to a tuple of key-value pairs, sorted by key
        return sorted(tuple(sorted(row.items())) for row in reader)

def compare_files(file1, file2):
    rows1 = read_csv(file1)
    rows2 = read_csv(file2)

    if rows1 == rows2:
        return True
    else:
        return False


def main():
    new_file_for_comparison = 'modular_test.csv'
    old_file_to_compare_with = 'test_changes.csv'

    result = compare_files(new_file_for_comparison, old_file_to_compare_with)
    if result:
        print('All tests passed ✅')
    else:
        print('Some tests failed ❌')

if __name__ == '__main__':
    main()
