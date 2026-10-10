from app.calculations import add, BankACC, InsufficientFunds
import pytest

@pytest.mark.parametrize("num1, num2, expected", [
    (3,2,5),
    (-6,5,-1),
    (-2,-6,-8)
])
def test_add(num1, num2, expected):
    print("testing add")
    assert add(num1,num2) == expected 

#FIXTURES helps in minimizing repeated code duplication, for eg instantiating BankACC here
@pytest.fixture
def zero_bank_acc():
      return BankACC() #starting_balance is set to zero

@pytest.fixture
def bank_acc():
      return BankACC(50) #starting_balance is set 50


def test_zero_bank_amt(zero_bank_acc):
      assert zero_bank_acc.balance == 0

def test_bank_set_amt(bank_acc): #the arg bank_amt here references to the bank_amt fixture defined above
     assert bank_acc.balance == 50 #the referenced fixture can be used as instance of bank acc

def test_deposit(bank_acc):
     assert bank_acc.deposit(50) == 100

def test_deposit(bank_acc):
     assert bank_acc.withdraw(20) == 30  

def test_collect_interest(bank_acc):
     #rounding off upto precision 6, cuz collect_interest() returns 55.00000000000001 which is not 55
     assert round(bank_acc.collect_interest(),6) == 55 #interest rate is 10%

@pytest.mark.parametrize("deposited, withdrew, rem_balance, balance_after_interest", [
    (200,100,100,110),
    (50,10,40,44)
])
#parameterize passes args as kwargs, so order of args doesnt matter but every parameters defined in decorator must be passed as args in test fn
def test_tx(zero_bank_acc, withdrew, deposited, rem_balance, balance_after_interest): 
     zero_bank_acc.deposit(deposited)
     zero_bank_acc.withdraw(withdrew)

     #u can write multiple asserts but NOTE: if one assert throws err, all asserts after that assert wont even run, 
     # this can hide the other tests, so use multiple asserts only if their goals are related to each other
     assert zero_bank_acc.balance == rem_balance
     assert round(zero_bank_acc.collect_interest(),6) == balance_after_interest 

def test_insufficient_funds(zero_bank_acc):
     #withdraw() has Exception defined, so even Exceptions will make test fail
     #so to let pytest know its supposed to receive Exception and dont make tests fail, then we use:
    #  with pytest.raises(Exception): #NOTE: if the withdraw() hasnt Exception defined then it will throw err as well cuz pytest.raises is expecting Exception here
    #     zero_bank_acc.deposit(40)
    #     zero_bank_acc.withdraw(50)

    #if the exception raised is exactly the exception we are expecting OR if it is inherited child of the exception we are expecting then test passes
    #thats why its recommended to use more specific exception than using General Exception
    with pytest.raises(InsufficientFunds): #note if the withdraw() hasnt Exception defined then it will throw err as well cuz pytest.raises is expecting Exception here
            zero_bank_acc.deposit(40)
            zero_bank_acc.withdraw(50)