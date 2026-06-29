import random
balance = random.randint(0, 1000000)  # create once
print("Please enter 4 digit PIN code")
pin_code = input()
if pin_code == "1234":
 print("PIN code is correct")
if pin_code != "1234":
    print("PIN code is not correct")
    exit()
print("1. Withdraw")
print("2. Deposit")
print("3. Check Balance")
print("4. Exit")
choose = input("Enter your choice: ")
if choose == "1":
    amount = int(input("How much to withdraw: "))
    balance: int = random.randint(0, 1000000)
    if amount > balance:
        print("Amount can't be higher than balance")
        exit()
    if amount < 0:
        print("Amount can't be lower than 0")
        exit()
    balance -= amount
    print("Withdrawn:"  +  str(amount)+"$" + "You're left with " +  str(balance)+"$")
    exit()
if choose == "2":
    amount = int(input("How much to deposit: "))
    print("You deposited " + str(amount)+"$")
    print("Your new balance is " + str(balance)+"$")
    if amount < 0:
        print("Amount can't be lower than 0")
    elif amount > 10000000000:
        print("Amount can't be higher than 10000000000")
        exit()
if choose == "3":
    print("Your balance is " + str(balance) +"$")
    exit()
if choose == "4":
    exit()



















































