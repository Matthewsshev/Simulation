import csv
import argparse
def read_csv(path):
    with open(f'Simulation_Temp/{path}.csv', newline='', encoding='utf-8') as f:
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

def parse_args():
    # Define argument parser
    parser = argparse.ArgumentParser()
    # Add argument for standard file
    parser.add_argument('-s', type=str, default='modular_test')
    # Add argument for new modified file, that needs to be compared
    parser.add_argument('-m', type=str, default='test_changes')
    return parser.parse_args()

def main():
    args = parse_args()
    new_file_for_comparison = args.m
    old_file_to_compare_with = args.s

    result = compare_files(new_file_for_comparison, old_file_to_compare_with)
    if result:
        print('All tests passed ✅')
    else:
        print('Some tests failed ❌')

if __name__ == '__main__':
    main()
