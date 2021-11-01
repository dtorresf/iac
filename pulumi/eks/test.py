public_cidr=["10.0.3.0/24","10.0.4.0/24"]

for index, cidr in enumerate(public_cidr, start=1):
	print(index)
	print(cidr)