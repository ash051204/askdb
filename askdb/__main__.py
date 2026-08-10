import argparse

from askdb.pipeline import answer, format_results


def main():
    parser = argparse.ArgumentParser(prog="askdb")
    parser.add_argument("question", help="Question to ask the database")
    args = parser.parse_args()

    sql, columns, rows, error = answer(args.question)

    print(sql)
    print(format_results(columns, rows))
    if error is not None:
        print(error)


if __name__ == "__main__":
    main()
