def add(a: int, b: int) -> int:
    return a + b

class InsufficientFunds(Exception):
    pass

class BankACC:
    def __init__(self, starting_balance=0):
        self.balance = starting_balance
    
    def deposit(self, amount):
        self.balance += amount
        return self.balance
    
    def withdraw(self, amount):
        #note if the Exception hasnt been defined here in withdraw() then it will make test fail cuz pytest.raises is expecting Exception in my_test.py
        if amount > self.balance:
            raise InsufficientFunds("Insufficient funds in bank account.")
        self.balance -= amount
        return self.balance

    def collect_interest(self):
        self.balance *= 1.1
        return self.balance