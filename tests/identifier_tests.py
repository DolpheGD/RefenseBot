from bot.helpers.slur_identifier import identify_slurs


if __name__ == "__main__":
    test_text = "test"
    while test_text:
        test_text = input("Enter a message to identify slurs in: ")
        result = identify_slurs(test_text)
        print(result)