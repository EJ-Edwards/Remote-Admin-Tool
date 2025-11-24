





def menu() -> None:
    print(TERMS)
    accept = input("Do you accept these Terms and Conditions? (y/n): ").strip().lower()
    if accept != "y":
        print("You must accept the Terms and Conditions to use Sentinal Link")
        return