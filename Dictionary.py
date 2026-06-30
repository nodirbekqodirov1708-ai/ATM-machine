products = {
    'laptop': 1200,
    'mouse': 25,
    'keyboard': 50,
    'monitor': 300,
    'headphones': 80
}

item = products['laptop']
print(f"The laptop costs ${item}")



customer = {
    'name':'john smith',
    'age':28,
    'city':'new york'
}

print(f"{customer['name'].title()},\
 lives in {customer['city'].title()},\
 and is {customer['age']} years old")



employee = {}
employee['name'] = 'michael brown'
employee['position'] = 'manager'
employee['salary'] = 4500

print(employee)
print(f"Employee {employee['name'].title()} works as a {employee['position'].title()}")



student = {
    'name':'emma wilson',
    'age':21,
    'grade':'A'
}

print(student)
del student['grade']
print(student)



devices = {
    'john':'iphone 16',
    'mike':'galaxy s24',
    'sarah':'pixel 9',
    'anna':'oneplus 13'
}

phone = devices['john']
print(f"John's phone is {phone}")



book = {
    'title':'python basics',
    'author':'james smith',
    'pages':350,
    'year':2024
}

print(book.items())

for key, value in book.items():
    print(f"Key: {key}")
    print(f"Value: {value}\n")



products = {
    'laptop':1200,
    'mouse':25,
    'keyboard':50,
    'monitor':300,
    'headphones':80
}

print(products.keys())

print("Products in the store:")
for product in products.keys():
    print(product.title())

