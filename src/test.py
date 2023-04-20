
class Bear():
    def eat(self):
        print("bear is eating")


class Dog():
    def eat(self):
        print("dog is eating")


l = [Dog(), Bear()]

for animal in l:
    animal.eat()