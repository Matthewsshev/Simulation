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
        return True, [], []  # Files are identical, no differences
    else:
        # Convert lists of tuples to sets for efficient difference finding
        set1 = set(rows1)
        set2 = set(rows2)

        # Find rows unique to each file
        diff_in_file1 = sorted(list(set1 - set2))  # Rows present in file1 but not file2
        diff_in_file2 = sorted(list(set2 - set1))  # Rows present in file2 but not file1

        return False, diff_in_file1, diff_in_file2

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

    result, diff_in_new, diff_in_old = compare_files(new_file_for_comparison, old_file_to_compare_with)
    if result:
        print('All tests passed ✅ - Files are identical.')
    else:
        print('Some tests failed ❌ - Files are different.')
        if diff_in_new is None and diff_in_old is None:
            print("Comparison could not be performed due to file reading errors.")
        else:
            quit()
            if diff_in_new:
                print(f"\n--- Rows unique to '{new_file_for_comparison}' (not in '{old_file_to_compare_with}') ---")
                for i, row in enumerate(diff_in_new):
                    print(f"  Row {i + 1}: {dict(row)}")  # Convert tuple back to dict for readability
            else:
                print(f"\n--- No unique rows found in '{new_file_for_comparison}' ---")

            if diff_in_old:
                print(f"\n--- Rows unique to '{old_file_to_compare_with}' (not in '{new_file_for_comparison}') ---")
                for i, row in enumerate(diff_in_old):
                    print(f"  Row {i + 1}: {dict(row)}")  # Convert tuple back to dict for readability
            else:
                print(f"\n--- No unique rows found in '{old_file_to_compare_with}' ---")


if __name__ == '__main__':
    main()


